---
name: cs-<agent-name>
description: <One-line description of what this agent does>
skills: <primary-skill-slug>
domain: <domain>
model: sonnet
tools: [Read, Write, Bash, Grep, Glob]
---

# <Agent Title> Agent

## Purpose

The cs-<agent-name> agent is a specialized <domain> orchestrator that coordinates multiple USAP skill packages to deliver <outcome>. It serves <target role> who need <high-level need>.

This agent is designed for <use case context>. By leveraging <skills>, it enables <key capability>.

The cs-<agent-name> agent bridges <gap> by providing actionable guidance on <topic 1>, <topic 2>, and <topic 3>. It operates at the <plane> plane and focuses on the <scope>.

## Skill Integration

**Primary Skills:**
- `../../<slug-1>/` — <purpose>
- `../../<slug-2>/` — <purpose>
- `../../<slug-3>/` — <purpose>

### Python Tools

1. **<Tool Name>**
   - **Purpose:** <what it does>
   - **Path:** `../../<slug>/scripts/<slug>_tool.py`
   - **Usage:** `python ../../<slug>/scripts/<slug>_tool.py --output json`
   - **Use Cases:** <when to invoke>

2. **<Tool Name>**
   - **Purpose:** <what it does>
   - **Path:** `../../<slug>/scripts/<slug>_tool.py`
   - **Usage:** `python ../../<slug>/scripts/<slug>_tool.py --output json`
   - **Use Cases:** <when to invoke>

### Knowledge Bases

1. **<Reference Name>**
   - **Location:** `../../<slug>/references/workflow.md`
   - **Content:** <what's inside>
   - **Use Case:** <when to reference>

### Templates

1. **Output Template**
   - **Location:** `../../<slug>/assets/templates/output-template.json`
   - **Use Case:** Validate agent output structure

## Workflows

### Workflow 1: <Primary Use Case Name>

**Goal:** <one-sentence goal>

**Steps:**
1. **<Action>** — <description>
   ```bash
   python ../../<slug>/scripts/<slug>_tool.py --output json
   ```
2. **<Action>** — <description>
3. **<Action>** — <description>
4. **<Action>** — <description>

**Expected Output:** <what success looks like>

**Example:**
```bash
python ../../<slug>/scripts/<slug>_tool.py --output json
```

### Workflow 2: <Secondary Use Case Name>

**Goal:** <one-sentence goal>

**Steps:**
1. **<Action>** — <description>
2. **<Action>** — <description>
3. **<Action>** — <description>

**Expected Output:** <what success looks like>

### Workflow 3: <Integration Use Case Name>

**Goal:** Coordinate multiple skills for <complex outcome>

**Steps:**
1. **Initiate** — Load skill 1
   ```bash
   python ../../<slug-1>/scripts/<slug-1>_tool.py --output json
   ```
2. **Enrich** — Feed output to skill 2
   ```bash
   python ../../<slug-2>/scripts/<slug-2>_tool.py --output json
   ```
3. **Report** — Consolidate findings

**Expected Output:** Consolidated structured report

## Integration Examples

```bash
# Run primary skill tool
python ../../<slug>/scripts/<slug>_tool.py --output json

# Chain skills
python ../../<slug-1>/scripts/<slug-1>_tool.py --output json | \
  python ../../<slug-2>/scripts/<slug-2>_tool.py --input -
```

## Success Metrics

- **Coverage:** Percentage of <scope> assessed per engagement
- **MTTD:** Mean time to detection reduced by target %
- **Finding rate:** Number of actionable findings per run
- **Escalation accuracy:** False positive rate on escalations

## Related Agents

- [cs-<related-agent>](../<domain>/cs-<related-agent>.md) — <how they relate>

## References

- [Primary Skill Documentation](../../<slug>/SKILL.md)
- [Workflow Guide](../../<slug>/references/workflow.md)
- [Agent Development Guide](../CLAUDE.md)
