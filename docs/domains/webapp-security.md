---
title: USAP webapp-security domain — OWASP Top 10 + API Security Top 10 skills
description: Webapp and API security skills for runtime triage and OWASP Top 10 2025 classification. Includes webapp-risk-triage, owasp-top10-classifier, api-security-posture. Open source, runs in any LLM.
---

# Domain: webapp-security

Webapp and API security skills for runtime triage and OWASP Top 10 / OWASP API Top 10 classification.

## Skills

| Slug | Level | Intent | Frameworks (frontmatter) |
|---|---|---|---|
| `webapp-risk-triage` | L3 | analyze | OWASP A01, A03, A05, A07; MITRE T1190 |
| `owasp-top10-classifier` | L3 | detect | OWASP A01–A08 |
| `api-security-posture` | L3 | analyze | OWASP A01, A03, A07; MITRE T1078, T1190 |

## Orchestrator

- [`cs-appsec-engineer`](https://github.com/jaskaranhundal/usap-skills/blob/main/agents/appsec/cs-appsec-engineer.md) — single entry point for triage, classification, and posture scoring. Bridges runtime (webapp-security) and build-time (appsec-devsecops) AppSec.

## When to use

- A webapp finding came in from a SAST/DAST scanner, a bug-bounty report, or a WAF alert: start with `cs-appsec-engineer` → `webapp-risk-triage`.
- A finding description needs to be bucketed into OWASP Top 10 2025: `owasp-top10-classifier`.
- An API surface (REST or GraphQL) needs a static posture score against OWASP API Security Top 10: `api-security-posture`.

## Quick start

```bash
# Triage the bundled sample finding
python3 webapp-security/webapp-risk-triage/scripts/webapp-risk-triage_tool.py --output json

# Classify a description into OWASP Top 10
python3 webapp-security/owasp-top10-classifier/scripts/owasp-top10-classifier_tool.py --output json

# Score an API descriptor against the OWASP API Top 10
python3 webapp-security/api-security-posture/scripts/api-security-posture_tool.py --output json
```

All three tools are stdlib only — no `pip install` required. Each emits a USAP 11-field contract payload.

## Source

- [webapp-security/ on GitHub](https://github.com/jaskaranhundal/usap-skills/tree/main/webapp-security)
- [webapp-security/CLAUDE.md (domain methodology)](https://github.com/jaskaranhundal/usap-skills/blob/main/webapp-security/CLAUDE.md)
