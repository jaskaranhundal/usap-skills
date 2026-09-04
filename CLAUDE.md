# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

---

## What this repo is

81 standalone LLM skill packages + 13 `cs-*` orchestrator agents for the [Unified Security Agent Platform (USAP)](https://github.com/jaskaranhundal/usap). Each `SKILL.md` is a complete LLM system prompt. Skills are usable standalone (paste into any LLM) or as a USAP git submodule.

---

## Repository layout

```
usap-skills/
├── <domain>/                  # 12 domain directories (see below)
│   ├── CLAUDE.md              # Domain-specific guidance
│   ├── README.md
│   └── <skill-slug>/          # Individual skill package
│       ├── SKILL.md           # LLM system prompt + YAML frontmatter
│       ├── README.md
│       ├── references/workflow.md
│       ├── assets/templates/output-template.json
│       ├── expected_outputs/sample_output.json
│       └── scripts/<slug>_tool.py
├── agents/                    # cs-* orchestrator agents
│   ├── CLAUDE.md              # Agent dev guide — read before creating agents
│   ├── security/              # cs-security-analyst, cs-incident-responder, cs-red-teamer, cs-blue-team-analyst, cs-cloud-investigator, cs-supply-chain-defender, cs-threat-intel-lead, cs-purple-team-lead
│   ├── appsec/                # cs-appsec-engineer
│   ├── devsecops/             # cs-devsecops-engineer
│   └── executive/             # cs-ciso-advisor
├── templates/                 # skill-template.md, agent-template.md, command-template.md
├── standards/                 # frontmatter-spec.md, level-guide.md, naming-conventions.md, output-contract.md
├── shared/scripts/            # cvss_scorer.py, bb_scope_enforcer.py (no external deps)
├── domains/                   # Domain index markdown files (one per domain)
└── references/                # Global reference docs
```

**12 domains:** `appsec-devsecops`, `cloud-infra`, `detection`, `governance`, `identity-access`, `pentest`, `platform-ai`, `red-team`, `response`, `risk-compliance`, `system-security`, `webapp-security`

---

## Common commands

```bash
# Run any skill tool (all tools support --output json)
python <domain>/<slug>/scripts/<slug>_tool.py --output json

# Run with input file
python <domain>/<slug>/scripts/<slug>_tool.py --input payload.json --output json

# Shared utilities (no deps required)
python shared/scripts/cvss_scorer.py --vector "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:C/C:H/I:H/A:H"
python shared/scripts/bb_scope_enforcer.py --target example.com --scope-file scope.json

# Find the next available agent_id before creating a new skill
grep -r "^agent_id:" */*/SKILL.md | awk -F': ' '{print $2}' | sort -n | tail -1

# Validate frontmatter presence across all skills
grep -rL "^agent_slug:" */*/SKILL.md
```

---

## Architecture: Skills vs Agents

| | Skill | cs-* Agent |
|---|---|---|
| Location | `<domain>/<slug>/` | `agents/<domain>/` |
| Structure | Full package (SKILL.md + scripts + refs + assets) | Single `.md` file with YAML frontmatter |
| Purpose | Self-contained LLM prompt + CLI tool | Orchestrates multiple skills into a workflow |
| References other skills | Never (self-contained) | Via relative paths `../../<slug>/` |
| Naming | `kebab-case` slugs | `cs-` prefix required |

**Key principle:** Agents orchestrate skills; skills never depend on other skills.

---

## SKILL.md frontmatter

Two frontmatter formats coexist. The **canonical format** (used in `templates/skill-template.md`) is the new standard:

```yaml
---
name: <slug>
description: USAP agent skill for <Title>. Use for <one-line purpose>.
license: MIT
metadata:
  version: 1.0.0
  author: USAP Team
  category: usap-detection   # see standards/frontmatter-spec.md for allowed values
  updated: YYYY-MM-DD
  agent_slug: "<slug>"       # quoted; must match name exactly
---
```

Older skills use an extended frontmatter (with `agent_id`, `level`, `plane`, `phase`, `ttl`, `approval_required`, `mutating_intents`, `can_execute`, `providers`, `required_invoke_role`, `required_approver_role`, `input_schema`, `output_schema`, `runtime_contract`). Both are valid — do not convert old skills unless explicitly asked.

---

## Skill levels

| Level | Role | Autonomy | Mutating? |
|---|---|---|---|
| L1 | Advisory / Board | Fully autonomous output | Never |
| L2 | CISO / Management | Autonomous analysis | Notifications only |
| L3 | SOC Analyst | Autonomous reads | Read-only tools |
| L4 | Technical / Expert | Supervised execution | Requires human gate |

Mutating intents (L4 skills that can recommend key rotation, isolation, etc.) must set `human_approval_required: true` in their output.

---

## Output contract

Every skill tool and SKILL.md must produce a JSON payload with these required fields:

| Field | Type | Notes |
|---|---|---|
| `agent_slug` | string | Must match directory slug |
| `intent_type` | string | `detect`, `respond`, `analyze`, `advise`, `escalate`, `report`, or `block` |
| `action` | string | Plain-English recommended next action |
| `rationale` | string | Evidence-based explanation |
| `confidence` | float | 0.0–1.0; below 0.5 = inconclusive |
| `severity` | string | `critical`, `high`, `medium`, `low`, or `informational` |
| `key_findings` | array[string] | At least one entry required |
| `evidence_references` | array[object] | Required when severity >= `high` |
| `next_agents` | array[string] | Downstream skill slugs (empty if terminal) |
| `human_approval_required` | boolean | True for any mutating action |
| `timestamp_utc` | string | ISO 8601 UTC |

Full schema and canonical example: `standards/output-contract.md`

---

## Naming conventions (enforced)

- Skill slugs: `lowercase-hyphenated`, max 4 words, no version suffixes
- Script files: `<slug>_tool.py` (hyphen in slug preserved, not converted to underscore)
- `cs-*` agents: `cs-` prefix, domain-scoped name
- Commit messages: Conventional Commits — `feat(skills):`, `fix(scripts):`, `docs(readme):`, `refactor(structure):`, `chore:`

Full spec: `standards/naming-conventions.md`

---

## Adding a new skill

1. Check the next `agent_id` (run the grep command above)
2. Copy `templates/skill-template.md` → `<domain>/<slug>/SKILL.md`
3. Create the full package structure: `SKILL.md`, `README.md`, `references/workflow.md`, `assets/templates/output-template.json`, `expected_outputs/sample_output.json`, `scripts/<slug>_tool.py`
4. Ensure the SKILL.md body contains: Identity section, at least one classification/decision table with MITRE ATT&CK mappings, numbered Reasoning Procedure, explicit Intent Classification rule
5. The Runtime Contract line must read: `../../agents/<slug>.yaml`
6. Verify quality checklist in `CONTRIBUTING.md` before committing

**Do not place skills at the repo root.** All skills live inside a domain subdirectory.

---

## Adding a new cs-* agent

1. Copy `templates/agent-template.md` → `agents/<domain>/cs-<name>.md`
2. Add YAML frontmatter with `cs-` prefix, `skills`, `domain`, `model: sonnet`, `tools`
3. Reference skills via `../../<slug>/scripts/<slug>_tool.py` (relative from `agents/<domain>/`)
4. Minimum 3 workflows with concrete bash commands
5. Update `agents/CLAUDE.md` agent catalog and root `README.md` agents table

Full guide: `agents/CLAUDE.md`

---

## Shared utilities

Scripts in `shared/scripts/` have no external dependencies. A script belongs here only if used by 3+ skills or provides core algorithmic capability (scoring, validation, classification). Single-skill helpers go in that skill's own `scripts/` directory.

---

## Domain CLAUDE.md files

Each domain directory contains a `CLAUDE.md` with: skills catalog, Python tools reference, SDLC/workflow integration, cascade intelligence (cross-skill routing), and domain-specific best practices. Read the relevant `<domain>/CLAUDE.md` before modifying skills in that domain.
