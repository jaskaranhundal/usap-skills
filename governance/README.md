# Governance Domain

Skills in the Governance domain manage the security program across its strategic, operational, and reporting dimensions. The domain spans enterprise architecture review, policy lifecycle management, security awareness measurement, findings and vulnerability tracking, KPI and metrics production, knowledge management, cross-domain posture scoring, and executive brief generation. Governance skills produce structured, auditable outputs that are consumed by executive stakeholders, board reporting cycles, and downstream risk and compliance workflows.

---

## Skills Index

| Skill | Description | Key Use Case |
|---|---|---|
| security-architecture | Reviews enterprise architecture against zero trust principles, TOGAF phases, and control coverage baselines. Identifies architectural risk, coverage gaps, and design-level remediation paths. | New cloud migration architecture review, zero trust maturity assessment, M&A integration security review |
| security-policy-control | Assesses security policy lifecycle status, control mapping completeness, and gap analysis against target frameworks. Produces a gap register with ownership assignments. | Annual policy review cycle, framework gap analysis, pre-audit policy readiness check |
| security-awareness | Analyzes phishing simulation results, training completion rates, and program effectiveness trends. Benchmarks against industry baselines and prior periods. | Quarterly awareness program review, post-phishing campaign debrief, board metrics for human risk |
| findings-tracker | Tracks finding lifecycle from discovery through closure, enforces SLA bands across criticality levels, and deduplicates findings across multiple scanning and detection sources. | Monthly SLA breach review, cross-source finding deduplication, audit evidence of finding closure |
| vulnerability-management | Full vulnerability lifecycle management using CVSS v3.1 base scores combined with EPSS exploitation probability for prioritization. Tracks remediation against SLA-based patch deadlines. | Enterprise patch prioritization, critical vulnerability SLA enforcement, board-level patch coverage reporting |
| metrics-reporting | Generates security KPI dashboards and period reports covering MTTD, MTTR, patch coverage, SLA compliance, false-positive rates, and training metrics. Tailors output format to audience (technical, management, board). | Monthly security operations metrics package, quarterly board security report input, executive dashboard refresh |
| knowledge-management | Maintains runbook currency, captures lessons learned from incidents and near-misses, and surfaces knowledge gaps that require documentation. Enforces post-incident runbook update obligations. | Post-incident lessons-learned capture, runbook currency audit, knowledge gap identification |
| security-posture-score | Aggregates findings, metrics, and control coverage from all security domains into a 0–100 composite posture scorecard with 90-day trending. Produces sub-scores by domain for drill-down analysis. | Quarterly board security posture report, period-over-period posture trending, program maturity benchmarking |
| ciso-brief-generator | Synthesizes posture score, vulnerability trends, metrics, and risk themes into board-ready narrative briefs. Generates executive summaries, risk themes, and recommended actions for non-technical audiences. | Quarterly board security presentation, monthly CISO stakeholder update, investor security assurance brief |

---

## Agent Links

The primary orchestrator for this domain is the [cs-ciso-advisor](../agents/executive/cs-ciso-advisor.md) agent, which coordinates governance skills to produce board-ready security posture reports, executive briefs, and program health assessments for CISO and board-level stakeholders.

The `cs-ciso-advisor` agent specifically orchestrates the following governance skills for its core workflow:

- `security-posture-score` — generates the composite posture score and domain sub-scores that anchor every executive deliverable
- `metrics-reporting` — supplies the KPI and metrics inputs that populate posture score sub-dimensions and brief narratives
- `ciso-brief-generator` — produces the final board-ready narrative from posture scores, metrics, and risk context

Typical orchestration patterns:

- Quarterly board report: `vulnerability-management` -> `metrics-reporting` -> `security-posture-score` -> `ciso-brief-generator`
- SLA breach escalation: `findings-tracker` -> `metrics-reporting` -> `ciso-brief-generator`
- Post-incident knowledge capture: `knowledge-management` -> `security-awareness` -> `metrics-reporting`

---

## Quick Commands

Run any skill tool directly from the repository root. All tools accept `--help` and `--output json` for structured output.

**security-architecture**
```bash
python governance/security-architecture/scripts/security-architecture_tool.py --help
python governance/security-architecture/scripts/security-architecture_tool.py --architecture cloud-migration --framework zero-trust --output json
```

**security-policy-control**
```bash
python governance/security-policy-control/scripts/security-policy-control_tool.py --help
python governance/security-policy-control/scripts/security-policy-control_tool.py --policy-set enterprise --framework iso27001 --output json
```

**security-awareness**
```bash
python governance/security-awareness/scripts/security-awareness_tool.py --help
python governance/security-awareness/scripts/security-awareness_tool.py --program enterprise --period last-quarter --output json
```

**findings-tracker**
```bash
python governance/findings-tracker/scripts/findings-tracker_tool.py --help
python governance/findings-tracker/scripts/findings-tracker_tool.py --source all --sla-band critical --output json
```

**vulnerability-management**
```bash
python governance/vulnerability-management/scripts/vulnerability-management_tool.py --help
python governance/vulnerability-management/scripts/vulnerability-management_tool.py --scope enterprise --cvss-floor 7.0 --epss-threshold 0.3 --output json
```

**metrics-reporting**
```bash
python governance/metrics-reporting/scripts/metrics-reporting_tool.py --help
python governance/metrics-reporting/scripts/metrics-reporting_tool.py --period last-30-days --metrics all --audience board --output json
```

**knowledge-management**
```bash
python governance/knowledge-management/scripts/knowledge-management_tool.py --help
python governance/knowledge-management/scripts/knowledge-management_tool.py --incident-id INC-2024-0042 --output json
```

**security-posture-score**
```bash
python governance/security-posture-score/scripts/security-posture-score_tool.py --help
python governance/security-posture-score/scripts/security-posture-score_tool.py --domains all --period last-quarter --output json
```

**ciso-brief-generator**
```bash
python governance/ciso-brief-generator/scripts/ciso-brief-generator_tool.py --help
python governance/ciso-brief-generator/scripts/ciso-brief-generator_tool.py --audience board --period last-quarter --format narrative --output json
```

---

## Full Domain Guide

For complete methodology, cross-skill workflow patterns, the Security Metrics Framework, Vulnerability Management SLA tables, Python tools reference, and domain best practices, see [CLAUDE.md](./CLAUDE.md).
