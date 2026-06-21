# USAP Enhancement Roadmap: Patterns from Claude Code Skills, Hermes Agent, and the 2026 AI Security Agent Landscape

Document owner: USAP maintainers
Status: Research draft, ready for prioritization
Branch context: `feat/expand-domains-and-ci`
Sibling docs: [`casky-ai-competitive-landscape.md`](./casky-ai-competitive-landscape.md), [`anthropic-cybersec-skills-gap-analysis.md`](./anthropic-cybersec-skills-gap-analysis.md)

---

## 1. Executive Summary

The five highest-leverage enhancements USAP should ship next, distilled from Claude Code skills, Casky's Hermes Agent, the 2026 agentic AI SOC landscape, and the open-source skills ecosystem on GitHub:

- **Adopt Claude Code's invocation-control frontmatter** (`disable-model-invocation`, `user-invocable`, `allowed-tools`, `disallowed-tools`, `context: fork`, `paths`, `model`, `effort`) as an additive overlay to USAP's `metadata.*` block. Unlocks Claude Code portability, makes L4 mutating skills safe to ship as slash commands, and expresses the L1–L4 autonomy model in machine-readable frontmatter. Reference: [code.claude.com/docs/en/skills](https://code.claude.com/docs/en/skills).
- **Ship a "scheduled persistence" deployment model** modeled on Hermes Agent's cron pillar — each `cs-*` orchestrator registers as a recurring job (nightly OWASP, weekly MITRE-coverage audit, monthly NIST posture) with Hermes's hard constraints: isolated sessions, no recursive job creation, FTS5 cross-session recall. The missing operating model that lets USAP compete with "always-on" agentic SOC vendors without writing a SaaS. References: [casky.ai/blog](https://casky.ai/blog/always-on-security-coverage-with-hermes-agent-and-claude-cybersecurity-skills), [mindstudio.ai](https://www.mindstudio.ai/blog/hermes-agent-5-pillar-architecture-memory-skills-soul-crons).
- **Replicate Anthropic's `defending-code-reference-harness` six-skill chain** (`/threat-model` → `/vuln-scan` → `/triage` → `/patch` → `/customize`) inside `appsec-devsecops/`, with a gVisor-sandboxed autonomous mode for offensive verification. The only first-party Anthropic blueprint that maps cleanly onto a defensive workflow. Reference: [github.com/anthropics/defending-code-reference-harness](https://github.com/anthropics/defending-code-reference-harness).
- **Add a `frameworks` block, an `index.json` registry, and an ATT&CK Navigator layer generator** derived from per-skill metadata. Lets USAP answer "what techniques are we covered against?" with a generated artifact rather than prose — the biggest discoverability gap vs. every reference. Reference: [github.com/mukul975/Anthropic-Cybersecurity-Skills](https://github.com/mukul975/Anthropic-Cybersecurity-Skills).
- **Reposition USAP as "skills + orchestrators that compose with any agent runtime"** via first-class adapters for Claude Code, Hermes Agent, and MCP. The market has bifurcated into hosted agentic SOCs (Simbian, 7AI, Prophet, Dropzone, Andesite, Conifers, Google) and embedded developer tools (Claude Code, Cursor, Codex CLI, Gemini CLI); USAP belongs in the second lane as the substrate the first will embed. References: [conifers.ai](https://www.conifers.ai/blog/top-ai-soc-agents/), [cloud.google.com](https://cloud.google.com/blog/products/identity-security/rsac-26-supercharging-agentic-ai-defense-with-frontline-threat-intelligence).

---

## 2. Reference 1: Claude Code Skill Conventions

### 2.1 What a Claude Code skill is

A Claude Code skill is a directory with a `SKILL.md` (YAML frontmatter + markdown). The directory name becomes the slash command. Skills live at four scopes — enterprise, personal (`~/.claude/skills/`), project (`.claude/skills/`), plugin — with enterprise winning, then personal, then project, then plugin (namespaced). Plugin-root skills use the frontmatter `name` field as the command name ([code.claude.com/docs/en/skills](https://code.claude.com/docs/en/skills)).

Claude Code follows the [agentskills.io](https://agentskills.io/specification) open standard with three first-party extensions: invocation control, subagent execution, and dynamic context injection. The agentskills.io minimum (`name`, `description`) is everything external hosts must honor, but the three extensions are exactly the controls USAP needs for its L1–L4 autonomy model.

### 2.2 The frontmatter surface that goes beyond the spec minimum

The full Claude Code frontmatter surface, beyond agentskills.io's two-field minimum, is:

| Field | What it does | USAP implication |
|---|---|---|
| `disable-model-invocation: true` | Only humans can invoke the skill; description is not in context | The right primitive for every L4 mutating skill (key rotation, isolation, account disable) |
| `user-invocable: false` | Only the model can invoke; users can't `/foo` it | The right primitive for background-knowledge skills like `platform-ai/guardrail` |
| `allowed-tools: Bash(git add *) Bash(git commit *) Read` | Pre-approves tool calls while the skill is active | Replaces ad-hoc tool-gate language in USAP SKILL.md prose with a machine-readable allowlist |
| `disallowed-tools: AskUserQuestion` | Removes tools from Claude's pool for this skill | Useful for autonomous L3 detection skills that should never pause for human input |
| `context: fork` + `agent: Explore` | Runs the skill in a forked subagent context so the parent thread doesn't accumulate context | Direct analog to USAP's `cs-*` orchestrator pattern, but at the skill layer |
| `model: opus` / `effort: high` | Per-skill model and reasoning-effort override | Lets a L1 board-report skill auto-promote to Opus while L3 triage stays on Sonnet |
| `paths: ["src/auth/**"]` | Only auto-activates when working with matching files | The right primitive for domain-scoped skills (e.g. an appsec skill that should only fire on PRs touching `auth/`) |
| `hooks` | Skill-scoped lifecycle hooks | Lets USAP enforce contract validation at skill exit without modifying global settings |
| `argument-hint` + `arguments` + `$ARGUMENTS[N]` | Named, positional argument substitution | Cleans up the CLI parsing inside USAP's `<slug>_tool.py` scripts |
| `` !`<command>` `` dynamic context | Runs shell commands before Claude sees the skill content | Replaces "paste your logs here" friction with `` !`tail -100 /var/log/auth.log` `` |

The most important convention is that **descriptions stay in context, bodies load on invocation and remain for the session** ([Skill content lifecycle](https://code.claude.com/docs/en/skills#skill-content-lifecycle)). Claude Code recommends `SKILL.md` under 500 lines. USAP's `references/workflow.md` pattern aligns, but USAP's 152–230-line persona blocks are at the upper bound.

### 2.3 Bundled and official Anthropic skills

Anthropic's `anthropics/skills` ships 17 first-party skills: `algorithmic-art`, `brand-guidelines`, `canvas-design`, `claude-api`, `doc-coauthoring`, `docx`, `frontend-design`, `internal-comms`, `mcp-builder`, `pdf`, `pptx`, `skill-creator`, `slack-gif-creator`, `theme-factory`, `web-artifacts-builder`, `webapp-testing`, `xlsx` ([github.com/anthropics/skills](https://github.com/anthropics/skills)). Document skills are source-available rather than Apache 2.0 — skills carrying executable parsers can ship under a different license than pure-prompt skills. No first-party Anthropic skill is security-focused; the closest is `webapp-testing`.

Anthropic ships security tooling separately:

- **`anthropics/claude-code-security-review`** — A GitHub Action that uses Claude to review PRs for SQL/command/LDAP/XPath/NoSQL/XXE injection, IDOR, hardcoded secrets, weak crypto, deserialization RCE, and DOM/reflected/stored XSS. Default findings exclude DoS, rate limiting, memory/CPU exhaustion, and open-redirect — a curated FP filter. Supports `false-positive-filtering-instructions` and `custom-security-scan-instructions` paths ([github.com/anthropics/claude-code-security-review](https://github.com/anthropics/claude-code-security-review)).
- **`anthropics/defending-code-reference-harness`** — Six interactive skills (`/quickstart`, `/threat-model`, `/vuln-scan`, `/triage`, `/patch`, `/customize`) plus a seven-stage autonomous pipeline (recon → find → verify → report → patch) under gVisor with egress restricted to the Claude API. `/customize` walks three questions — what signals a finding, what proves it, how do we build and run — to port the pipeline to a new language/vuln class. The cleanest first-party Anthropic blueprint for an AppSec agent ([github.com/anthropics/defending-code-reference-harness](https://github.com/anthropics/defending-code-reference-harness)).

### 2.4 Bundled `/code-review` and `/security-review`, plus subagent composition

Claude Code bundles `/code-review`, `/security-review`, `/debug`, `/loop`, `/batch`, `/run`, `/verify`. They are prompt-based, not fixed logic. A project-scoped `.claude/skills/code-review/` overrides the bundle. The override hierarchy (enterprise > personal > project > plugin > bundled) means USAP can ship more opinionated `/code-review` and `/security-review` than Anthropic's, and users get the override for free.

Skills compose with subagents in two directions: `context: fork` in a `SKILL.md` makes the skill body the prompt for a forked subagent inheriting an agent-type system prompt (Explore, Plan) but not parent context. Subagents with a `skills` field preload full skill content at startup. USAP's existing `cs-*` v2 contract maps onto the second direction; the first (`context: fork`) is currently unused in USAP and would let individual skills delegate noisy investigation steps without needing a whole orchestrator.

---

## 3. Reference 2: Hermes Agent Deep Dive

### 3.1 What Hermes Agent is

Hermes Agent is NousResearch's open-source autonomous AI agent framework — not a Casky product, but the substrate Casky pairs with the 754 Claude Cybersecurity Skills to ship "always-on coverage" without a SOC ([casky.ai/blog](https://casky.ai/blog/always-on-security-coverage-with-hermes-agent-and-claude-cybersecurity-skills)). Hermes runs as a background process, maintains state across runs, executes structured tasks via external APIs, and operates across 20+ messaging platforms simultaneously ([hermes-agent.nousresearch.com/docs/](https://hermes-agent.nousresearch.com/docs/)).

### 3.2 The five-pillar architecture

Hermes is "built on five pillars: memory (`user.md` + `memory.md`), skills, soul, crons, and a self-improving loop" ([mindstudio.ai](https://www.mindstudio.ai/blog/hermes-agent-5-pillar-architecture-memory-skills-soul-crons)).

- **Memory** — `user.md` carries "who you are — your name, your communication style, your preferences." `memory.md` carries "the environment — active projects, business context, key relationships, ongoing work." FTS5 full-text search powers cross-session recall with periodic LLM summarization.
- **Skills** — "A markdown file with YAML front matter" — exactly the agentskills.io shape USAP produces. Hermes "creates skills from experience, improves them during use."
- **Soul** — `soul.md` "shapes the agent's personality and tone" and evolves with user feedback. USAP's persona blocks fill this role but are baked into each `SKILL.md`.
- **Crons** — Jobs live in `~/.hermes/cron/jobs.json`; the gateway ticks every 60 seconds; due jobs run in fresh, isolated sessions. Critically, "cron sessions cannot recursively create more cron jobs, which prevents runaway automation." Casky pitches: "Configure Hermes Agent to run an OWASP scan every night at 2am, a MITRE coverage audit every Monday, and a NIST posture check on the first of every month."
- **Self-improving loop** — A closed learning loop updating persistent memory, creating/refining skills, surfacing past sessions through FTS5 with Honcho dialectic user modeling.

### 3.3 Casky's positioning

Casky positions Hermes + Claude Cybersecurity Skills as the antidote to "no SOC" environments — orgs that cannot staff a 24/7 detection operation but can afford an always-on agent running scheduled scans across web applications (OWASP Top 10), detection rule coverage (MITRE ATT&CK), environment posture (NIST CSF 2.0), and log patterns (threat intelligence correlation). This is **scheduled persistence**, not real-time SIEM — Casky is competing with the *audit cadence* organizations claim to have but don't.

### 3.4 What USAP can adopt vs. counter-position against

Adopt: a cron primitive at the agent layer — each `cs-*` ships a `cron.example.json` mapping its command menu onto a Hermes-compatible job spec (`cs-security-analyst` runs Monday morning, `cs-ciso-advisor` first of month, `cs-incident-responder` refuses cron registration). Isolated cron sessions with FTS5 read-only memory recall. `user.md` + `memory.md` + `soul.md` as siblings to `SKILL.md`, moving persona out of `SKILL.md` body.

Counter-position against: "No SOC required" as a sales claim — scheduled scans surface debt, they do not replace a 24/7 analyst workflow. Claude lock-in — Hermes is model-agnostic; Casky's hosted layer is Claude-only. USAP keeps scheduled persistence without inheriting the Claude wall.

---

## 4. Reference 3: AI Security Agent Landscape (2026)

Building on the six profiles in [`casky-ai-competitive-landscape.md`](./casky-ai-competitive-landscape.md), four new entrants and two structural shifts have crystallized in 2026.

### 4.1 New entrants beyond Simbian/7AI/Prophet/Dropzone/Andesite/Casky

- **Conifers.ai CognitiveSOC** — Gartner-recognized "company to beat in AI SOC Agents for Threat Investigation." Patent-pending **mesh agentic AI** with adaptive learning, institutional-knowledge integration, SOC 2 Type II audit trails. Mesh framing distinguishes Conifers from 7AI's swarm and Prophet's lifecycle chain ([conifers.ai](https://www.conifers.ai/blog/top-ai-soc-agents/)).
- **SentinelOne Purple AI "Athena"** — End-to-end agentic investigation cycles with Singularity Hyperautomation for no-code workflow creation. IDC-validated 338% three-year ROI, 63% faster threat identification.
- **Google Agentic SOC** — At RSAC 2026, Google ships three agents: **Triage and Investigation**, **Dark Web Intelligence Agent** (98% accuracy on intent-based analysis, not keyword matching), and **custom enterprise agents via remote MCP servers**. Backed by Gemini reasoning, GTIG integration, Mandiant's 500,000+ investigation hours. Model Armor mitigates prompt injection and tool poisoning at the MCP boundary ([cloud.google.com](https://cloud.google.com/blog/products/identity-security/rsac-26-supercharging-agentic-ai-defense-with-frontline-threat-intelligence)).
- **UnderDefense Agentic AI SOC** — Transparent pricing ($11–15/endpoint/month, no per-alert surcharges), 250+ bi-directional integrations, ChatOps user verification, "Detection Logic as Code" framing, six-year zero-ransomware claim ([underdefense.com](https://underdefense.com/blog/agentic-soc-platforms/)).
- **Radiant Security** — Adaptive AI handling novel alert types without predefined playbooks. Flat-rate ~$1,188/year is the most aggressive pricing in the cohort. Direct shot at SOAR's playbook-authoring tax.
- **Intezer ForensicAI** — LLM reasoning + deterministic forensic tools. Sub-minute triage, <2% escalation rate, deterministic audit trails. Forensic-grade rather than triage-grade positioning.

### 4.2 Structural shifts USAP should track

- **MCP as agent-to-agent substrate.** Google's agentic SOC is the most consequential MCP bet in security: customers build domain-specific agents on customer infra, plug into Google's reasoning via remote MCP. Andesite is BYO-LLM. Conifers, Radiant, and UnderDefense are all backing into MCP postures. USAP's "works in any LLM" claim needs a first-class MCP server adapter to be load-bearing.
- **Reasoning trail + audit trail is the new SLA.** Every 2026 entrant publishes a variant: "Glass Box reasoning" (Dropzone), "Evidentiary AI audit trails" (Andesite), "reasoned verdicts" (Google), "deterministic audit trails" (Intezer), "transparent reasoning chain" (Prophet). USAP's 11-field contract requires `rationale` and `evidence_references` per skill but has no agent-level decision log spanning a multi-step `cs-*` invocation.
- **Anthropic Project Glasswing as skill-standardization vector.** Glasswing's ~150 partners across 15+ countries scan codebases with Claude Mythos Preview and have surfaced 10,000+ high/critical findings ([anthropic.com](https://www.anthropic.com/news/expanding-project-glasswing)). The shared pattern — patches + pre-release vulnerability prevention + pentest + threat detection + legacy rebuild in memory-safe languages — is the **defensive composition pattern** USAP's `cs-supply-chain-defender` and `cs-appsec-engineer` already approximate. USAP can mirror the composition without joining the coalition.

---

## 5. Reference 4: Open-Source AI Security Skills Ecosystem

### 5.1 What's gaining traction on GitHub

Five distinct skill ecosystem shapes are emerging:

- **Single-vendor megacatalogs** — `mukul975/Anthropic-Cybersecurity-Skills` (754 skills, 26 domains, 5-framework mapping, 16.8k stars). Breadth-first, one repo, every domain.
- **Curated cybersec packs** — `Masriyan/Claude-Code-CyberSecurity-Skill` (15 skills, recon → red team → blue team); `pitimon/claude-cybersecurity-skill` (22 domains incl. Agentic AI Security, Post-Quantum, Web3, OT/ICS, bilingual Thai+English).
- **Multi-agent specialist packs** — `AgriciDaniel/claude-cybersecurity` (8 parallel specialists invoked via `/cybersecurity --scope --focus --compliance`, ~5,350 lines across orchestrator + 23 reference docs).
- **Vendor-engineering packs** — `Security-Phoenix-demo/security-skills-claude-code` (12-role Phoenix Pipeline, four-tier source authority ranking CISA/NVD → vendor → news → OSINT, active SessionStart/PreToolUse/PostToolUse/SessionEnd hooks, MCP servers bridging skills to plugins).
- **Awesome-list aggregators** — `VoltAgent/awesome-agent-skills` (1000+ skills incl. Trail of Bits' 21 security skills), `alirezarezvani/claude-skills` (337 skills, 30+ agents), `simota/agent-skills` (140+ named-persona agents — Sentinel SAST, Probe DAST, Breach red team).

### 5.2 What's in mukul975's repo beyond what USAP has adopted

Three patterns the prior [`anthropic-cybersec-skills-gap-analysis.md`](./anthropic-cybersec-skills-gap-analysis.md) underweighted:

- **`mitre_f3` frontmatter** — A 2026-added MITRE Fight Fraud Framework v1.1 mapping. USAP has no fraud taxonomy; cheapest way to add one.
- **`index.json` as a 30-token discovery layer** — Agents scan 754 frontmatters in one pass at ~30 tokens each, then load top 3–5 by match. USAP has no equivalent; agents must walk the filesystem.
- **Framework cross-mapping per skill** — A skill like `performing-memory-forensics-with-volatility3` carries `mitre_attack`, `nist_csf`, `atlas_techniques`, `d3fend_techniques`, `nist_ai_rmf` simultaneously. USAP's frontmatter spec does not allow this.

### 5.3 Three patterns USAP isn't using yet

- **Authorization-gated CLI on offensive skills.** mukul975 and `briiirussell/cybersecurity-skills` enforce per-skill authorization checks; `briiirussell`'s `red-team-engagement` "refuses to plan anything against systems the user cannot demonstrate authorization for." USAP's `bb_scope_enforcer.py` covers scope but no per-skill red-team tool gates execution at the CLI.
- **Named-agent taglines.** `simota/agent-skills` gives each agent a memorable line (Sentinel: *"Security is not a feature. It's a responsibility."* Breach: *"Think like an attacker. Defend like an engineer."*). USAP has Alex for `cs-security-analyst` but the brand layer is inconsistent across the other 11 agents — a 30-minute fix that buys CISO-brief recall.
- **Three-tier boundary block.** `simota/agent-skills` enforces "Always do / Ask first / Never do" markers in every `SKILL.md`. USAP's failure-mode and success-criteria coverage is spread across the v2 contract; a single per-skill block would be more legible.

---

## 6. Pattern Catalog

Twenty patterns extracted from the four references, each with source, USAP gap, and one-line adoption suggestion. The Effort column targets a single PR's worth of work: S = under a day, M = one sprint, L = multi-sprint.

| # | Pattern | Source | USAP gap | Suggested adoption |
|---|---|---|---|---|
| 1 | Invocation-control frontmatter (`disable-model-invocation`, `user-invocable`) | Claude Code skills | USAP has no machine-readable user-vs-model invocation gate | Add both fields to `standards/frontmatter-spec.md`; require `disable-model-invocation: true` on every L4 mutating skill |
| 2 | `allowed-tools` and `disallowed-tools` frontmatter | Claude Code skills | USAP encodes tool gates in prose, not frontmatter | Extend frontmatter spec; CI rule that L3 skills cannot have empty `allowed-tools` |
| 3 | Per-skill model/effort override (`model: opus`, `effort: high`) | Claude Code skills | USAP runs every skill at session default | L1 board skills auto-promote to Opus, L3 stays on Sonnet, L4 forces high effort |
| 4 | `paths` glob auto-activation | Claude Code skills | USAP skills are always-available across the repo | Domain-scoped skills declare `paths` so they only auto-load on relevant file edits |
| 5 | `context: fork` subagent execution | Claude Code skills | USAP delegates only at the `cs-*` agent layer | Noisy investigation skills (log triage, packet capture) declare `context: fork` directly |
| 6 | Dynamic context injection (`` !`<command>` ``) | Claude Code skills | USAP `SKILL.md` files describe what to paste rather than fetching live | `cs-security-analyst` skills inject `!`tail -n 200 /var/log/auth.log`` directly |
| 7 | Hierarchical skill override (enterprise > personal > project > plugin > bundled) | Claude Code skills | USAP only ships at one level | Document and test that `.claude/skills/code-review/` overrides USAP's bundled version |
| 8 | Six-skill interactive AppSec chain (`/threat-model` → `/vuln-scan` → `/triage` → `/patch` → `/customize`) | `anthropics/defending-code-reference-harness` | USAP's `appsec-devsecops/` has no chained workflow | Adopt the chain verbatim under `appsec-devsecops/`, route through `cs-appsec-engineer` |
| 9 | gVisor-sandboxed autonomous mode for offensive verification | `anthropics/defending-code-reference-harness` | USAP red-team skills run unsandboxed | Add a `harness/` directory with gVisor wrappers for red-team and pentest skills |
| 10 | Curated FP filter (excludes DoS/rate-limit/open-redirect by default) | `anthropics/claude-code-security-review` | USAP's AppSec skills have no opinion on what counts as a real finding | Add a `false_positives_excluded` array to AppSec skill frontmatter |
| 11 | Cron pillar with isolated sessions, no recursive job creation | Hermes Agent | USAP has no scheduled-persistence story | Ship `cs-*/cron.example.json` per agent; document Hermes-compatible job spec |
| 12 | FTS5 cross-session memory recall | Hermes Agent | USAP scheduled runs would be amnesic | Adopt a `memory/` SQLite store per agent; expose to scheduled runs read-only |
| 13 | `user.md` + `memory.md` + `soul.md` separation | Hermes Agent | USAP bakes persona into `SKILL.md` | Move persona blocks to per-agent `soul.md`; reduces `SKILL.md` line count |
| 14 | Mesh agentic architecture | Conifers CognitiveSOC | USAP has linear orchestrators only | Document a mesh topology in `agents/CLAUDE.md` for multi-agent investigation |
| 15 | Remote MCP server adapter | Google Agentic SOC | USAP cannot plug into Google/Andesite/Anthropic agentic platforms directly | Ship `adapters/mcp/` with a Python MCP server that exposes USAP skills as MCP tools |
| 16 | Decision-log audit trail per agent invocation | Andesite "Evidentiary AI" / Dropzone "Glass Box" / Prophet "transparent reasoning" | USAP has per-skill `rationale` but no agent-level chain | Add `agents/<slug>.invocation.jsonl` write contract to v2 agent spec |
| 17 | `frameworks` block carrying 4–5 arrays per skill | `mukul975/Anthropic-Cybersecurity-Skills` | USAP frontmatter has no framework arrays | Add `metadata.frameworks.{mitre_attack, nist_csf, mitre_atlas, owasp_top10, mitre_f3}` |
| 18 | `index.json` skill registry + ATT&CK Navigator layer generator | `mukul975/Anthropic-Cybersecurity-Skills` | USAP has no machine-readable catalog | Generate from frontmatter on every PR via `.github/workflows/build-index.yml` |
| 19 | 8-parallel-specialist invocation (`/cybersecurity --scope --focus --compliance`) | `AgriciDaniel/claude-cybersecurity` | `cs-security-analyst` triggers one workflow at a time | Add `--parallel` flag that spawns N specialist `cs-*` agents in parallel |
| 20 | Named-agent personas with taglines | `simota/agent-skills` | USAP brand layer is inconsistent | Adopt taglines for all 12 `cs-*` agents in their frontmatter |
| 21 | Three-tier boundary blocks (Always do / Ask first / Never do) | `simota/agent-skills` | USAP failure modes spread across persona + contract | Add a single boundary block to every `SKILL.md` body |
| 22 | Authorization-gated CLI on offensive tools (`--authorized` exit 0/1/2) | `mukul975` and `briiirussell` | `shared/scripts/bb_scope_enforcer.py` covers scope but no per-skill gate | Require `--authorized` on every red-team and pentest `<slug>_tool.py` |
| 23 | Tiered workflows by time budget (Quick / Full / Continuous) | `mukul975/Anthropic-Cybersecurity-Skills` | USAP `references/workflow.md` is single-mode linear | Refactor top 3 L3 skills into 3 tiers each |
| 24 | Four-tier source authority ranking (gov → vendor → news → OSINT) | `Security-Phoenix-demo` | USAP threat-intel skill ranks sources implicitly | Add an authority-rank field to evidence_references |
| 25 | Project Glasswing defensive composition (patches + pre-release + pentest + threat detection + legacy rebuild) | Anthropic Project Glasswing | USAP `cs-supply-chain-defender` approximates this but isn't named-and-shaped | Document the composition explicitly in `cs-supply-chain-defender` workflows |

---

## 7. Prioritized Enhancement Roadmap

Each row maps a pattern from section 6 onto a concrete change. Effort: S = under one sprint, M = one sprint, L = multi-sprint. Priority: HIGH = ship in next two sprints, MED = ship in next quarter, LOW = ship when capacity permits.

| Priority | Effort | Enhancement | Why | Concrete first step | Reference source |
|---|---|---|---|---|---|
| HIGH | S | Adopt `disable-model-invocation` and `user-invocable` in `standards/frontmatter-spec.md` and templates | The cleanest one-line expression of USAP's L1–L4 autonomy model; unlocks Claude Code-native L4 mutating-skill safety | Edit `/Users/jaskarn.singh/Documents/PREPO/usap-skills/standards/frontmatter-spec.md`; mark every L4 mutating skill | Claude Code skills |
| HIGH | S | Add `allowed-tools` + `disallowed-tools` to frontmatter; require on L3+ skills | Pre-approve tools at skill scope; removes prose-only tool gates | Update `templates/skill-template.md`; add validator rule | Claude Code skills |
| HIGH | M | Ship `metadata.frameworks.{mitre_attack, nist_csf, mitre_atlas, owasp_top10, mitre_f3}` block | Closes the 75 pp ATT&CK coverage gap vs. mukul975; enables Navigator export | Extend spec, backfill 4 detection skills, commit pilot mapping | mukul975 |
| HIGH | M | Generate `index.json` + `mappings/mitre-attack/attack-navigator-layer.json` from frontmatter | No machine catalog today; everyone else has one | Add `tools/build_index.py` + `.github/workflows/build-index.yml` | mukul975 |
| HIGH | M | Replicate `defending-code-reference-harness` six-skill chain inside `appsec-devsecops/` | Anthropic's only first-party defensive blueprint; clean fit with USAP's `cs-appsec-engineer` | Scaffold `appsec-devsecops/{threat-model,vuln-scan,triage,patch,customize}/` from the template | Anthropic |
| HIGH | M | Add Hermes-compatible `cron.example.json` per `cs-*` agent + docs | Casky has proven scheduled persistence is a real product wedge | Author `cron.example.json` for `cs-security-analyst` and `cs-ciso-advisor` first | Hermes Agent / Casky |
| HIGH | L | Ship `adapters/mcp/` with a Python MCP server that exposes USAP skills as MCP tools | Google, Andesite, and Anthropic all rely on MCP; "works in any LLM" is hollow without it | Stand up an MCP server that lists USAP skills as tools and forwards invocation to `<slug>_tool.py` | Google Agentic SOC |
| HIGH | M | Per-`cs-*` invocation decision log under `agents/<slug>.invocation.jsonl` | Every commercial AI SOC publishes a reasoning trail SLA | Extend v2 agent contract; require append per workflow step | Andesite / Dropzone / Prophet |
| HIGH | S | Authorization-gated CLI on every red-team / pentest `<slug>_tool.py` (`--authorized` exit codes 0/1/2) | mukul975 and briiirussell prove this is table stakes for credible offensive skills | Add `bb_scope_enforcer.py` invocation as a decorator in `red-team/` and `pentest/` tool scripts | mukul975 / briiirussell |
| MED | S | `context: fork` declarations on noisy L3 investigation skills | Reduces parent thread bloat; aligns with Claude Code subagent execution | Pick `detection/threat-hunting` and `response/forensics`; add to frontmatter | Claude Code skills |
| MED | S | Per-skill `model` and `effort` overrides | L1 board skills want Opus; L3 triage wants Sonnet; L4 should force high effort | Update spec; pilot on `cs-ciso-advisor` (Opus) and `cs-security-analyst` (Sonnet) | Claude Code skills |
| MED | S | `paths` glob on domain-scoped skills | Stops appsec skills from auto-loading when the user is editing infra config | Add to all `appsec-devsecops/` skills with `paths: ["**/auth/**", "**/api/**"]` | Claude Code skills |
| MED | M | Tiered workflows (Quick / Full / Continuous) in `references/workflow.md` for top 5 L3 skills | mukul975's pattern is operationally proven; USAP single-mode workflows under-serve real time pressure | Refactor `detection/threat-hunting`, `red-team/red-team-operations`, `response/incident-commander` first | mukul975 |
| MED | M | Three-tier boundary block (Always do / Ask first / Never do) in every `SKILL.md` body | Consolidates failure-mode and success-criteria into a single legible block | Update template; pilot on 3 skills per domain | `simota/agent-skills` |
| MED | S | Named taglines on all 12 `cs-*` agents | Brand recall; CISO buyers do not remember `cs-supply-chain-defender` but they do remember Alex | Edit each `cs-*.md`; add a one-line tagline under the `name` field | `simota/agent-skills` |
| MED | M | `--parallel` flag on `cs-security-analyst` that fans out to specialist agents | AgriciDaniel's pattern; one entry point routes to 8 parallel specialists | Extend command menu; spawn N agents via the v2 agent contract | `AgriciDaniel/claude-cybersecurity` |
| MED | M | Dynamic context injection (`` !`<command>` ``) in evidence-collection skills | Replaces "paste your logs here" friction in `response/` and `detection/` skills | Pilot in `response/incident-classification` | Claude Code skills |
| MED | S | Curated FP filter array per AppSec skill | Anthropic's `claude-code-security-review` ships an opinion on what's noise | Add `false_positives_excluded` to AppSec skill frontmatter | Anthropic |
| MED | M | Per-agent `soul.md` next to `cs-*.md` for persona text | Reduces SKILL.md/CS-agent file line count; aligns with Hermes file model | Pilot on `cs-security-analyst` (Alex) | Hermes Agent |
| MED | M | Document a mesh agentic topology for cross-domain investigation | Conifers' wedge; relevant when an incident spans cloud + endpoint + identity | Add `agents/topologies/mesh.md`; reference from `cs-incident-responder` | Conifers CognitiveSOC |
| LOW | M | Memory store (SQLite + FTS5) per project, exposed read-only to scheduled runs | Required to make cron-scheduled USAP runs non-amnesic | Author `shared/scripts/memory_store.py`; gate behind opt-in flag | Hermes Agent |
| LOW | S | Four-tier source authority ranking (gov → vendor → news → OSINT) field in evidence_references | Phoenix pattern; clarifies what's a primary vs. tertiary citation | Extend output contract optional fields | Phoenix Security |
| LOW | M | Glasswing-shaped defensive composition explicitly documented in `cs-supply-chain-defender` | Mirrors what 150+ Glasswing partners are doing without joining the coalition | Author a "composition" section in the agent's workflow doc | Anthropic Project Glasswing |
| LOW | L | LOW-priority domain expansion: `mobile-security/`, `cryptography-ops/`, `web3-security/` | Real gaps but small ACS footprint and uncertain demand inside USAP's SOC-focused positioning | Defer until HIGH+MED roadmap items land | mukul975 / pitimon |

---

## 8. Quick Wins (Top 3, Shippable in 1–2 Sprints)

### 8.1 Quick Win 1 — Invocation-control + tool-gating frontmatter overlay (effort: S, unblocks roadmap)

Files to edit:

- `/Users/jaskarn.singh/Documents/PREPO/usap-skills/standards/frontmatter-spec.md` — add an "Invocation Control" subsection documenting `disable-model-invocation` (required true on every L4 mutating skill), `user-invocable`, `allowed-tools`, `disallowed-tools`. Document the rule that L3 read-only skills require non-empty `allowed-tools`.
- `/Users/jaskarn.singh/Documents/PREPO/usap-skills/templates/skill-template.md` — add the four fields under `metadata:` with commented usage notes.
- `/Users/jaskarn.singh/Documents/PREPO/usap-skills/standards/level-guide.md` — bind L1/L2/L3/L4 to specific invocation-control defaults (L1: `user-invocable: false`; L4: `disable-model-invocation: true`).

Files to create:

- `/Users/jaskarn.singh/Documents/PREPO/usap-skills/tools/validate_invocation_control.py` (stdlib only) — walks all `SKILL.md` files, asserts the L1–L4 invariants above, exits non-zero on violation. Wire it into the existing skills-validation workflow.

Acceptance: every L4 skill on disk carries `disable-model-invocation: true`; every L3 skill carries a non-empty `allowed-tools`; the validator exits 0.

### 8.2 Quick Win 2 — `frameworks` block + `index.json` + Navigator layer (effort: M)

Files to edit:

- `/Users/jaskarn.singh/Documents/PREPO/usap-skills/standards/frontmatter-spec.md` — add an optional "Framework Mappings" subsection defining `metadata.frameworks.{mitre_attack, nist_csf, mitre_atlas, owasp_top10, mitre_f3}` as `array[string]`, max 8 IDs per field per skill.
- `/Users/jaskarn.singh/Documents/PREPO/usap-skills/templates/skill-template.md` — add commented placeholder block.

Files to create:

- `/Users/jaskarn.singh/Documents/PREPO/usap-skills/shared/scripts/framework_extractor.py` — stdlib-only. Two modes: `--emit coverage` writes `mappings/mitre-attack/coverage-summary.md` and `mappings/nist-csf/csf-alignment.md`; `--emit navigator` writes `mappings/mitre-attack/attack-navigator-layer.json` (Navigator v4.5 schema). Reads `metadata.frameworks.*` first, falls back to regex over body markdown.
- `/Users/jaskarn.singh/Documents/PREPO/usap-skills/tools/build_index.py` — walks `*/*/SKILL.md`, parses frontmatter, emits `index.json` (per-skill: `name`, `description`, `domain`, `path`, `category`, `agent_slug`, `frameworks`).
- `/Users/jaskarn.singh/Documents/PREPO/usap-skills/.github/workflows/build-index.yml` — runs on push to main; commits regenerated `index.json` and `mappings/` if drift.
- `/Users/jaskarn.singh/Documents/PREPO/usap-skills/mappings/README.md` — static doc explaining the generation contract.

Pilot: backfill `metadata.frameworks` on the 4 detection skills that already cite T-IDs in body prose (`detection-engineering`, `threat-hunting`, `threat-intelligence`, `behavioral-analytics`). Verify Navigator layer loads cleanly at [mitre-attack.github.io/attack-navigator](https://mitre-attack.github.io/attack-navigator/).

Acceptance: `index.json` exists at repo root, lists all 74 skills with non-empty `frameworks` arrays on the 4 backfilled skills, and the Navigator layer renders.

### 8.3 Quick Win 3 — `appsec-devsecops/` interactive AppSec chain ported from `defending-code-reference-harness` (effort: M)

Files to create under `/Users/jaskarn.singh/Documents/PREPO/usap-skills/appsec-devsecops/`:

- `threat-model/SKILL.md` (L3, intent_type `analyze`) — builds a STRIDE+DREAD threat model from a target spec; emits to `<target>/THREAT_MODEL.md`.
- `vuln-scan/SKILL.md` (L3, intent_type `detect`) — runs static analysis scoped by the threat model; emits to `<target>/VULN-FINDINGS.json` with the 11-field contract.
- `finding-triage/SKILL.md` (L3, intent_type `analyze`) — verifies, dedupes, ranks findings; emits to `<target>/TRIAGE.md`.
- `patch-candidate/SKILL.md` (L4, intent_type `respond`, `human_approval_required: true`, `disable-model-invocation: true`) — generates candidate patches; never auto-applies.
- `appsec-customize/SKILL.md` (L3, intent_type `advise`) — walks Anthropic's three customization questions to port the pipeline to a new language/vuln class.

Files to edit:

- `/Users/jaskarn.singh/Documents/PREPO/usap-skills/agents/appsec-devsecops/cs-appsec-engineer.md` (or create from `templates/agent-template.md` if missing) — wire the five skills into a `cs-appsec-engineer` command menu (`/threat-model`, `/vuln-scan`, `/triage`, `/patch`, `/customize`) and document the chain with MANDATORY EXECUTION RULES that require `/threat-model` to run before `/vuln-scan`.
- `/Users/jaskarn.singh/Documents/PREPO/usap-skills/CLAUDE.md` — bump skill count claim; add the five new skills under `appsec-devsecops`.

Acceptance: invoking `cs-appsec-engineer` triggers the chain on a target directory; each step writes a contract-compliant payload; the `/patch` step refuses to run without explicit human approval.

---

## 9. Anti-Patterns to Avoid

### 9.1 "No SOC required" as a sales claim

Casky's blog pitches Hermes + Claude Cybersecurity Skills as a SOC replacement. This is technically and ethically wrong. Scheduled scans surface debt; they do not detect lateral movement during a live engagement, and they do not stand up an IR plan when an exec asks for one at 11pm on a Saturday. USAP should adopt Hermes-style scheduled persistence as a *capability* — never as a positioning claim. The honest pitch is "USAP runs scheduled audits and on-demand investigations from your existing LLM; if you need 24/7 human-led detection, you still need a SOC or an MDR."

### 9.2 Closed-Claude lock-in dressed up as model-agnosticism

Casky's skills repo claims platform compatibility with Claude Code, Cursor, Windsurf, Codex CLI, Gemini CLI, LangChain, CrewAI, AutoGen, Semantic Kernel, MCP. The hosted Casky SaaS layer is Claude-only. The same fork is open to USAP: write skills that claim to run anywhere, then ship one runtime that only honors Claude. USAP should keep its model-agnostic posture load-bearing by validating end-to-end on at least one non-Anthropic model per release (Sonnet 4.6 plus ChatGPT-5 or Gemini 2.5 Pro) before claiming portability in any README.

### 9.3 Prosumer brand positioning ($49/month, "career on-ramp")

Casky's $49/month wedge is real revenue but a strategic ceiling. Once you are the product juniors and career switchers buy, you are not the product CISOs buy. USAP's open-source corpus is the opposite: free, embeddable, defensible because anyone can fork and white-label. Positioning USAP as a "skills bundle for security learners" would collapse the cs-* orchestration story into a CTF prep pack and burn the ICP. The four target ICPs from the competitive analysis (in-house SOC, DevSecOps, internal red-team, MSSPs/consultancies) should be reinforced in every public-facing piece of copy.

### 9.4 Skill-count theater

mukul975 advertises 754 skills. The catalog includes deception-technology with 2 skills, blockchain-security with 1, firmware-analysis with 1. Volume without depth is noise. USAP's positioning is the opposite: fewer, deeper, agent-orchestratable skills with structured runtime guarantees. The README should lead with "12 orchestrators, 74 skills, one output contract" — not "we shipped 200 skills this quarter." The roadmap in section 7 deliberately ranks framework arrays, AppSec chains, and cron infrastructure ahead of new-domain expansion for this reason.

### 9.5 Hand-maintained framework coverage docs

mukul975 has already drifted: the top-level README claims `MITRE ATT&CK v19.1`, the mappings README says `Enterprise v15`, the Navigator JSON says `Enterprise v14`. Three different versions in three docs in the same repo. USAP should never accept a hand-maintained coverage artifact. Every mapping doc must be regenerated by `shared/scripts/framework_extractor.py`, and the CI workflow must `git diff --exit-code mappings/` to fail on drift. Treat the static `mappings/*/README.md` as the only writable surface.

---

## 10. Open Questions (Requiring User Decision)

1. **Invocation-control rollout posture.** Should `disable-model-invocation` and `user-invocable` be retrofitted across all 74 existing skills in one PR (faster shipping, larger blast radius) or domain-by-domain with a CI WARN-then-FAIL ladder (safer, multi-sprint)? The roadmap assumes the latter.
2. **Hermes cron coupling vs. cron-agnostic spec.** Should USAP ship Hermes-specific `cron.example.json` files (assumes user runs Hermes), or a more abstract `schedule.yaml` spec that Hermes and other runtimes (e.g., GitHub Actions, AWS EventBridge) can adapt? Hermes-specific is faster but couples USAP to one runtime.
3. **MCP server adapter scope.** Should `adapters/mcp/` expose every USAP skill as an MCP tool (broad surface, hard to govern) or only the `cs-*` orchestrators (smaller surface, better routing)? Google's pattern is "build your own agent on top of remote MCP," which suggests `cs-*`-only is the right granularity.
4. **AppSec chain authorship.** Should the five new `appsec-devsecops/` skills be authored fresh against the Anthropic blueprint, or should USAP ship a thin wrapper that delegates to `defending-code-reference-harness`? The first is more work but keeps USAP fully owned; the second is faster but creates a runtime dependency on an Anthropic-controlled repo.
5. **Decision-log persistence boundary.** The proposed `agents/<slug>.invocation.jsonl` log captures every step of a `cs-*` invocation. Should this write into the project repo (committed, auditable) or into a `~/.usap/logs/` sidecar (private, not committed)? Auditors will want the first; operators will want the second.
6. **`soul.md` migration vs. retention.** Moving persona blocks out of `SKILL.md` and into per-agent `soul.md` is non-breaking but invasive. Should this happen in this expansion sprint or be deferred until USAP ships a Hermes-adapter release?
7. **Glasswing partnership posture.** Anthropic's expansion of Project Glasswing has added ~150 organizations spanning power, water, healthcare, communications, and hardware. Should USAP formally request inclusion (positions USAP as a coalition member with privileged access to Mythos Preview), or stay strictly arms-length and mirror the composition pattern in `cs-supply-chain-defender` without participating? The first gives credibility; the second protects the open-source positioning from any future Anthropic-only requirement.

---

## 11. Sources

### Claude Code and Anthropic Skills

- [code.claude.com/docs/en/skills](https://code.claude.com/docs/en/skills) — Claude Code skills documentation (canonical reference for all section 2 patterns)
- [agentskills.io/specification](https://agentskills.io/specification) — Agent Skills open standard frontmatter spec
- [github.com/anthropics/skills](https://github.com/anthropics/skills) — Anthropic's official 17-skill repository
- [github.com/anthropics/claude-code-security-review](https://github.com/anthropics/claude-code-security-review) — Anthropic's first-party security-review GitHub Action
- [github.com/anthropics/defending-code-reference-harness](https://github.com/anthropics/defending-code-reference-harness) — Anthropic's six-skill AppSec chain plus gVisor-sandboxed autonomous harness

### Hermes Agent and Casky

- [hermes-agent.nousresearch.com/docs/](https://hermes-agent.nousresearch.com/docs/) — Hermes Agent official documentation
- [mindstudio.ai blog on Hermes 5-pillar architecture](https://www.mindstudio.ai/blog/hermes-agent-5-pillar-architecture-memory-skills-soul-crons) — Memory, skills, soul, crons, self-improving loop deep dive
- [github.com/NousResearch/hermes-agent](https://github.com/NousResearch/hermes-agent/releases) — Hermes releases and changelog
- [casky.ai blog on Hermes + Cybersecurity Skills](https://casky.ai/blog/always-on-security-coverage-with-hermes-agent-and-claude-cybersecurity-skills) — Casky's positioning of scheduled AI scanning
- [casky.ai blog index](https://casky.ai/blog) — Full Casky blog (ClawBots and Project Glasswing posts return 404 as of June 2026)
- [github.com/SamurAIGPT/awesome-hermes-agent](https://github.com/SamurAIGPT/awesome-hermes-agent) — Community curation of Hermes skills, plugins, and integrations
- [github.com/mudrii/hermes-agent-docs](https://github.com/mudrii/hermes-agent-docs) — Community documentation mirror

### AI Security Agent Landscape (2026 entrants)

- [anthropic.com/news/expanding-project-glasswing](https://www.anthropic.com/news/expanding-project-glasswing) — Project Glasswing coalition expansion announcement (~150 partners, 10,000+ findings)
- [conifers.ai/blog/top-ai-soc-agents/](https://www.conifers.ai/blog/top-ai-soc-agents/) — Top 10 AI SOC platforms in 2026 (Conifers, Microsoft, CrowdStrike, Torq, Splunk, Palo Alto Cortex XSIAM, IBM, Intezer, Dropzone, Vectra)
- [conifers.ai/blog on 2026 predictions](https://www.conifers.ai/blog/5-cybersecurity-predictions-for-2026-agentic-ai-security-agi-and-the-new-soc-model) — Conifers' agentic-AI predictions
- [underdefense.com/blog/agentic-soc-platforms/](https://underdefense.com/blog/agentic-soc-platforms/) — 8-platform comparison including UnderDefense, Radiant Security, Intezer ForensicAI
- [cloud.google.com on agentic SOC at RSAC 2026](https://cloud.google.com/blog/products/identity-security/rsac-26-supercharging-agentic-ai-defense-with-frontline-threat-intelligence) — Google's Triage + Dark Web Intelligence + custom MCP agents
- [newsroom.cisco.com on Cisco agentic security](https://newsroom.cisco.com/c/r/newsroom/en/us/a/y2026/m03/cisco-reimagines-security-for-the-agentic-workforce.html) — Cisco's RSAC 2026 agentic-workforce launch
- [theregister.com on AI agents as 2026 insider threat](https://www.theregister.com/2026/01/04/ai_agents_insider_threats_panw/) — Palo Alto security-intel positioning
- [bvp.com/atlas on securing AI agents](https://bvp.com/atlas/securing-ai-agents-the-defining-cybersecurity-challenge-of-2026) — Bessemer Atlas 2026 outlook

### Open-source AI security skills ecosystem

- [github.com/mukul975/Anthropic-Cybersecurity-Skills](https://github.com/mukul975/Anthropic-Cybersecurity-Skills) — 754 skills, 26 domains, 5-framework mapping, 16.8k stars
- [github.com/Masriyan/Claude-Code-CyberSecurity-Skill](https://github.com/Masriyan/Claude-Code-CyberSecurity-Skill) — 15-skill curated pack with offensive/defensive/IR coverage
- [github.com/pitimon/claude-cybersecurity-skill](https://github.com/pitimon/claude-cybersecurity-skill) — 22-domain Claude Code plugin, bilingual Thai+English, 73-framework coverage
- [github.com/AgriciDaniel/claude-cybersecurity](https://github.com/AgriciDaniel/claude-cybersecurity) — 8-parallel-specialist agent architecture with OWASP 2025 + CWE Top 25 + MITRE ATT&CK
- [github.com/briiirussell/cybersecurity-skills](https://github.com/briiirussell/cybersecurity-skills) — 29 skills across red/blue/purple team with authorization gating
- [github.com/Security-Phoenix-demo/security-skills-claude-code](https://github.com/Security-Phoenix-demo/security-skills-claude-code) — Phoenix Pipeline (12 roles), CTI domain research, OpenGrep rule generator
- [github.com/Cornjebus/security-analyzer](https://github.com/Cornjebus/security-analyzer) — Comprehensive security analyzer with CVE/exploit fetching and phased remediation
- [github.com/VoltAgent/awesome-agent-skills](https://github.com/VoltAgent/awesome-agent-skills) — 1000+ curated agent skills (includes Trail of Bits' 21 security skills)
- [github.com/alirezarezvani/claude-skills](https://github.com/alirezarezvani/claude-skills) — 337 skills, 30+ agents, 70+ custom commands across 8+ coding agents
- [github.com/simota/agent-skills](https://github.com/simota/agent-skills) — 140+ named-agent personas (Sentinel SAST, Probe DAST, Breach red team) with taglines and three-tier boundaries
- [github.com/mouadja02/skills](https://github.com/mouadja02/skills) — 723 agent skills across 31 categories
- [github.com/topics/claude-code-skills](https://github.com/topics/claude-code-skills) — GitHub topic discovery for community skill packs
- [github.com/topics/claude-skills](https://github.com/topics/claude-skills) — Broader Claude skills topic with current community work

### USAP and prior research

- [github.com/jaskaranhundal/usap-skills](https://github.com/jaskaranhundal/usap-skills) — This repository
- [jaskaranhundal.github.io/usap-skills/](https://jaskaranhundal.github.io/usap-skills/) — USAP documentation site
- [/Users/jaskarn.singh/Documents/PREPO/usap-skills/docs/research/casky-ai-competitive-landscape.md](./casky-ai-competitive-landscape.md) — Prior competitive analysis (Casky + 5 enterprise vendors)
- [/Users/jaskarn.singh/Documents/PREPO/usap-skills/docs/research/anthropic-cybersec-skills-gap-analysis.md](./anthropic-cybersec-skills-gap-analysis.md) — Prior USAP vs. mukul975 gap analysis

End of document.
