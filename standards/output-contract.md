# Output Contract

Every USAP agent skill must produce a JSON payload conforming to this schema. The `guardrail` skill validates all outputs before they are forwarded to the orchestrator or human operator.

---

## Required Fields

| Field | Type | Description |
|---|---|---|
| `agent_slug` | string | Exact slug of the skill that produced this output |
| `intent_type` | string | One of: `detect`, `respond`, `analyze`, `advise`, `escalate`, `report`, `block` |
| `action` | string | Recommended next action in plain English |
| `rationale` | string | Evidence-based explanation for the recommended action |
| `confidence` | float | 0.0–1.0; below 0.5 triggers inconclusive flag |
| `severity` | string | One of: `critical`, `high`, `medium`, `low`, `informational` |
| `key_findings` | array[string] | Ordered list of discrete findings supporting the recommendation |
| `evidence_references` | array[object] | Source artifacts, log lines, timestamps used as evidence |
| `next_agents` | array[string] | Skill slugs to invoke next (empty if terminal) |
| `human_approval_required` | boolean | True if a mutating action requires human gate |
| `timestamp_utc` | string | ISO 8601 UTC timestamp of output generation |

---

## Optional Fields

| Field | Type | Description |
|---|---|---|
| `mitre_ttps` | array[string] | MITRE ATT&CK technique IDs (e.g., `T1078`, `T1059.001`) |
| `cvss_score` | float | CVSS v3.1 base score if applicable |
| `epss_score` | float | EPSS probability score if applicable |
| `affected_assets` | array[string] | Hostnames, IPs, or ARNs of affected systems |
| `remediation_steps` | array[string] | Ordered remediation actions |
| `regulatory_flags` | array[string] | Triggered compliance framework clauses |
| `risk_score` | integer | 0–100 composite risk score |
| `escalation_reason` | string | Why escalation was triggered (if applicable) |
| `communication_standard_applied` | boolean | True if human-facing narrative follows the 5-part Communication Standard format |

---

## Canonical Example

```json
{
  "agent_slug": "secrets-exposure",
  "intent_type": "detect",
  "action": "Revoke AWS access key AKIA... immediately and rotate all credentials in the affected repository.",
  "rationale": "High-entropy string matching AWS access key pattern detected in git history commit abc123. Key has been present for 14 days. CloudTrail shows no anomalous usage yet, but exposure window is open.",
  "confidence": 0.94,
  "severity": "critical",
  "key_findings": [
    "AWS access key AKIA... found in commit abc123 on branch main",
    "Key present for 14 days — blast radius is open",
    "No anomalous CloudTrail usage detected in 14-day window"
  ],
  "evidence_references": [
    {"source": "git-history", "ref": "abc123", "timestamp_utc": "2026-03-01T14:22:00Z"},
    {"source": "cloudtrail", "ref": "no-anomaly", "timestamp_utc": "2026-03-08T09:00:00Z"}
  ],
  "next_agents": ["incident-commander", "compliance-mapping"],
  "human_approval_required": true,
  "mitre_ttps": ["T1552.001"],
  "affected_assets": ["repo:acme/backend", "iam:AKIA..."],
  "remediation_steps": [
    "Revoke key AKIA... in AWS IAM console immediately.",
    "Rotate all secrets in repository config/prod.env.",
    "Audit CloudTrail for last 90 days for key usage.",
    "Rewrite git history to remove secret from all branches."
  ],
  "regulatory_flags": ["PCI-DSS 8.3.2", "SOC2 CC6.1"],
  "timestamp_utc": "2026-03-08T09:05:00Z"
}
```

---

## Validation Rules

1. `confidence` must be a float between 0.0 and 1.0 inclusive.
2. `severity` must be exactly one of the five allowed values.
3. `intent_type` must be one of the seven allowed values.
4. `key_findings` must contain at least one entry.
5. `evidence_references` must contain at least one entry for severity >= `high`.
6. `human_approval_required` must be `true` for any action that mutates production state.
7. `next_agents` must only reference valid USAP skill slugs.
8. `timestamp_utc` must be a valid ISO 8601 string.

---

## Guardrail Enforcement

The `guardrail` skill automatically validates outputs. Validation failures produce:

```json
{
  "guardrail_status": "FAIL",
  "violations": [
    "confidence out of range: -0.1",
    "missing required field: key_findings"
  ],
  "agent_slug": "<originating-skill>",
  "timestamp_utc": "<ISO8601>"
}
```

---

## Communication Standard for Human-Facing Output

When a skill produces output intended for a human operator (not a downstream agent), format the narrative response in this 5-part structure:

```
BOTTOM LINE: [one sentence verdict — always first]
WHAT: [findings with confidence tag: verified / medium / assumed]
WHY THIS MATTERS: [business/security impact, 1-3 sentences]
HOW TO ACT: [action → owner role → urgency]
YOUR DECISION (if applicable): [Option A vs B with trade-offs]
```

**Rules:**
- Bottom line always first — no preamble or context-setting before the verdict
- Maximum 5 WHAT bullets — prioritize by severity
- Every action must have an owner role and a time constraint
- No process narration — state what was found and what to do, not what steps were taken
- YOUR DECISION section included only when the operator must choose between paths with materially different trade-offs

Set `communication_standard_applied: true` in the JSON output when this format is used.
