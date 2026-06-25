# USAP Slash Commands

Claude Code slash commands for the Unified Security Agent Platform (USAP). These commands let you load any USAP skill as a live LLM persona and run structured compliance tests — all inside a Claude Code session.

---

## Commands

| Command | Usage | Purpose |
|---|---|---|
| `/usap:run` | `/usap:run <skill-slug>` | Load any SKILL.md and activate it as your operating persona |
| `/usap:test` | `/usap:test <skill-slug>` | Run the FortiGate zero-day scenario + 6-problem compliance scorecard |
| `/usap:compare` | `/usap:compare` | Before/after v1 vs v2 comparison for `zero-day-response` |
| `/usap:challenge` | `/usap:challenge` | Run `cs-security-analyst` against the Perfect Storm 8-vector crisis + 12-check mock scorecard |
| `/usap:fortigate` | `/usap:fortigate` | Run `cs-security-analyst` (AT + CA workflows) against the Fintech FortiGate zero-day + 7-task scorecard |
| `/usap:orchestrate` | `/usap:orchestrate` | Run full 4-agent chain (analyst → responder → CISO → program-manager) against Perfect Storm |

---

## Quick Start

```
# Activate a skill and ask it a question
/usap:run zero-day-response
> We have a FortiOS CVSS 9.8 zero-day with no patch. What do we do?

# Run the compliance test (FortiGate scenario, 6 checks)
/usap:test zero-day-response

# See the before/after fix comparison
/usap:compare

# Run cs-security-analyst against the world's hardest scenario (12-check mock comparison)
/usap:challenge

# Run cs-security-analyst (AT + CA) against the Fintech FortiGate zero-day (7-task scorecard)
/usap:fortigate

# Run the full 4-agent orchestration chain against the Perfect Storm
/usap:orchestrate
```

---

## How It Works

Each `.md` file in this directory is a Claude Code slash command. When invoked, Claude reads the command body and follows the instructions — including using the `Read` and `Glob` tools to load the target SKILL.md.

The skill's `## Persona` and `## Reasoning Procedure` sections become Claude's active operating context. All output follows the USAP output contract (JSON + executive summary).

---

## Available Skill Slugs

Skills are organized by domain. Use the slug (directory name) with `/usap:run`:

**Detection:** `threat-hunting`, `secrets-exposure`, `behavioral-analytics`, `telemetry-signal-quality`, `network-exposure`, `attack-surface-management`, `deception-honeypot`, `detection-engineering`, `threat-intelligence`

**Response:** `zero-day-response`, `containment-advisor`, `incident-classification`, `forensics`, `zero-day-response-governance`

**Governance:** `security-architecture`, `security-policy-control`, `security-awareness`, `findings-tracker`, `vulnerability-management`, `metrics-reporting`, `security-posture-score`, `ciso-brief-generator`, `knowledge-management`, `security-roadmap-planner`, `security-debt-tracker`

**AppSec/DevSecOps:** `appsec-code-review`, `sast-dast-coordinator`, `supply-chain-risk`, `supply-chain-simulation`, `build-integrity`, `devsecops-pipeline`, `secure-sdlc`, `security-requirements-review`

**Cloud/Infra:** `cloud-security-posture`, `iac-security`, `cloud-workload-protection`, `endpoint-os-security`, `ot-iot-device-security`

**Identity/Access:** `identity-access-risk`, `data-security-classification`, `cryptography-key-management`, `insider-physical-risk`

**Platform/AI:** `orchestrator`, `tool-execution-broker`, `guardrail`, `ai-agent-security`, `ai-ethics-governance`, `agent-integrity-monitor`, `third-party-vendor-risk`

**Red Team:** `red-team-planner`, `red-team-operations`, `safe-exploitation`, `attack-path-analysis`, `ai-red-teaming`, `security-research`

**Risk/Compliance:** `enterprise-risk-assessment`, `risk-threat-modeling`, `compliance-mapping`, `privacy-dpia`, `quantum-security-readiness`, `regulatory-horizon`, `cyber-insurance`, `internal-audit-assurance`

---

## Test Fixtures

| File | Purpose |
|---|---|
| `tests/scenarios/fortigate-zero-day.json` | FortiGate zero-day test input (used by `/usap:test`) |
| `tests/scenarios/fintech-fortigate-zero-day.json` | Enriched fintech FortiGate scenario — 5 tasks, 5 UNKNOWN fields (used by `/usap:fortigate`) |
| `tests/scenarios/nation-state-apt-crisis.json` | Perfect Storm 8-vector compound crisis (used by `/usap:challenge`, `/usap:orchestrate`) |
| `tests/fixtures/zero-day-response-v1.md` | Pre-fix SKILL.md baseline (git HEAD before fix commit) |
| `tests/expected/zero-day-response-v2-scorecard.md` | Reference: 6/6 passing scorecard for `zero-day-response` v2 |
| `tests/expected/apt-crisis-scorecard.md` | Reference: 12/12 passing scorecard for `cs-security-analyst` vs Perfect Storm |
| `tests/mocks/cs-security-analyst-apt-mock.json` | Gold-standard expected analyst output (used by `/usap:challenge`) |
| `tests/mocks/orchestration-chain-mock.json` | Expected 4-agent handoff chain output (used by `/usap:orchestrate`) |
