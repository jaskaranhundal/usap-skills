# Level Guide

This document defines the L1–L4 skill levels used across USAP skill packages, along with plane definitions, phase mappings, and role mapping tables.

---

## Level Definitions

| Level | Name | Description | Autonomy | Human Gate |
|---|---|---|---|---|
| **L1** | Advisory | Provides frameworks and guidance only. No actions taken. | Fully autonomous output | Never required |
| **L2** | Analytical | Produces analysis, scores, and recommendations. May trigger notifications. | Autonomous analysis | Required for notifications |
| **L3** | Operational | Executes bounded queries and assessments. May invoke read-only tools. | Autonomous reads | Required for writes |
| **L4** | Executive | Can invoke mutating actions (write, delete, block, isolate). | Supervised execution | Always required |

### Level Selection Guide

- **Use L1** when the skill only produces threat models, frameworks, or advisory documents.
- **Use L2** when the skill produces scores, risk ratings, or board-level summaries.
- **Use L3** when the skill executes queries against live telemetry or runs scans.
- **Use L4** when the skill can take actions that change system state (revoke keys, isolate hosts, block IPs).

---

## Level → Invocation-Control Mapping

These bind the L1–L4 levels above to specific Claude Code invocation-control frontmatter fields (see `standards/frontmatter-spec.md` "Invocation Control"). `tools/validate_invocation_control.py` enforces these invariants.

| Level | `disable-model-invocation` | `user-invocable` | `allowed-tools` | `context` |
|---|---|---|---|---|
| **L1 (advisory)** | `false` | optional (`false` for pure helper skills) | omitted (no host-tool dependency) | `inherit` |
| **L2 (analytical)** | `false` | `true` | omitted | `inherit` |
| **L3 (operational)** | `false` | `true` | **required non-empty** (declare read tools) | `fork` recommended for evidence-handling skills |
| **L4 (executive)** | **`true` (required)** | `true` | **required non-empty** (declare mutating tools) | `fork` recommended |

### Rationale

- **L4 + `disable-model-invocation: true`** — the L4 contract gates every mutating action behind a human. The frontmatter field is the machine-readable expression of that gate. External hosts (Claude Code, Cursor, Goose) will refuse to let the model auto-invoke the skill.
- **L3 / L4 + non-empty `allowed-tools`** — declare the host tools the skill expects so clients can refuse out-of-policy commands without parsing prose. Skills with no host-tool dependency (purely analytical) omit the field.
- **`disallowed-tools: "Bash(rm:*) Bash(sudo:*)"`** is recommended on every L3 / L4 skill as layered defense; the runtime should already block these.
- **`context: fork`** on evidence-handling L3 skills makes outputs reproducible — the skill cannot be biased by prior chat history.

### Where the level is declared

USAP currently signals the level in two places:

1. **The `metadata.usap_level` field** (recommended, optional). Add to canonical frontmatter as a string `"L1"` / `"L2"` / `"L3"` / `"L4"`. Read by the validator.
2. **The body decision table** ("L3 / Operational") — humans read this; the validator does not parse it.

Until `metadata.usap_level` is backfilled, the validator falls back to heuristics: skills with body text mentioning "mutating", "containment", or having an `_actor.py` script are flagged as L4 candidates and warned about missing `disable-model-invocation`.

---

## Plane Definitions

| Plane | Description | Skills |
|---|---|---|
| **work** | Hands-on analysis and operations | `threat-hunting`, `forensics`, `red-team-operations` |
| **control** | Orchestration, gating, and policy enforcement | `orchestrator`, `guardrail`, `tool-execution-broker` |
| **governance** | Risk, compliance, and executive reporting | `enterprise-risk-assessment`, `compliance-mapping`, `metrics-reporting` |

---

## Phase Definitions

| Phase | Description | Typical Actions |
|---|---|---|
| **phase1** | Preparation and planning | Threat modeling, policy review, architecture assessment |
| **phase2** | Active analysis and detection | Threat hunting, SIEM queries, posture scanning |
| **phase3** | Response and recovery | Containment, forensics, remediation tracking |

---

## Role Mapping Table

| Skill Level | Primary Operator Role | Secondary Operator Role |
|---|---|---|
| L1 | Security Architect | Risk Officer |
| L2 | Security Manager | CISO / Board |
| L3 | SOC Analyst (Tier 2) | Threat Hunter |
| L4 | Incident Commander | SOC Lead |

---

## Level x Plane Matrix

| | work | control | governance |
|---|---|---|---|
| **L1** | Threat modeling, architecture review | — | Policy advisory |
| **L2** | Risk scoring, posture assessment | Orchestration routing | Board reporting |
| **L3** | Active threat hunting, SIEM queries | Guardrail validation | Compliance mapping |
| **L4** | Incident response, exploitation | Tool execution brokering | Regulatory escalation |

---

## Frontmatter Usage

In `SKILL.md`:
```yaml
metadata:
  level: L3
  plane: work
  phase: phase2
```

In agent files:
```yaml
---
level: L4
plane: control
---
```
