# Frontmatter Specification

Every `SKILL.md` file must begin with a valid YAML frontmatter block. This document defines all fields, their types, allowed values, and examples.

---

## Required Fields

### `name`
- **Type:** string
- **Pattern:** lowercase, hyphens only, no spaces
- **Example:** `threat-hunting`
- **Rules:** Must match the directory slug exactly.

### `description`
- **Type:** string
- **Pattern:** "USAP agent skill for <Title>. Use for <one-line purpose>."
- **Example:** `USAP agent skill for Threat Hunting. Use for Perform hypothesis-driven threat hunting across telemetry.`
- **Rules:** Must include both the title and a one-line use case.

### `license`
- **Type:** string
- **Allowed values:** `MIT`, `Apache-2.0`, `GPL-3.0`
- **Default:** `MIT`
- **Example:** `MIT`

### `metadata`
- **Type:** object
- **Required subfields:** `version`, `author`, `category`, `updated`, `agent_slug`

---

## Metadata Subfields

### `metadata.version`
- **Type:** string (semver)
- **Pattern:** `MAJOR.MINOR.PATCH`
- **Example:** `1.0.0`
- **Rules:** Increment MINOR for feature additions, PATCH for fixes, MAJOR for breaking changes.

### `metadata.author`
- **Type:** string
- **Default:** `USAP Team`
- **Example:** `USAP Team`

### `metadata.category`
- **Type:** string
- **Allowed values:**
  - `usap-adversary`, `usap-appsec-devsecops`, `usap-control-plane`,
  - `usap-detection`, `usap-devsecops`, `usap-engineering`,
  - `usap-executive`, `usap-governance`, `usap-identity-access`,
  - `usap-infrastructure`, `usap-operations`, `usap-pentest`,
  - `usap-platform-ai`, `usap-red-team`, `usap-response`,
  - `usap-risk-compliance`, `usap-safety`, `usap-system-security`,
  - `usap-webapp`
- **Example:** `usap-operations`
- **Rules:** Enum extended on 2026-06-20 to reflect the 11-domain layout (was an 8-token subset of the active categories). Extended again the same day with `usap-webapp` for the new `webapp-security/` domain. The validator at `tools/validate_skill.py` and the spec must stay in sync — adding a new category requires updating both.

### `metadata.updated`
- **Type:** string (ISO date)
- **Pattern:** `YYYY-MM-DD`
- **Example:** `2026-03-08`
- **Rules:** Update on every material change to SKILL.md content.

### `metadata.agent_slug`
- **Type:** string (quoted)
- **Rules:** Must exactly match `name` field. Quoted to prevent YAML parsing issues with hyphens.
- **Example:** `"threat-hunting"`

---

## Canonical Example

```yaml
---
name: secrets-exposure
description: USAP agent skill for Secrets Exposure. Use for Credential exposure analysis across repositories, logs, and environment variables.
license: MIT
metadata:
  version: 1.0.0
  author: USAP Team
  category: usap-detection
  updated: 2026-03-08
  agent_slug: "secrets-exposure"
---
```

---

## Framework Mappings

Skills may declare machine-readable framework coverage under `metadata.frameworks`. Every key is optional. Each value is an array of identifier strings. The cap is 8 IDs per framework per skill — keep mappings focused on what the skill primarily covers; broader sweeps belong in repo-level coverage docs.

### `metadata.frameworks.mitre_attack`
- **Type:** `array[string]`
- **Pattern:** `T\d{4}(\.\d{3})?` (MITRE ATT&CK Enterprise technique or sub-technique ID)
- **Example:** `[T1078, T1059.001, T1083]`

### `metadata.frameworks.nist_csf`
- **Type:** `array[string]`
- **Pattern:** `[A-Z]{2}\.[A-Z]{2}-\d{2}` (NIST CSF 2.0 subcategory ID)
- **Example:** `[DE.CM-01, DE.AE-02, ID.RA-05]`

### `metadata.frameworks.mitre_atlas`
- **Type:** `array[string]`
- **Pattern:** `AML\.T\d{4}(\.\d{3})?` (MITRE ATLAS technique ID)
- **Example:** `[AML.T0040, AML.T0051]`

### `metadata.frameworks.owasp_top10`
- **Type:** `array[string]`
- **Pattern:** `A\d{2}` (OWASP Top 10 2025 category code, e.g. `A01`)
- **Example:** `[A01, A03, A07]`

