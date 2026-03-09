# Red Team Domain

---

## AUTHORIZATION WARNING

No skill in this domain may be invoked without explicit written authorization from the asset owner. A signed Rules of Engagement (RoE) document with defined scope boundaries, abort procedures, and a legal authorization letter must be in hand before any engagement planning or tool execution begins. Unauthorized use of these skills against systems you do not own or have not been granted explicit written permission to test is illegal and a violation of this repository's use policy.

---

Seven skill packages covering the full adversarial engagement lifecycle: planning, operations, safe exploitation, continuous penetration testing, attack path analysis, AI/ML adversarial testing, and security research. All skills enforce an authorization gate at invocation. Mutating actions against target systems require an approved RoE document before any action is taken.

---

## Skills

| Skill | Slug | Level | Intent | Description |
|---|---|---|---|---|
| [Red Team Planner](red-team-planner/SKILL.md) | `red-team-planner` | L3 | `read_only` + `mutating/engagement_action` | Engagement planning, objectives definition, scope boundary documentation, RoE validation, and phase map generation. First skill to invoke; validates the Authorization Gate. |
| [Red Team Operations](red-team-operations/SKILL.md) | `red-team-operations` | L3 | `mutating/engagement_action` | Kill chain execution planning: OPSEC design, C2 architecture selection, lateral movement playbooks, and exfil staging. Requires signed RoE. |
| [Safe Exploitation](safe-exploitation/SKILL.md) | `safe-exploitation` | L3 | `mutating/engagement_action` | Scoped exploitation within defined RoE boundaries. Enforces minimal footprint, mandatory abort conditions, and post-exploitation scope validation before each action. |
| [Continuous Pentesting](continuous-pentesting/SKILL.md) | `continuous-pentesting` | L3 | `read_only` | Ingests and prioritizes BAS (Breach and Attack Simulation) tool results, identifies automated testing coverage gaps, and deduplicates findings against manual engagement output. |
| [Attack Path Analysis](attack-path-analysis/SKILL.md) | `attack-path-analysis` | L3 | `read_only` | Maps lateral movement paths through network topology from a starting node to target assets. Identifies choke points and defensive gaps. Read-only analysis; execution requires `red-team-operations`. |
| [AI Red Teaming](ai-red-teaming/SKILL.md) | `ai-red-teaming` | L4 | `mutating/engagement_action` | Adversarial testing of AI/ML systems: prompt injection, jailbreaks, model inversion, training data extraction, and alignment bypass testing. Requires explicit AI system owner authorization. |
| [Security Research](security-research/SKILL.md) | `security-research` | L3 | `read_only` + `mutating/engagement_action` | CVE research, scoped PoC development, vulnerability reproduction, and responsible disclosure workflow support. PoC scope is validated before any development begins. |

---

## Agent Links

The primary orchestrator for this domain is the [cs-red-teamer](../agents/security/cs-red-teamer.md) agent. It coordinates red team skills for full engagement lifecycle management, enforces the Authorization Gate at invocation, sequences skills across the six-phase engagement lifecycle, and routes final reports to the appropriate downstream consumers.

Typical orchestration patterns:

- Full engagement: `red-team-planner` -> `red-team-operations` -> `safe-exploitation` -> `attack-path-analysis` -> `continuous-pentesting` -> `red-team-planner` (reporting phase)
- AI system assessment: `red-team-planner` -> `ai-red-teaming` -> `red-team-planner` (reporting phase)
- CVE validation: `security-research` -> `safe-exploitation` (authorized reproduction) -> `red-team-planner` (disclosure documentation)
- Automated coverage gap: `continuous-pentesting` -> `attack-path-analysis` -> `red-team-operations` (targeted manual follow-up)

---

## Quick Commands

Run any skill tool directly from the repository root. All tools accept `--help` and `--output json` for structured output. All tools enforce authorization validation as the first step.

**red-team-planner**
```bash
python red-team/red-team-planner/scripts/red-team-planner_tool.py --help

# Generate engagement phase map from scope file
python red-team/red-team-planner/scripts/red-team-planner_tool.py \
  --scope-file ./engagement/scope.json --duration-days 14 --output json
```

**red-team-operations**
```bash
python red-team/red-team-operations/scripts/red-team-operations_tool.py --help

# Generate kill chain phase plan for initial access phase
python red-team/red-team-operations/scripts/red-team-operations_tool.py \
  --phase initial-access --opsec-level high --output json

# C2 architecture design
python red-team/red-team-operations/scripts/red-team-operations_tool.py \
  --phase command-and-control --c2-type https-malleable --output json
```

