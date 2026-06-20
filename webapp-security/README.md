# webapp-security

Webapp and API security skills for runtime triage and OWASP Top 10 / OWASP API Top 10 classification. Three anchor skills:

| Skill | Use it for |
|---|---|
| [`webapp-risk-triage`](webapp-risk-triage/SKILL.md) | First-pass triage of a webapp finding: which OWASP category, what severity, who triages next |
| [`owasp-top10-classifier`](owasp-top10-classifier/SKILL.md) | Classify a finding description into OWASP Top 10 2025 categories with confidence scoring |
| [`api-security-posture`](api-security-posture/SKILL.md) | Score an API surface against OWASP API Security Top 10 |

Scope is the **runtime** webapp surface. Build-time AppSec (SAST, dependency analysis, supply chain) lives in [`appsec-devsecops/`](../appsec-devsecops/README.md).

See [CLAUDE.md](CLAUDE.md) for the domain methodology, workflow patterns, and integration with other USAP domains.
