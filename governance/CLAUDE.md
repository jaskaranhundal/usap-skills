# Governance Domain — CLAUDE.md

## Purpose

The Governance domain contains skills for managing the security program across its strategic, operational, and reporting dimensions. Skills in this domain span the full governance lifecycle: from enterprise architecture review and policy adequacy analysis through security awareness program management, findings and vulnerability lifecycle tracking, KPI and metrics production, knowledge capture, cross-domain posture scoring, and executive brief generation.

Governance skills are advisory by design. They produce structured payloads — scored risk summaries, policy gap reports, board metrics, and posture narratives — that are consumed by executive stakeholders, downstream risk and compliance workflows, and detection response teams. Mutating actions (policy enforcement, patch deployment, access revocation) require explicit human approval gates and are carried out in their respective operational domains.

Subdomains covered by this domain:

- Enterprise security architecture review (zero trust, control coverage gaps, TOGAF alignment)
- Security policy lifecycle and control mapping
- Security awareness, training effectiveness, and phishing simulation analysis
- Findings lifecycle management and SLA enforcement
- Vulnerability management with CVSS v3.1 and EPSS-based prioritization
- Security KPIs, MTTD/MTTR, and board-level metrics reporting
- Knowledge management, runbooks, and lessons-learned capture
- Cross-domain security posture scoring and trending
- CISO-level executive brief and board narrative generation

---

## Skills Catalog

| Skill | Slug | Primary Tool | Coverage |
|---|---|---|---|
| security-architecture | governance/security-architecture | security-architecture_tool.py | Enterprise architecture, TOGAF |
| security-policy-control | governance/security-policy-control | security-policy-control_tool.py | Policy lifecycle, control mapping |
| security-awareness | governance/security-awareness | security-awareness_tool.py | Training programs, phishing simulations |
| findings-tracker | governance/findings-tracker | findings-tracker_tool.py | Finding lifecycle, SLA management |
| vulnerability-management | governance/vulnerability-management | vulnerability-management_tool.py | CVSS, patch prioritization |
| metrics-reporting | governance/metrics-reporting | metrics-reporting_tool.py | KPIs, MTTD/MTTR, board metrics |
| knowledge-management | governance/knowledge-management | knowledge-management_tool.py | Runbooks, lessons learned |
| security-posture-score | governance/security-posture-score | security-posture-score_tool.py | Cross-domain scoring |
| ciso-brief-generator | governance/ciso-brief-generator | ciso-brief-generator_tool.py | Executive briefs |

All skill paths are relative from the repository root as `governance/<slug>/`. For example, the vulnerability-management skill lives at `governance/vulnerability-management/`.

---

## Python Tools Reference

| Tool | Path | Purpose | Key Args |
|---|---|---|---|
| security-architecture_tool.py | governance/security-architecture/scripts/security-architecture_tool.py | Reviews enterprise architecture against zero trust principles, TOGAF phases, and control coverage baselines | `--architecture`, `--framework`, `--output` |
| security-policy-control_tool.py | governance/security-policy-control/scripts/security-policy-control_tool.py | Assesses policy lifecycle status, control mapping completeness, and gap analysis against target frameworks | `--policy-set`, `--framework`, `--output` |
| security-awareness_tool.py | governance/security-awareness/scripts/security-awareness_tool.py | Analyzes phishing simulation results, training completion rates, and program effectiveness trends | `--program`, `--period`, `--output` |
| findings-tracker_tool.py | governance/findings-tracker/scripts/findings-tracker_tool.py | Tracks finding lifecycle from discovery through closure, enforces SLA bands, deduplicates across sources | `--source`, `--sla-band`, `--output` |
| vulnerability-management_tool.py | governance/vulnerability-management/scripts/vulnerability-management_tool.py | Full vulnerability lifecycle: CVSS v3.1 + EPSS scoring, SLA-based patch prioritization, remediation tracking | `--scope`, `--cvss-floor`, `--epss-threshold`, `--output` |
| metrics-reporting_tool.py | governance/metrics-reporting/scripts/metrics-reporting_tool.py | Generates KPI dashboards: MTTD, MTTR, patch coverage, SLA compliance, false-positive rates | `--period`, `--metrics`, `--audience`, `--output` |
| knowledge-management_tool.py | governance/knowledge-management/scripts/knowledge-management_tool.py | Maintains runbook currency, captures lessons learned, and surfaces knowledge gaps from recent incidents | `--runbook`, `--incident-id`, `--output` |
| security-posture-score_tool.py | governance/security-posture-score/scripts/security-posture-score_tool.py | Aggregates findings, metrics, and control coverage from all domains into a 0–100 executive scorecard | `--domains`, `--period`, `--output` |
| ciso-brief-generator_tool.py | governance/ciso-brief-generator/scripts/ciso-brief-generator_tool.py | Synthesizes posture score, vulnerability trends, and metrics into board-ready narrative briefs | `--audience`, `--period`, `--format`, `--output` |

