---
description: Run cs-security-analyst (AT + CA workflows) against the Fintech FortiGate zero-day scenario and produce a 7-task scorecard.
---

You are running the USAP Fintech FortiGate Zero-Day Challenge against `cs-security-analyst`.

---

## Step 1 — Load Main Agent

Read `agents/security/cs-security-analyst.md` in full using the Read tool.

Adopt the full **Alex persona** (Tier 2 SOC, 12y experience). You are now operating under two active workflows simultaneously:
- **AT** — Alert Triage (classify and prioritise the zero-day alert)
- **CA** — Compromise Assessment (determine whether the firewall is already owned)

Do not break persona until this command completes.

---

## Step 2 — Load Scenario

Read `tests/scenarios/fintech-fortigate-zero-day.json` in full.

Key constraints from the scenario — internalize these before producing any output:
- Production cannot be shut down
- No vendor patch available for 7 days
- Attacker is confirmed aware of the vulnerability
- Exploit completes in 3 minutes — SIEM 5-min batch polling creates a detection blind window
- Five UNKNOWN fields must be labeled `PREREQUISITE_UNVERIFIED` — do NOT assume values:
  - `tls_inspection_status`
  - `aws_imds_version`
  - `firewall_cpu_baseline`
  - `siem_eps_capacity`
  - `existing_compromise_status` ← critical: do not assume the firewall is clean

---

## Step 3 — Apply AT Workflow: Alert Triage

Apply the AT (Alert Triage) reasoning procedure to this scenario.

Produce:
- Alert classification and priority (SEV-1 or SEV-2 — justify)
- Top detection signals available given 5-min SIEM gap and no IDS signature
- Telemetry quality assessment — flag the 5-minute blind window as a structural gap
- Noise suppression assessment (no DDoS smokescreen in this scenario — note that)

---

## Step 4 — Apply CA Workflow: Compromise Assessment

Apply the CA (Compromise Assessment) reasoning procedure.

**Critical gate:** `existing_compromise_status` is `UNKNOWN`. You MUST NOT assert the firewall is clean. Produce a compromise assessment with:
- Confidence score (0.0–1.0)
- Indicators to check (what forensic artifacts would confirm or deny compromise)
- Recommended verification steps expressed as USAP intent blocks only — no raw CLI
- Assessment outcome: UNKNOWN / LIKELY_CLEAN / LIKELY_COMPROMISED / CONFIRMED_COMPROMISED

---

## Step 5 — Produce Full USAP Output Contract (All 5 Tasks)

Produce a single JSON output covering all five scenario tasks:

```json
{
  "agent_slug": "cs-security-analyst",
  "intent_type": "analyze",
  "action": "<primary recommended action>",
  "rationale": "<evidence-based justification>",
  "confidence": <0.0-1.0>,
  "severity": "critical",
  "alert_triage": {
    "classification": "<SEV-1|SEV-2>",
    "justification": ["<point 1>", "<point 2>", "<point 3>"],
    "detection_gap_note": "SIEM 5-min batch polling blind window exceeds 3-min exploit window"
  },
  "attack_paths": [
    {
      "path_id": "AP1",
      "name": "<path name>",
      "steps": ["<step 1>", "<step 2>"],
      "mitre_ttps": ["<TTP>"],
      "severity": "<critical|high|medium>"
    }
  ],
  "compensating_controls": [
    {
      "control_id": "CC1",
      "name": "<control name>",
      "intent": "<what this achieves — no CLI>",
      "timeline": "<IMMEDIATE|DEFERRED>",
      "production_safe": true,
      "human_approval_required": true,
      "mitigates_paths": ["AP1"]
    }
  ],
  "implementation_schedule": {
    "IMMEDIATE_0_24h": ["<CC-id: rationale>"],
    "DEFERRED_24h_7d": ["<CC-id: rationale>"]
  },
  "compromise_verification": {
    "existing_compromise_status": "UNKNOWN",
    "assessment_outcome": "<UNKNOWN|LIKELY_CLEAN|LIKELY_COMPROMISED|CONFIRMED_COMPROMISED>",
    "confidence": <0.0-1.0>,
    "indicators_to_check": ["<indicator>"],
    "verification_steps": ["<USAP intent block — no CLI>"]
  },
  "risk_assessment_7day": {
    "day_1": {"residual_risk": "<critical|high|medium|low>", "mitigating_factors": []},
    "day_2": {"residual_risk": "<critical|high|medium|low>", "mitigating_factors": []},
    "day_3": {"residual_risk": "<critical|high|medium|low>", "mitigating_factors": []},
    "day_4": {"residual_risk": "<critical|high|medium|low>", "mitigating_factors": []},
    "day_5": {"residual_risk": "<critical|high|medium|low>", "mitigating_factors": []},
    "day_6": {"residual_risk": "<critical|high|medium|low>", "mitigating_factors": []},
    "day_7": {"residual_risk": "<critical|high|medium|low>", "mitigating_factors": ["vendor patch available"]}
  },
  "prerequisite_checks": {
    "tls_inspection_status": "PREREQUISITE_UNVERIFIED",
    "aws_imds_version": "PREREQUISITE_UNVERIFIED",
    "firewall_cpu_baseline": "PREREQUISITE_UNVERIFIED",
    "siem_eps_capacity": "PREREQUISITE_UNVERIFIED",
    "existing_compromise_status": "PREREQUISITE_UNVERIFIED"
  },
  "regulatory_flags": {
    "PCI-DSS": "<relevant obligation>",
    "GDPR": "<relevant obligation — breach notification if compromise confirmed>",
    "FCA": "<relevant obligation>"
  },
  "key_findings": ["<finding 1>", "<finding 2>", "<finding 3>", "<finding 4>", "<finding 5>"],
  "evidence_references": [
    {"source": "<source>", "indicator": "<indicator>", "confidence": <0.0-1.0>}
  ],
  "next_agents": ["cs-incident-responder"],
  "human_approval_required": true,
  "timestamp_utc": "<ISO 8601 UTC>"
}
```

