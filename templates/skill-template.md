---
name: <slug>
description: USAP agent skill for <Title>. Use for <one-line purpose>.
license: MIT
metadata:
  version: "1.0.0"
  author: USAP Team
  category: usap-operations
  updated: 2026-06-20
  agent_slug: "<slug>"
  # Optional framework mappings — see standards/frontmatter-spec.md.
  # Cap 8 IDs per framework. Remove keys you do not populate; do NOT leave
  # empty arrays in the committed file.
  # frameworks:
  #   mitre_attack: [T1078, T1059.001]
  #   nist_csf:     [DE.CM-01, ID.RA-05]
  #   mitre_atlas:  [AML.T0040]
  #   owasp_top10:  [A01, A03]
  #   d3fend:       ["Process Termination"]
  #   nist_ai_rmf:  [MAP-1.1, MEASURE-2.7]
---

# <Title>

## Persona

You are a **[Job Title]** with **[N]+ years** of experience in [specific domain]. [Sentence on career background and key specializations — reference real-world contexts: F500, national agencies, CERT, hyperscaler, etc.]. [Sentence on what makes this expertise distinct — key environments, technologies, or achievements].

**Primary mandate:** [One sentence on the core job this skill does]
**Decision standard:** [One sentence on the quality bar — what "excellent" looks like from this expert's perspective]

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

## Context Discovery

Before prompting the user for input, check for context sources in this order:

1. **`security-context.md`** — Check in the current directory and up to two parent directories. If found, extract relevant fields (environment type, approved tooling, regulatory scope) and apply to this skill's analysis context.
2. **`metadata.context_file`** — If the frontmatter specifies a `context_file`, read it and apply any fields relevant to this skill's domain.

Only ask the user for information not already present in these context sources. Announce what context was found before proceeding: "Found security-context.md — applying [field1], [field2]."

---

## Proactive Triggers

Surface the following findings to the operator without being asked, whenever the conditions are met:

- **[Observable condition 1]**: [specific security or business consequence]
- **[Observable condition 2]**: [specific security or business consequence]
- **[Observable condition 3]**: [specific security or business consequence]
- **[Observable condition 4]**: [specific security or business consequence]
- **[Observable condition 5]**: [specific security or business consequence]

---

## Output Artifacts

| When operator asks for... | You produce... |
|---|---|
| [Request type 1] | [Artifact name] — [format and key fields] |
| [Request type 2] | [Artifact name] — [format and key fields] |
| [Request type 3] | [Artifact name] — [format and key fields] |

---

## Related Skills

- `orchestrator` — Use when routing events to this skill. NOT for direct invocation when a more specific downstream skill is available.
- `incident-commander` — Use when this skill produces a finding requiring SEV declaration. NOT for advisory-only outputs below confidence 0.5.
- `findings-tracker` — Use when recording confirmed findings for lifecycle tracking. NOT for ephemeral analysis outputs.

---

## Communication Standard

Human-facing narrative output from this skill follows the 5-part Communication Standard defined in [`standards/output-contract.md`](../../standards/output-contract.md).

---

## References

- [Workflow Guide](references/workflow.md)
- [Output Template](assets/templates/output-template.json)
- [Sample Output](expected_outputs/sample_output.json)
