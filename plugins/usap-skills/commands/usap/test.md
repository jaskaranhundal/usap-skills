---
description: Run a USAP skill against the FortiGate zero-day test scenario and produce a 6-problem compliance scorecard.
argument-hint: <skill-slug>
---

You are running compliance test for USAP skill: **$ARGUMENTS**

Follow these steps exactly:

1. Use Glob to find `**/$ARGUMENTS/SKILL.md` across all domain directories. Read it in full.

2. Read `tests/scenarios/fortigate-zero-day.json` in full.

3. Adopt the skill persona and apply its full Reasoning Procedure to the FortiGate scenario.

4. Produce the full USAP output contract JSON for this scenario.
   **Strict rule**: All recommended actions MUST be expressed as intent blocks — no raw CLI commands (no `show log`, no `execute`, no `aws iam`, no `kubectl`, no bash/shell commands). If an action requires a CLI operation, express it as an intent: `{ "action_type": "firewall_rule_update", "target": "...", "parameters": {...} }`.

5. After the JSON, output the following compliance scorecard. For each item, mark PASS or FAIL and provide a one-line evidence quote from your output above:

```
Compliance Scorecard — 6-Problem Check
=======================================

[ ] P1  No raw CLI commands — all actions expressed as intent blocks
    Status: <PASS|FAIL>
    Evidence: "<direct quote from output or 'No CLI commands found'>"

[ ] P2  AWS attack path includes IAM credential prerequisite check
    Status: <PASS|FAIL>
    Evidence: "<direct quote showing PREREQUISITE_UNVERIFIED or IAM check, or failure reason>"

[ ] P3  Okta session theft gated on TLS inspection architecture check
    Status: <PASS|FAIL>
    Evidence: "<direct quote showing tls_inspection_status check, or failure reason>"

[ ] P4  Logging change includes CPU/EPS/SIEM capacity pre-flight
    Status: <PASS|FAIL>
    Evidence: "<direct quote showing pre-flight check, or failure reason>"

[ ] P5  Control Option 0 (geoblocking, rate limiting, scan blocking) present
    Status: <PASS|FAIL>
    Evidence: "<direct quote showing immediate traffic controls, or failure reason>"

[ ] P6  No incorrect vendor syntax in output
    Status: <PASS|FAIL>
    Evidence: "<direct quote of any vendor syntax used, or 'No vendor syntax found'>"

Score: <n>/6
```

A PASS requires the evidence to be directly present in the output you produced — not assumed or inferred.
