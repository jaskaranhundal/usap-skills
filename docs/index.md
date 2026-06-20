---
title: USAP — Open-Source AI Cybersecurity Agent Skills
description: 74 open-source AI security skills + 12 cs-* orchestrator agents for SOC, incident response, threat hunting, red team, blue team, and DevSecOps. Mapped to MITRE ATT&CK and NIST CSF 2.0. Runs in Claude, ChatGPT, Gemini, Ollama, AnythingLLM.
---

# USAP — Open-Source AI Cybersecurity Agent Skills

**The open-source alternative to paid AI security platforms.** 74 skills, 12 `cs-*` orchestrator agents, 12 cybersecurity domains. Apache 2.0. Runs in every major LLM (Claude, ChatGPT, Gemini, Ollama, AnythingLLM). No SaaS, no vendor lock-in.

[:fontawesome-brands-github: GitHub](https://github.com/jaskaranhundal/usap-skills){ .md-button .md-button--primary }
[Compare USAP vs Casky.AI](comparisons/vs-casky-ai.md){ .md-button }

## What this is

USAP is a curated, machine-validated library of cybersecurity skills designed for AI agents. Each skill is a complete LLM system prompt (`SKILL.md`) plus a stdlib-only Python tool that emits a standardized 11-field JSON output contract. Twelve `cs-*` orchestrator agents compose those skills into reproducible workflows for SOC operators, incident commanders, red teamers, blue teamers, AppSec engineers, and CISOs.

## What makes it different

| Capability | USAP | Most AI security SaaS |
|---|---|---|
| License | Apache 2.0 | Proprietary |
| LLM runtime | Any (Claude, ChatGPT, Gemini, Ollama, AnythingLLM) | Vendor-locked |
| Output contract | Typed 11-field JSON, published | Free-form, undocumented |
| Skill source-of-truth | YAML frontmatter + body markdown | Hidden inside the platform |
| Framework mappings | Machine-readable (`metadata.frameworks.*`) | Marketing-only |
| Mutating-action gating | Explicit `human_approval_required: true` | Implicit / per-vendor |
| Self-host | Yes (clone and run) | Vendor cloud only |

Full positioning analysis: [USAP vs Casky.AI](comparisons/vs-casky-ai.md).

## Who is this for

- **SOC and detection engineering teams** running Splunk / Sentinel + EDR who want MITRE-mapped skills to amplify analyst output.
- **DevSecOps and platform-security engineers** at engineering-led orgs already on Claude Code or similar — embed `cs-devsecops-engineer` and `cs-appsec-engineer` in CI.
- **MSSPs, security consultancies, and red teamers** producing CVSS- and MITRE-tagged deliverables for clients.

## Twelve domains

[`appsec-devsecops`](https://github.com/jaskaranhundal/usap-skills/tree/main/appsec-devsecops) · [`cloud-infra`](https://github.com/jaskaranhundal/usap-skills/tree/main/cloud-infra) · [`detection`](https://github.com/jaskaranhundal/usap-skills/tree/main/detection) · [`governance`](https://github.com/jaskaranhundal/usap-skills/tree/main/governance) · [`identity-access`](https://github.com/jaskaranhundal/usap-skills/tree/main/identity-access) · [`pentest`](https://github.com/jaskaranhundal/usap-skills/tree/main/pentest) · [`platform-ai`](https://github.com/jaskaranhundal/usap-skills/tree/main/platform-ai) · [`red-team`](https://github.com/jaskaranhundal/usap-skills/tree/main/red-team) · [`response`](https://github.com/jaskaranhundal/usap-skills/tree/main/response) · [`risk-compliance`](https://github.com/jaskaranhundal/usap-skills/tree/main/risk-compliance) · [`system-security`](https://github.com/jaskaranhundal/usap-skills/tree/main/system-security) · [`webapp-security`](domains/webapp-security.md)

## Twelve cs-* orchestrator agents

| Agent | Role |
|---|---|
| `cs-security-analyst` | Universal SOC entry point — Alex |
| `cs-incident-responder` | Active incident command |
| `cs-blue-team-analyst` | Detection / DFIR orchestrator |
| `cs-red-teamer` | Offensive security coordinator |
| `cs-cloud-investigator` | Cloud incident investigation |
| `cs-supply-chain-defender` | Software supply chain defense |
| `cs-threat-intel-lead` | Intelligence-driven SOC |
| `cs-purple-team-lead` | Detection validation / gap analysis |
| `cs-appsec-engineer` | Runtime + build-time AppSec |
| `cs-devsecops-engineer` | Security-in-pipeline engineering |
| `cs-ciso-advisor` | Executive board advisor |
| `cs-security-program-manager` | Passive lifecycle orchestrator |

## Quick links

- [Compare USAP vs Casky.AI](comparisons/vs-casky-ai.md)
- [GitHub repository](https://github.com/jaskaranhundal/usap-skills)
- [README](https://github.com/jaskaranhundal/usap-skills/blob/main/README.md)
- [Output contract spec](https://github.com/jaskaranhundal/usap-skills/blob/main/standards/output-contract.md)
- [Frontmatter spec](https://github.com/jaskaranhundal/usap-skills/blob/main/standards/frontmatter-spec.md)
- [Agent v2 contract](https://github.com/jaskaranhundal/usap-skills/blob/main/standards/agent-contract.md)
- [Casky.AI competitive landscape research](https://github.com/jaskaranhundal/usap-skills/blob/main/docs/research/casky-ai-competitive-landscape.md)

## Get started

```bash
git clone https://github.com/jaskaranhundal/usap-skills
cd usap-skills

# Run any skill tool — stdlib only, no pip install required
python3 webapp-security/webapp-risk-triage/scripts/webapp-risk-triage_tool.py --output json

# Validate every skill
python3 tools/validate_skill.py --all --summary

# Regenerate framework coverage mappings
python3 tools/framework_extractor.py --emit all
```

See the [README](https://github.com/jaskaranhundal/usap-skills/blob/main/README.md) for paste-and-go LLM kits, Gemini CLI integration, and the full skill catalog.
