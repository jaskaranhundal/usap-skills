# Frontmatter Specification

Every `SKILL.md` file must begin with a valid YAML frontmatter block. This document defines all fields, their types, allowed values, and examples.

## agentskills.io conformance

USAP's frontmatter is a strict superset of the [agentskills.io Skill specification](https://agentskills.io/specification). Verified on 2026-06-20 against the published spec:

| Spec field | USAP behaviour | Conformance |
|---|---|---|
| `name` (required, 1–64 chars, kebab-case, no leading/trailing/consecutive hyphens, matches parent dir) | Enforced by `tools/validate_skill.py` via `KEBAB_RE`, `MAX_NAME_LEN`, and the `name != slug` check | Full |
| `description` (required, 1–1024 chars, non-empty) | Required; minimum 50 chars (stricter than spec) | Full + stricter |
| `license` (optional, free text) | Required, restricted to `MIT` / `Apache-2.0` / `GPL-3.0` (stricter than spec) | Full + stricter |
| `compatibility` (optional, max 500 chars) | Populated on the L4 / tool-dependent skills (cloud scanners, KMS, AD/LDAP, forensics, pentest, red-team) | Full |
| `metadata` (optional, arbitrary key-value mapping) | Used heavily — canonical 5+5 schema lives here plus optional `frameworks.*`. The spec explicitly says clients may store extra properties under `metadata` | Full |
| `allowed-tools` (optional, **space-separated string**, experimental) | Populated as a string per the spec on the same L4 / tool-dependent skills | Full |

USAP keeps the 5 required `metadata.*` subfields nested under `metadata`, where the spec explicitly designates it as the arbitrary-key-value escape hatch.

USAP's `version` (under `metadata`) is always quoted (`"1.0.0"`) so YAML parsers do not silently coerce it to a float on certain ill-formed strings.

### Framework keys: top-level, not nested under metadata

**Planning correction (2026-06-27).** The agentskills.io ecosystem (Anthropic Conformant Skills, ACS) places framework coverage keys at the YAML top level — not under `metadata.frameworks`. The earlier USAP convention of nesting under `metadata.frameworks` is non-conformant with the ACS canonical layout. New skills SHOULD declare framework coverage as the optional top-level keys `mitre_attack`, `nist_csf`, `mitre_atlas`, `owasp_top10`, `d3fend`, `nist_ai_rmf` (each `array[string]`, ≤8 entries).

`metadata.frameworks.*` remains accepted by the validator for backward compatibility with the ~9 skills already populated, but is deprecated for new authoring. Both the top-level keys and the nested `metadata.frameworks.*` block are validated when present; they may coexist on the same skill during the rollout window.

Rationale: agentskills.io spec expects top-level framework keys for cross-tool consumption (Navigator integrations, CSF crosswalks). Nesting under `metadata` puts them in the unstructured escape-hatch namespace where third-party tools cannot rely on them.

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

Skills declare machine-readable framework coverage as **top-level** YAML keys (preferred, agentskills.io conformant). The validator also accepts the legacy nested form under `metadata.frameworks.*` for backward compatibility — do not author new skills that way.

Every key is optional. Each value is an array of identifier strings. The cap is 8 IDs per framework per skill — keep mappings focused on what the skill primarily covers; broader sweeps belong in repo-level coverage docs.

Top-level form (preferred):

```yaml
---
name: detection-engineering
description: ...
license: MIT
mitre_attack: [T1059.001, T1098.001, T1110, T1562.008]
nist_csf:     [DE.AE-02, DE.CM-01, DE.CM-09]
metadata:
  version: "2.0.0"
  ...
---
```

The six framework keys (`mitre_attack`, `nist_csf`, `mitre_atlas`, `owasp_top10`, `d3fend`, `nist_ai_rmf`) defined below apply identically whether they appear at the top level or nested under `metadata.frameworks`.

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

## Invocation Control (Claude Code extensions to agentskills.io)

These optional top-level fields layer onto the agentskills.io minimum (which only requires `name` and `description`). They are honored verbatim by Claude Code; other clients can ignore them safely. USAP uses them to express its L1–L4 autonomy model in machine-readable frontmatter rather than only in prose.

Source: <https://code.claude.com/docs/en/skills>.

### `disable-model-invocation`
- **Type:** boolean
- **Default:** `false`
- **Meaning:** If `true`, only humans can invoke this skill (the model cannot select it autonomously). Required on every L4 (mutating) USAP skill.
- **USAP invariant:** L4 skills must set `disable-model-invocation: true`. The L4 contract gates every mutating action behind a human; this field is the machine-readable expression of that gate.

