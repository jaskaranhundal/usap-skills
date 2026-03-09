---
name: <slug>
description: USAP agent skill for <Title>. Use for <one-line purpose>.
license: MIT
metadata:
  version: 1.0.0
  author: USAP Team
  category: usap-operations
  updated: 2026-03-08
  agent_slug: "<slug>"
---

# <Title>

## Overview
<2-3 sentence description of what this skill does, when to invoke it, and what it produces.>

## Keywords
- usap
- security-agent
- mcp
- <domain-tag>
- <phase-tag>
- operations

## Quick Start
```bash
python scripts/<slug>_tool.py --help
python scripts/<slug>_tool.py --output json
```

## Core Workflows
1. Validate input context and required fields.
2. Apply deterministic and policy-aligned reasoning for agent <slug>.
3. Emit structured recommendation payloads for orchestrator processing.
4. Enforce human approval gates for mutating actions.

---

## Skill Identity

| Field | Value |
|---|---|
| **Slug** | `<slug>` |
| **Level** | L<N> |
| **Plane** | work / control / governance |
| **Phase** | phase1 / phase2 / phase3 |
| **Domain** | <domain> |
| **Role** | <analyst role this skill serves> |
| **Authorization required** | yes / no |

---

## Input Schema

```json
{
  "event_type": "<event_type>",
  "severity": "critical | high | medium | low | informational",
  "raw_payload": {
    "<field>": "<description>"
  },
  "context": {
    "environment": "production | staging | development",
    "affected_systems": [],
    "timestamp_utc": "<ISO8601>"
  }
}
```

---

## Core Methodology

### Step 1: Input Validation
Verify all required fields are present. Reject inputs missing `event_type` or `raw_payload` with a structured error.

### Step 2: <Primary Analysis Step>
<Describe the main analytical process this skill performs.>

### Step 3: <Secondary Step>
<Describe any supporting analysis, scoring, or enrichment.>

### Step 4: Output Generation
Produce a structured JSON payload conforming to the output contract. Include `action`, `rationale`, `intent_type`, `confidence`, `key_findings`, `evidence_references`, and `timestamp_utc`.

---

## Output Contract

```json
{
  "agent_slug": "<slug>",
  "intent_type": "<intent_type>",
  "action": "<recommended action>",
  "rationale": "<reasoning>",
  "confidence": 0.0,
  "severity": "critical | high | medium | low | informational",
  "key_findings": [],
  "evidence_references": [],
  "next_agents": [],
  "human_approval_required": true,
  "timestamp_utc": "<ISO8601>"
}
```

---

## Escalation Logic

| Condition | Action |
|---|---|
| Confidence < 0.5 | Flag as inconclusive, request additional telemetry |
| Severity = critical | Immediately escalate to `incident-commander` |
| Authorization missing | Abort and return policy violation error |
| Data quality insufficient | Escalate to `telemetry-signal-quality` |

---

## Related Skills

- `orchestrator` — routes events to this skill
- `incident-commander` — receives escalations from this skill
- `findings-tracker` — records findings produced by this skill

---

## References

- [Workflow Guide](references/workflow.md)
- [Output Template](assets/templates/output-template.json)
- [Sample Output](expected_outputs/sample_output.json)
