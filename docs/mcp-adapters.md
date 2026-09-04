---
title: USAP MCP Adapters (Phase 3)
description: Reference adapters that turn USAP's routing decisions into real downstream-MCP calls. Phase 3 ships fixture-mode adapters for Slack, GitHub, and Splunk; the four real-security MCPs (CrowdStrike, FortiGate, Okta, AWS Security Hub) stay declared-but-disabled until production-grade adapters land.
---

# USAP MCP Adapters (Phase 3)

Phase 3 closes the loop: the router (Phase 2) decides which specialist MCP should handle a payload, and Phase 3 actually invokes that adapter as a subprocess, captures the response, and writes the dispatch result to the audit log.

What's new in Phase 3:

- **Three reference adapters** under `adapters/` — Slack, GitHub, Splunk. Each is a small (~70 LOC) MCP server that the router launches on demand.
- **A shared scaffolding library** at `adapters/_lib.py` so each adapter only declares its capabilities and fixtures — the MCP protocol plumbing is reused.
- **`tools/mcp_dispatch.py`** — the dispatcher. Resolves the registry's `command + args`, spawns the adapter as a subprocess, walks the JSON-RPC handshake, invokes the capability, captures the response, terminates cleanly.
- **Router auto-dispatch** for non-mutating, no-approval-needed calls. The result includes `outcome.response` with the actual adapter return.
- **`dispatch_after_approval` MCP tool** — when `route_payload` returned `approval_required` and the calling client surfaced the prompt to the user, the client calls this to invoke the capability with an approval token. Writes paired `approval_granted` + `dispatch` audit lines.

## The Phase 3 flow, end to end

```
   1. Skill emits 11-field payload
                  │
                  ▼
   2. Client calls route_payload(payload)  ← MCP server, Phase 1
                  │
                  ▼
   3. Router scores enabled MCPs           ← Phase 2
                  │
            ┌─────┴─────┐
            ▼           ▼
       no_match     approval_required        OR     dispatched
       (return)     (return prompt)                   ↓
                          │              4. Dispatcher launches adapter
                          ▼                  as subprocess              ← Phase 3
                  5. Client shows                     ↓
                     prompt to user           5. Adapter handles call,
                          │                      returns JSON
                          ▼                            ↓
                  6. Client calls           6. Dispatcher captures,
                     dispatch_after_approval    writes dispatch audit
                          │                            ↓
                          └─────────► same dispatcher  → return outcome
```

## The three Phase 3 adapters

All three ship with `USAP_ADAPTER_MODE=fixture` as the default. They return canned data shaped like the real API responses, so:

- Smoke tests in CI can run them with zero credentials.
- First-time users see realistic output without configuring auth.
- Production deployment is a single env-var flip (`USAP_ADAPTER_MODE=live`) plus the documented per-adapter credentials.

### Slack (`adapters/slack/server.py`)

| Capability | Mutating | Approval | Purpose |
|---|---|---|---|
| `read_channel` | no | no | Read the last N messages from a channel. |
| `post_message` | yes | yes | Post a message. Gated. |

Live mode credential: `SLACK_BOT_TOKEN` (Bot User OAuth token).

### GitHub (`adapters/github/server.py`)

| Capability | Mutating | Approval | Purpose |
|---|---|---|---|
| `list_repos` | no | no | List visible repos. |
| `get_pr_diff` | no | no | Fetch a PR's unified diff. |
| `open_issue` | yes | yes | Open a new issue. Gated. |

Live mode credential: `GITHUB_TOKEN` (PAT or fine-grained PAT or GitHub App installation token).

### Splunk (`adapters/splunk/server.py`)

| Capability | Mutating | Approval | Purpose |
|---|---|---|---|
| `search` | no | no | Run an SPL search. |
| `list_indexes` | no | no | List indexes and their EPS health. |

Live mode credentials: `SPLUNK_HOST`, `SPLUNK_TOKEN` (HEC or session token).

## The four reservation entries