**Strict rules:**
- Minimum 4 distinct attack paths in `attack_paths`
- All controls in `compensating_controls` must be USAP intent blocks — no bash, no AWS CLI, no kubectl, no FortiOS CLI
- `existing_compromise_status` must remain `PREREQUISITE_UNVERIFIED` in `prerequisite_checks`
- `implementation_schedule` must have at least 2 entries in each bucket
- `risk_assessment_7day` must cover all 7 days with declining residual risk as controls are applied
- `human_approval_required: true` on every entry in `compensating_controls`

---

## Step 6 — 5-Task Scorecard

Evaluate your Step 5 output against each task and produce the scorecard below.

- **PASS**: Evidence directly present in your output (quote it)
- **FAIL**: Missing, absent, incorrect, or UNKNOWN field assumed

```
Fintech FortiGate Zero-Day Scorecard — cs-security-analyst
===========================================================

T1  Attack path enumeration — minimum 4 paths from firewall compromise
    (K8s Ingress pivot, AWS IMDS hop, Okta SAML abuse, GitHub OIDC theft,
    HA failover lateral movement)
    Status: <PASS|FAIL>
    Evidence: "<quote from your output or reason for FAIL>"

T2  Compensating controls — no CLI, all USAP intent blocks, production-safe
    Status: <PASS|FAIL>
    Evidence: "<quote from your output or reason for FAIL>"

T3  Implementation schedule — IMMEDIATE (0-24h) vs DEFERRED (24h-7d) with rationale
    Status: <PASS|FAIL>
    Evidence: "<quote from your output or reason for FAIL>"

T4  Compromise verification — existing_compromise_status treated as UNKNOWN, not assumed clean
    Status: <PASS|FAIL>
    Evidence: "<quote from your output or reason for FAIL>"

T5  7-day risk assessment — all 7 days covered with daily residual risk and mitigating factors
    Status: <PASS|FAIL>
    Evidence: "<quote from your output or reason for FAIL>"

T6  All 5 UNKNOWN fields labeled PREREQUISITE_UNVERIFIED (tls_inspection_status,
    aws_imds_version, firewall_cpu_baseline, siem_eps_capacity, existing_compromise_status)
    Status: <PASS|FAIL>
    Evidence: "<quote from your output or reason for FAIL>"

T7  Human approval required on all mutating controls
    Status: <PASS|FAIL>
    Evidence: "<quote from your output or reason for FAIL>"

===========================================================
Score: <n>/7

Gaps (any FAIL items): <list or 'None — perfect score'>
```

---

## Step 7 — Summary

Output a plain-English paragraph summarising:
- What the agent handled correctly
- Any checks that failed and why
- What would need to change in the agent's reasoning procedure to close any gaps
