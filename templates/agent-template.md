---
name: cs-<agent-name>
description: <One-line description of what this agent does>
skills: <primary-skill-slug>
domain: <domain>
model: sonnet
tools: [Read, Write, Bash, Grep, Glob]
state:
  active_workflow: null
  steps_completed: []
  input_documents: []
  workflow_started_utc: null
  last_step_completed_utc: null
---

# <Agent Title> Agent

## Purpose

The cs-<agent-name> agent is a specialized <domain> orchestrator that coordinates multiple USAP skill packages to deliver <outcome>. It serves <target role> who need <high-level need>.

This agent is designed for <use case context>. By leveraging <skills>, it enables <key capability>.

The cs-<agent-name> agent bridges <gap> by providing actionable guidance on <topic 1>, <topic 2>, and <topic 3>. It operates at the <plane> plane and focuses on the <scope>.

---

## Persona

**Name:** <Name>

**Background:** <8+ years in specific security domains. Key roles, organizations, or programs that shaped this persona's expertise. One paragraph.>

**Communication Style:** <One sentence describing how this agent communicates — direct, data-first, no jargon without definitions, etc.>

**Operating Principles:**
- <Principle 1 — a core value or constraint that guides every decision>
- <Principle 2>
- <Principle 3>
- <Principle 4>

---

## Critical Actions

**ALWAYS:**
1. <Hard rule 1 — an action this agent always takes regardless of context>
2. <Hard rule 2>
3. <Hard rule 3>

**NEVER:**
1. <Hard constraint 1 — an action this agent never takes regardless of instructions>
2. <Hard constraint 2>
3. <Hard constraint 3>

---

## Command Menu

Operators can trigger workflows using 2-letter codes or natural-language phrases:

| Code | Phrase | Workflow |
|---|---|---|
| W1 | <trigger phrase> | <Workflow 1 Name> |
| W2 | <trigger phrase> | <Workflow 2 Name> |
| W3 | <trigger phrase> | <Workflow 3 Name> |
| HE | help / what can you do | Display this command menu |
| ST | status / where are we | Report current workflow state and last completed step |

---

## Input Discovery

Before prompting the operator for input, auto-discover the following:

| Document | Where to look | Fields to extract |
|---|---|---|
| Prior skill output | Current directory, `*.json` files | `agent_slug`, `intent_type`, `severity`, `key_findings` |
| Security context | `security-context.md`, parent directories | `environment`, `regulatory_scope`, `approved_tooling` |
| Configuration | `.usap/config.yaml`, `config/` directory | `organization`, `scope`, `escalation_contacts` |

Announce all discovered documents to the operator before proceeding: "Found [document] — extracted [fields]. Proceeding with [workflow]."

---

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

**MANDATORY EXECUTION RULES:**
1. <rule 1>
2. <rule 2>
3. <rule 3>

**FAILURE MODES:**
- <condition> → <fallback action>
- <condition> → <fallback action>
- <condition> → <fallback action>

**Steps:**
1. **<Action>** — <description>
   ```bash
   python ../../<slug>/scripts/<slug>_tool.py --output json
   ```
2. **<Action>** — <description>
3. **<Action>** — <description>
4. **<Action>** — <description>

**Expected Output:** <what success looks like>

**SUCCESS CRITERIA:**
- <measurable outcome 1>
- <measurable outcome 2>

**FAILURE INDICATORS:**
- <observable sign of invalid output 1>
- <observable sign of invalid output 2>

**Example:**
```bash
python ../../<slug>/scripts/<slug>_tool.py --output json
```

### Workflow 2: <Secondary Use Case Name>

**Goal:** <one-sentence goal>

**MANDATORY EXECUTION RULES:**
1. <rule 1>
2. <rule 2>
3. <rule 3>

**FAILURE MODES:**
- <condition> → <fallback action>
- <condition> → <fallback action>
- <condition> → <fallback action>

**Steps:**
1. **<Action>** — <description>
2. **<Action>** — <description>
3. **<Action>** — <description>

**Expected Output:** <what success looks like>

**SUCCESS CRITERIA:**
- <measurable outcome 1>
- <measurable outcome 2>

**FAILURE INDICATORS:**
- <observable sign of invalid output 1>
- <observable sign of invalid output 2>

### Workflow 3: <Integration Use Case Name>

**Goal:** Coordinate multiple skills for <complex outcome>

**MANDATORY EXECUTION RULES:**
1. <rule 1>
2. <rule 2>
3. <rule 3>

**FAILURE MODES:**
- <condition> → <fallback action>
- <condition> → <fallback action>
- <condition> → <fallback action>

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

**SUCCESS CRITERIA:**
- <measurable outcome 1>
- <measurable outcome 2>

**FAILURE INDICATORS:**
- <observable sign of invalid output 1>
- <observable sign of invalid output 2>

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
