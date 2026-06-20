# USAP vs Anthropic-Cybersecurity-Skills (ACS) — Gap Analysis and Improvement Roadmap

Document owner: USAP maintainers
Status: Draft for review
Scope: `/Users/jaskarn.singh/Documents/PREPO/usap-skills` vs `/Users/jaskarn.singh/Documents/PREPO/usap-skills/references/Anthropic-Cybersecurity-Skills`
Branch context: `feat/expand-domains-and-ci`

---

## 1. Executive Summary

The Anthropic-Cybersecurity-Skills (ACS) corpus is a community-built, Apache-2.0, 754-skill library covering 26 cybersecurity subdomains. Every ACS `SKILL.md` is a tool-walkthrough operational playbook with structured YAML frontmatter (MITRE ATT&CK and NIST CSF arrays on 100% of skills) and a flat per-skill layout (`SKILL.md` + `scripts/` + `references/`). It ships no orchestration layer, no agents, no structured runtime output contract, and no per-skill autonomy/approval taxonomy. It is breadth-first, advisory markdown.

USAP is the opposite shape: 68 active-domain skills across 9 directories (claimed 71/11 in `CLAUDE.md` — drift exists), 6 `cs-*` orchestrator agents (claimed 7), an 11-field structured JSON output contract, an L1–L4 autonomy taxonomy with explicit `human_approval_required` mutating-intent gates, and a guardrail-enforced runtime envelope. USAP is depth-first agentic infrastructure.

The top five improvements for USAP are: (1) reconcile the doc-vs-disk count drift before any expansion; (2) add structured framework-mapping arrays (`mitre_attack`, `nist_csf`, `mitre_atlas`, `owasp_top10`) to `metadata.frameworks` and auto-generate a `mappings/` coverage tree; (3) port ACS's stdlib-only validator pattern into `tools/validate_skill.py` plus a `validate-skills.yml` CI gate; (4) materialize three new high-priority domains as agentic anchors (webapp-security, container-k8s-security, phishing-defense) plus matching `cs-*` orchestrators; (5) deepen the 56 no-op `<slug>_tool.py` stub scripts and rewrite the 56 placeholder `expected_outputs/sample_output.json` files so the documented quick-start commands actually emit contract-compliant payloads.