---

## Security Metrics Framework

The following KPIs are the primary measurements tracked across the governance domain. All metrics are computed by `metrics-reporting` and consumed by `security-posture-score` and `ciso-brief-generator`.

| Metric | Formula | Target | Tool |
|---|---|---|---|
| Mean Time to Detect (MTTD) | Avg(detection_timestamp - compromise_timestamp) | < 24 hours for Critical | metrics-reporting |
| Mean Time to Respond (MTTR) | Avg(resolution_timestamp - detection_timestamp) | < 4 hours for Critical | metrics-reporting |
| Mean Time to Remediate (MTTRem) | Avg(patch_timestamp - discovery_timestamp) | < 15 days for Critical | vulnerability-management |
| Patch Coverage | (patched_critical_vulns / total_critical_vulns) × 100 | > 95% for Critical CVEs | vulnerability-management |
| SLA Compliance Rate | (findings_closed_on_time / total_findings) × 100 | > 90% overall | findings-tracker |
| False Positive Rate | (fp_findings / total_findings) × 100 | < 10% | findings-tracker |
| Phishing Click Rate | (users_clicked / users_tested) × 100 | < 5% | security-awareness |
| Training Completion Rate | (trained_users / total_users) × 100 | > 95% quarterly | security-awareness |
| Security Posture Score | Weighted composite of domain sub-scores | > 75 / 100 | security-posture-score |
| Architecture Control Coverage | (implemented_controls / required_controls) × 100 | > 85% | security-architecture |

---

## Vulnerability Management SLA

Patch prioritization uses CVSS v3.1 base scores combined with EPSS exploitation probability to assign SLA bands. The `vulnerability-management` tool enforces these bands and escalates breaches to `findings-tracker`.

| CVSS Range | EPSS Modifier | Patch SLA | Escalation Path |
|---|---|---|---|
| 9.0–10.0 (Critical) | Any | 15 days | CISO + System Owner + Vulnerability Team |
| 9.0–10.0 (Critical) | EPSS > 0.5 | 7 days | CISO + System Owner + Incident Commander |
| 7.0–8.9 (High) | Any | 30 days | Vulnerability Team + System Owner |
| 7.0–8.9 (High) | EPSS > 0.5 | 15 days | CISO + Vulnerability Team |
| 4.0–6.9 (Medium) | Any | 60 days | System Owner |
| 0.1–3.9 (Low) | Any | 90 days | System Owner |
| Any | EPSS > 0.7 | Escalate to next higher band | Vulnerability Team |

EPSS threshold of 0.5 indicates a 50% or greater probability of exploitation in the wild within 30 days. Findings in this category automatically inherit the next-higher SLA band regardless of CVSS score.

---

## Security Architecture Framework Alignment

The `security-architecture` skill evaluates enterprise architecture against the following frameworks and principles. When invoking the skill, specify the target framework to constrain the analysis scope.

| Framework | Focus Area | Primary Assessment Criteria | Governance Output |
|---|---|---|---|
| Zero Trust | Network and identity segmentation | Verify-explicitly, least-privilege, assume-breach coverage | Architecture gap register |
| TOGAF | Enterprise architecture lifecycle | ADM phase adherence, architecture board alignment | Architecture risk report |
| SABSA | Security architecture methodology | Business attribute profile, security domain coverage | Control mapping matrix |
| CIS Controls v8 | Implementation group coverage | IG1/IG2/IG3 control implementation status | Control coverage dashboard |
| NIST SP 800-207 | Zero trust architecture | Seven tenets assessment, PEP/PDP deployment model | Zero trust maturity score |

Architecture reviews are scoped to a triggering change event: a new system deployment, a network segment modification, a cloud service adoption, or a merger/acquisition integration. Open-ended architecture reviews without a defined scope boundary produce low-signal outputs and should not be used for audit evidence purposes.

---

## Security Posture Score Composition

The `security-posture-score` skill computes a 0–100 composite score from weighted sub-scores across all active security domains. The following table defines the default weight allocation. Weights are configurable through the tool's `--weight-profile` argument.

| Domain | Sub-Score Dimension | Default Weight | Source Skills |
|---|---|---|---|
| Vulnerability Management | Patch coverage, SLA compliance, EPSS-weighted open vuln count | 25% | vulnerability-management, findings-tracker |
| Detection Coverage | ATT&CK technique coverage, telemetry health, alert fidelity | 20% | detection/detection-engineering, detection/telemetry-signal-quality |
| Policy and Control | Policy lifecycle completeness, control mapping coverage | 15% | security-policy-control, security-architecture |
| Awareness and Culture | Phishing click rate, training completion, repeat offender rate | 10% | security-awareness |
| Incident Response | MTTD, MTTR, playbook coverage, post-incident review completion | 15% | metrics-reporting, knowledge-management |
| Risk and Compliance | Framework gap count, regulatory obligation SLA compliance | 10% | risk-compliance/compliance-mapping |
| Knowledge Currency | Runbook staleness, lessons-learned capture rate | 5% | knowledge-management |

