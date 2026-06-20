---
title: USAP vs Casky.AI — open-source alternative to the AI security investigation platform
description: How USAP compares to Casky.AI. USAP is the open-source Apache 2.0 alternative with orchestrator agents and a typed output contract; Casky is a $49/month Claude-only SaaS. Side-by-side feature comparison.
---

# USAP vs Casky.AI

**TL;DR.** Casky.AI is a Claude-native, paid AI security investigation platform ($49/month + a waitlisted free tier, with a closed enterprise SKU). USAP is the open-source Apache 2.0 alternative — same shape of skills library, plus `cs-*` orchestrator agents and a typed runtime output contract that the Casky platform does not publish. USAP runs in any LLM (Claude, ChatGPT, Gemini, Ollama, AnythingLLM) and is free to self-host.

If you already own LLM access and don't want to rent another SaaS, USAP is the cleaner fit.

## At a glance

| Dimension | USAP | Casky.AI |
|---|---|---|
| License | Apache 2.0 | Closed SaaS |
| Pricing | Free, self-host | $49/mo paid; free Playground tier with waitlist; enterprise gated |
| LLM runtime | Any (Claude, ChatGPT, Gemini, Ollama, AnythingLLM) | Claude only (Sonnet 4.6) |
| Skill source-of-truth | YAML frontmatter + body markdown in `<domain>/<slug>/SKILL.md` | Open repo (`mukul975/Anthropic-Cybersecurity-Skills`); platform is closed |
| Skill count | 74 | 754 (Casky-adjacent open repo); platform inherits |
| Domain count | 12 | 12 (cloud / web-API / malware / IR / network / IAM / red team / DevSecOps / threat intel / SOC ops / container / OSINT) |
| Orchestrator agents | **12 `cs-*` agents** with v2 contract (Persona / Critical Actions / Command Menu / 3+ workflows w/ MANDATORY/FAILURE/SUCCESS blocks) | None published |
| Output contract | **Typed 11-field JSON** with required `human_approval_required` mutating-action gate (`standards/output-contract.md`) | Free-form deliverables (CVSS + MITRE tags + remediation in prose) |
| Framework mappings | Machine-readable `metadata.frameworks.{mitre_attack, nist_csf, mitre_atlas, owasp_top10, d3fend, nist_ai_rmf}`, auto-generates ATT&CK Navigator + CSF coverage docs | Marketing claim only (ATT&CK v19.1, NIST CSF 2.0, ATLAS, D3FEND, NIST AI RMF, OWASP 2025); no per-skill metadata or auto-generated coverage docs |
| Autonomy / approval model | L1–L4 levels documented (`standards/level-guide.md`); mutating intents must set `human_approval_required: true` | Not published |
| Distribution | GitHub repo, Claude Code plugin, AnythingLLM package, paste-and-go LLM bundles | Casky.ai web playground; gated enterprise SKU |
| Connectors (SIEM / EDR / cloud) | Runs alongside whatever your LLM can read; no bundled connectors | Casky platform's "Actual mode" advertised but unspecified |

## Where Casky wins

- **Investigation deliverables**. Casky's hero promise is artifact-to-finding in three minutes — paste real logs, get a CVSS-scored, MITRE-mapped, client-ready report. The interactive Skills Lab UI and "reasoning transparency" (live Claude extended-thinking stream) are nice-to-have features USAP does not replicate.
- **Career on-ramp**. Casky's career-path framing (Cloud Security Engineer, Network Security Engineer, Web & App Security Engineer, SOC Analyst, future Penetration Tester) explicitly courts juniors and career switchers. USAP is built for practitioners and engineering-led orgs, not training.
- **Brand**. Casky has a memorable name, a polished site, and a clear competitive wedge against training/CTF incumbents (HackTheBox, TryHackMe, SANS).

## Where USAP wins

- **Open source, no SaaS**. Clone the repo, paste a SKILL.md into your LLM, run. No waitlist. No `$49/mo` wall. No SSO upcharge. Apache 2.0 — MSSPs and consultancies can embed and white-label.
- **Model-agnostic**. Every `SKILL.md` is a complete LLM system prompt that runs in Claude, ChatGPT, Gemini, Ollama, AnythingLLM. Casky's SaaS is Claude-only, even though Casky's underlying skills repo is model-agnostic.
- **Orchestrator agents**. The 12 `cs-*` agents compose skills into reproducible workflows the Casky platform does not publish. USAP `cs-security-analyst` ("Alex") is the universal entry point; cascades to `cs-incident-responder`, `cs-blue-team-analyst`, `cs-purple-team-lead`, etc.
- **Typed 11-field output contract**. Every skill emits CVSS, MITRE technique IDs, evidence references, severity, confidence, key findings, recommended next agent, and an explicit `human_approval_required` boolean. Safe to embed in production agent stacks where competitor copilots remain black boxes.
- **Machine-readable framework coverage**. USAP's per-skill `metadata.frameworks.*` arrays drive auto-generated ATT&CK Navigator and NIST CSF coverage docs in [`mappings/`](https://github.com/jaskaranhundal/usap-skills/tree/main/mappings). CI fails on drift.

## Who should pick which

| If you are... | Pick |
|---|---|
| A SOC engineer / detection engineer in a 50–500-person security org who already owns LLM access | **USAP** |
| A DevSecOps or platform-security engineer who wants security skills in CI / Claude Code | **USAP** |
| An MSSP / consultancy needing white-labelled CVSS / MITRE deliverables | **USAP** (Apache 2.0 permits embedding) |
| A junior analyst, student, or career switcher building a portfolio | **Casky** (Skills Lab + career paths) |
| You want a hosted "paste real evidence, get a client-ready report" workflow you do not have to operate | **Casky** ($49/mo) |
| You need FedRAMP High or air-gapped operation | Neither — see [Andesite](https://andesite.ai/) |

## Source

This page is a public-facing summary of [`docs/research/casky-ai-competitive-landscape.md`](https://github.com/jaskaranhundal/usap-skills/blob/main/docs/research/casky-ai-competitive-landscape.md), produced from a multi-agent workflow that profiled casky.ai across five lenses (product, target market, pricing, positioning, technology) and deep-dived five additional competitors (Simbian, 7AI, Prophet Security, Dropzone AI, Andesite).
