# USAP Skill Authoring Standard

This is the canonical reference for authoring a USAP skill. It defines the "DNA" of a SKILL.md — the frontmatter shape, the body sections, the framework-mapping syntax, and the host-tool dependency declaration. New contributors should read this top-to-bottom before opening a PR.

For the schema-level rules (regexes, enums, validator behaviour), see [`frontmatter-spec.md`](frontmatter-spec.md). For the JSON payload contract, see [`output-contract.md`](output-contract.md). For naming, see [`naming-conventions.md`](naming-conventions.md).

---

## 1. Audience

This standard is aimed at:

- External contributors building skills against the agentskills.io specification who want to publish into USAP.
- Internal contributors backfilling, maintaining, or splitting existing skills.
- Tooling authors (validator, MCP router, framework extractor) that need a single doc to point at.

Pre-existing skills are not auto-migrated to this standard. Apply it when you create a new skill or materially rewrite an existing one.

---

## 2. Frontmatter shape

Every SKILL.md starts with a YAML frontmatter block fenced by `---`. The canonical shape is:

```yaml
---
name: <slug>
description: USAP agent skill for <Title>. Use when <one-line trigger>.
license: MIT

# Optional top-level framework mapping (agentskills.io conformant placement).
# Each array is capped at 8 IDs.
mitre_attack: [T1078, T1110]
nist_csf:     [DE.CM-01, DE.AE-02]
# mitre_atlas:  [AML.T0040]
# owasp_top10:  [A01, A03]
# d3fend:       ["Process Termination"]
# nist_ai_rmf:  [MAP-1.1, MEASURE-2.7]

metadata:
  version: "1.0.0"
  author: USAP Team
  category: usap-detection
  updated: 2026-06-27
  agent_slug: "<slug>"

  # Optional: external CLI binaries the skill's tool script invokes.
  # Omit entirely when the skill is stdlib-only Python.
  # requires:
  #   bins: ["nmap", "kubectl"]
  #   install:
  #     macos: "brew install nmap kubernetes-cli"
  #     linux: "apt-get install -y nmap kubectl"
---
```

### 2.1 Required top-level

- `name` — kebab-case, matches the directory slug.
- `description` — third-person, ≤200 chars, contains a "Use when" / "Use for" trigger phrase. Validated by `tools/validate_description.py`.
- `license` — one of `MIT`, `Apache-2.0`, `GPL-3.0`.

### 2.2 Required `metadata.*`

- `version` — semver, quoted.
- `author` — typically `USAP Team`.
- `category` — one of the 19 enum tokens listed in `frontmatter-spec.md`.
- `updated` — ISO `YYYY-MM-DD`.
- `agent_slug` — quoted, must equal `name`.

### 2.3 Optional blocks

- **Framework mappings (top-level).** Six keys, each `array[string]`, each capped at 8 entries. Top-level placement is the agentskills.io-conformant location. The legacy `metadata.frameworks.*` placement is still accepted by the validator but deprecated for new skills.
- **`metadata.requires.bins`.** External CLI binaries the tool script depends on. Bare names, no paths, no flags. When present, also fill in `metadata.requires.install` for the platforms you support.
- **Invocation control fields.** `disable-model-invocation`, `user-invocable`, `allowed-tools`, `disallowed-tools`, `context`, `paths`, `model`, `effort` — see `frontmatter-spec.md` for the L1–L4 invariants.

---

## 3. Body sections

Every SKILL.md body MUST include these sections in order. Sections marked optional may be omitted when not relevant; required sections are validated at review time and gated by `tools/validate_skill.py` / `tools/validate_structure.py`.

### 3.1 Persona (required)

A 2–4 sentence operator persona — job title, years of experience, real-world context (F500, CERT, national agency, hyperscaler). Closes with two single-line declarations:

- `**Primary mandate:** ...` — the core job this skill does.
- `**Decision standard:** ...` — what "excellent" looks like from this expert's lens.

The persona is what the runtime injects into the system prompt. Avoid generic "I am an AI assistant" framing — write it as if briefing a new hire.

### 3.2 Reasoning Procedure (required)

A numbered list (typically 4–8 steps) describing how the skill reasons from input to output. Each step is one declarative sentence — no nested bullets, no hedging. Steps must be deterministic enough that two analysts following the procedure on the same input produce comparable outputs.

### 3.3 Intent Classification (required)

A short explicit rule that maps the skill's findings to one of the seven `intent_type` values defined in `output-contract.md` (`detect`, `respond`, `analyze`, `advise`, `escalate`, `report`, `block`). Stating the rule out loud prevents intent drift across the skill family.

Example:

> Classify as `escalate` when a finding has corroborating evidence in two independent data sources AND severity ≥ high. Otherwise classify as `analyze`.

