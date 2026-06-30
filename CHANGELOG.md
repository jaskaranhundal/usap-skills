# Changelog

All notable changes to USAP are recorded here. Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/); USAP follows [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

_No unreleased changes yet._

## [1.8.0] — 2026-06-27

### Added — polyglot + discoverability + operator UX bundle

This is a six-slice bundle shipped by parallel worktree agents into one PR. The thread is: USAP was Claude-Code-only with no machine-discoverable index, no MITRE Navigator artefact, no operator self-diagnosis. After v1.8.0 it's a polyglot AI-security library that registers with `agentskills.io`-style external tools, ships an auto-generated ATT&CK Navigator layer, and self-checks its own runtime state.

- **Polyglot sync (1 of 6).** `scripts/sync_codex_skills.py`, `sync_gemini_skills.py`, `sync_cursor_skills.py`, `sync_windsurf_skills.py`, `sync_aider_skills.py` + `sync_all.py` walk every `SKILL.md` and mirror them as relative symlinks under `.codex/`, `.gemini/`, `.cursor/`, `.windsurf/`, `.aider/`, with a `skills-index.json` per platform. The same SKILL.md is the source of truth for all 6 LLM clients. `--check` is idempotent and CI-friendly.
- **ATT&CK Navigator + ATTACK_COVERAGE.md (2 of 6).** `tools/framework_extractor.py` extended to scan body T-IDs (`T\d{4}(\.\d{3})?`) in addition to optional top-level `mitre_attack:` keys. Emits `mappings/mitre-attack/attack-navigator-layer.json` (Navigator v4.5+ schema; 79 T-IDs covered across 26 skills) and `mappings/mitre-attack/ATTACK_COVERAGE.md` (per-tactic kill-chain rollup). Load the JSON at `https://mitre-attack.github.io/attack-navigator/` for the visual.
- **Frontmatter conformance + validator hardening (3 of 6, biggest slice).** `standards/frontmatter-spec.md` now documents optional top-level framework keys (`mitre_attack`, `nist_csf`, `mitre_atlas`, `owasp_top10`, `d3fend`, `nist_ai_rmf`) — agentskills.io-conformant placement. Earlier `metadata.frameworks` nesting is deprecated but still validated for back-compat. New `standards/SKILL-AUTHORING-STANDARD.md` is the canonical contributor "DNA" doc. `standards/canonical-domains.md` pins 11 canonical domain slugs + aliases; `tools/validate_skill.py` rejects non-canonical paths. New `tools/validate_description.py` (third-person voice + trigger phrase) and `tools/validate_structure.py` (required package files) surface 22 over-long descriptions and 2 packages with missing structure as backlog. `metadata.requires.{bins,install}` schema reserved.
- **Operator UX (4 of 6).** `agents/meta/cs-usap-next.md` (Nova persona, v2 contract, ST/NX/AC/RJ/HE command menu) — state-aware "what's next" advisor that reads `~/.usap/`, runner state, registry, and git. `tools/usap_doctor.py --check / --fix / --report yaml` diagnoses operator defects (mixed-mode audit logs, stale runner.pid, missing audit key). `tools/usap_onboard.py --quiet / --enable <job>` does first-time setup with `~/.usap/.audit_key` (chmod 600) and prints the env-var export line. `audit/2026-Q2/RUBRIC.md` is a Pocock-style 7-dimension scoring rubric; `audit/2026-Q2/00-MASTER.md` is the scoring scaffold.
- **Root `index.json` + drift gate (5 of 6).** Repo root carries `index.json` (37 KB; 79 skills + 12 agents + 12 domains; agentskills.io-style schema) and `index.summary.json` (counts-only for badges). `.github/workflows/regen-index.yml` runs `tools/build_index.py --check` on every push and fails if regen would change anything. Agent discovery now walks `agents/**/cs-*.md` instead of a hard-coded list.
- **`cs-purple-team-lead` + themed scenario harness (6 of 6).** `agents/security/cs-purple-team-lead.md` rewritten to v2 contract: orchestrates `cs-red-teamer` + `cs-blue-team-analyst` + `cs-incident-responder` per session; PT/TT/DR/AC/HE command menu; MANDATORY EXECUTION RULES enforce ≥2 sub-agents per workflow + 11-field contract output. `tests/scenarios/themes/` adds a YAML manifest + three substantive scenarios (`ransomware/2026-q3-fintech-ransomware.yaml`, `supply-chain/2026-q3-npm-malicious-dep.yaml`, `cloud-misconfig/2026-q3-iam-overpermission.yaml`).

### Verified

- `tools/validate_skill.py --all` — 79/79 PASS (with new canonical-domain + framework + requires-bins checks active)
- `tools/mcp_server_test.py` — 32/32 PASS
- `tools/usap_loop_demo.py` — end-to-end chain valid, signed
- `tools/build_index.py --check`, `tools/framework_extractor.py --check`, `scripts/sync_all.py --check` — all OK (deterministic)
- `tools/usap_runner.py --validate`, `tools/mcp_registry.py --validate` — both OK
- `tools/usap_doctor.py --check` — surfaces the documented mixed-mode audit warning; runner + registry green

### Backlog surfaced (not blocking)

- 22/79 skills have over-long descriptions (`tools/validate_description.py --all`)
- 2/79 skill packages missing scripts (red-team domain)
- Live `~/.usap/audit/2026-06-27.jsonl` has mixed signed/unsigned lines from earlier-in-day runs without `USAP_AUDIT_KEY` exported — documented gotcha (`docs/mcp-scheduled.md` §7), operator action only

### Planning correction (carried in this bundle)

The plan file's Phase 2.1 specified `metadata.frameworks.*` for framework keys. ACS (the agentskills.io-conformant reference repo) uses YAML top-level placement. v1.8.0 adopts the top-level placement as canonical and validates both shapes for the rollout window. Future Phase 6 (agentskills.io listing submission) builds on the corrected placement.

## [1.7.0] — 2026-06-26

### Added — completes the master-MCP architecture

- **Scheduled persistence runner (Phase 4).** `tools/usap_runner.py` (~310 LOC) is a cron-style scheduler that fires skill workflows on a clock and dispatches results through the routing layer to a downstream MCP. Supports `M H * * *`, `*/N * * * *`, `@every Ns`, `@hourly`, `@daily`. Run modes: `--validate`, `--list`, `--once <job-id>`, `--run` (foreground daemon with graceful SIGTERM).
- `runner/runner.yaml` — declares scheduled jobs with skill / schedule / dispatch_to / dispatch_args. Four sample jobs shipped, all `enabled: false` by default.
- **Tamper-resistant audit log.** `tools/mcp_audit.py` rewritten with:
  - SHA-256 hash chain — every line carries `prev_hash` = SHA-256 of the previous line. Insertion, deletion, or modification of any line is detected.
  - Optional HMAC-SHA256 signatures — if `USAP_AUDIT_KEY` is set in the environment, every line carries a signature. The verifier checks both chain AND every signature.
  - `--verify` CLI mode walks the chain and reports any tampering.
  - `USAP_AUDIT_KEY` accepts hex bytes, a path to a keyfile, or a passphrase.
- `docs/mcp-scheduled.md` — Phase 4 docs: runner config schema, supported cron syntax, audit chain + signature design, production deployment notes (systemd, key management, log rotation, daily verification).
- `tools/mcp_server_test.py` extended from 27 to 32 assertions. Tests audit-log creation, `prev_hash` presence on every entry, `GENESIS` on the first entry, and full chain verification.

### How Phase 4 completes the vision

After v1.7.0 USAP is:
- An MCP server any client can connect to (Phase 1).
- A routing layer that gates mutating actions behind human approval (Phase 2).
- A dispatcher that actually invokes downstream adapters (Phase 3).
- A scheduler that fires workflows on a clock (Phase 4).
- A tamper-resistant audit log of every event (Phase 4).

That's the "minimum human intervention, maximum tool capability" architecture, complete: safe actions auto-execute, dangerous actions gate behind approval, scheduled workflows need no human, and the audit trail any compliance reviewer would demand is built in by default.

### Safety invariants (carried forward)

- Mutating capabilities MUST declare `approval_required: true` in the registry. Loader rejects violators.
- Every routing / approval / dispatch / scheduled-run event writes an audit line.
- Runner refuses to invoke mutating capabilities — only the human-gated `dispatch_after_approval` path can call those.
- Stdlib only.

## [1.6.0] — 2026-06-26

### Added

- **MCP adapters + dispatch (Phase 3).** Three reference adapters land under `adapters/` — Slack, GitHub, Splunk. Each is a small (~70 LOC) MCP server the router launches as a subprocess on demand. Default mode is `USAP_ADAPTER_MODE=fixture` so CI and first-time users get realistic responses with zero credentials. Live mode is one env-var flip + the documented per-adapter token.
- `adapters/_lib.py` (~145 LOC) — shared scaffolding so each adapter only declares capabilities + fixtures; the MCP protocol plumbing is reused.
- `tools/mcp_dispatch.py` (~190 LOC) — launches an adapter as a subprocess, walks the JSON-RPC handshake, invokes a capability, captures the response, terminates cleanly. Bounded timeout (default 20s).
- Router auto-dispatches non-mutating, no-approval-needed routes. Returns `status: dispatched` with `outcome.response` carrying the adapter's actual reply.
- New `dispatch_after_approval` MCP tool. When `route_payload` returns `approval_required`, the calling client surfaces the prompt to the user, then calls `dispatch_after_approval(mcp_id, capability_id, arguments, approval_token)` to actually invoke the capability. Writes paired `approval_granted` + `dispatch` audit lines.
- `registry/usap-mcp-registry.yaml` updates: `slack`, `github`, `splunk` flipped to `enabled: true` (Phase 3 adapters land). `crowdstrike`, `fortigate`, `okta`, `aws-security-hub` stay `enabled: false` until their production adapters land in a follow-up.
- `docs/mcp-adapters.md` — adapter authoring guide, Phase 3 flow diagram, the four reservation entries and their planned landing order.
- `tools/mcp_server_test.py` extended from 23 to 27 assertions. Adds `dispatch_after_approval` to the tool list, exercises actual splunk dispatch end-to-end, exercises a Slack approval-flow dispatch, and exercises the disabled-MCP failure path.

### Why this matters

Phase 1 + 2 proved discovery + routing + audit. Phase 3 closes the loop by making the router actually invoke vendor MCPs. The four production-security adapters (CrowdStrike / FortiGate / Okta / AWS Security Hub) are declared in the registry but disabled — they ship as follow-up PRs against a tested decision model.

### Safety invariants (carried forward)

- Mutating capabilities MUST declare `approval_required: true` in the registry. Loader rejects violators.
- Every dispatch writes audit lines (route → approval_granted? → dispatch).
- Deterministic routing. Stdlib only.

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

[Unreleased]: https://github.com/jaskaranhundal/usap-skills/compare/v1.8.0...HEAD
[1.8.0]: https://github.com/jaskaranhundal/usap-skills/compare/v1.7.0...v1.8.0
[1.7.0]: https://github.com/jaskaranhundal/usap-skills/compare/v1.6.0...v1.7.0
[1.6.0]: https://github.com/jaskaranhundal/usap-skills/compare/v1.5.0...v1.6.0
[1.5.0]: https://github.com/jaskaranhundal/usap-skills/compare/v1.4.0...v1.5.0
[1.4.0]: https://github.com/jaskaranhundal/usap-skills/compare/v1.1.1...v1.4.0
[1.1.1]: https://github.com/jaskaranhundal/usap-skills/compare/v1.1.0...v1.1.1
[1.1.0]: https://github.com/jaskaranhundal/usap-skills/compare/v1.0.0...v1.1.0
[1.0.0]: https://github.com/jaskaranhundal/usap-skills/releases/tag/v1.0.0