A composite score below 60 triggers an automatic CISO brief within five business days. A score below 50 triggers board notification. Score deltas greater than 10 points in either direction within a single reporting period are flagged as anomalous and require a root-cause explanation appended to the brief.

---

## Domain Best Practices

1. **Posture scores must be accompanied by trend data.** A point-in-time score is insufficient for executive decision-making. Every `security-posture-score` output must include a 90-day trend line and a period-over-period delta. A score of 74 that is rising from 60 conveys a different risk story than a score of 74 that is falling from 85.

2. **Metrics must be tied to source data.** Board-level metrics reported without a data provenance statement are not auditable. Every metric produced by `metrics-reporting` must cite the data sources, collection period, and any known gaps or exclusions. Undisclosed gaps in coverage are a material misrepresentation of the security posture.

3. **CISO briefs must distinguish signal from noise.** Executive audiences do not process raw finding counts. The `ciso-brief-generator` should surface trend changes, SLA breach rates, and new risk themes — not enumerate individual findings. Narrative quality is the primary quality measure for brief outputs.

4. **Policy gaps require an owner and a remediation date.** A gap identified by `security-policy-control` that has no assigned owner is an unactioned risk. Every identified gap must be translated into a tracked finding with a named owner and an SLA-compliant remediation date before the policy review cycle closes.

5. **Architecture reviews must be scoped to a change event.** A security architecture review is most valuable when anchored to a specific change: a new system, a network segment expansion, a cloud migration. Open-ended reviews produce low-signal outputs. Define the architecture boundary, the triggering change, and the target frameworks (TOGAF, SABSA, zero trust) before invoking `security-architecture`.

6. **Awareness metrics require a control-group baseline.** Phishing simulation click rates are only meaningful relative to a pre-program baseline and a peer benchmark. `security-awareness` outputs must include both to support program effectiveness claims. A 5% click rate is excellent if the starting rate was 30%; it is poor if the industry benchmark is 2%.

7. **Knowledge management is a post-incident obligation.** Every incident that escalates past Severity 3 must produce an updated or validated runbook within 14 days of closure. The `knowledge-management` tool should be invoked as a mandatory step in the post-incident review process, not as an optional enhancement.

8. **Vulnerability SLA breaches must trigger board visibility.** Any Critical or High vulnerability that breaches its SLA band must be surfaced in the next CISO brief, regardless of compensating controls in place. The existence of a compensating control should be documented alongside the breach, not used to suppress it from executive reporting.

---

## Knowledge Management and Runbook Standards

The `knowledge-management` skill enforces a set of content standards for all runbooks and lessons-learned artifacts stored in the governance knowledge base. These standards exist to ensure that knowledge artifacts are actionable during high-stress incident scenarios and auditable during post-incident reviews.

### Runbook Quality Requirements

Every runbook registered in the knowledge base must meet the following criteria:

| Criterion | Requirement | Enforcement |
|---|---|---|
| Trigger definition | Explicit conditions that prompt runbook activation (alert name, severity level, indicator type) | knowledge-management validation check |
| Owner | Named role and backup role; not a team name or alias | knowledge-management validation check |
| Last validated date | Within 90 days; runbooks older than 90 days are flagged as stale | knowledge-management staleness report |
| Step atomicity | Each step is a single executable action; compound steps are split | Manual review at authoring |
| Rollback section | Explicit rollback procedures for every destructive action in the runbook | knowledge-management validation check |
| Approval gates | Steps requiring human approval are explicitly marked | knowledge-management validation check |
| Test evidence | At least one tabletop or live-fire test result with date and participants | knowledge-management validation check |

### Lessons-Learned Capture Requirements

Every post-incident review for incidents at Severity 3 or higher must produce a lessons-learned artifact with the following mandatory fields: incident ID, incident timeline (detection, escalation, containment, resolution), root cause statement, contributing factors, actions taken, effectiveness assessment, and improvement actions with named owners and 30-day deadlines. The `knowledge-management` tool generates a structured template for each required field and validates completeness before archiving.

---

## Workflow Patterns

### Monthly Security Governance Cycle

A structured monthly cadence that produces the full governance reporting stack. This workflow is the primary input to the quarterly board security report.

