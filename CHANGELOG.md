# Changelog

All notable changes to USAP are recorded here. Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/); USAP follows [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

_No unreleased changes yet._

## [1.5.0] — 2026-06-26

### Added

- **MCP routing layer (Phase 2).** USAP becomes the master MCP. The router takes an 11-field payload from a skill, looks up the matching specialist MCP from a YAML registry, and returns either an approval prompt (if mutating) or a dispatch decision.
- `registry/usap-mcp-registry.yaml` — declares 7 downstream MCPs (Slack, GitHub, Splunk, CrowdStrike, FortiGate, Okta, AWS Security Hub) with per-capability `mutating` + `approval_required` declarations. All `enabled: false` by default; Phase 3 ships the actual adapter binaries.
- `tools/mcp_registry.py` (~320 LOC) — stdlib-only YAML loader + structural validator. Enforces unique IDs, valid intents, and the rule that every mutating capability MUST have `approval_required: true`.
- `tools/mcp_router.py` (~190 LOC) — given a payload, scores every enabled MCP by `intent_type` match and `next_agents` overlap, picks the best candidate, gates on `human_approval_required`.
- `tools/mcp_audit.py` (~85 LOC) — JSONL audit-log writer at `~/.usap/audit/YYYY-MM-DD.jsonl` (overridable via `USAP_AUDIT_DIR`). Every routing decision lands here before return.
- Two new MCP tools on `tools/mcp_server.py`: `route_payload(payload)` (the router) and `list_mcps()` (the registry).
- `docs/mcp-routing.md` — Phase 2 docs: registry shape, routing logic, audit log, client integration, design rules for future phases.
- `tools/mcp_server_test.py` extended from 17 to 23 assertions (adds list_mcps + 4 routing assertions).

### Why Phase 2 doesn't dispatch

Phase 2 returns `would_dispatch` instead of actually invoking the downstream adapter. Phase 3 owns dispatch. This split lets us prove routing logic + approval gate + audit log are correct **before** any real specialist MCP adapter exists. Phase 3 plugs adapters into a tested decision model.

### Safety invariants

- Mutating capabilities MUST declare `approval_required: true` in the registry. The loader rejects any registry that violates this.
- Every routing decision writes one audit line; no exceptions.
- The router is deterministic: same payload + same registry = same decision, always.
- Stdlib only — no new dependencies.

## [1.4.0] — 2026-06-26

### Added

- **MCP server (Phase 1).** `tools/mcp_server.py` exposes USAP as a [Model Context Protocol](https://modelcontextprotocol.io) server over stdio. Any MCP-compatible client — Claude Code, Cursor, Codex CLI, Gemini CLI, Goose, OpenCode — can now:
  - Discover the 79 USAP skills and 12 `cs-*` orchestrator agents via the `list_skills`, `list_agents` tools or via `resources/list`.
  - Load any skill or agent definition into the client's LLM context via `get_skill`, `get_agent`, or `resources/read`.
  - Validate a JSON payload against the typed 11-field output contract via `validate_payload`.
- `tools/mcp_server_test.py` smoke test covering 17 assertions across the JSON-RPC handshake, all 5 tools, resource enumeration, resource read, and error handling.
- `docs/mcp-server.md` install + usage docs with client-specific config examples (Claude Code, Cursor, Codex CLI, Gemini CLI).
- "Option 4 — MCP server" section in `README.md` pointing at the new install path.

### Why this matters

Phase 1 is read-only discovery + load. Phase 2 — already scoped — turns this server into the **master MCP** that routes security intents to downstream vendor MCPs (Splunk, CrowdStrike, FortiGate, Okta, AWS Security Hub, GitHub, Slack), with the contract's `human_approval_required` field enforcing the human gate before any mutating downstream call. The Phase 1 transport, discovery model, and contract validator are the foundation that work builds on.

### Notes

- Stdlib only — no new dependencies.
- ~440 lines of Python over JSON-RPC 2.0 / newline-delimited JSON, the standard MCP stdio transport.

## [1.1.1] — 2026-06-25

### Added

- Documented Claude Code plugin install path in `README.md` (`/plugin marketplace add jaskaranhundal/usap-skills` then `/plugin install usap-skills@usap`).
- `LAUNCH.md` removed from public tree and added to `.gitignore`; preserved locally as the private launch playbook.
- "Try it in 60 seconds" block restructured into three labelled options (Claude Code plugin, paste-into-any-LLM bundle, no-install web demo).

### Fixed

- `.claude-plugin/marketplace.json` was a copy of `plugin.json`; rewritten as a proper Claude Code marketplace catalogue with `owner`, `metadata`, and `plugins[]` listing USAP as the single offering.
- `.claude-plugin/plugin.json` expanded with `keywords[]`, structured `repository` block, and a description that names the 7 slash commands and 6 user-invocable skills the plugin actually installs.
- Stale plugin manifest claiming "66 skills / v1.0.0 / MIT" corrected to "79 / v1.1.0 / Apache-2.0" (introduced in v1.1.0, missed at tag).

### Removed

- `skills/` (74 broken/stale symlinks into the domain dirs — nothing referenced the flat path, and it was stale at 74 vs the actual 79).
- Root-level `assets/usap-linkedin.png` (duplicate of `docs/design-system/assets/usap-linkedin.png`).
- `.claude/launch.json` (local debug config referencing non-existent /tmp paths).
- `.claude/settings.local.json` and `push_usap.py` (working-tree-only files that were already gitignored).

### Relocated

- `assets/usap-linkedin-philosophy.md` → `docs/design-system/brand/design-philosophy.md` (Signal Architecture brand material belongs in the design-system tree).

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

[Unreleased]: https://github.com/jaskaranhundal/usap-skills/compare/v1.5.0...HEAD
[1.5.0]: https://github.com/jaskaranhundal/usap-skills/compare/v1.4.0...v1.5.0
[1.4.0]: https://github.com/jaskaranhundal/usap-skills/compare/v1.1.1...v1.4.0
[1.1.1]: https://github.com/jaskaranhundal/usap-skills/compare/v1.1.0...v1.1.1
[1.1.0]: https://github.com/jaskaranhundal/usap-skills/compare/v1.0.0...v1.1.0
[1.0.0]: https://github.com/jaskaranhundal/usap-skills/releases/tag/v1.0.0