What NOT to copy from ACS: the `domain: cybersecurity` flat single-domain model, per-skill third-party Python dependencies (102 ACS scripts import `requests`, 22 import `pandas`), PowerShell-only skill scripts, the looser two-field frontmatter (which would regress USAP's stricter 5+5 canonical schema), and the manual mapping-doc maintenance pattern that has already produced inconsistent framework version claims inside ACS itself (`v19.1` vs `v15` vs `v14` across three different ACS docs). Most of all, do not wholesale copy ACS skills — the license is compatible, but verbatim copy dilutes USAP's agentic identity.

---

## 2. Side-by-side Comparison

| Dimension | USAP (this repo) | ACS (`references/Anthropic-Cybersecurity-Skills/`) |
|---|---|---|
| Total skills | 68 active-domain `SKILL.md` (claimed 71 in `CLAUDE.md`) | 754 `SKILL.md`, verified via `find skills -name SKILL.md \| wc -l` |
| Top-level domains | 9 actual (`appsec-devsecops`, `cloud-infra`, `detection`, `governance`, `identity-access`, `platform-ai`, `red-team`, `response`, `risk-compliance`); claimed 11 (`pentest`, `system-security` missing) | 1 root domain (`cybersecurity`); 26 subdomains advertised, 45 distinct raw `subdomain:` values, 32 canonical after alias mapping |
| Framework mappings (per-skill, machine-readable) | None in frontmatter. Prose-only. MITRE ATT&CK mentioned in 19/71 skills (27%); NIST CSF in 4/71 (5.6%); MITRE D3FEND in 0/71; MITRE ATLAS in 1/71; NIST AI RMF in 1/71 | `mitre_attack` and `nist_csf` on 754/754 (100%); `d3fend_techniques` on 139/754 (18%); `nist_ai_rmf` on 85/754 (11%); `atlas_techniques` on 81/754 (11%) |
| Repo-level coverage artifacts | None | `mappings/attack-navigator-layer.json` (v4.5, 218 techniques, 14/14 tactics), `mappings/mitre-attack/coverage-summary.md`, `mappings/nist-csf/csf-alignment.md`, `mappings/owasp/README.md`, top-level `ATTACK_COVERAGE.md`, `index.json` (754-entry skill catalog) |
| Frontmatter standard | Canonical 5 top-level + 5 metadata fields (`name`, `description`, `license`, `metadata.{version,author,category,updated,agent_slug}`); category restricted to 8 enum tokens; 14 skills still on extended legacy frontmatter with `agent_id/level/plane/phase/ttl/approval_required/mutating_intents/can_execute/providers/required_invoke_role/required_approver_role` | 2 required (`name`, `description`) + `domain/subdomain/tags/version/author/license` + framework arrays. No autonomy/approval taxonomy. |
| Skill package structure | `SKILL.md` + `README.md` + `references/workflow.md` + `assets/templates/output-template.json` + `expected_outputs/sample_output.json` + `scripts/<slug>_tool.py` | `SKILL.md` + `LICENSE` + `references/` + `scripts/` (`assets/` optional, no `expected_outputs`) |
| Skill body convention | Identity + classification/decision table with MITRE references + numbered Reasoning Procedure + Intent Classification rule (compliance is uneven across the 5 audited skills) | Fixed H2 spine: `When to Use`, `Prerequisites`, `Workflow` (numbered `### Step N:` with bash), `Verification` |
| Runtime output | 11-field JSON contract (`agent_slug`, `intent_type`, `action`, `rationale`, `confidence`, `severity`, `key_findings`, `evidence_references`, `next_agents`, `human_approval_required`, `timestamp_utc`); enforced by `platform-ai/guardrail` | None. Free-form Markdown plus per-tool JSON. |
| Per-skill tooling | 66 `<slug>_tool.py` scripts. 56 are 31-line argparse stubs printing hardcoded payloads; only 4 contain real logic (>100 LOC). All stdlib-only. | 1,030 Python scripts, 2 PowerShell, 0 bash. Mean 400–640 LOC. Heavy use of `requests` (102), `pandas` (22), `boto3` (18), `yaml` (11), `cryptography`, `paramiko`, `ldap3`, `yara`. |
| Shared utilities | `shared/scripts/` — 8 files, stdlib-only (notably `cvss_scorer.py`, `bb_scope_enforcer.py`) | `tools/validate-skill.py` (291 LOC, stdlib) — frontmatter linter only |
| Validation tooling | None on disk. CLAUDE.md offers grep one-liners. CI claimed to enforce 11-field contract but no `.github/workflows/` directory exists in USAP. | `tools/validate-skill.py` (stdlib YAML parser, subdomain alias map, kebab-case + length checks) plus `.github/workflows/validate-skills.yml` and `update-index.yml` |
| Orchestration layer | 6 `cs-*` agents on disk (`cs-ciso-advisor`, `cs-devsecops-engineer`, `cs-incident-responder`, `cs-red-teamer`, `cs-security-analyst`, `cs-security-program-manager`); v2 spec (Persona, Command Menu, MANDATORY EXECUTION RULES, FAILURE MODES, SUCCESS CRITERIA, state block). `cs-blue-team-analyst` referenced in CLAUDE.md but missing on disk. | None. Flat skill library; no agent files, no router. |
| Autonomy/approval model | L1–L4 levels documented in `standards/level-guide.md`; `mutating_intents` and `human_approval_required` enforced via runtime envelope | None |
| License | MIT (template) | Apache-2.0 (every skill) |
| Authorship attribution | `author: USAP Team` uniformly; no per-skill `LICENSE` | `author: mahipal` uniformly; per-skill `LICENSE` file |
| Target user | SOC engineers, SecOps, CISOs needing structured agentic orchestration over a curated, contract-validated skill set | Practitioners running deep, command-first operational playbooks in any LLM harness |
| agentskills.io conformance | ~95% conformant (5+5 schema is spec-friendly); 28 metadata-list violations in 14 legacy skills; `version` is unquoted in all 68 skills (parses as string by accident); no `compatibility` or `allowed-tools` fields populated | Less spec-friendly at the surface — 6+ non-spec keys (`domain`, `subdomain`, `tags`, `nist_csf`, `mitre_attack`, etc.) are at YAML top level instead of nested under `metadata` |

---

## 3. Where ACS Is Stronger (concrete deltas)

### 3.1 Structured framework mappings on every skill

ACS makes every framework citation machine-readable. From `references/Anthropic-Cybersecurity-Skills/skills/hunting-for-process-injection-techniques/SKILL.md`:

```yaml
mitre_attack: [T1046, T1057, T1082, T1083, T1055]
nist_csf:    [DE.CM-01, DE.AE-02, DE.AE-07, ID.RA-05]
d3fend_techniques: [Executable Denylisting, Execution Isolation, ...]
```

USAP stores the same information in markdown body tables (when it stores it at all). Quantitative deltas (per the inventory):

- NIST CSF coverage: USAP 4/71 skills (5.6%) vs ACS 754/754 (100%) — +94 pp.
- MITRE ATT&CK coverage: USAP 18/71 (25%) vs ACS 754/754 (100%) — +75 pp.
- MITRE D3FEND: USAP 0/71 (0%) vs ACS 139/754 (18.4%) — +18.4 pp.
- MITRE ATLAS: USAP 1/71 (1.4%) vs ACS 81/754 (10.7%) — +9.3 pp.

### 3.2 A repo-level coverage layer derived from the per-skill tags

`references/Anthropic-Cybersecurity-Skills/mappings/attack-navigator-layer.json` is a 3,593-line ATT&CK Navigator v4.5 layer that scores 218 techniques across 14/14 tactics by skill count (top three: `T1059.001` PowerShell with 26 skills, `T1055` Process Injection with 17, `T1053.005` Scheduled Task with 16). The companion `mappings/mitre-attack/coverage-summary.md` provides a per-tactic skill-count table plus a 24-subdomain × 14-tactic heat map. USAP has zero comparable artifacts.

### 3.3 A working frontmatter validator

`references/Anthropic-Cybersecurity-Skills/tools/validate-skill.py` (291 lines, stdlib only) enforces required fields, kebab-case name (1–64 chars), description minimum length (50 chars), `domain: cybersecurity`, subdomain from a canonical alias map (`_SUBDOMAIN_ALIASES` at lines 18–59), and ≥2 tags. USAP has no equivalent on disk; CLAUDE.md offers only grep one-liners and the claimed CI contract check has no workflow file in the repo.

### 3.4 Substantive per-skill scripts

ACS scripts run real logic. A 7-script sample totaled 3,481 LOC: `senior-security` 1,125 LOC across `secret_scanner.py` and `threat_modeler.py`; `threat-detection` 571 LOC; `red-team` 420 LOC; `ai-security` 564 LOC; `information-security-manager-iso27001` 801 LOC. USAP's repo-wide distribution: 56 of 65 active-domain tool scripts are 31-line argparse stubs that print a hardcoded payload and exit. Only 4 scripts in USAP exceed 100 LOC (`governance/security-roadmap-planner` 322 LOC, `governance/security-debt-tracker` 270 LOC, `appsec-devsecops/security-requirements-review` 339 LOC, `detection/secrets-exposure/scan_for_secrets.py` 641 LOC).

### 3.5 Body-shape stability

ACS skills follow one body spine in 4 of 5 audited cases: `## When to Use` → `## Prerequisites` → `## Workflow` (numbered `### Step N:` blocks with fenced bash) → `## Verification`. Stable anchors enable downstream tooling that extracts sections (e.g., a workflow-renderer or an OWASP-mapper). USAP templates leave body free-form, so the five audited skills lead with `## Persona`, `## Identity`, `## Core Workflows`, or `## USAP Runtime Contract` in different orders.

### 3.6 Router/dispatch skills

`references/Anthropic-Cybersecurity-Skills/engineering-team/skills/senior-security/SKILL.md` is a pure router: it owns one workflow (STRIDE + DREAD threat modeling plus a secret scan) and routes 10 other security request types to sibling skills via an explicit table. Quote: *"This skill does exactly one job itself … and routes every other security request to the specialist skill that owns that lane."* USAP has no router skill; orchestration happens at the `cs-*` agent level only, which is heavier-weight than a routing skill.

### 3.7 Authorization-gated tools at the CLI

`references/Anthropic-Cybersecurity-Skills/engineering-team/skills/red-team/SKILL.md` line 45: *"The engagement_planner.py tool will not generate output without the `--authorized` flag."* Exit-code contract: 0 clean, 1 missing-auth, 2 scope-violation. USAP's `shared/scripts/bb_scope_enforcer.py` covers scope, but no per-skill red-team tool gates execution at the CLI surface this way.

### 3.8 Numbered Anti-Patterns sections

Three of the five sampled ACS security skills carry a numbered `Anti-Patterns` section (e.g., `threat-detection` 7 items, `red-team` 7 items), each entry written as a complete paragraph naming the failure mode plus the fix. USAP skills have no equivalent; guardrails are scattered across persona, decision-standard, and runtime-contract blocks.

### 3.9 Tiered workflows by time-budget

ACS `threat-detection` ships three explicitly tiered workflows: `Workflow 1: Quick Hunt (30 Minutes)`, `Workflow 2: Full Threat Hunt (Multi-Day)`, `Workflow 3: Continuous Monitoring (Automated)`. Same pattern in `red-team` (Quick Engagement Scoping / Full Red Team Engagement / Assumed Breach Tabletop). USAP `references/workflow.md` files are single-mode linear procedures.

### 3.10 Forcing-question compliance skills

`references/Anthropic-Cybersecurity-Skills/compliance-os/skills/iso27001-audit-prep/SKILL.md` is ~140 lines, organised as six named forcing questions, each with a one-line guardrail in bold (e.g., line 24: *"What's the audit scope, and is rolling 3-year coverage on track?"* → *"No 3-year coverage discipline, no defensible programme."*). USAP risk-compliance skills are heavier, prose-driven, and do not use this interrogation pattern that auditors recognise.

---

## 4. Where USAP Is Stronger (concrete deltas)

### 4.1 Structured 11-field JSON output contract

`standards/output-contract.md` requires every skill to emit a payload with `agent_slug`, `intent_type` (from a 7-token enum: `detect, respond, analyze, advise, escalate, report, block`), `action`, `rationale`, `confidence` (float 0–1), `severity` (5-token enum), `key_findings`, `evidence_references` (required when severity ≥ high), `next_agents`, `human_approval_required`, `timestamp_utc`. Enforcement is delegated to the `platform-ai/guardrail` skill at runtime. ACS has no runtime contract — every tool emits its own JSON shape, and the resulting catalog cannot be composed by an orchestrator without per-skill adapters.

### 4.2 L1–L4 autonomy model with explicit approval gates

`standards/level-guide.md` defines L1 (advisory / board), L2 (CISO / management), L3 (SOC analyst, read-only tools), L4 (technical / expert, supervised execution). L4 skills with mutating intents (key rotation, isolation, account disablement) must set `human_approval_required: true` in their output. ACS skills are uniformly advisory-markdown with no machine-readable approval signal, so a non-USAP harness cannot enforce gates without reading prose.

### 4.3 cs-* orchestration layer

The six on-disk `cs-*` agents (`agents/<domain>/cs-*.md`) implement a v2 spec — Persona, Critical Actions, Command Menu, Workflow MANDATORY EXECUTION RULES, FAILURE MODES, SUCCESS CRITERIA, FAILURE INDICATORS, and a state block — that composes skills into reproducible workflows. ACS has no equivalent (its `tools/` holds only a frontmatter linter). USAP's `agents/CLAUDE.md` documents the active/passive agent split as a deliberate design principle.

### 4.4 Standalone-LLM usability

Every USAP `SKILL.md` is hand-authored with a 152–230-line persona block, classification table with MITRE references, intent-classification rule, and explicit cascade-intelligence pointers — designed to paste into any LLM as a system prompt. ACS skills are operationally excellent but assume a specific tool surface (e.g., `lsblk`, `volatility3`, `trivy`); paste them into an air-gapped LLM and they leave the user with command instructions they cannot run.

### 4.5 Quality-over-breadth domain selection

USAP's 9 active domains map directly to SOC, AppSec, CISO, IR, and red-team roles a security org actually staffs. ACS's 26 subdomains spread thin: deception-technology has 2 skills, blockchain-security 1, firmware-analysis 1 — not enough depth to be useful, just enough to claim coverage. USAP picks fewer fights and goes deeper per domain (governance has 11 skills, detection 9, red-team 9, risk-compliance 8).

### 4.6 Strict frontmatter discipline

USAP's 8-token `metadata.category` enum and quoted `metadata.agent_slug == name` invariant make every skill machine-routable. ACS's 45 distinct raw `subdomain:` values require alias normalisation just to count them, and even after canonicalisation the values split into 32 buckets, several with <3 skills. USAP's surface is smaller because it's curated.

### 4.7 Shared cross-skill utilities with provenance

`shared/scripts/cvss_scorer.py` and `bb_scope_enforcer.py` are stdlib-only utilities used by 3+ skills. The repo CLAUDE.md gates new shared utilities on the "used by 3+ skills or provides core algorithmic capability" rule. ACS has only one tools-tier script (`validate-skill.py`); all other tooling lives inside each skill's own `scripts/` folder, with no cross-skill primitives.

### 4.8 Closer to agentskills.io spec intent

USAP nests its non-spec extensions inside `metadata.*`. The spec explicitly designates `metadata` as the arbitrary key-value escape hatch. ACS puts `domain`, `subdomain`, `tags`, `mitre_attack`, `nist_csf`, etc. at the YAML top level — six non-spec keys per skill across 754 files. Spot checks confirm USAP satisfies the spec's two hard rules (name matches parent directory; description non-empty under 1024 chars) on all 68 active-domain skills.

---

## 5. Prioritized Improvement Roadmap

| Priority | Effort | Change | Why | Concrete first step |
|---|---|---|---|---|
| HIGH | S | Reconcile doc-vs-disk count drift in `CLAUDE.md` and `README.md` (claims 71 skills / 11 domains / 7 agents; actual 68 / 9 / 6) | Every other roadmap item compounds the credibility gap if shipped on top of stale counts | Edit `/Users/jaskarn.singh/Documents/PREPO/usap-skills/CLAUDE.md` 11-domains line and `agents/CLAUDE.md` catalog; fix `cs-security-analyst.md` line 22 "66 skills" → 68 |
| HIGH | S | Materialize or remove the missing `pentest/`, `system-security/`, and `agents/security/cs-blue-team-analyst.md` | The repo currently advertises directories that do not exist on disk | Either `mkdir` the two domain dirs with an index README + 1 anchor skill each and create the agent from `templates/agent-template.md`, or delete the claims |
| HIGH | M | Add `metadata.frameworks.{mitre_attack, nist_csf, mitre_atlas, owasp_top10}` arrays to `standards/frontmatter-spec.md` and `templates/skill-template.md` | Enables Navigator export, CISO-brief automation, and auditor evidence off a single source; closes the +75 pp ATT&CK coverage gap | Extend `standards/frontmatter-spec.md` with an additive, optional "Framework Mappings" subsection (cap 8 IDs per skill) |
| HIGH | M | Port `tools/validate_skill.py` (stdlib only) from ACS pattern + add `.github/workflows/validate-skills.yml` | USAP has no on-disk validator; the claimed CI 11-field contract has no workflow file | Copy `references/Anthropic-Cybersecurity-Skills/tools/validate-skill.py` to `tools/validate_skill.py`; replace `REQUIRED_FIELDS` with USAP's 5+5; add legacy-frontmatter warn pass |
| HIGH | M | Auto-generate `mappings/mitre-attack/coverage-summary.md` + `mappings/mitre-attack/attack-navigator-layer.json` via `shared/scripts/framework_extractor.py` | No coverage artifact exists; analysts cannot answer "what techniques is USAP covered against?" | Pilot on the 4 detection skills that already cite T-IDs in body tables (`detection-engineering`, `threat-hunting`, `threat-intelligence`, `behavioral-analytics`) |
| HIGH | L | Add 3 new high-priority domains: `webapp-security/`, `container-k8s-security/`, `phishing-defense/` (3 anchor skills each, ~9 skills total) | ACS has 42 webapp / 30 container / 16 phishing skills; USAP has 0 dedicated coverage in these high-volume SOC areas | Expand `metadata.category` enum with `usap-webapp`, `usap-container`, `usap-phishing`; scaffold 3 anchor skills per domain from `templates/skill-template.md` |
| HIGH | L | Add at least 4 new cs-* agents: `cs-cloud-investigator`, `cs-supply-chain-defender`, `cs-threat-intel-lead`, `cs-purple-team-lead` (plus the missing `cs-blue-team-analyst`) | Six agents cover ~3 lenses; ACS subdomain volume reveals 17+ uncovered specialist areas | Promote agent v2 spec (Persona/Command Menu/MANDATORY/FAILURE/SUCCESS) from `agents/CLAUDE.md` into `standards/agent-contract.md`; scaffold one new agent per sprint |
| HIGH | M | Replace 56 placeholder `expected_outputs/sample_output.json` files with contract-compliant payloads | Documented `python <slug>_tool.py --output json` examples fail USAP's own 11-field validation today — credibility risk | Generate one canonical sample per skill via a `shared/scripts/sample_emitter.py` that reads `metadata` + SKILL body and emits the 11 required fields with placeholder values |
| MED | L | Deepen the 56 no-op 31-line `<slug>_tool.py` stubs into real logic (target: 4 → 30+ scripts with >100 LOC) | Skills as advertised vs scripts as shipped diverge sharply; only 4 of 65 scripts contain real logic | Pick 5 high-leverage skills per sprint (start with `response/incident-classification`, `detection/threat-hunting`, `red-team/red-team-operations`, `governance/findings-tracker`, `risk-compliance/risk-threat-modeling`) and rewrite their tools to emit contract-compliant payloads driven by input data |
| MED | M | Add machine-readable `index.json` at repo root via `tools/build_index.py` + `.github/workflows/update-index.yml` | No machine catalog exists; the 71/68 mismatch persists because counts are hand-maintained | Walk `*/*/SKILL.md` across 9 active domains, parse 5-key frontmatter, emit ACS-style JSON with `name/description/domain/path/category/agent_slug` |
| MED | S | Adopt agentskills.io spec compliance fixes: quote `version: "1.0.0"` in all 68 files; move 28 list-in-`metadata` violations from the 14 legacy skills into a sibling `usap_extensions:` block | Unlocks 39+ skills-compatible client portability (Cursor, Goose, OpenCode, etc.) for ~zero engineering cost | Run `find appsec-devsecops cloud-infra detection governance identity-access platform-ai red-team response risk-compliance -name SKILL.md -exec sed -i.bak -E 's/^(  version: )([0-9.]+)$/\1"\2"/' {} \;` |
| MED | M | Add 4 MED-priority domains in sequence: `malware-analysis/`, `endpoint-edr/` (promoted from `cloud-infra/endpoint-os-security`), `digital-forensics/` (promoted from `response/forensics`), `network-security/` | ACS depth (39 malware / 17 endpoint / 37 forensics / 40 network) reveals real triage capability gaps | Phase after HIGH-priority adds; reuse the promotion pattern (move existing skill into new domain, update all references) |
| MED | S | Add `compatibility:` and `allowed-tools:` per agentskills.io spec on tool-dependent skills (cloud scanners, KMS, AD/LDAP, nmap, Volatility, semgrep) | Six skill categories have implicit env needs documented only in prose; spec adoption is high-leverage low-cost | Start with the 14 cloud-infra/pentest-flavored skills; one line each, e.g., `compatibility: Requires Python 3.11+, trivy CLI, network access to target cluster` |
| MED | S | Promote agent v2 contract into versioned `standards/agent-contract.md`, sibling to `output-contract.md` | The differentiator (Persona/Command Menu/MANDATORY/FAILURE/SUCCESS) is only documented in `agents/CLAUDE.md` prose | Extract sections 3–5 of `agents/CLAUDE.md` into the new standards file; reference it from `templates/agent-template.md` |
| MED | M | Add a router/dispatch skill at the top of each domain (start with `appsec-devsecops`, `detection`, `red-team`) modeled on ACS `senior-security` | Routes work into the right lane before invocation — reduces context bloat from skills speculatively loaded into a session | Create `appsec-devsecops/appsec-router/SKILL.md` owning one workflow (e.g., quick risk triage) and routing all other AppSec asks via a markdown table |
| MED | S | Add numbered `Anti-Patterns` sections (5–7 items) to every L3+ skill body | Codifies failure modes the persona prose misses; mirrors ACS pattern observed in `threat-detection`, `red-team`, `ai-security` | Pilot on `detection/threat-hunting`, `red-team/red-team-operations`, `response/incident-commander` — the three most-used skills per `cs-*` agent skills lists |
| MED | S | Add tiered time-budget workflows (Quick / Full / Continuous) to every L3+ workflow reference | Single-mode linear workflows under-serve real SOC time pressure; ACS tiers are operationally proven | Refactor `references/workflow.md` for `detection/threat-hunting`, `red-team/red-team-operations`, and `response/incident-commander` into 3 tiers each |
| MED | S | Add `--authorized` CLI gate pattern to red-team tools (semantic exit codes 0/1/2) | ACS engagement_planner.py refuses to emit output without authorization; USAP `bb_scope_enforcer.py` covers scope but no individual red-team tool gates execution | Modify `red-team/red-team-operations/scripts/red-team-operations_tool.py` to require `--authorized` + scope file; reuse `bb_scope_enforcer.py` internally |
| LOW | M | Add LOW-priority domains: `mobile-security/`, `cryptography-ops/` expansion | Real gaps but small ACS footprint and uncertain user demand inside USAP's SOC-focused positioning | Defer until HIGH+MED domains land and CI is green |
| LOW | S | Adopt ACS body-section anchors (`## When to Use`, `## Prerequisites`, `## Workflow`, `## Verification`) as additive recommendations in `templates/skill-template.md` | Stable anchors enable section-extraction tooling; non-breaking change | Add the 4 anchors as recommended-section headings below the existing Identity/Persona block; do NOT touch the 14 legacy skills |

---

## 6. Concrete Adoption Plan — Top 3 Quick Wins for the Next Sprint

### Quick Win 1 — Reconcile doc-vs-disk drift, then ship the validator and a CI gate (effort: S+M, blocking everything else)

Files to edit:

- `/Users/jaskarn.singh/Documents/PREPO/usap-skills/CLAUDE.md` — change "71 standalone LLM skill packages + 7 cs-* orchestrator agents" to "68 active-domain skills + 6 cs-* agents" until the missing pieces ship; change "11 domains" line to list the 9 that actually exist on disk; remove the `pentest` and `system-security` entries from the inline list.
- `/Users/jaskarn.singh/Documents/PREPO/usap-skills/agents/security/cs-security-analyst.md` line 22 — change `Alex knows all 66 USAP skills` to the live count (68) or, better, parameterise via a template.
- `/Users/jaskarn.singh/Documents/PREPO/usap-skills/agents/CLAUDE.md` — remove the `cs-blue-team-analyst` entry from the agent catalog OR scaffold the missing file under `agents/security/cs-blue-team-analyst.md` from `templates/agent-template.md`.

Files to create:

- `/Users/jaskarn.singh/Documents/PREPO/usap-skills/tools/validate_skill.py` (stdlib-only). Port `references/Anthropic-Cybersecurity-Skills/tools/validate-skill.py` and replace `REQUIRED_FIELDS` with USAP's canonical 5+5 schema. Add a non-blocking WARN pass for the 14 legacy extended-frontmatter skills. Reject `*.ps1` under any `<skill>/scripts/`.
- `/Users/jaskarn.singh/Documents/PREPO/usap-skills/tools/output_contract.py` — refactor `tests/skill_runner.py`'s 11-field validator into a re-usable function `validate_payload(dict) -> list[str]`.
- `/Users/jaskarn.singh/Documents/PREPO/usap-skills/.github/workflows/validate-skills.yml` — triggered on push and PR paths `*/*/SKILL.md`; runs `python3 tools/validate_skill.py --all`; emits per-domain skill count to `GITHUB_STEP_SUMMARY` so future count drift fails the build.

Acceptance: `python3 tools/validate_skill.py --all` exits 0 on the current 68 active-domain skills (with 14 WARN entries for legacy frontmatter); the workflow's GITHUB_STEP_SUMMARY shows 9 domains × the per-domain skill counts that match the inventory.

### Quick Win 2 — Add the framework-mappings schema slot and ship the pilot Navigator layer (effort: M)

Files to edit:

- `/Users/jaskarn.singh/Documents/PREPO/usap-skills/standards/frontmatter-spec.md` — add a new optional "Framework Mappings" section defining `metadata.frameworks.{mitre_attack, nist_csf, mitre_atlas, owasp_top10}` as `array[string]`. Cap 8 IDs per skill. Document the relationship to runtime field `mitre_ttps` in `standards/output-contract.md`.
- `/Users/jaskarn.singh/Documents/PREPO/usap-skills/templates/skill-template.md` — add a commented placeholder block under `metadata:`.

Files to create:

- `/Users/jaskarn.singh/Documents/PREPO/usap-skills/shared/scripts/framework_extractor.py` — stdlib-only. Two modes: `--emit coverage` writes `mappings/mitre-attack/coverage-summary.md` and `mappings/nist-csf/csf-alignment.md`; `--emit navigator` writes `mappings/mitre-attack/attack-navigator-layer.json` (Navigator v4.5 schema). Reads `metadata.frameworks.*` first, falls back to regex over body markdown (`T\d{4}(\.\d{3})?` and `[A-Z]{2}\.[A-Z]{2}-\d{2}`).
- `/Users/jaskarn.singh/Documents/PREPO/usap-skills/mappings/README.md`, `mappings/mitre-attack/README.md`, `mappings/nist-csf/README.md` — static READMEs; coverage docs are generated only.

Pilot backfill: tag `metadata.frameworks` on the 4 detection skills that already cite T-IDs in body prose (`detection-engineering`, `threat-hunting`, `threat-intelligence`, `behavioral-analytics`). Verify `python3 shared/scripts/framework_extractor.py --emit navigator` produces a Navigator layer that loads cleanly in MITRE Navigator.

Acceptance: `mappings/mitre-attack/attack-navigator-layer.json` exists, validates against Navigator v4.5 schema, and lists ≥10 techniques from the 4 detection skills.

### Quick Win 3 — Scaffold one high-priority domain end-to-end as a template for the rest (effort: M)

Pick `webapp-security/` as the pilot domain (highest ACS volume, clearest agentic positioning).

Files to create:

- `/Users/jaskarn.singh/Documents/PREPO/usap-skills/webapp-security/CLAUDE.md` — domain guidance modeled on `governance/CLAUDE.md`.
- `/Users/jaskarn.singh/Documents/PREPO/usap-skills/webapp-security/README.md`.
- Three anchor skills, each scaffolded from `templates/skill-template.md`:
  - `webapp-security/webapp-risk-triage/` (L3, intent_type: `analyze`)
  - `webapp-security/owasp-top10-classifier/` (L3, intent_type: `detect`)
  - `webapp-security/api-security-posture/` (L3, intent_type: `analyze`)
- Each skill folder gets the full canonical package: `SKILL.md` (with `metadata.frameworks.owasp_top10: [A01, A03, ...]`), `README.md`, `references/workflow.md`, `assets/templates/output-template.json`, `expected_outputs/sample_output.json` (contract-compliant), `scripts/<slug>_tool.py` (real argparse logic that reads an input JSON and emits the 11-field payload).
- `/Users/jaskarn.singh/Documents/PREPO/usap-skills/domains/webapp-security.md` — domain index entry.
- `/Users/jaskarn.singh/Documents/PREPO/usap-skills/agents/appsec/cs-appsec-engineer.md` — new `cs-*` agent orchestrating the 3 webapp skills plus existing `appsec-devsecops/sast-dast-coordinator` and `appsec-devsecops/secure-sdlc`. Use v2 contract (Persona, Command Menu, MANDATORY EXECUTION RULES, FAILURE MODES, SUCCESS CRITERIA, state block).

Files to edit:

- `/Users/jaskarn.singh/Documents/PREPO/usap-skills/standards/frontmatter-spec.md` — extend `metadata.category` enum with `usap-webapp`.
- `/Users/jaskarn.singh/Documents/PREPO/usap-skills/CLAUDE.md` — bump domain claim from 9 to 10; add `webapp-security` to the domain list.
- `/Users/jaskarn.singh/Documents/PREPO/usap-skills/README.md` — domain count + skill count update.

Acceptance: `tools/validate_skill.py --all` passes on the 3 new skills; `cs-appsec-engineer` agent loads cleanly via `cs-*` invocation; sample `python3 webapp-security/webapp-risk-triage/scripts/webapp-risk-triage_tool.py --output json` emits a payload that passes `tools/output_contract.py`.

Once these 3 quick wins land on `feat/expand-domains-and-ci`, the same pattern fans out across `container-k8s-security/`, `phishing-defense/`, and the MED-priority domains in subsequent sprints.

---

## 7. Anti-Patterns to Avoid (3–5 things ACS does that USAP should NOT copy)

### 7.1 Do not import ACS skills verbatim or adopt their flat single-domain frontmatter

ACS uses `domain: cybersecurity` on every skill and pushes the real taxonomy into a 45-distinct-value `subdomain:` field at YAML top level. Copying this regresses USAP's stricter 9-domain directory layout and 8-token `metadata.category` enum, both of which power the `cs-*` routing model. Worse, ACS's two-field frontmatter (`name`, `description` only required) cannot carry USAP's L1–L4 levels, mutating-intent declarations, or approval-required flags. Wholesale adoption would silently strip governance controls from the 14 legacy skills that depend on those fields. Cite ACS in `references/` and re-author the equivalent agentic skill — never copy.

### 7.2 Do not allow third-party Python dependencies in `<slug>_tool.py`

ACS skills routinely import `requests` (102 scripts), `pandas` (22), `boto3` (18), `yaml` (11), `numpy` (6), plus `cryptography`, `paramiko`, `ldap3`, `pefile`, `yara`, `kubernetes`, `flask`. This breaks USAP's offline/air-gap-friendly guarantee that any `_tool.py` runs against a fresh `python3` with no `pip install`. Once one USAP skill ships with `import requests`, future contributions will follow and the guarantee dies. If an L4 skill genuinely needs a live API actor, ship it as a separate `<slug>_actor.py` with a leading docstring listing third-party deps and require `human_approval_required: true` in the agent yaml — but keep `<slug>_tool.py` stdlib-only.

### 7.3 Do not accept PowerShell-only skill scripts

ACS ships two `.ps1` files under `<skill>/scripts/` (e.g., `Deploy-ADHoneytokens.ps1`, `audit_smb_signing.ps1`) with `#Requires -Modules ActiveDirectory` and `#Requires -Version 5.1` headers that force Windows + RSAT and exclude macOS/Linux CI runners. USAP positions skills as portable LLM prompts plus advisory tools; introducing a PowerShell-only script at the `scripts/` tier signals that some skills require Windows — contradicting the runtime-agnostic 11-field JSON contract. Add a validator rule that rejects `*.ps1` anywhere under `<skill>/scripts/`. If a Windows-only workflow is necessary, document the commands in `references/workflow.md` and let the user run them externally.

### 7.4 Do not maintain framework coverage docs by hand

ACS hand-edits `mappings/nist-csf/csf-alignment.md` and `mappings/mitre-attack/coverage-summary.md`, and the artifacts have already drifted: the top-level README claims `MITRE ATT&CK v19.1`, the mappings README says `Enterprise v15`, the Navigator JSON says `Enterprise v14`. Three different versions in three different docs in the same repo. USAP should never accept a hand-maintained mapping artifact — every coverage doc must be regenerated by `shared/scripts/framework_extractor.py` and the CI workflow must `git diff --exit-code mappings/` to fail on drift. Treat the static `mappings/*/README.md` as the only writable surface; everything else is generated.

### 7.5 Do not optimise for skill count at the cost of agentic identity

ACS's 754-skill marketing is a real asset for breadth — but it also produces deception-technology with 2 skills, blockchain-security with 1, firmware-analysis with 1. Volume without depth is noise. USAP's positioning is the opposite: fewer, deeper, agent-orchestratable skills with structured runtime guarantees. Don't chase ACS's skill count; chase the cs-* orchestration story and the 11-field contract. The README should lead with "USAP is the orchestration layer for atomic cybersecurity skills" and treat skill count as a follower metric.

---

## 8. Open Questions (require user decision)

1. **Domain materialization vs. removal.** Should the missing `pentest/` and `system-security/` directories be scaffolded (committing to ship anchor skills + a `cs-*` agent for each within 2 sprints) or removed from the `CLAUDE.md` 11-domain claim and the `domains/` index? The two paths have different cost profiles.

2. **Framework-mapping schema location.** Place the new framework arrays at `metadata.frameworks.{mitre_attack, nist_csf, ...}` (nested, keeps top-level frontmatter clean) or at the YAML top level matching ACS's shape (eases reverse compatibility with ACS tooling)? The inventory recommends nested for spec-conformance and clean separation; user should confirm.

3. **Legacy extended-frontmatter migration.** The 14 active-domain skills using `agent_id`/`level`/`plane`/`phase`/`ttl`/`mutating_intents`/`providers` fields work today and the project CLAUDE.md says "do not convert old skills unless explicitly asked." Confirm: keep both formats indefinitely, migrate over time, or commit to a deprecation timeline?

4. **License posture for cross-references to ACS.** USAP is MIT; ACS is Apache-2.0. Re-authoring ACS workflows under USAP MIT is fine; citing ACS skill paths in USAP `references/` is fine. Is verbatim quoting (e.g., embedding an ACS step in a USAP `SKILL.md`) acceptable with attribution, or should we prohibit it to keep license boundaries clean?

5. **Agent expansion ordering.** Five new cs-* agents are proposed (`cs-cloud-investigator`, `cs-supply-chain-defender`, `cs-threat-intel-lead`, `cs-forensics-lead`, `cs-purple-team-lead`) plus the missing `cs-blue-team-analyst`. Should they ship in domain-priority order (cloud first, supply-chain second) or in SOC-shift order (blue-team-analyst first since it fills a documented gap)?

6. **Quick-win sequencing.** Are the three quick wins (validator+CI, framework-mappings pilot, webapp-security pilot domain) acceptable as the next-sprint scope, or should one be deferred? They are roughly equal effort and can run in parallel, but ship-order matters for CI gating (validator first unblocks everything else).

7. **agentskills.io public listing.** USAP is 95% conformant once `version` is quoted and the 28 metadata-list violations are resolved. Should the project pursue public listing in the agentskills.io directory (positioning USAP as the first cybersecurity-focused skills pack with structured output guarantees), or keep the conformance posture internal until the cs-* orchestration story is more mature?

---

End of document.