`crowdstrike`, `fortigate`, `okta`, and `aws-security-hub` stay declared in the registry as `enabled: false`. The routing logic ignores them, but their declarations document where production-grade adapters will plug in. Each is a future PR (~300–500 LOC of stdlib + HTTPS over the vendor's REST API).

The order in which they should land is roughly:

1. **AWS Security Hub** (read-only `list_findings`, simpler IAM)
2. **Okta** (read-only `list_events`, well-documented System Log API)
3. **Splunk live mode** — promotes the existing fixture-mode adapter
4. **CrowdStrike** (read-only `list_detections` first; `isolate_host` later, with extra approval bar)
5. **FortiGate** (read-only `list_policies` first; mutation last)

Each follows the same pattern as the three shipped adapters — a thin wrapper around `_lib.run_adapter()` with capability declarations, fixtures, and a `live_fn` that calls the vendor API.

## Authoring a new adapter

```python
#!/usr/bin/env python3
"""USAP specialist-MCP adapter: <vendor>."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from _lib import run_adapter

CAPABILITIES = [
    {
        "name": "<capability_id>",
        "description": "<what this does>",
        "inputSchema": {"type": "object", "properties": {...}},
    },
]

FIXTURES = {
    "<capability_id>": {"<canned response>": "..."},
}

def live(capability: str, args: dict) -> dict:
    """Real-mode handler. Called when USAP_ADAPTER_MODE=live."""
    # ... real HTTPS call ...
    return {"...": "..."}

if __name__ == "__main__":
    sys.exit(run_adapter(
        name="<vendor>",
        version="1.0.0",
        capabilities=CAPABILITIES,
        fixtures=FIXTURES,
        live_fn=live,
    ))
```

Then add the matching entry to `registry/usap-mcp-registry.yaml` with `enabled: false` until the adapter is reviewed. Don't forget: every mutating capability MUST declare `approval_required: true` — the registry validator will reject it otherwise.

## The dispatcher contract

`tools/mcp_dispatch.py` exposes one function:

```python
def dispatch(mcp: dict, capability_id: str, arguments: dict | None = None,
             timeout: float = 20.0) -> dict:
    """Returns {ok, adapter, capability, response, error}."""
```

Invariants:

1. **One adapter call per dispatch.** No connection pooling in Phase 3 — simple is correct.
2. **Bounded latency.** Default 20s timeout; configurable per call. Raises `DispatchError` on timeout (audit log records the failure).
3. **Clean subprocess termination.** stdin closes → SIGTERM → SIGKILL fallback.
4. **Returns parsed JSON.** The adapter writes JSON-stringified content; the dispatcher parses it for the caller.

## Try it locally

Phase 3 includes a CLI for ad-hoc dispatch:

```bash
# Read-only call (fixture mode):
python3 tools/mcp_dispatch.py slack read_channel --args '{"channel":"#secops"}'

# A full router run from a payload:
python3 -c "
import sys, json
sys.path.insert(0, 'tools')
from mcp_router import route
print(json.dumps(route({
    'intent_type': 'detect',
    'next_agents': ['cs-security-analyst'],
    'human_approval_required': False,
    'dispatch_args': {'spl': 'index=okta_logs failed_login'},
}), indent=2))
"
```

The first command exercises the dispatcher directly. The second exercises the full route → dispatch → audit chain.

## Approval flow from a client

1. Client calls `route_payload(payload)`. Router scores, decides this needs approval, returns `approval_required` with a prompt.
2. Client renders the prompt to the user.
3. User approves.
4. Client calls `dispatch_after_approval(mcp_id, capability_id, arguments, approval_token)`.
5. USAP writes `approval_granted` audit line, then dispatches via `tools/mcp_dispatch.py`, then writes `dispatch` audit line.
6. Outcome returns to the client.

Phase 3 trust model: the client is trusted to actually show the prompt. Phase 4 will tighten this with USAP-signed approval tokens.

## What Phase 4 adds

Phase 4 layers automation:

- **Scheduled persistence runner.** Cron-style scheduler that fires skill workflows on a clock (e.g. `attack-surface-management` every day at 09:00). Dispatches results through the routing layer to Slack via the Phase 3 adapter.
- **Cryptographic audit signing.** Every audit line signed with a per-deployment Ed25519 key. Reader verifies. Tamper-detection for compliance.
- **Webhook ingress.** External systems POST a payload, trigger a workflow.
- **The four real-security adapters** (CrowdStrike, FortiGate, Okta, AWS Security Hub) graduate from declared-but-disabled to enabled production adapters.

## See also

- [`docs/mcp-server.md`](mcp-server.md) — Phase 1 (server foundations)
- [`docs/mcp-routing.md`](mcp-routing.md) — Phase 2 (router + registry + audit)
- [`adapters/_lib.py`](https://github.com/jaskaranhundal/usap-skills/blob/main/adapters/_lib.py) — shared adapter scaffolding
- [Model Context Protocol spec](https://modelcontextprotocol.io/specification)