**safe-exploitation**
```bash
python red-team/safe-exploitation/scripts/safe-exploitation_tool.py --help

# Scoped exploitation attempt with abort conditions
python red-team/safe-exploitation/scripts/safe-exploitation_tool.py \
  --target 10.1.2.3 --scope-file ./engagement/scope.json \
  --abort-conditions ./engagement/abort.json --output json
```

**continuous-pentesting**
```bash
python red-team/continuous-pentesting/scripts/continuous-pentesting_tool.py --help

# Ingest and prioritize BAS tool results
python red-team/continuous-pentesting/scripts/continuous-pentesting_tool.py \
  --bas-results ./bas-output.json --framework attack --priority-threshold high --output json
```

**attack-path-analysis**
```bash
python red-team/attack-path-analysis/scripts/attack-path-analysis_tool.py --help

# Map lateral movement paths from initial access to target
python red-team/attack-path-analysis/scripts/attack-path-analysis_tool.py \
  --source-node 10.1.2.3 --target-asset db-prod-01 \
  --topology-file ./engagement/topology.json --output json
```

**ai-red-teaming**
```bash
python red-team/ai-red-teaming/scripts/ai-red-teaming_tool.py --help

# Prompt injection test suite
python red-team/ai-red-teaming/scripts/ai-red-teaming_tool.py \
  --model-endpoint https://api.internal/v1/chat \
  --test-type prompt-injection --output json

# Full adversarial test catalog
python red-team/ai-red-teaming/scripts/ai-red-teaming_tool.py \
  --model-endpoint https://api.internal/v1/chat \
  --test-type all --attack-catalog standard --output json
```

**security-research**
```bash
python red-team/security-research/scripts/security-research_tool.py --help

# CVE research and PoC scope validation
python red-team/security-research/scripts/security-research_tool.py \
  --cve-id CVE-2024-12345 --target-version 3.2.1 \
  --disclosure-deadline 2025-06-01 --output json
```

---

## Engagement Lifecycle

```
red-team-planner  →  red-team-operations  →  safe-exploitation  →  attack-path-analysis
                                                                            |
                                          continuous-pentesting  ←──────────┘
                                                   |
                                          security-research  (if CVE or novel technique required)
                                                   |
                                          red-team-planner  (reporting phase)
```

1. `red-team-planner` validates authorization, defines objectives, and generates the phase map.
2. `red-team-operations` plans kill chain execution with OPSEC and C2 design.
3. `safe-exploitation` executes scoped exploitation within abort conditions.
4. `attack-path-analysis` maps lateral movement paths to target assets.
5. `continuous-pentesting` identifies automated testing gaps and validates BAS coverage.
6. `security-research` supports novel vulnerability research within defined disclosure scope.
7. `red-team-planner` aggregates all findings into the final report with ATT&CK mapping.

---

## Kill Chain Coverage

| Kill Chain Phase | Skills |
|---|---|
| Reconnaissance | red-team-operations, attack-path-analysis |
| Weaponization | red-team-planner, security-research |
| Delivery | safe-exploitation, red-team-operations |
| Exploitation | safe-exploitation |
| Installation | red-team-operations, safe-exploitation |
| Command and Control | red-team-operations |
| Actions on Objectives | attack-path-analysis, safe-exploitation |

---

## Pre-Engagement Authorization Checklist

Before invoking any skill in this domain, confirm the following items are satisfied:

- [ ] Signed Rules of Engagement document with asset owner signature
- [ ] Defined in-scope IP ranges, domains, accounts, and systems
- [ ] Explicit out-of-scope declarations
- [ ] Emergency contact list and abort escalation path
- [ ] Data handling agreement for discovered vulnerabilities
- [ ] Legal authorization letter from asset owner or designated representative
- [ ] Engagement start and end dates confirmed in writing

For AI red teaming, additionally confirm:
- [ ] Written AI system owner authorization naming the specific model endpoint
- [ ] Confirmation that the endpoint is non-production or production testing is explicitly authorized

---

## Downstream Integrations

| Finding Type | Cascades To |
|---|---|
| Detection gap confirmed by red team | `detection/detection-engineering` (new rule candidates) |
| UEBA evasion finding | `detection/behavioral-analytics` (threshold calibration) |
| Application vulnerability confirmed exploitable | `appsec-devsecops/sast-dast-coordinator` (scanner gap) |
| CVE confirmed reproducible | `security-research` (disclosure workflow), `vulnerability-management` |
| Attack path to critical asset confirmed | `risk-compliance/findings-tracker`, `ciso-brief-generator` |
| AI safety filter bypass confirmed | `platform-ai/` (model hardening guidance) |

---

## Full Domain Guide

For complete methodology, the six-phase engagement lifecycle, Authorization Gate details, Kill Chain Phase Coverage Matrix, AI red teaming sub-phases, MITRE ATT&CK technique coverage, domain best practices, and authoring notes, see [CLAUDE.md](./CLAUDE.md).
