---
title: USAP Scheduled Persistence + Audit Signing (Phase 4)
description: Cron-style runner that fires skill workflows on a clock, dispatches results through the routing layer to Slack / GitHub / Splunk, and writes hash-chained HMAC-signed audit log lines that detect any tampering.
---

# USAP Scheduled Persistence + Audit Signing (Phase 4)

Phase 4 layers two pieces on top of the routing + dispatch foundation built in Phases 1–3:

1. **A scheduled runner** (`tools/usap_runner.py`) that fires skill workflows on a clock — daily, hourly, every N minutes — and dispatches the results through the routing layer to a downstream MCP adapter. This is the "always-on coverage" tier: USAP runs attack-surface scans every hour, secrets sweeps every morning, SIEM anomaly checks every fifteen minutes, posting deltas to Slack / GitHub issues / PagerDuty without a human starting each run.
2. **Tamper-resistant audit logs.** Every audit line now includes a SHA-256 hash of the previous line (a chain), and if `USAP_AUDIT_KEY` is set, an HMAC-SHA256 signature over its content. The `tools/mcp_audit.py --verify` reader walks the chain, recomputes every hash, and checks every signature. Any insertion, deletion, or modification anywhere in the log is detected.

Both pieces are stdlib only.

## Scheduled runner

### The schedule config

`runner/runner.yaml` declares jobs:

```yaml
version: 1
jobs:
  - id: hourly-attack-surface
    skill: attack-surface-management
    schedule: "@hourly"
    intent_type: detect
    dispatch_to: splunk
    dispatch_args:
      spl: "index=netflow earliest=-1h | stats count by src_ip"
    enabled: false        # flip to true to activate

  - id: daily-secrets-scan
    skill: secrets-exposure
    schedule: "0 9 * * *"  # daily 09:00 UTC
    intent_type: detect
    dispatch_to: github
    dispatch_args:
      org: acme
    enabled: false
```

### Supported schedule syntax

Phase 4 implements a deliberately small subset of cron. Anything outside this is rejected at validation time.

| Format | Meaning |
|---|---|
| `M H * * *` | Fire daily at HH:MM (UTC). Days-of-month, month, day-of-week must all be `*`. |
| `*/N * * * *` | Fire every N minutes. Hour must be `*`. |
| `@every Ns` | Fire every N seconds. Useful for testing. |
| `@hourly` | Fire once per hour, on first tick after a new hour starts. |
| `@daily` | Fire once per day. |

If you need full cron expressiveness (specific weekdays, ranges, lists), wrap the runner in a system cron / systemd timer that fires `python3 tools/usap_runner.py --once <job-id>` at the right moments.

### Run modes

```bash
# Validate the config
python3 tools/usap_runner.py --validate

# List configured jobs
python3 tools/usap_runner.py --list

# Run one job once, ignoring schedule (good for testing)
python3 tools/usap_runner.py --once smoke-test-job

# Foreground daemon (Ctrl-C to stop)
python3 tools/usap_runner.py --run

# Background under systemd / launchd: same command,
# the runner handles SIGINT/SIGTERM gracefully.
python3 tools/usap_runner.py --run --poll-interval 30
```

### What the runner does on each fire

1. Synthesizes a deterministic 11-field payload for the job (intent_type, severity=informational, etc.). The runner doesn't invoke the skill's LLM — it produces a payload whose only purpose is to drive the routing decision.
2. Writes a `scheduled_run` audit line.
3. Calls `dispatch_after_approval(dispatch_to, capability, dispatch_args)` — bypassing the human gate because the runner is locally trusted and the configured capability must already be a non-mutating one (the runner refuses to invoke mutating capabilities).
4. Writes a `dispatch` audit line with the outcome.

If the dispatched MCP is `enabled: false` in the registry, the runner returns `dispatch_failed`. That's a configuration error, not a security issue.

## Audit chain + HMAC signing

### The chain

Every line in `~/.usap/audit/YYYY-MM-DD.jsonl` carries a `prev_hash` field:

- First line of a fresh log: `prev_hash = "GENESIS"`.
- Every subsequent line: `prev_hash = SHA-256(previous full line including its prev_hash and sig)`.

A verifier walks the file forward, recomputes each line's expected `prev_hash`, and reports any mismatch. Insertion, deletion, or modification of any line breaks the chain at that point and at every line after it.

### The signature

If `USAP_AUDIT_KEY` is set in the environment, every line additionally carries a `sig` field:

```
sig = HMAC-SHA256(JSON(line without sig field), USAP_AUDIT_KEY)
```

`USAP_AUDIT_KEY` accepts three forms:

