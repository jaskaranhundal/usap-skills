# Changelog

All notable changes to USAP are recorded here. Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/); USAP follows [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

_No unreleased changes yet._

## [1.1.0] — 2026-06-22

### Added

- 5-skill AppSec chain ported from Anthropic's defensive-AI reference harness: `threat-model`, `vuln-scan`, `finding-triage`, `patch-candidate`, `appsec-customize`. Each emits an 11-field payload and chains through `next_agents`.
- 3 new `webapp-security/` skills: `webapp-risk-triage`, `owasp-top10-classifier`, `api-security-posture` (with OWASP Top 10 framework mappings).
- 4 new `cs-*` orchestrator agents in `agents/security/`: `cs-cloud-investigator`, `cs-supply-chain-defender`, `cs-threat-intel-lead`, `cs-purple-team-lead`. Brings the count to 12 cs-* agents across 5 domain dirs (security 8, appsec 1, devsecops 1, executive 1, governance 1).
- `metadata.frameworks.{mitre_attack, nist_csf, mitre_atlas, owasp_top10, d3fend, nist_ai_rmf}` schema slot on every skill, driving auto-generated `mappings/mitre-attack/attack-navigator-layer.json` and `mappings/nist-csf/csf-alignment.md` via `tools/framework_extractor.py`.
- Three stdlib-only validators under `tools/`: `validate_skill.py` (canonical frontmatter), `validate_invocation_control.py` (L1-L4 invocation gate), `output_contract.py` (11-field payload).
- Blocking CI workflows: `.github/workflows/validate-skills.yml`, `.github/workflows/build-index.yml`, `.github/workflows/bundle-dist.yml`, `.github/workflows/docs-deploy.yml`.
- MkDocs Material docs site at <https://jaskaranhundal.github.io/usap-skills/> with `SoftwareApplication` JSON-LD injected via `overrides/main.html`.
- README architecture diagram (Mermaid), end-to-end demo transcript with real 11-field output, Proof section linking every marketing claim to a committed file.
- `SECURITY.md` (disclosure policy) and `SELF-AUDIT.md` (live validator-state report).
- `agentskills.io`-spec conformance section in `standards/frontmatter-spec.md` plus the optional Invocation Control extensions (`disable-model-invocation`, `user-invocable`, `allowed-tools`, `disallowed-tools`, `context`, `paths`, `model`, `effort`).
- `standards/agent-contract.md` v2 — formal spec for `cs-*` orchestrator agents (Persona, Critical Actions, Command Menu, MANDATORY/FAILURE/SUCCESS blocks).

### Changed

- Skill count: 56 → 79 across 12 active domains.
- `cs-*` agent count: 5 → 12.
- Domain count: 9 → 12 (added `pentest/`, `system-security/`, `webapp-security/`).
- README rewrite: new ≤25-word hook, badge counts aligned to disk reality, ICP / "who is this for" section, Quick Start matrix.
- `shared/scripts/bundle_usap.py` extended from a 6-skill / 5-agent hardcoded list to the full 12-domain / 12-agent inventory; CLI help text now matches the live skill total.
- `agents/security/cs-security-analyst.md` updated to reference all 79 skills (was 71).
- GitHub repo description, topics, and homepage URL aligned with current state.

### Removed

- Public-research and competitive-analysis files (`docs/research/`, `docs/comparisons/`) moved out of the repo to a local-only `references/private-research/` workspace.
- Hardcoded "66 skills + 5 agents" snippet in bundle output.
- Legacy mentions of "71 skills" / "74 skills" / "7 cs-* agents" across `GEMINI.md`, `agents/security/cs-security-analyst.md`, `docs/index.md`, `docs/TECHNICAL_REFERENCE.md`, `docs/domains/index.md`, `anythingllm-package/README.md`, `mkdocs.yml`.

### Security

- `tools/validate_invocation_control.py` now runs in strict mode in CI — any L3 / L4 skill missing the required `disable-model-invocation`, `user-invocable`, or `allowed-tools` invariant fails the build.
- Every commit on `main` runs the full validator sweep via `.github/workflows/validate-skills.yml`.

## [1.0.0] — initial release

- 56 USAP skill packages across 9 active domains.
- 5 `cs-*` orchestrator agents (`cs-security-analyst`, `cs-incident-responder`, `cs-red-teamer`, `cs-devsecops-engineer`, `cs-ciso-advisor`).
- Apache 2.0 license.
- Tagged at commit `4e7622b`.

[Unreleased]: https://github.com/jaskaranhundal/usap-skills/compare/v1.1.0...HEAD
[1.1.0]: https://github.com/jaskaranhundal/usap-skills/compare/v1.0.0...v1.1.0
[1.0.0]: https://github.com/jaskaranhundal/usap-skills/releases/tag/v1.0.0
