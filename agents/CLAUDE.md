# Agent Development Guide

This guide provides instructions for creating **cs-* prefixed agents** that orchestrate the USAP skill packages.

## What are cs-* Agents?

**cs-* agents** are specialized orchestrators that combine multiple USAP skills into coherent, role-specific workflows. Each agent:
- References skills via relative paths (`../../<slug>/`)
- Executes Python automation tools from skill packages
- Follows the established SKILL.md workflow patterns
- Maintains skill portability and independence

**Key Principle:** Agents ORCHESTRATE skills, they do not replace them. Skills remain self-contained and portable.

## Agent vs Skill

| Aspect | Agent (cs-*) | Skill |
|---|---|---|
| **Purpose** | Orchestrate and execute workflows | Provide tools, knowledge, templates |
| **Location** | `agents/<domain>/` | `<slug>/` |
| **Structure** | Single .md file with YAML frontmatter | SKILL.md + scripts/ + references/ + assets/ |
| **Integration** | References skills via `../../<slug>/` | Self-contained, no dependencies |
| **Naming** | `cs-security-analyst`, `cs-ciso-advisor` | `threat-hunting`, `secrets-exposure` |

## Directory Structure

```
agents/
├── CLAUDE.md                        # This file
├── security/
│   ├── cs-security-analyst.md       # Tier 2 SOC analyst orchestrator
│   ├── cs-incident-responder.md     # Incident lifecycle manager
│   └── cs-red-teamer.md             # Offensive security coordinator
├── devsecops/
│   └── cs-devsecops-engineer.md     # Security-in-pipeline engineer
└── executive/
    └── cs-ciso-advisor.md           # Executive security advisor
```

## Required Frontmatter

```yaml
---
name: cs-<agent-name>
description: <one-line description>
skills: <primary-skill-slug>
domain: <security|devsecops|executive>
model: sonnet
tools: [Read, Write, Bash, Grep, Glob]
---
```

## Required Sections

1. **Purpose** (2-3 paragraphs)
2. **Skill Integration** (skill location, Python tools, knowledge bases)
3. **Workflows** (minimum 3 workflows with steps and examples)
4. **Integration Examples** (concrete bash commands)
5. **Success Metrics**
6. **Related Agents**
7. **References**

---

## Required Agent Sections (v2)

All cs-* agents created or updated after 2026-03-10 must include these 12 sections in order:

1. **YAML Frontmatter** — Required fields + optional `state:` block
2. **Purpose** — 2-3 paragraphs: role, audience, and what gap the agent fills
3. **Persona** ← NEW — Named identity, background, communication style, operating principles
4. **Critical Actions** ← NEW — ALWAYS (3) and NEVER (3) hard operational rules
5. **Command Menu** ← NEW — 2-letter trigger codes mapped to workflow names + HE (help) + ST (status)
6. **Input Discovery** ← NEW — Documents to auto-discover before prompting for input
7. **Skill Integration** — Skill paths, Python tools, knowledge bases
8. **Workflows** — Minimum 3 workflows, each with MANDATORY EXECUTION RULES + FAILURE MODES + SUCCESS CRITERIA + FAILURE INDICATORS
9. **Integration Examples** — Runnable bash command blocks
10. **Success Metrics** — Measurable outcomes (not aspirational)
11. **Related Agents** — Agents that send to or receive from this agent
12. **References** — Links to primary SKILL.md files used

### Workflow Block Requirements (v2)

Each workflow must include at the top (after **Goal:**):

```
MANDATORY EXECUTION RULES:
1. [rule]
2. [rule]
3. [rule]

FAILURE MODES:
- [condition] → [fallback]
- [condition] → [fallback]
- [condition] → [fallback]
```

And at the bottom (after **Expected Output:**):

```
SUCCESS CRITERIA:
- [measurable outcome]
- [measurable outcome]

FAILURE INDICATORS:
- [observable sign of invalid output]
- [observable sign of invalid output]
```

### Optional `state:` Frontmatter Block

Add to agent YAML to enable workflow state tracking:

```yaml
state:
  active_workflow: null
  steps_completed: []
  input_documents: []
  workflow_started_utc: null
  last_step_completed_utc: null
```

## Path Resolution

From `agents/security/cs-security-analyst.md` to a skill:
```
agents/security/ → ../../ → repo root → threat-hunting/
```

So: `../../threat-hunting/scripts/threat-hunting_tool.py`

## Quality Checklist

- [ ] YAML frontmatter valid
- [ ] `cs-` prefix used
- [ ] All skill slugs referenced are valid (exist in repo)
- [ ] Relative paths resolve correctly
- [ ] At least 3 workflows documented
- [ ] Integration examples tested
- [ ] Success metrics defined

## Creating a New Agent

1. Copy `../../templates/agent-template.md`
2. Fill in YAML frontmatter
3. Write Purpose, Skill Integration, Workflows sections
4. Test all relative paths
5. Update `agents/CLAUDE.md` agent catalog
6. Update root `README.md` agents table
7. Commit: `feat(agents): implement cs-<agent-name>`
