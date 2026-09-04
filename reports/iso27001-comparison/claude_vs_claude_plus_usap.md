---
title: Claude Code (alone) vs Claude Code + USAP — Side-by-Side
generated_utc: 2026-06-27
audience: security engineer / SOC / DevSecOps lead deciding whether to install USAP
verdict_one_liner: |
  Bare Claude Code is a brilliant generalist with file/shell/web tools.
  Claude Code + USAP is the same brilliant generalist plus a typed
  11-field decision contract, 79 domain skills, 7 cs-* personas, gated
  action plumbing, scheduled runs, and a tamper-resistant audit log.
mode: read-only
---

# Claude Code (alone) vs Claude Code + USAP

## What each one IS

**Claude Code alone** — interactive LLM agent with Read/Write/Edit/Bash/Grep/Glob/WebFetch and MCP. No security-domain priors beyond what's in the model. Every session re-derives "what's a SEV-1?", "what does an incident response runbook look like?", "is this control mutating?" from first principles. Output is free-form prose unless you prompt for structure each time.

**Claude Code + USAP** — same agent, but every security task drops into a typed contract, a domain persona, and a gated action surface:

- **79 skills** across 11 domains, each a self-contained system prompt with a reasoning procedure, classification tables, ATT&CK mappings, and a contract-compliant JSON output template.
- **7 `cs-*` agents** (Alex the SOC analyst, the incident responder, CISO advisor, red-teamer, blue-team analyst, cloud investigator, supply-chain defender) — each a persona with a command menu (AT/TH/CA/DI/GU/OR/SK/MC/HE/ST) that calls skills as substeps.
- **MCP server** any client (Claude Code, Cursor, Codex, Gemini, Goose) can plug into.
- **Router + registry** — payloads route to the right specialist MCP; mutating actions gate behind an approval prompt.
- **Dispatcher + 3 live adapters** (Slack, GitHub, Splunk) + 4 declared-but-disabled (CrowdStrike, FortiGate, Okta, AWS Security Hub).
- **Cron-style scheduler** — workflows fire on a clock, refuse to invoke mutating capabilities.
- **Hash-chained + HMAC-signed audit log** — `mcp_audit --verify` catches any tampering.

## Side-by-side on the work a SOC / security engineer actually does

| Dimension | Claude Code alone | Claude Code + USAP | Why USAP wins |
|---|---|---|---|
| Alert triage from raw logs | Reads the logs, gives a prose verdict. Quality depends on prompt. | Drop into Alex via `usap-alex` slash command; runs the `AT` workflow with a fixed reasoning procedure (classification table, MITRE TTP mapping, 11-field JSON out). | Repeatable shape. Output is auditable, machine-parseable, and feeds the next agent. |
| Incident response runbook | Generates one from memory each time. | `cs-incident-responder` already encodes containment / eradication / recovery phases per NIST 800-61. | No re-derivation drift. |
| Vulnerability triage | Reads the scanner output, summarises. | `appsec-devsecops/vuln-scan` skill — CVSS-aware, exploit-availability-aware, prod-blast-radius-aware, emits gated remediation intents. | The gating is the safety net. |
| Threat hunting | Free-form hypothesis. | `detection/threat-hunting` skill — pyramid-of-pain anchored, ATT&CK-tagged, behavioural-analytics-linked. | Tactic / technique consistency across hunts. |
| CISO-level advisory | Generic best-practice prose. | `cs-ciso-advisor` agent — board-grade output, risk-register-ready format. | Audience-correct. |
| Red team / purple team | One-off attack chain narrative. | `red-team/*` skills + `cs-red-teamer` + `cs-purple-team-lead` (planned). | Reusable across engagements. |
| Mutating action (kill process, isolate host, rotate key) | Will happily run the bash command if you let it. | Refuses; routes through `dispatch_after_approval` only. Refuses entirely from the scheduled runner. | Hard gate, not a vibe. |
| Audit / forensic record of decisions | None — your scrollback. | Every routing / approval / dispatch / scheduled-run event in `~/.usap/audit/<date>.jsonl`, SHA-256 chained, HMAC-signed when key set. `--verify` detects tampering. | This is the ISO 27001 A.8.15 compliance story; bare Claude has nothing here. |
| Cron / always-on monitoring | None — has to be sitting at the terminal. | `tools/usap_runner.py` foreground daemon, systemd-friendly, refuses to invoke mutating capabilities. | Replaces "human at terminal" with "scheduled signal". |
| Compliance evidence collection | None | The audit log IS the evidence. | Auditor walks `--verify` output. |
| Cross-client portability (Cursor, Codex, Gemini, Goose) | Each agent re-derives. | All clients hit the same MCP server, get the same skills + agents + decisions. | Vendor-independent. |
| Output contract | Free-form text. | 11 typed fields (`agent_slug`, `intent_type`, `severity`, `confidence`, `key_findings`, `evidence_references`, `next_agents`, `human_approval_required`, `timestamp_utc` + two more). | Machine-handed-off, chainable. |
| Onboarding a new engineer | "Read these docs and good luck." | Skill bodies double as training material — each one is a system-prompt + classification table + reasoning procedure. | Knowledge externalised. |

