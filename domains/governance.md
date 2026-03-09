# Governance Domain

Skills in this domain manage security program governance, policy adequacy, and findings lifecycle management.

## Skills

| Slug | Level | Description |
|---|---|---|
| `security-architecture` | L2 | Security architecture review: zero trust assessment, control coverage gaps, architecture risk |
| `security-policy-control` | L2 | Security policy adequacy review: gap analysis against frameworks, control effectiveness |
| `security-awareness` | L2 | Security awareness program assessment: phishing simulation results, training effectiveness |
| `findings-tracker` | L3 | Tracks, triages, deduplicates, and ages security findings across the vulnerability lifecycle |
| `vulnerability-management` | L3 | Full vulnerability lifecycle: CVSS v3.1 + EPSS scoring, SLA-based prioritization, remediation tracking |
| `metrics-reporting` | L2 | Security KPI and metrics reporting: MTTR, MTTD, patch coverage, SLA compliance |
| `security-posture-score` | L3 | Cross-domain security posture scoring: aggregates findings into an executive scorecard |
| `ciso-brief-generator` | L2 | Generates CISO-level security briefs: risk posture summaries, board-ready narratives |

## Workflow: Governance Reporting Cycle

```
vulnerability-management → findings-tracker → metrics-reporting → security-posture-score → ciso-brief-generator
```

## Key Metrics Tracked

| Metric | Target | Skill |
|---|---|---|
| MTTR (Mean Time to Remediate) | < 30 days for Critical | `metrics-reporting` |
| MTTD (Mean Time to Detect) | < 24 hours for Critical | `metrics-reporting` |
| Patch Coverage | > 95% for Critical CVEs | `vulnerability-management` |
| False Positive Rate | < 10% | `findings-tracker` |
| Security Posture Score | > 75/100 | `security-posture-score` |

## Orchestrator Agent

[cs-ciso-advisor](../agents/executive/cs-ciso-advisor.md) — uses governance skills to generate board-ready security posture reports.