| Form | Behaviour |
|---|---|
| `0123abcd...` (≥32 hex chars) | Decoded as raw bytes — production deployment. |
| `/path/to/keyfile` (existing file) | Bytes read from the file. |
| any other string | Treated as a passphrase, derived to bytes via SHA-256. |

The verifier reads `USAP_AUDIT_KEY` the same way and recomputes every signature. An attacker who controls the disk but not the key cannot forge new lines; an attacker who controls both still has to break the hash chain to insert anything.

### Verifying

```bash
python3 tools/mcp_audit.py --verify
```

Exit 0 = chain valid + every signature matches (or no key configured). Exit 1 = the verifier prints the specific lines that fail and why.

### Tail

```bash
python3 tools/mcp_audit.py --tail 20
```

Shows the last 20 entries with their event and decision status. Lines that carry a signature show `[signed]`.

## How it fits with the rest of USAP

```
                          Phase 4: cron / time
                                  │
                                  ▼
                  ┌──────────────────────────────┐
                  │     usap_runner.py           │
                  │  • parse runner.yaml         │
                  │  • daemon loop               │
                  │  • dispatch_after_approval   │
                  │  • writes scheduled_run +    │
                  │    dispatch audit lines      │
                  └──────────────┬───────────────┘
                                 ▼
                     Phase 2/3: router + dispatcher
                                 │
                                 ▼
                     Phase 3: specialist MCP adapter
                                 │
                                 ▼
                      Real vendor (Slack / GitHub / Splunk / …)

   In parallel, every Phase 2/3/4 event writes one line into
   ~/.usap/audit/YYYY-MM-DD.jsonl — hash-chained, optionally HMAC-signed.
```

## The complete master-MCP vision (Phases 1–4)

After Phase 4, USAP is:

- **An MCP server** any MCP-compatible client can connect to (Phase 1)
- **A routing layer** that takes 11-field payloads from skills and decides which specialist MCP should handle them, gated on `human_approval_required` (Phase 2)
- **A dispatcher** that actually launches adapters and invokes capabilities (Phase 3)
- **A scheduler** that fires workflows on a clock (Phase 4)
- **A tamper-resistant audit log** of every routing, approval, dispatch, and scheduled-run event (Phase 4)

Plus seven reference adapters in the registry: 3 enabled today (Slack, GitHub, Splunk) and 4 declared-but-disabled awaiting production-grade implementations (CrowdStrike, FortiGate, Okta, AWS Security Hub).

That is the "minimum human intervention, maximum tool capability" architecture: USAP routes everything safe automatically, gates everything dangerous behind the approval flow, runs workflows on a schedule with no human required, and produces an audit log that any compliance reviewer can trust because it's tamper-detecting.

## Production deployment notes

When running for real (not just smoke tests):

1. **Flip the three adapters' `enabled` flag** in `registry/usap-mcp-registry.yaml`. Phase 3 ships them all enabled in fixture mode by default; nothing prevents you from running it as-is. For real responses, set `USAP_ADAPTER_MODE=live` AND supply the documented per-adapter credentials.
2. **Flip the runner jobs' `enabled` flag** in `runner/runner.yaml`. Default state is all jobs `enabled: false`.
3. **Set `USAP_AUDIT_KEY`** to a real per-deployment secret (32+ hex chars from `python3 -c 'import secrets; print(secrets.token_hex(32))'`, or a path to a key file with 0600 permissions).
4. **Run under systemd** or another process supervisor — `python3 tools/usap_runner.py --run` runs in the foreground and handles SIGTERM gracefully.
5. **Rotate audit logs** by date — they're already date-partitioned. Archive previous days off the running host once they've been verified.
6. **Verify daily.** Schedule a separate cron job that runs `python3 tools/mcp_audit.py --verify` against yesterday's log and alerts on FAIL.

## See also

- [`docs/mcp-server.md`](mcp-server.md) — Phase 1: discovery + load
- [`docs/mcp-routing.md`](mcp-routing.md) — Phase 2: router + registry
- [`docs/mcp-adapters.md`](mcp-adapters.md) — Phase 3: adapters + dispatch
- [`runner/runner.yaml`](https://github.com/jaskaranhundal/usap-skills/blob/main/runner/runner.yaml) — schedule config
- [`tools/usap_runner.py`](https://github.com/jaskaranhundal/usap-skills/blob/main/tools/usap_runner.py) — the runner
- [`tools/mcp_audit.py`](https://github.com/jaskaranhundal/usap-skills/blob/main/tools/mcp_audit.py) — the audit writer + verifier