### `metadata.frameworks.d3fend`
- **Type:** `array[string]`
- **Pattern:** MITRE D3FEND technique label (e.g. `Process Termination`); free text accepted, no strict pattern. Cap 8.
- **Example:** `["Process Termination", "Executable Denylisting"]`

### `metadata.frameworks.nist_ai_rmf`
- **Type:** `array[string]`
- **Pattern:** `[A-Z]{2}-\d+(\.\d+)*` (NIST AI RMF function/subcategory, e.g. `MAP-1.1`)
- **Example:** `[MAP-1.1, MEASURE-2.7]`

### Source-of-truth rule

`metadata.frameworks.*` is the canonical machine-readable record of a skill's framework coverage. Body-prose citations (e.g. "we map to T1078 here") are allowed but do not feed the auto-generated `mappings/` artifacts. The validator does not enforce a body-vs-frontmatter cross-check yet; that lands when `shared/scripts/framework_extractor.py` adds a `--check` mode in a later phase.

### Auto-generation

`tools/framework_extractor.py` walks every active-domain SKILL.md and emits:

- `mappings/mitre-attack/attack-navigator-layer.json` (MITRE Navigator v4.5 schema)
- `mappings/mitre-attack/coverage-summary.md`
- `mappings/nist-csf/csf-alignment.md`

These artifacts are regenerated on every CI run and `git diff --exit-code mappings/` fails the build if the committed coverage docs drift from the source-of-truth frontmatter. Do not hand-edit any file under `mappings/` except the static `README.md` per subdirectory.

---

## Optional Metadata Fields

### `metadata.context_file`
- **Type:** string
- **Pattern:** relative path from skill root
- **Example:** `"../../shared/security-context.md"`
- **Rules:** Points to a domain context document the skill reads before prompting the user. If present, the skill must check this file first and apply its contents before asking for missing input.

### `metadata.proactive_triggers_count`
- **Type:** integer
- **Allowed values:** 4–6
- **Example:** `5`
- **Rules:** Must match the number of entries in the `## Proactive Triggers` section of SKILL.md. Validated at review time.

### `metadata.output_artifacts_count`
- **Type:** integer
- **Allowed values:** 3–6
- **Example:** `4`
- **Rules:** Must match the number of rows in the `## Output Artifacts` table of SKILL.md. Validated at review time.

### `metadata.skill_size_kb`
- **Type:** float
- **Example:** `8.4`
- **Rules:** Approximate size of SKILL.md in kilobytes. Must be ≤10 or include a rationale comment explaining why the size is acceptable. Content exceeding 10KB should be moved to `references/`.

---

## Category → Domain Mapping

| Category | Domain dirs it covers |
|---|---|
| `usap-adversary` | `red-team`, parts of `pentest` |
| `usap-appsec-devsecops` | `appsec-devsecops` (legacy slug) |
| `usap-control-plane` | `platform-ai` (control-plane skills) |
| `usap-detection` | `detection` |
| `usap-devsecops` | `appsec-devsecops` |
| `usap-engineering` | (reserved, non-security utilities) |
| `usap-executive` | `governance/ciso-brief-generator` and other board-facing skills |
| `usap-governance` | `governance` |
| `usap-identity-access` | `identity-access` |
| `usap-infrastructure` | `cloud-infra`, parts of `system-security` |
| `usap-operations` | Cross-domain orchestration skills, `detection/*-engineering` |
| `usap-pentest` | `pentest` |
| `usap-platform-ai` | `platform-ai` |
| `usap-red-team` | `red-team` (legacy slug) |
| `usap-response` | `response` |
| `usap-risk-compliance` | `risk-compliance` |
| `usap-safety` | AI safety / guardrail skills |
| `usap-system-security` | `system-security` |
| `usap-webapp` | `webapp-security` |

---

## Validation Checklist

- [ ] `name` matches directory slug
- [ ] `description` follows "USAP agent skill for..." pattern
- [ ] `license` is one of the allowed values
- [ ] `metadata.version` is valid semver
- [ ] `metadata.category` is one of the allowed categories
- [ ] `metadata.updated` is today's date or earlier
- [ ] `metadata.agent_slug` is quoted and matches `name`
- [ ] SKILL.md ≤10KB; overflow moved to `references/`
- [ ] `## Proactive Triggers` section present with 4–6 entries
- [ ] `## Output Artifacts` table present with 3–6 rows
