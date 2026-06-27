---
title: USAP Audit Capability vs ISO 27001:2022 — Side-by-Side Comparison
generated_utc: 2026-06-27
source_iso: ISO/IEC 27001:2022 Annex A control text (canonical)
source_usap: USAP v1.7.0 master-MCP loop demo (this branch)
audit_dir: reports/iso27001-comparison/_audit/
mode: read-only
---

# USAP Audit Capability vs ISO 27001:2022 — Side-by-Side

## Why this report exists

You asked for a comparison of "our current ISO audit" against USAP's audit
chain. The Jira board (`dev`) returned 404 on every endpoint despite
`mcp__jira__jira_auth_status` reporting `authenticated: true`, so we used the
canonical ISO 27001:2022 Annex A control text as the comparator. Re-run after
the Jira basic-auth token is refreshed and we can swap in the actual board
findings without changing the loop.

## What was run

An end-to-end USAP loop into an isolated audit directory
(`reports/iso27001-comparison/_audit/`) under HMAC key
`USAP_AUDIT_KEY=iso27001-comparison-demo-key-not-prod`. Read-only against
the registry and the file system outside that directory.

| Phase | What ran | Evidence |
|---|---|---|
| 1 | `validate_payload` on `appsec-devsecops/vuln-scan` sample | `loop_decisions.json` step 1 |
| 2 | `route_payload(detect)` → auto-dispatched to `splunk` | `loop_decisions.json` step 2 + audit event `dispatch` |
| 3 | `dispatch_after_approval(slack/post_message)` after gated prompt | `loop_decisions.json` step 3 + `approval_granted` then `dispatch` |
| 4 | Synthetic `scheduled_run` + gated dispatch (runner equivalent) | `loop_decisions.json` step 4 + `scheduled_run` event |
| 4 | `mcp_audit.verify(latest log)` | `loop_decisions.json` step 5 (ok: true) |
| – | Full 32-assertion smoke test (`tools/mcp_server_test.py`) | All PASS |

Audit chain on the isolated log: **valid**, every line **signed**, every
line carries `prev_hash`, first line `prev_hash = GENESIS`.

## Side-by-side: ISO 27001:2022 Annex A vs USAP v1.7.0

| ISO 27001:2022 control | What ISO requires | USAP evidence | Verdict | Confidence |
|---|---|---|---|---|
| **A.5.34 — Privacy and protection of personally identifiable information (PII)** | Identify and meet PII-related obligations; logs containing personal data must be handled per privacy policy. | USAP carries no PII by default. Payloads are 11-field decision objects (intent, severity, findings) and dispatch arguments. The router never serializes raw user data. | MEETS (by-design omission) | High — verified by reading `mcp_router.py` `_score_mcp` + `dispatch_after_approval` (no PII fields harvested). |
| **A.8.15 — Logging** | Produce, store, protect and analyse logs that record activities, exceptions, faults and information security events. | Every routing, approval, dispatch, scheduled-run and failed-dispatch event writes one JSONL line to `~/.usap/audit/<date>.jsonl` via `tools/mcp_audit.py::write_audit`. Demo produced 6 entries spanning `dispatch`, `approval_granted`, `scheduled_run`. | MEETS | High — observed in `reports/iso27001-comparison/_audit/2026-06-27.jsonl`. |
| **A.8.15 — Logging (sub-clause: integrity)** | Logs shall be protected from tampering and unauthorized access. | SHA-256 hash chain on every line (`prev_hash` of previous full line; first = `GENESIS`). Tamper detection demonstrated in `tools/mcp_audit.py::verify`. | MEETS (cryptographic) | High — `mcp_audit --verify` returned `OK`; chain verified end-to-end. |
| **A.8.15 — Logging (sub-clause: authenticity)** | Logs should be attributable and resistant to forgery. | Optional HMAC-SHA256 per line via `USAP_AUDIT_KEY` env var (hex, keyfile, or passphrase forms). All 6 demo entries display `[signed]` in `mcp_audit --tail`. | MEETS when key configured | High — every demo line carries `sig`; verifier checks both chain and signature. |
| **A.8.16 — Monitoring activities** | Networks, systems and applications shall be monitored for anomalous behaviour; identified events shall trigger appropriate responses. | `tools/mcp_audit.py --verify` is the daily monitor. The runner can fire `attack-surface-management`, `secrets-exposure`, `okta-anomaly` on a clock — see `runner/runner.yaml`. | PARTIAL | Medium — verifier exists; production needs a daily cron + alert on FAIL. Documented in `docs/mcp-scheduled.md` §"Production deployment notes" #6. |
| **A.8.17 — Clock synchronization** | Clocks of all relevant systems shall be synchronised to approved time sources. | Every audit entry carries an ISO 8601 UTC `timestamp_utc` written via `datetime.now(timezone.utc)`. USAP does not enforce host NTP. | PARTIAL | Medium — UTC discipline at write time is correct; host-level NTP is the operator's responsibility. |
| **A.5.30 — ICT readiness for business continuity** | Plan, implement, maintain and test ICT continuity. | Runner is foreground + SIGTERM-graceful. The audit log is date-partitioned so a single corrupt day does not invalidate prior days. No tested DR drill bundled. | PARTIAL | Medium — graceful shutdown verified; full DR runbook is operator responsibility. |
| **A.5.7 — Threat intelligence** | Information relating to threats shall be collected and analysed. | Out of scope of USAP core; supported by `detection/threat-intelligence` + `detection/threat-hunting` skills, but neither is auto-fired. | GAP (by-scope) | High — USAP is plumbing, not a TI feed. |
| **A.8.30 — Outsourced development** | Direct, monitor and review outsourced development. | Not applicable to USAP (open-source, no outsourcing). | N/A | High |
| **A.6.3 — Information security awareness, education and training** | Personnel shall receive security awareness. | Not applicable to USAP as a system. | N/A | High |

