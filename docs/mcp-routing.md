---
title: USAP MCP Routing (Phase 2)
description: USAP as the master MCP. Routes 11-field payloads from skills to downstream specialist vendor MCPs (Splunk, CrowdStrike, FortiGate, Okta, AWS Security Hub, GitHub, Slack), with the contract's human_approval_required field enforcing the human gate.
---

# USAP MCP Routing (Phase 2)

Phase 2 turns the read-only Phase 1 MCP server into the **master MCP that routes other vendor MCPs.** A skill (or an orchestrator agent calling a skill) emits an 11-field USAP payload. The router looks up which specialist MCP would handle it next, returns either an approval prompt (if any mutating action is involved) or a dispatch decision, and writes every step to an audit log.

Phase 2 ships:

- The **registry** (`registry/usap-mcp-registry.yaml`) — declares the specialist MCPs and their capabilities.
- The **loader / validator** (`tools/mcp_registry.py`) — parses the registry and enforces schema rules.
- The **router** (`tools/mcp_router.py`) — given a payload, picks the best candidate MCP.
- The **audit writer** (`tools/mcp_audit.py`) — JSONL log under `~/.usap/audit/YYYY-MM-DD.jsonl`.
- Two new MCP tools on the server: `route_payload` and `list_mcps`.

**Phase 2 does not actually invoke downstream adapters.** That's Phase 3 — the actual Splunk / CrowdStrike / FortiGate / etc. binaries. Phase 2's job is to prove the routing decision is correct, the approval gate fires when it should, and the audit log captures everything. That way Phase 3 can plug in real adapters without re-litigating the decision model.

## The registry

`registry/usap-mcp-registry.yaml` declares every specialist MCP USAP knows how to route to. Each entry has:

```yaml
- id: crowdstrike                          # stable identifier
  name: CrowdStrike Falcon                 # human-readable
  enabled: false                           # router skips if disabled
  transport: stdio                         # how the adapter is launched
  command: python3
  args: ["./adapters/crowdstrike/server.py"]
  capabilities:
    - id: list_detections
      mutating: false
      approval_required: false
    - id: isolate_host
      mutating: true
      approval_required: true               # gate fires on this capability
  routes_intent: [respond, block]           # which intent_type values match
  relevant_agents: [cs-incident-responder]  # which cs-* agents send work here
```

Validate the registry locally:

```bash
python3 tools/mcp_registry.py --validate
python3 tools/mcp_registry.py --list
python3 tools/mcp_registry.py --explain crowdstrike
```

The validator enforces:

- Every MCP has `id`, `name`, `transport`, `command`, `args`, `capabilities`.
- Every capability has `id`, `mutating`, `approval_required`.
- `routes_intent` values are from the 7-intent enum.
- **Every mutating capability must have `approval_required: true`.** A registry entry that declares a mutating capability without an approval gate is a config bug; the router refuses to load it. Safety-by-default.
- `id` uniqueness across the whole registry.

## The routing decision

`tools/mcp_router.py` scores every enabled MCP against the payload:

| Signal | Score |
|---|---|
| Payload `intent_type` ∈ MCP's `routes_intent` | +2 |
| Each `cs-*` agent in payload's `next_agents` ∈ MCP's `relevant_agents` | +1 |
| MCP `enabled: false` | excluded |

Ties break alphabetically on MCP id, so the decision is deterministic.

The router returns one of three statuses:

| Status | What it means |
|---|---|
| `no_match` | No enabled MCP scored positive. Includes a list of considered MCPs for diagnostics. |
| `approval_required` | A candidate matched **but** either the payload's `human_approval_required: true` OR the selected capability's `approval_required: true` is set. Returns an approval prompt the calling client must surface to the user. Phase 3 will dispatch after approval; Phase 2 stops here. |
| `would_dispatch` | A safe (non-mutating, no-approval-needed) match. Phase 2 returns the MCP + capability that **would** be invoked. Phase 3 actually invokes. |

Every result includes the candidate alternatives (top 4), so a client can offer "or do this instead" UX.

## The audit log

`tools/mcp_audit.py` writes one JSONL entry per routing decision:

```json
{"timestamp_utc":"2026-06-26T15:41:23.456Z","event":"route","payload":{...},"decision":{"status":"approval_required","selected_mcp":"slack","selected_capability":"post_message", ...}}
```

Default location: `~/.usap/audit/YYYY-MM-DD.jsonl`. Override with `USAP_AUDIT_DIR=/path/to/audit-dir`.