```
vulnerability-management     (score and prioritize all open vulnerabilities; identify SLA breaches)
       |
       v
findings-tracker             (reconcile finding lifecycle; flag overdue items; dedup across sources)
       |
       v
security-awareness           (pull training completion and phishing simulation results for the period)
       |
       v
metrics-reporting            (compile MTTD, MTTR, patch coverage, SLA compliance, FP rate)
       |
       v
security-posture-score       (aggregate cross-domain sub-scores; compute composite posture score)
       |
       v
ciso-brief-generator         (synthesize all inputs into board-ready narrative with trend analysis)
```

Each skill passes its structured JSON output as context to the next. The final CISO brief includes an appendix with the raw metric inputs and their source provenance statements.

---

### Vulnerability SLA Tracking

An event-driven workflow triggered whenever a new vulnerability scan batch is ingested, or when the daily SLA timer job identifies approaching or breached deadlines.

```
vulnerability-management     (ingest new scan batch; assign CVSS + EPSS scores; set SLA deadlines)
       |
       v
findings-tracker             (register findings; check for existing duplicates; age existing items)
       |
       +--> [SLA on track]        --> update tracking record; no escalation
       |
       +--> [SLA at 75% elapsed]  --> notify system owner; auto-draft remediation reminder
       |
       +--> [SLA breached]        --> escalate per CVSS/EPSS band; flag for ciso-brief-generator
       |
       v
metrics-reporting            (update SLA compliance rate; flag breach in period metrics)
```

SLA breach notifications include: vulnerability ID, CVSS score, EPSS score, assigned SLA band, discovery date, deadline date, and system owner contact. The breach record is included in the next posture score computation as a weighted negative input.

---

## Related Domains

### risk-compliance/

The `risk-compliance/` domain is the primary upstream source of risk context for governance outputs. Governance skills consume enterprise risk assessment heat maps, regulatory compliance gap reports, and DPIA findings as inputs to posture scoring and CISO brief generation.

Key integration points:
- `risk-compliance/enterprise-risk-assessment` risk heat maps inform the threat-landscape section of `governance/ciso-brief-generator` briefs
- `risk-compliance/compliance-mapping` framework gap reports feed `governance/security-policy-control` policy adequacy reviews
- `risk-compliance/regulatory-horizon` emerging requirement alerts trigger `governance/security-architecture` architecture reviews for impacted control domains
- `risk-compliance/quantum-security-readiness` readiness scores are included as a forward-looking risk section in quarterly posture reports

Full domain reference: `risk-compliance/CLAUDE.md`

### detection/

The `detection/` domain is the primary source of operational finding data for governance metrics. Vulnerability findings, behavioral anomalies, and threat hunt verdicts flow from detection into governance for lifecycle management and reporting.

Key integration points:
- `detection/threat-hunting` confirmed findings register in `governance/findings-tracker` for SLA assignment
- `detection/telemetry-signal-quality` data coverage metrics feed `governance/metrics-reporting` as a data quality input dimension
- `detection/behavioral-analytics` entity risk scores inform the insider threat section of `governance/ciso-brief-generator` briefs
- `detection/attack-surface-management` exposure findings feed `governance/vulnerability-management` for prioritization and SLA assignment

Full domain reference: `detection/CLAUDE.md`

---

## Path Reference

All skill paths in this domain are relative from the repository root using the convention `governance/<slug>/`. Sub-paths within each skill follow the standard USAP skill layout:

```
governance/<slug>/
  README.md          -- skill overview and quick commands
  SKILL.md           -- full skill specification and methodology
  scripts/           -- executable Python tools
  references/        -- supporting documentation
  expected_outputs/  -- representative tool outputs for validation
  assets/            -- supporting data files
```

To invoke any tool directly from the repository root:

```bash
python governance/<slug>/scripts/<tool>.py --help
```

Example invocations:

```bash
python governance/vulnerability-management/scripts/vulnerability-management_tool.py --scope enterprise --cvss-floor 7.0 --epss-threshold 0.3 --output json
python governance/metrics-reporting/scripts/metrics-reporting_tool.py --period last-30-days --metrics all --audience board --output json
python governance/security-posture-score/scripts/security-posture-score_tool.py --domains all --period last-quarter --output json
python governance/ciso-brief-generator/scripts/ciso-brief-generator_tool.py --audience board --period last-quarter --format narrative --output pdf
python governance/findings-tracker/scripts/findings-tracker_tool.py --source all --sla-band critical --output json
python governance/knowledge-management/scripts/knowledge-management_tool.py --incident-id INC-2024-0042 --output json
python governance/security-architecture/scripts/security-architecture_tool.py --architecture zero-trust --framework nist-sp-800-207 --output json
python governance/security-awareness/scripts/security-awareness_tool.py --program enterprise --period last-quarter --output json
python governance/security-policy-control/scripts/security-policy-control_tool.py --policy-set enterprise --framework iso27001 --output json
```