Legend — **MEETS**: USAP capability fully satisfies the control. **PARTIAL**:
USAP provides the technical means; operator must wire up cron / NTP / DR for
full compliance. **GAP**: USAP does not address; intentional or expected.

## Per-event coverage of A.8.15 sub-requirements

ISO 27001:2022 A.8.15 paragraphs (a) through (h) — the canonical sub-list:

| A.8.15 paragraph | Requirement | USAP coverage |
|---|---|---|
| (a) | User IDs | `approval_token` field in `approval_granted` event; routing payload's `agent_slug`. |
| (b) | System activities | Every routing decision, dispatch and scheduled-run is written. |
| (c) | Dates / times / details of key events | `timestamp_utc` on every line. |
| (d) | Device identity / location | Not captured — host-level concern. |
| (e) | Records of attempted access | `dispatch_failed` and `approval_granted_dispatch_failed` events are explicit. Demo produced one such entry (crowdstrike disabled). |
| (f) | Changes to system / data | Mutating capabilities can only be invoked through the `dispatch_after_approval` gate, which writes paired `approval_granted` + `dispatch` lines. |
| (g) | Files / network resources accessed | Capability ID + arguments are recorded in `decision` field. |
| (h) | Alarms raised by access control | Disabled-MCP and unknown-MCP attempts write `dispatch_failed` lines. |

## Confidence in the comparison itself

| Source | Confidence | Notes |
|---|---|---|
| USAP side | High | All 32 smoke assertions PASS; chain verified; report mirrors actual events. |
| ISO side | High | Annex A.5.34 / A.8.15 / A.8.16 / A.8.17 / A.5.7 / A.5.30 control text is canonical (ISO/IEC 27001:2022, October 2022 revision). |
| Gap between this analysis and an actual ISMS audit | Medium | A real audit asks for Statement of Applicability, policies, evidence period (typically 3-6 months), and tester independence. This is a capability comparison, not an audit-in-the-formal-sense. |

## What this comparison cannot tell you

- Whether **your** Statement of Applicability scopes A.8.15 / A.8.16 the way
  USAP's audit chain assumes. SoA is org-specific.
- Whether the production runtime actually has a configured `USAP_AUDIT_KEY`,
  a daily `mcp_audit --verify` cron, NTP discipline on the host, and 3+ months
  of retained logs. Those are operational, not architectural.
- Whether the Jira board on `dev` documents findings that contradict the
  above. (Jira basic-auth refused every endpoint despite reporting
  `authenticated: true` — re-run after refreshing the token.)

## Files produced (all under `reports/iso27001-comparison/`)

- `loop_decisions.json` — 5 steps + 6 audit entries captured at demo time
- `_audit/2026-06-27.jsonl` — signed, hash-chained audit log
- `comparison.md` — this file

## How to reproduce

```bash
export USAP_AUDIT_DIR="$(pwd)/reports/iso27001-comparison/_audit"
export USAP_AUDIT_KEY="iso27001-comparison-demo-key-not-prod"
rm -rf "$USAP_AUDIT_DIR" && mkdir -p "$USAP_AUDIT_DIR"
python3 tools/usap_loop_demo.py
python3 tools/mcp_server_test.py
python3 tools/mcp_audit.py --verify
```

Three green outputs, no network calls, no mutating actions outside the gated
dispatch path, no writes outside the audit dir and this report dir.
