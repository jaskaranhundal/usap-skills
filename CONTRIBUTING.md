# Contributing to usap-skills

This repo is the public skill library for [USAP](https://github.com/jaskaranhundal/usap).
Each directory is a self-contained agent skill package. Contributions here add new agents
or improve existing ones — no platform code required.

---

## What belongs here

- New security agent skill packages (public, non-offensive)
- New engineering, DevOps, or executive skill packages
- New `cs-*` orchestrator agents in `agents/<domain>/`
- Improvements to existing SKILL.md prompts (better reasoning procedures, new classification tables, updated MITRE mappings)
- New or improved reference documents (`references/`)
- Better expected output examples (`expected_outputs/`)
- Fixes to existing scripts (`scripts/`)

Bug bounty and offensive techniques belong in [usap-bugbounty](https://github.com/jaskaranhundal/usap-bugbounty) (private).

---

## Skill package structure

Every agent is a directory named by its slug:

```
<slug>/
  SKILL.md                              # LLM system prompt + YAML frontmatter
  README.md                             # Human-readable description
  references/
    workflow.md                         # Analysis procedure (required)
    *.md                                # Additional reference documents
  assets/
    templates/
      output-template.json              # Output schema template
  expected_outputs/
    sample_output.json                  # Representative LLM output
  scripts/
    <slug>_tool.py                      # CLI tool for this skill (required)
    pre_analysis.py                     # Optional: deterministic pre-analysis
```

---

## SKILL.md frontmatter

Use this exact frontmatter template. All fields are required.

```yaml
---
name: <slug>
agent_slug: <slug>
agent_id: <next available integer>
level: L1|L2|L3|L4
plane: work|board
phase: mvp|phase1|phase2
ttl: 300
approval_required: false
mutating_intents: []
can_execute: false
providers: [anythingllm, ollama, mock]
required_invoke_role: soc_analyst
required_approver_role: soc_lead
input_schema: schemas/input/<slug>.yaml
output_schema: schemas/output/<slug>.yaml
runtime_contract: agents/<slug>.yaml
---
```

**Level guide:**

| Level | Role | Examples |
|---|---|---|
| L1 | Board / Executive | cyber-insurance, enterprise-risk-assessment |
| L2 | Management / CISO | incident-commander, compliance-mapping, metrics-reporting |
| L3 | SOC / Analyst | threat-hunting, secrets-exposure, containment-advisor |
| L4 | Technical / Tool | identity-access-risk, endpoint-os-security, tool-execution-broker |

**Intent classification:**

- `mutating_intents: []` — agent only recommends (read_only), no human approval needed
- `mutating_intents: [credential_operation]` — agent can recommend key rotation/revocation, requires approval
- `mutating_intents: [policy_change, network_change, device_config_change, remediation_action]` — other mutating categories

---

## SKILL.md body structure

A high-quality SKILL.md follows this structure:

```markdown
# Agent Name

## Identity
Who you are, what your function is, what you never do.

## Classification Tables
Decision tables with columns: Type | Indicators | Severity | MITRE Technique

## Blast Radius / Severity Matrix
Tiered impact assessment with specific criteria per tier.

## Attacker Timeline (for detection agents)
T+0, T+5 min, T+15 min timeline of attacker actions post-compromise.

## Confidence Scoring
Table mapping evidence type to confidence range (0.0 to 1.0).

## Cascade Intelligence
- What upstream agent outputs you consume and how
- What downstream agents consume your output

## Reasoning Procedure
Step 1, Step 2, ... — ordered, numbered steps. No skipping.

## Intent Classification
Explicit rule: confidence >= X AND condition Y -> intent_type: mutating

## What You MUST Do / MUST NOT Do
Hard constraints.

## Post-Incident Review Questions (optional)
5-7 PIR questions for after resolution.

## Tool Integration (if applicable)
CLI usage examples for scripts in this package.

## Knowledge Sources
List of references/ files and what each contains.

## MCP Connector Output Contract (if mutating)
JSON snippet for mcp_connector, target, parameters.

## Runtime Contract
- ../../agents/<slug>.yaml
```

---

## README.md per agent

Every agent README must include:

1. **What it does** — 2-3 sentences
2. **When to trigger** — event types or conditions
3. **Key outputs** — 3-5 fields the LLM returns
4. **Intent classification** — read_only or mutating (what triggers approval)
5. **Works with** — upstream/downstream agents
6. **Standalone use** — copy-paste command

See `secrets-exposure/README.md` for a reference example.

---

## Adding a new agent — step by step

### 1. Pick the next available agent_id

```bash
# Check the highest existing agent_id across all SKILL.md files
grep -r "^agent_id:" */SKILL.md | awk -F: '{print $3}' | sort -n | tail -1
```

### 2. Create the directory

```bash
mkdir my-new-agent
```

### 3. Write SKILL.md

Copy the frontmatter template. Write the body following the structure above.

The minimum viable SKILL.md body must include:
- Identity section
- At least one classification or decision table
- Reasoning procedure (numbered steps)
- Intent classification rule
- Runtime Contract line: `../../agents/my-new-agent.yaml`

### 4. Write README.md

Use the template from step above.

### 5. Create required files

```bash
mkdir -p my-new-agent/references my-new-agent/assets/templates my-new-agent/expected_outputs my-new-agent/scripts
touch my-new-agent/references/workflow.md
touch my-new-agent/assets/templates/output-template.json
touch my-new-agent/expected_outputs/sample_output.json
touch my-new-agent/scripts/my-new-agent_tool.py
```

### 6. Write references/workflow.md

Document the step-by-step analysis workflow for a human analyst performing this task manually.
The SKILL.md Reasoning Procedure mirrors this workflow for the LLM.

### 7. Write expected_outputs/sample_output.json

A realistic LLM output for a representative input. Should include all required output contract fields:
`action`, `rationale`, `requires_approval`, `approver_roles`, `summary`, `key_findings`,
`recommendation`, `intent_type`, `confidence`, `evidence_references`, `timestamp_utc`.

### 8. Register in the USAP platform (separate step)

After your PR here is merged, open a follow-up PR in [usap](https://github.com/jaskaranhundal/usap) to:
- Add the agent manifest to `agents/<slug>.yaml`
- Add the entry to `config/agent-catalog.yaml`
- Add routing rules to `policies/rules/default-routing.yaml`

---

## Quality bar

Before opening a PR, verify:

```
[ ] SKILL.md frontmatter uses the standard format (all required fields present)
[ ] agent_slug in frontmatter matches directory name
[ ] agent_slug in frontmatter matches the body text (search for agent_slug value)
[ ] Runtime Contract line present: ../../agents/<slug>.yaml
[ ] Classification table(s) present with MITRE ATT&CK mappings where applicable
[ ] Reasoning procedure has numbered steps
[ ] Intent classification rule explicitly states when mutating applies
[ ] README.md is not the boilerplate template (must have real content)
[ ] references/workflow.md has actual workflow content
[ ] expected_outputs/sample_output.json validates against the output contract
[ ] No paid API keys referenced in any file
[ ] No offensive techniques (those go to usap-bugbounty)
[ ] SKILL.md ≤10KB (check: wc -c SKILL.md)
[ ] ## Proactive Triggers present with 4-6 triggers
[ ] ## Output Artifacts table present with 3-6 rows
[ ] ## Related Skills entries include NOT-scenarios
[ ] ## Context Discovery section present
[ ] Python tool runs zero-config: python scripts/<slug>_tool.py --output json
[ ] Python tool has --help (argparse required)
[ ] If tool scores, output includes risk_score (0-100 int) alongside confidence float
```

---

## Submitting a PR

1. Fork this repo
2. Create a branch: `git checkout -b feat/my-new-agent` or `fix/agent-slug-improvement`
3. Make your changes
4. Open a PR against `main` with:
   - Title: `feat: add <slug> agent` or `improve: <slug> — <what changed>`
   - Description: what the agent does and why it belongs in this library

---

## Adding a cs-* Orchestrator Agent

Orchestrator agents live in `agents/<domain>/` and combine multiple skills into role-specific workflows.

### Agent File Structure

```
agents/
├── CLAUDE.md                  # Agent development guide
├── security/
│   └── cs-security-analyst.md
├── devsecops/
│   └── cs-devsecops-engineer.md
└── executive/
    └── cs-ciso-advisor.md
```

### Required Frontmatter

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

### Required Sections

1. **Purpose** — 2-3 paragraphs explaining the agent's role and audience
2. **Skill Integration** — skill paths, Python tools, knowledge bases
3. **Workflows** — minimum 3 workflows with named steps and bash commands
4. **Integration Examples** — runnable bash command block
5. **Success Metrics** — 5+ measurable outcomes
6. **Related Agents** — links to agents that receive or send to this agent
7. **References** — links to primary skill SKILL.md files

### Path Convention

From `agents/security/cs-my-agent.md`, reference skills via:
```bash
../../<slug>/scripts/<slug>_tool.py
```

### Agent Quality Checklist

```
[ ] YAML frontmatter valid with cs-* prefix
[ ] All skill slugs referenced exist in the repo
[ ] Relative paths resolve correctly from agents/domain/
[ ] At least 3 workflows with concrete bash commands
[ ] Success metrics are measurable (not aspirational)
[ ] agents/CLAUDE.md agent catalog updated
[ ] README.md agents table updated
```

See [agents/CLAUDE.md](agents/CLAUDE.md) for the full agent development guide.

---

## Questions

Open an issue in this repo. For platform questions, use [usap issues](https://github.com/jaskaranhundal/usap/issues).
