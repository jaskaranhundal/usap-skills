# cs-* Agent Contract (v2)

Every `cs-*` orchestrator agent in `agents/<domain>/cs-<slug>.md` must conform to this contract. The contract was promoted out of prose in `agents/CLAUDE.md` on 2026-06-20 into this standards file so contributors can review it without re-reading the dev guide. The dev guide remains the authoring walkthrough; this file is the spec.

## Required YAML frontmatter

```yaml
---
name: cs-<slug>                 # kebab-case; cs- prefix required
description: <one-line description, 50+ chars>
skills: <primary-skill-slug>    # comma-separated if multiple
domain: security | appsec | devsecops | executive | governance
model: sonnet
tools: [Read, Write, Bash, Grep, Glob]
state:                          # optional but recommended
  active_workflow: null
  steps_completed: []
  input_documents: []
  workflow_started_utc: null
  last_step_completed_utc: null
---
```

`state:` is optional but recommended. When present, the orchestrator tracks workflow state across operator turns.

## Required body sections (12, in order)

1. **YAML Frontmatter** — required fields above plus optional `state:` block.
2. **Purpose** — 2–3 paragraphs: role, audience, the gap this agent fills.
3. **Persona** — Named identity, background, communication style, operating principles.
4. **Critical Actions** — Three ALWAYS rules and three NEVER rules. No more, no fewer.
5. **Command Menu** — 2-letter trigger codes mapped to workflow names. `HE` (help) and `ST` (status) are required. 4–8 codes total is the sweet spot.
6. **Input Discovery** — Documents to auto-discover before prompting for input. Format: table of `(document, location, fields)`.
7. **Skill Integration** — Skill paths (relative from `agents/<domain>/`), Python tools, knowledge bases. Sub-sections for primary skills and cascades.
8. **Workflows** — At least three. Each workflow block must include the four required sub-blocks (see below).
9. **Integration Examples** — Runnable bash command blocks the operator can copy.
10. **Success Metrics** — Measurable outcomes (counts, percentages, latencies). Not aspirational.
11. **Related Agents** — `Sends to:` and `Receives from:` lines naming the connected `cs-*` agents.
12. **References** — Links to primary `SKILL.md` files used and any standards referenced.

## Workflow block sub-blocks (4 required)

Inside every workflow:

```
**Goal:** <one sentence>

**MANDATORY EXECUTION RULES:**
1. <rule>
2. <rule>
3. <rule>

**Steps:** <runnable bash or numbered prose>

**FAILURE MODES:**
- <condition> → <fallback>
- <condition> → <fallback>
- <condition> → <fallback>

**Expected Output:** <one paragraph naming the artifact shape>

**SUCCESS CRITERIA:**
- <measurable outcome>
- <measurable outcome>

**FAILURE INDICATORS:**
- <observable sign of invalid output>
- <observable sign of invalid output>
```

Each agent ships at least three workflows. Each workflow's sub-blocks are non-optional — a workflow missing any of the four (MANDATORY EXECUTION RULES, FAILURE MODES, SUCCESS CRITERIA, FAILURE INDICATORS) is a v1 artifact and fails the contract.

## Passive vs Reactive split (architectural rule)

- **Passive workflows are owned exclusively by `cs-security-program-manager`.** No other `cs-*` agent self-initiates a passive/scheduled workflow.
- **Reactive workflows** are owned by their domain agent (`cs-security-analyst`, `cs-incident-responder`, `cs-red-teamer`, `cs-blue-team-analyst`, `cs-appsec-engineer`, `cs-devsecops-engineer`, `cs-ciso-advisor`).
- `cs-security-program-manager` may route findings to any reactive agent; reactive agents never dispatch back. Reactive outputs may be consumed by `cs-security-program-manager` in subsequent passive scans.

A finding escalates from a passive workflow (e.g., `SC` proactive scan) to a reactive agent (`AT` alert triage) only when (a) severity is `critical` or `high` AND (b) corroborated by ≥ 2 independent passive scan signals.

## Path resolution

Skill paths inside an agent file are relative from the agent's location:

```
agents/security/cs-security-analyst.md  →  ../../detection/threat-hunting/
```

Use `../../<domain>/<slug>/` for skills and `../<other-domain>/cs-<slug>.md` for sibling agents.

## Naming

- `cs-` prefix is required.
- Slug is kebab-case, max 4 words.
- File lives in `agents/<owning-domain>/cs-<slug>.md`.
- Catalog entry in `agents/CLAUDE.md` and `README.md` agents table must be updated in the same PR.

## Quality checklist (PR review)

- [ ] YAML frontmatter valid; `cs-` prefix; all skill slugs in `skills:` exist on disk.
- [ ] All 12 body sections present, in order.
- [ ] Three ALWAYS and three NEVER rules in Critical Actions.
- [ ] Command Menu includes `HE` and `ST`.
- [ ] At least three workflows; each with all four sub-blocks.
- [ ] Relative skill paths resolve (`../../<domain>/<slug>/`).
- [ ] Success Metrics are measurable, not aspirational.
- [ ] `agents/CLAUDE.md` catalog and `README.md` agents table updated.

Contract version: **v2.0** (this file). Bumping the contract requires a major-version PR that updates every existing `cs-*` agent.
