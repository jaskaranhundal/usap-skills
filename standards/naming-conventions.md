# Naming Conventions

This document defines all naming patterns for the USAP skills repository.

---

## Skill Slug Patterns

| Pattern | Rule | Example |
|---|---|---|
| All lowercase | No uppercase letters | `threat-hunting` not `Threat-Hunting` |
| Hyphens only | No underscores or spaces | `cloud-security-posture` not `cloud_security_posture` |
| Descriptive noun phrases | Describes what the skill does | `secrets-exposure`, `identity-access-risk` |
| No version suffixes | Versioning via frontmatter | `vulnerability-management` not `vulnerability-management-v2` |
| Maximum 4 words | Keep slugs concise | `zero-day-response` not `zero-day-incident-response-advisor` |

---

## Script Naming

| Pattern | Rule | Example |
|---|---|---|
| `<slug>_tool.py` | Primary CLI tool | `threat-hunting_tool.py` |
| `pre_analysis.py` | Optional deterministic pre-processing | `pre_analysis.py` |
| Snake case | Python files use underscores | `threat_hunting_tool.py` (alternative for importability) |
| No spaces | No spaces in any filename | N/A |

**Note:** The primary tool filename uses the full slug with hyphen preserved (`<slug>_tool.py`) to match the directory name exactly. Internal Python identifiers use snake_case per PEP 8.

---

## Agent Naming

| Pattern | Rule | Example |
|---|---|---|
| `cs-` prefix | All agent files start with `cs-` | `cs-security-analyst` |
| Domain-scoped | Reflect the domain in the name | `cs-devsecops-engineer` |
| Max 4 words after prefix | Keep agent names concise | `cs-ciso-advisor` |

---

## File Structure Conventions

```
<slug>/
├── SKILL.md                    # Uppercase, no extension alternatives
├── README.md                   # Uppercase
├── references/
│   └── workflow.md             # Lowercase
├── assets/
│   └── templates/
│       └── output-template.json  # Lowercase, hyphens
├── expected_outputs/
│   └── sample_output.json      # Lowercase, underscores for directory
└── scripts/
    └── <slug>_tool.py          # Lowercase, slug + _tool.py
```

---

## Domain Directory Names

| Domain | Directory |
|---|---|
| Security Agents | `agents/security/` |
| DevSecOps Agents | `agents/devsecops/` |
| Executive Agents | `agents/executive/` |
| Detection Domain | `domains/detection.md` |
| Response Domain | `domains/response.md` |

---

## Commit Message Conventions

Follow Conventional Commits:

| Type | When to use | Example |
|---|---|---|
| `feat` | New skill or agent | `feat(skills): add ai-red-teaming skill package` |
| `fix` | Bug fix in script or content | `fix(scripts): correct cvss scoring in secrets-exposure` |
| `docs` | Documentation only change | `docs(readme): add agents table to index` |
| `refactor` | Restructure without new features | `refactor(structure): reorganize into domains/ layout` |
| `chore` | Maintenance tasks | `chore(deps): update frontmatter dates` |
