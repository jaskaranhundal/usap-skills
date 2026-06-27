# USAP Skill Audit Rubric — 2026-Q2

Pocock-style 7-dimension scoring rubric. Each skill is scored 0-2 per
dimension; total drives the verdict band.

## Dimensions

### 1. Trigger quality (0-2)

Does the `description:` field name a clear "Use when" condition that an LLM
host can match without guessing?

- **0** — Description is generic ("security skill for X") or missing a trigger.
- **1** — Trigger present but ambiguous ("use for security questions").
- **2** — Specific, observable trigger ("Use when a CVE scanner emits a new
  finding above CVSS 7.0").

### 2. Context economy (0-2)

What does the skill load vs. what does it actually need?

- **0** — SKILL.md exceeds 100 lines without progressive disclosure;
  references files that aren't used.
- **1** — Loads roughly the right context but carries dead references.
- **2** — Tight: every loaded reference is used in the workflow.

### 3. Tool wiring (0-2)

Does `scripts/<slug>_tool.py` emit a contract-compliant 11-field payload?

- **0** — Tool missing, or payload missing required fields.
- **1** — Payload present but optional fields like `evidence_references`
  empty when severity >= `high`.
- **2** — Full contract, including `next_agents`, `human_approval_required`,
  and ISO 8601 `timestamp_utc`.

### 4. Verification loop (0-2)

Is there a way for the LLM to check its own output before returning?

- **0** — No self-check. The LLM emits and exits.
- **1** — Verification mentioned but not enforced ("ensure findings cite
  evidence" with no procedure).
- **2** — Explicit numbered self-check (e.g., "Step 5: re-read every
  finding; reject any without an `evidence_references` entry").

### 5. Real-world expertise (0-2)

Does the body reflect SOC / IR / appsec practice, or generic AI prose?

- **0** — Generic ("threats can be detected by analyzing patterns").
- **1** — Mentions named frameworks (MITRE, NIST) but no operator-grade
  detail.
- **2** — Practitioner detail: named tools, named MITRE ATT&CK sub-techniques,
  references to typical false-positive patterns, escalation thresholds.

### 6. Freshness (0-2)

Last `updated:` value relative to audit date.

- **0** — `updated:` > 12 months old, or missing.
- **1** — `updated:` 6–12 months old.
- **2** — `updated:` ≤ 6 months old.

### 7. No filler (0-2)

Signal-to-noise ratio. Strip the markdown headers and count the load-bearing
sentences vs. boilerplate.

- **0** — > 30% boilerplate ("In today's evolving threat landscape...").
- **1** — Some restatement, some filler in transitions.
- **2** — Every paragraph carries a load-bearing claim, instruction, or
  reference.

## Verdict bands

Total = sum of the 7 dimensions (0-14).

| Total | Verdict | Action |
|---|---|---|
| 12-14 | KEEP | Ship as-is; no PR needed |
| 9-11 | OPTIMIZE | Open a `chore(skills):` PR addressing the weakest 1-2 dimensions |
| 5-8 | REWRITE | Open a `refactor(skills):` PR; reuse only the agent_id, MITRE mappings, and tool scaffold |
| 0-4 | CUT-OR-MERGE | Open an issue: either delete the skill or merge it into a sibling skill with ≥ 50% overlap |

## Tie-breakers

- If two skills score identically and overlap >= 50% in workflow, prefer
  CUT-OR-MERGE on the newer one (the older skill has invocation history).
- Freshness alone never bumps a skill above OPTIMIZE — a fresh `updated:`
  field on a bad skill is just a fresh tombstone.
- Tool wiring failures (dimension 3 = 0) cap the verdict at REWRITE,
  regardless of how the other dimensions score — a skill that emits the
  wrong payload contract is unusable downstream.

## Recording format

In `<cycle>/<domain>.md`, one row per skill:

```markdown
| skill | 1.trig | 2.ctx | 3.tool | 4.verif | 5.expert | 6.fresh | 7.filler | total | verdict |
|---|---|---|---|---|---|---|---|---|---|
| threat-hunting | 2 | 2 | 2 | 1 | 2 | 2 | 2 | 13 | KEEP |
```