Tail the latest log:

```bash
python3 tools/mcp_audit.py --tail 20
```

Phase 2 ships the writer. Phase 3 adds a richer reader (`tail --follow`, filter by event, filter by mcp). Phase 4 adds **cryptographic signing** so the log is unfalsifiable for compliance purposes.

## Using it from an MCP client

After connecting USAP's MCP server (see [`docs/mcp-server.md`](mcp-server.md) for client config), two new tools become available:

### `route_payload`

```jsonrpc
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "tools/call",
  "params": {
    "name": "route_payload",
    "arguments": {
      "payload": {
        "agent_slug": "containment-advisor",
        "intent_type": "block",
        "action": "Block source IP 198.51.100.42 at the edge firewall.",
        "rationale": "Confirmed external scanner; high confidence.",
        "confidence": 0.91,
        "severity": "high",
        "key_findings": ["..."],
        "evidence_references": [{"source":"siem","ref":"...","quote":"..."}],
        "next_agents": ["cs-incident-responder"],
        "human_approval_required": true,
        "timestamp_utc": "2026-06-26T15:00:00Z"
      }
    }
  }
}
```

Returns the routing decision as a single text content block. Example response (Phase 2; FortiGate adapter not yet enabled):

```json
{
  "status": "approval_required",
  "selected_mcp": "fortigate",
  "selected_mcp_name": "FortiGate",
  "selected_capability": "block_ip",
  "mutating": true,
  "approval_prompt": "USAP wants to call 'FortiGate' → block_ip (severity=high, mutating=True).\nRationale: Confirmed external scanner; high confidence.\nApprove? Reject? Or rewrite the action.",
  "alternatives": ["crowdstrike", "okta"],
  "phase": 2,
  "phase_note": "Phase 2 returns the approval prompt only. Phase 3 will dispatch once the user approves."
}
```

### `list_mcps`

Returns the full registry as a human-readable list — id, status, declared intents, capabilities. Useful for the client UI to surface "here's what USAP can route to."

## What Phase 3 adds

Phase 3 (next minor release) wires actual dispatch:

- Reference adapter binaries for at least: Slack, GitHub, AWS Security Hub, Splunk, CrowdStrike. Each ~300–500 LOC stdlib + minimal HTTPS over the vendor's public API.
- After an `approval_required` decision, the calling client sends `{"approved": true}` back; USAP launches the adapter, dispatches the capability call, captures the response, writes a second audit line (`event: "dispatch"`), and returns the downstream result.
- Capability-call timeout + retry policy.
- Adapter health checks (`tools/mcp_health.py`).

## What Phase 4 adds

Phase 4 layers automation on top of the routing layer:

- **Scheduled persistence runner** — cron-style scheduler that fires skill workflows on a clock (e.g. `attack-surface-management` every day at 09:00). Dispatches results through the routing layer to Slack / Discord / PagerDuty.
- **Cryptographic audit signing** — every audit-log line is signed with a per-deployment Ed25519 key. Reader verifies. Tamper-detection for compliance.
- **Webhook ingress** — external systems can POST a payload to USAP and trigger a workflow.

## Phase 2 design rules — for future PRs

1. **Mutating capabilities MUST have `approval_required: true` in the registry.** The loader rejects a registry that violates this. Don't lower the bar.
2. **Phase 2 never dispatches.** Even if a capability has `approval_required: false`, Phase 2 returns `would_dispatch`, not `dispatched`. Phase 3 owns dispatch.
3. **Every routing decision writes one audit line.** No exceptions. If `write_audit` fails (disk full, permission denied), the routing decision still returns to the caller — but a separate WARN is emitted to stderr.
4. **The router is deterministic.** Same payload + same registry = same decision, always. This matters for test reproducibility and for audit-log review.
5. **Stdlib only.** Same constraint as Phase 1. MCP transport is JSON-RPC over stdio; YAML parsing is in `tools/mcp_registry.py`.

## See also

- [`docs/mcp-server.md`](mcp-server.md) — Phase 1, the discovery + load primitives this builds on
- [`registry/usap-mcp-registry.yaml`](https://github.com/jaskaranhundal/usap-skills/blob/main/registry/usap-mcp-registry.yaml) — the registry
- [`standards/output-contract.md`](https://github.com/jaskaranhundal/usap-skills/blob/main/standards/output-contract.md) — the 11-field contract the router reads
- [Model Context Protocol spec](https://modelcontextprotocol.io/specification)
