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
