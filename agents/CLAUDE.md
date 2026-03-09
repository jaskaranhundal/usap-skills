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
