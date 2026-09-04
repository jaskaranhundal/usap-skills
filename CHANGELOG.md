# Changelog

All notable changes to USAP are recorded here. Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/); USAP follows [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Fixed

- **Dispatch timeout is a real bound.** `tools/mcp_dispatch.py` read adapter output with a blocking `readline()` inside its deadline loop, so an adapter that stayed alive without emitting a newline hung `dispatch(timeout=…)` indefinitely. The reader is now non-blocking (`selectors` plus `os.read`), re-checks the deadline between reads and treats EOF as premature exit. Regression test `tools/mcp_dispatch_test.py` uses a fake adapter that stalls after a partial line.

## [1.13.0] — 2026-07-03

### Adoption + reach — make the moat obvious

USAP's architecture already leads the reference repos (none have a live MCP runtime, evidence gate, reproducible scoring, or independent eval). This release closes the credibility/reach gap so visitors see that in seconds.

### Added

- **`examples/README.md`** — a reproducible showcase: every one of the four pillars (connector-agnostic resolution, the evidence gate rejecting prose, reproducible EPSS/CVSS/confidence, the held-out eval) shown with **real command output** the reader can re-run. The best "prove it works" artifact in the repo.
- **`INSTALLATION.md`** — one consolidated per-platform install guide (Claude Code plugin, Cursor/Windsurf/Codex/Gemini/Aider polyglot, ChatGPT Custom GPT, Ollama/AnythingLLM paste, the stdlib Python tooling, and MCP-server registration).
- **`custom-gpt/README.md`** — a ChatGPT Custom GPT instruction set that runs USAP's 11-field contract + evidence discipline + gated mutation, extending USAP's reach beyond Claude.
- **`CITATION.cff`** — standard citation metadata so USAP can be cited in research and shows a "Cite this repository" button on GitHub.
- README links the examples showcase + installation guide prominently near the top.

### Verified

- Every command shown in `examples/README.md` re-runs to the documented output.
- Full suite green: `validate_skill --all` 79/79, `mcp_server_test` 32/32, `regen_samples --check`.

## [1.12.0] — 2026-07-03

### Pillar 1 rollout — the whole cs-* fleet drives on the data backend

v1.9.0 wired the flagship `cs-security-analyst` to the connector-agnostic MCP data backend. This rolls that exact pattern across the **remaining 10 cs-* agents**, so every persona now fetches evidence from live connectors and cites resolvable sources instead of reasoning from pasted logs.

### Added / Changed

- **10 cs-* agents wired to MCP:** `cs-incident-responder`, `cs-cloud-investigator`, `cs-supply-chain-defender`, `cs-blue-team-analyst`, `cs-red-teamer`, `cs-purple-team-lead`, `cs-threat-intel-lead`, `cs-devsecops-engineer`, `cs-ciso-advisor`, `cs-appsec-engineer`. Each declares a connector-agnostic `usap_mcp` frontmatter whitelist (domain read capabilities + gated mutating ones), fetches evidence in its workflows via logical `mcp:` names and cites `evidence_references[].source` as `mcp:<logical>:<tool>:<tool_call_id>` (or `https://` / `local://`), carries a "Live MCP Data Backend" section, and has all "Future: MCP Connector Integration" / "paste logs" prose removed.
- **Registry logical vocabulary extended** (`registry/usap-mcp-registry.yaml`): added `edr.list_detections`, `identity.list_events`, `firewall.list_policies` (read) plus gated `edr.isolate_host`, `firewall.block_ip`, `identity.suspend_user`, `code.open_issue` (mutating). 12 logical names total; every agent `mcp:` reference is a verified subset.

### How it was built (resilience note)

The 10 agents were fanned out to parallel worktree subagents. Most hit a shared session-token limit mid-edit and died before committing. Their edits were recovered from the worktrees, validated (YAML parses, no paste prose, Live MCP section), and the ones that died just before their final section — plus `cs-threat-intel-lead`, whose worktree never persisted — were completed by hand. All 10 verified complete.

### Completes Pillar 1

All 11 verdict-producing cs-* agents (analyst from v1.9.0 + these 10) now fetch from the connector-agnostic backend. Mutating actions (host isolation, IP block, user suspension, issue creation) are declared only as `gated` capabilities requiring `human_approval_required: true`.

### Verified

- Registry validates (12 logical names); every agent `mcp:` reference resolves to a declared logical name (0 unknown).
- `validate_skill --all` 79/79, `mcp_server_test` 32/32, `regen_samples --check` green.

## [1.11.0] — 2026-07-03

### Pillar 4 — independent evaluation (stop grading USAP against itself)

The fourth 7.5→9.5 pillar. The `fortigate`/`challenge`/`compare` commands grade USAP against USAP's own canonical scorecards — circular. This adds a held-out, hand-labeled corpus USAP did not write, and a metrics engine that scores against it.

### Added

- **Held-out corpus.** `tests/holdout/cases/*.json` — 12 hand-labeled cases: **7 real threats** (Log4Shell, xz-utils backdoor, Capital One SSRF→IMDS, Okta session theft, MOVEit/Cl0p, Midnight Blizzard OAuth abuse, a live-key leak) and **5 benign-but-noisy false-positive traps** (an authorized vuln scan, HR-driven bulk offboarding, a CI service-account burst, a contracted pentest window, the AWS documentation example key in a fixture). Each case names its public `source` and defends its label. The negatives are what make precision and false-positive-rate honest.
- **Evaluation engine.** `tests/holdout_runner.py` (stdlib) computes precision / recall / F1 / false-positive-rate / severity-accuracy / intent-accuracy / MTTD from USAP predictions vs the labels. Pluggable responder: `--responder synthetic --predictions <file>` scores a pre-produced batch (and is how the engine is unit-tested); `--responder llm` is the documented seam to drive each cs-* persona live (needs an LLM endpoint — deliberately not run in CI).
- `tests/holdout/README.md` (labeling rules + the LLM integration seam) and `tests/holdout/RELEASES.md` (per-release precision/recall/FPR/MTTD table, baseline pending a live run).
- **CI self-check.** `validate-skills.yml` gains a deterministic step that runs the synthetic example (a deliberately-imperfect predictor) and asserts its fixed metrics (precision/recall 0.8571, FPR 0.20). If they move without a corpus change, the scoring engine regressed.

### Why the LLM part isn't wired here

Driving the personas live needs a model endpoint; this environment has none reachable (Ollama not running). The corpus, the metrics engine, and the CI protection are complete and verified — wiring a concrete `--responder llm` endpoint is the remaining integration step, and the first live run seeds the `RELEASES.md` baseline.

### Verified

- Engine metrics hand-verified: TP=6 FP=1 FN=1 TN=4 → precision 0.8571, recall 0.8571, FPR 0.20, F1 0.8571, MTTD 17.5.
- Full `validate-skills.yml` suite (incl. the new self-check) + `mcp_server_test` 32/32 + `validate_skill --all` 79/79 all green.

## [1.10.0] — 2026-07-03

### Pillar 3 — reproducible scoring (kill the narrated number)

The second of the 7.5→9.5 pillars. Where v1.9.0 made every *claim* traceable to a fetched artifact, this makes every *number* reproducible. The rule: if a number can be computed, compute it from the canonical source; if it can't, say "qualitative" — never fabricate.

### Added

- **EPSS from the FIRST feed.** `shared/scripts/epss_scorer.py` (stdlib `urllib`) fetches the real EPSS probability + percentile for a CVE from `api.first.org`, caches to `~/.usap/cache/epss/<cve>.json` (24h TTL), and extracts CVE ids from free text. Unreachable feed or unknown CVE → a *qualitative* result (`epss: null` + note), never a fabricated score. CLI: `--cve CVE-2021-44228` / `--text "…"`. Verified live: Log4Shell → 0.99999, xz-backdoor → 0.85974.
- **Written confidence rubric.** `shared/scripts/confidence_rubric.py` computes confidence deterministically from evidence: source-reliability tiers (primary 0.90 / secondary 0.70 / tertiary 0.50), a corroboration lift for additional agreeing sources, and a dissent penalty — clamped to a 0.99 ceiling (no finite evidence justifies certainty). `standards/confidence-rubric.md` is the human-readable spec that maps 1:1 to the code. CLI: `confidence_rubric.py --secondary 2` → 0.84.
- **CVSS reproducibility check in the contract.** `tools/output_contract.py::validate_scores_reproducible()` rejects any payload whose claimed `cvss_score` disagrees (>0.1) with the CVSS vector it cites, recomputed via the existing `shared/scripts/cvss_scorer.py`. Narrowly scoped — fires only when a numeric `cvss_score` AND a vector are both present, so it catches fabricated numbers without touching the corpus. Wired into `validate_payload(score_checks=True)`, independent of the evidence gate.
- **vuln-scan computes confidence from the rubric.** `appsec-devsecops/vuln-scan/scripts/vuln-scan_tool.py` replaces its `0.85 − 0.05·merges` heuristic with a `score_confidence()` call (scanner = secondary source; a threat-model mapping corroborates → second source). Output is now reproducible run-to-run and carries the rubric's rationale. Sample updated to the computed 0.84.

### Fixed

- **v1.9.0 regression in `tools/regen_samples.py`.** v1.9.0 made the evidence gate default-on in `validate_payload`; the sample generator validated its structural stubs with that default and errored (`GENERATOR ERROR … evidence gate`), and it stopped recognising hand-authored samples as "already clean." `regen_samples.py` now validates structurally (`evidence_gate=False`), matching the corpus CI's `--structural-only` pass. `regen_samples.py --check` is green again (0 written, 79 left alone). *(This CI step was not run during the v1.9.0 verification — added to the standard pre-ship suite going forward.)*

### Verified

- All 9 `validate-skills.yml` CI steps pass locally + `mcp_server_test` 32/32 + `validate_skill --all` 79/79 + `invocation-control --strict` exit 0.
- EPSS live-feed, confidence-rubric determinism/monotonicity, CVSS cross-check (rejects fabricated, accepts matching), and vuln-scan reproducible-confidence all unit-tested.

## [1.9.0] — 2026-07-03

### The data-backend MVP — USAP verdicts become verifiable, not just plausible

v1.4–v1.8 built the MCP road (server, router, dispatcher, scheduler, audit chain). This release makes the flagship persona **drive on it**: `cs-security-analyst` (Alex) now fetches evidence from live MCP connectors and every verdict it emits must cite a resolvable source. Two locked design decisions shape it — a **connector-agnostic** abstraction (portable to any environment) and the **hardest-line** evidence gate (no verdict without a resolvable source, at any severity).

### Added

- **Connector-agnostic logical-name resolver.** `registry/usap-mcp-registry.yaml` gains a `logical_names:` block mapping logical capabilities (`siem.search`, `code.list_repos`, `code.get_pr_diff`, `cloud.list_findings`, `slack.post_message`) to an ordered list of physical MCP implementations. `tools/mcp_router.py::resolve_logical()` resolves a logical name to whichever physical MCP the operator has `enabled` — preferred-first, deterministic. The same `cs-security-analyst` works against Splunk, Elastic, or Sentinel with no edit; if nothing implements a capability it resolves to `None` and the agent degrades gracefully. `tools/mcp_registry.py` validates the block (structural errors fatal; zero-enabled implementations = non-fatal WARN). CLI: `python3 tools/mcp_router.py --resolve mcp:siem:search`.
- **Hardest-line evidence gate.** `tools/output_contract.py::validate_evidence_resolvable()` requires every payload — at ANY severity, including `informational` — to cite ≥1 `evidence_references[].source` that resolves to one of four forms: `mcp:<logical>:<tool>:<tool_call_id>` (logical name must be declared in the registry), `https://…`, `s3://…`, or `local://<repo-relative-path>` (path must exist). Prose sources like `"scanner"` are rejected. Wired into `validate_payload(payload, evidence_gate=True)` (default on) and enforced at the runtime contract boundary — the MCP server's `validate_payload` tool. Documented in `standards/output-contract.md` → "Resolvable Evidence Gate".
- **`cs-security-analyst` rewired to the data backend.** Frontmatter declares a connector-agnostic `usap_mcp` whitelist (read-only logical capabilities + the single gated mutating one). The AT / TH / CA workflows now fetch evidence via `mcp:siem:search` / `mcp:code:get_pr_diff` / `mcp:cloud:list_findings` and emit verdicts whose `evidence_references` cite the `mcp:` tool-call id that produced each finding. New "Live MCP Data Backend" section replaces the old "Future: MCP Connector Integration" / "paste logs" prose (deleted). Graceful degradation is a hard rule: no connector → mark the axis UNKNOWN, never narrate assumed telemetry as observed.
- **Reference MCP adapters travel with the plugin.** `.claude-plugin/plugin.json` gains an `mcpServers` block declaring the three reference adapters (Splunk, GitHub, Slack) in safe `USAP_ADAPTER_MODE=fixture` by default, so a fresh install can demo routing/dispatch with zero credentials.

### Changed

- `.github/workflows/validate-skills.yml`: the blocking corpus contract check runs `--structural-only` (11-field structure, unchanged blocking behaviour); a **new non-blocking** step reports evidence-gate rollout status. This keeps `main` green while the gate rolls out sample-by-sample.
- `appsec-devsecops/vuln-scan` sample migrated to `mcp:code:get_pr_diff:…` evidence sources — the first gate-compliant sample and the canonical pattern for the rollout.

### Rollout backlog (failing the gate BY DESIGN)

The gate is enforced at the runtime boundary now, but only **1 of 79** committed skill samples cites resolvable evidence today (vuln-scan). The other **78 samples fail the gate by design** — each is migrated as its owning skill/agent is wired to the data backend in the per-agent rollout. This is the intended "surface the gap loudly" signal, not a regression; structural CI stays green.

### Deviations from plan (documented)

- The agent's logical MCP whitelist lives in a dedicated `usap_mcp:` frontmatter block, not the Claude Code `tools:` grant field — `tools:` controls real tool access, and injecting non-existent logical names there would confuse the agent loader.
- The `mcpServers` block lives in the **repo-root** `.claude-plugin/plugin.json` (where `${CLAUDE_PLUGIN_ROOT}/adapters/` resolves), not `plugins/usap/.claude-plugin/plugin.json` — the marketplace source is `./plugins/usap` but the adapters live at repo root. Bundling adapters under the marketplace plugin is a follow-up.

### Verified

- `tools/validate_skill.py --all` → 79/79 PASS; `tools/validate_invocation_control.py --all --strict` → exit 0.
- `tools/mcp_server_test.py` → 32/32 PASS (gate now enforced at the server boundary).
- Resolver: `siem.search`→`mcp__splunk__search`; with only GitHub enabled, `siem.search`→`None` (graceful), flip Splunk on → resolves. `mcp:siem:search` normalises to `siem.search`.
- Gate: 1 positive + 4 negatives (empty / prose / missing local path / unknown logical) all correct; `--structural-only` bypass confirmed.
- Structural corpus check stays green (79/79); loop demo chain verifies + signed.

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

[Unreleased]: https://github.com/jaskaranhundal/usap-skills/compare/v1.13.0...HEAD
[1.13.0]: https://github.com/jaskaranhundal/usap-skills/compare/v1.12.0...v1.13.0
[1.12.0]: https://github.com/jaskaranhundal/usap-skills/compare/v1.11.0...v1.12.0
[1.11.0]: https://github.com/jaskaranhundal/usap-skills/compare/v1.10.0...v1.11.0
[1.10.0]: https://github.com/jaskaranhundal/usap-skills/compare/v1.9.0...v1.10.0
[1.9.0]: https://github.com/jaskaranhundal/usap-skills/compare/v1.8.0...v1.9.0
[1.8.0]: https://github.com/jaskaranhundal/usap-skills/compare/v1.7.0...v1.8.0
[1.7.0]: https://github.com/jaskaranhundal/usap-skills/compare/v1.6.0...v1.7.0
[1.6.0]: https://github.com/jaskaranhundal/usap-skills/compare/v1.5.0...v1.6.0
[1.5.0]: https://github.com/jaskaranhundal/usap-skills/compare/v1.4.0...v1.5.0
[1.4.0]: https://github.com/jaskaranhundal/usap-skills/compare/v1.1.1...v1.4.0
[1.1.1]: https://github.com/jaskaranhundal/usap-skills/compare/v1.1.0...v1.1.1
[1.1.0]: https://github.com/jaskaranhundal/usap-skills/compare/v1.0.0...v1.1.0
[1.0.0]: https://github.com/jaskaranhundal/usap-skills/releases/tag/v1.0.0