### 3.4 Output Contract reminder (required)

A fenced JSON block showing the 11-field output payload populated for this skill's typical run. The full schema lives in `standards/output-contract.md` — this section is a reminder, not the spec.

### 3.5 Proactive Triggers (recommended, 4–6 entries)

Observable conditions under which the skill should surface a finding to the operator without being asked. Each entry pairs a condition with its operational consequence.

### 3.6 Output Artifacts (recommended, 3–6 rows)

A `When operator asks for X / You produce Y` table that lets the runtime route operator requests to the correct artifact format.

### 3.7 References (required)

Links to the supporting package files:

- [Workflow Guide](references/workflow.md)
- [Output Template](assets/templates/output-template.json)
- [Sample Output](expected_outputs/sample_output.json)

---

## 4. Framework mapping syntax

Use the top-level keys (`mitre_attack`, `nist_csf`, etc.) — not nested under `metadata.frameworks`. The validator accepts both forms but new skills must use top-level placement for agentskills.io conformance.

Rules:

1. Each array is capped at 8 entries. If the skill covers more than 8 IDs in a framework, pick the highest-signal eight and document the rest in `references/workflow.md`.
2. IDs must match the validator pattern:
   - `mitre_attack`: `T\d{4}(\.\d{3})?` — e.g. `T1078`, `T1059.001`.
   - `nist_csf`: `[A-Z]{2}\.[A-Z]{2}-\d{2}` — e.g. `DE.CM-01`.
   - `mitre_atlas`: `AML\.T\d{4}(\.\d{3})?`.
   - `owasp_top10`: `A\d{2}`.
   - `d3fend`: free text.
   - `nist_ai_rmf`: `[A-Z]{2,7}-\d+(\.\d+)*`.
3. Body-prose citations are allowed but do not feed the auto-generated `mappings/` artifacts. Only frontmatter is canonical.
4. Do not leave empty arrays in the committed file. If you have no IDs for a framework, omit the key.

---

## 5. `metadata.requires.bins` syntax

When the skill's `scripts/<slug>_tool.py` invokes an external binary via `subprocess.run`, `subprocess.check_output`, or checks for one via `shutil.which`, declare every such binary under `metadata.requires.bins`. This is what lets the MCP router refuse to dispatch the skill into an environment that lacks the dependency.

Rules:

1. Bare executable names — `nmap`, not `/usr/local/bin/nmap`, not `nmap -sS`.
2. List every distinct binary the script can call, including conditionally-invoked fallbacks.
3. When `requires.bins` is present, populate `requires.install` for at least `macos` and `linux` — free text install hints, one line per platform.
4. Stdlib-only Python scripts (no external binaries) omit `requires` entirely. Invoking another Python script via `sys.executable` does not count as an external binary dependency.

Example:

```yaml
metadata:
  requires:
    bins: ["nmap", "masscan"]
    install:
      macos: "brew install nmap masscan"
      linux: "apt-get install -y nmap masscan"
```

---

## 6. Naming reminder

- Skill slugs are lowercase-hyphenated, max 4 words, no version suffixes. See `naming-conventions.md`.
- Tool script is `scripts/<slug>_tool.py` — hyphens in the slug are preserved.
- `cs-*` agent names live under `agents/<domain>/cs-<name>.md`.
- Commits follow Conventional Commits — `feat(skills):`, `fix(scripts):`, `docs(readme):`, etc.

---

## 7. Package layout

Every skill is a directory under one of the 11 canonical domain slugs in [`canonical-domains.md`](canonical-domains.md):

```
<domain>/<slug>/
  SKILL.md                                  # this spec
  README.md
  references/workflow.md
  assets/templates/output-template.json
  expected_outputs/sample_output.json
  scripts/<slug>_tool.py
```

`tools/validate_structure.py` enforces these paths exist for every active-domain skill.

---

## 8. Validator gates

A skill PR must pass all three:

1. `python3 tools/validate_skill.py --all` — frontmatter schema, canonical domain placement, framework array caps.
2. `python3 tools/validate_description.py --all` — third-person voice, ≤200 chars, trigger phrase present.
3. `python3 tools/validate_structure.py --all` — required files exist on disk.

Plus the MCP smoke tests must still pass: `python3 tools/mcp_server_test.py`.

---

## 9. See also

- [`frontmatter-spec.md`](frontmatter-spec.md) — schema-level rules, regexes, enums.
- [`output-contract.md`](output-contract.md) — the 11-field JSON output payload.
- [`canonical-domains.md`](canonical-domains.md) — the 11 domain slugs and their rejected aliases.
- [`naming-conventions.md`](naming-conventions.md) — slug, script, and commit-message conventions.
- [`level-guide.md`](level-guide.md) — L1–L4 autonomy model and the invocation-control invariants.
