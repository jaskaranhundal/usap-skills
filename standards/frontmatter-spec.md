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
  - `usap-risk-compliance`, `usap-safety`, `usap-system-security`
- **Example:** `usap-operations`
- **Rules:** Enum extended on 2026-06-20 to reflect the 11-domain layout (was an 8-token subset of the active categories). The validator at `tools/validate_skill.py` and the spec must stay in sync — adding a new category requires updating both.

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