## Where Claude alone is genuinely fine (no need for USAP)

Don't over-buy. USAP earns its keep on **security workflows that repeat, need auditability, or need a hard mutating-action gate**. Bare Claude is great for:

- One-off code review, refactor, debugging
- General research / writing / explanation
- Tasks that don't need a fixed output contract
- Single-user "thinking partner" sessions where nothing leaves the terminal
- Anything you'd never want to audit a year later

If your task is "explain this CrowdStrike alert in plain English" — bare Claude.  
If your task is "triage 47 CrowdStrike alerts overnight, gate any containment behind my approval, leave a tamper-evident record" — Claude + USAP.

## Concrete delta on a SEV-1 scenario

**Scenario:** Suspected FortiGate zero-day. Production cannot be shut down. No patch for 7 days.

| Step | Bare Claude | Claude + USAP |
|---|---|---|
| Classification | Prose SEV-1 verdict, justification varies session to session. | Alex `AT` + `CA` produces typed JSON with attack paths (≥4 enumerated), compensating controls (USAP intent blocks, no raw CLI), 7-day risk trajectory, `existing_compromise_status` treated as `UNKNOWN` not assumed clean. |
| Compensating controls | Tends to emit raw `iptables` / cloud CLI. | Forced into "USAP intent blocks" — no CLI in the output by contract. |
| Approval gate | None — would run the command. | Containment routes through `dispatch_after_approval` (slack/post_message, or to-be-built fortigate adapter). Without approval token, won't dispatch. |
| Persistence of decision | Scrollback only. | JSON line in audit log, signed, chained, recoverable a year later. |
| Cross-shift handoff | Re-explain to the next shift. | Next shift opens the same agent, reads the audit log + JSON output. State is in artefacts, not heads. |

## One honest disadvantage to flag

USAP adds **vocabulary cost**. You learn 11 fields, 7 agents, the AT/TH/CA/DI/GU/OR/SK/MC command menu. Bare Claude is "type English, get English". For a 10-minute task that won't repeat, the vocabulary cost is overhead, not value. For a SOC that runs the same 5 workflows weekly, the cost is paid down inside a week.

## The 30-second decision rule

- Are you the only operator, doing one-off security thinking? → **Claude alone** is plenty.
- Are you a team / regulated environment / need an audit trail / repeat the same task 3+ times? → **Claude + USAP** earns its cost in <1 sprint.
- Are you compliance-driven (ISO 27001, ISO 42001, SOC 2)? → USAP's chained + signed audit log is the cheapest A.8.15 evidence you'll find.
