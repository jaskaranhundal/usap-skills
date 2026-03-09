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
- **Allowed values:** `usap-operations`, `usap-detection`, `usap-response`, `usap-governance`, `usap-red-team`, `usap-devsecops`, `usap-engineering`, `usap-executive`
- **Example:** `usap-operations`

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

## Category → Domain Mapping

| Category | Domain |
|---|---|
| `usap-operations` | Orchestration, Operations |
| `usap-detection` | Detection, Telemetry |
| `usap-response` | Incident Response, Forensics |
| `usap-governance` | Risk, Compliance, Governance |
| `usap-red-team` | Red Team, Testing |
| `usap-devsecops` | DevSecOps, AppSec |
| `usap-engineering` | Engineering (non-security) |
| `usap-executive` | Executive, Board |

---

## Validation Checklist

- [ ] `name` matches directory slug
- [ ] `description` follows "USAP agent skill for..." pattern
- [ ] `license` is one of the allowed values
- [ ] `metadata.version` is valid semver
- [ ] `metadata.category` is one of the allowed categories
- [ ] `metadata.updated` is today's date or earlier
- [ ] `metadata.agent_slug` is quoted and matches `name`