### `user-invocable`
- **Type:** boolean
- **Default:** `true`
- **Meaning:** If `false`, the skill is not exposed as a slash command and can only be triggered programmatically by another skill or agent. Useful for sub-skills that should never appear in a `/help` listing.
- **USAP invariant:** L1 advisory skills may set `user-invocable: false` when they are pure helpers (no operator-facing surface). All other levels keep the default.

### `allowed-tools`
- **Type:** string (space-separated)
- **Format:** Claude Code grammar — `Bash(git:*) Bash(jq:*) Read Write`. Each token is a tool name optionally followed by a pattern in parentheses.
- **USAP invariant:** Every L3 and L4 skill that depends on host tools must declare a non-empty `allowed-tools` so external clients can refuse out-of-policy commands. L1 / L2 advisory skills typically omit this field (no host-tool dependency).
- **Conformance:** agentskills.io defines this field as "experimental"; USAP's use of it is forward-compatible.

### `disallowed-tools`
- **Type:** string (space-separated)
- **Format:** Same grammar as `allowed-tools`.
- **Meaning:** Explicit denylist that overrides any inherited allowlist.
- **USAP invariant:** Recommended on every L3 / L4 skill — at minimum `Bash(rm:*) Bash(sudo:*)` to prevent accidental host damage. This is layered defense; the runtime should already block these.

### `context`
- **Type:** string enum: `inherit` (default), `fork`
- **Meaning:** `fork` runs the skill in a fresh model context (no parent conversation history). Useful for skills where prior chat context would bias the result (e.g., evidence-only triage).
- **USAP invariant:** Recommended `fork` on L3 evidence-handling skills (forensics, incident-classification, finding-triage). The fresh context makes the skill output reproducible and replayable.

### `paths`
- **Type:** `array[string]` (glob patterns)
- **Meaning:** Restricts the skill to operating on files matching the listed globs. The model can still read other paths if `allowed-tools` permits, but the skill's operational scope is documented here.
- **USAP invariant:** Recommended on every L3 / L4 skill that mutates files. Skills with no on-disk surface (advisory / scoring / classification) omit it.

### `model`
- **Type:** string
- **Meaning:** Override the default model for this skill. Honored by Claude Code; ignored by clients that pin model per session.
- **USAP invariant:** Use sparingly. Most skills should not override the operator's session model.

### `effort`
- **Type:** string enum: `low`, `medium`, `high`, `xhigh`, `max`
- **Meaning:** Reasoning effort override. Higher = deeper thinking, slower output.
- **USAP invariant:** Use sparingly. Default to operator's session effort.

### Level → invocation-control invariants (summary)

| Level | `disable-model-invocation` | `user-invocable` | `allowed-tools` | `context` |
|---|---|---|---|---|
| L1 (advisory) | false | optional | omitted | inherit |
| L2 (analytical) | false | true | omitted | inherit |
| L3 (operational) | false | true | required, non-empty | `fork` if evidence-handling |
| L4 (executive) | **true** (required) | true | required, non-empty | `fork` recommended |

`tools/validate_invocation_control.py` enforces these invariants. The check WARNs on violations during the rollout window; failures will become errors once at least 80% of L3 / L4 skills are backfilled.

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

### `metadata.requires.bins`
- **Type:** `array[string]`
- **Example:** `["nmap", "kubectl"]`
- **Rules:** External CLI binaries the skill's `scripts/<slug>_tool.py` invokes via `subprocess.run` or checks via `shutil.which`. Entries are bare executable names (no path, no flags). When omitted, the skill is assumed stdlib-only Python with no host-tool dependency.

### `metadata.requires.install`
- **Type:** object with optional `macos` and `linux` string keys
- **Example:** `{macos: "brew install nmap", linux: "apt-get install -y nmap"}`
- **Rules:** Human-readable install hints for the binaries in `metadata.requires.bins`. Free text — the validator does not parse package-manager syntax. Use this so a contributor on a fresh box can pick up the skill without spelunking.

---

## Canonical Domain Slugs

Skills MUST live under one of the 11 canonical domain slugs documented in [`standards/canonical-domains.md`](canonical-domains.md). The validator FAILs on any SKILL.md whose first path segment is a known alias (e.g. `red-teaming`, `webapp`) rather than the canonical slug (`red-team`, `webapp-security`). Pin the canonical name in the directory at create time — renaming a domain mid-project requires updating mappings, agents, and CI in lockstep.

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
