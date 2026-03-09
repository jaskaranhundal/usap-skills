# Risk & Compliance Domain — CLAUDE.md

## Purpose

The Risk & Compliance domain contains skills for quantifying enterprise risk, modeling threats at the design and architecture level, mapping security controls to regulatory frameworks, tracking emerging regulatory obligations, conducting privacy impact assessments, evaluating cyber insurance adequacy, gathering internal audit evidence, and assessing organizational readiness for post-quantum cryptography standards.

Risk and compliance skills are advisory and analytical. They produce structured risk registers, heat maps, compliance gap reports, DPIA outputs, and readiness assessments. These payloads are consumed by the governance domain for posture scoring and executive reporting, by the detection domain for risk-contextualized finding prioritization, and by security and legal stakeholders for regulatory decision-making. Mutating actions — enforcing controls, modifying data processing activities, renegotiating insurance policies — require explicit human approval and are executed by the relevant operational functions.

Subdomains covered by this domain:

- Enterprise risk quantification and board risk heat map generation
- Threat modeling using STRIDE, PASTA, and LINDDUN methodologies
- Multi-framework compliance mapping and control cross-walk
- Regulatory horizon scanning (NIS2, DORA, state privacy laws, sector-specific rules)
- GDPR Data Protection Impact Assessment (DPIA) and Privacy Impact Assessment (PIA)
- Cyber insurance coverage adequacy analysis against incident scenario libraries
- Internal audit evidence collection and controls testing for SOC 2, ISO 27001, SOX, and FedRAMP
- Post-quantum cryptography readiness assessment against NIST PQC standards

---

## Skills Catalog

| Skill | Slug | Primary Tool | Coverage |
|---|---|---|---|
| enterprise-risk-assessment | risk-compliance/enterprise-risk-assessment | enterprise-risk-assessment_tool.py | Board risk, heat maps |
| risk-threat-modeling | risk-compliance/risk-threat-modeling | risk-threat-modeling_tool.py | STRIDE, PASTA, LINDDUN |
| compliance-mapping | risk-compliance/compliance-mapping | compliance-mapping_tool.py | Multi-framework mapping |
| regulatory-horizon | risk-compliance/regulatory-horizon | regulatory-horizon_tool.py | Regulatory watch, NIS2, DORA |
| privacy-dpia | risk-compliance/privacy-dpia | privacy-dpia_tool.py | GDPR DPIA, PIA |
| cyber-insurance | risk-compliance/cyber-insurance | cyber-insurance_tool.py | Coverage adequacy |
| internal-audit-assurance | risk-compliance/internal-audit-assurance | internal-audit-assurance_tool.py | Audit evidence, controls testing |
| quantum-security-readiness | risk-compliance/quantum-security-readiness | quantum-security-readiness_tool.py | PQC readiness, NIST PQC standards |

All skill paths are relative from the repository root as `risk-compliance/<slug>/`. For example, the compliance-mapping skill lives at `risk-compliance/compliance-mapping/`.

---

## Python Tools Reference

| Tool | Path | Purpose | Key Args |
|---|---|---|---|
| enterprise-risk-assessment_tool.py | risk-compliance/enterprise-risk-assessment/scripts/enterprise-risk-assessment_tool.py | Aggregates risk scenarios into board-level heat maps; scores by Likelihood × Impact; aligns to risk appetite | `--scope`, `--risk-appetite`, `--output` |
| risk-threat-modeling_tool.py | risk-compliance/risk-threat-modeling/scripts/risk-threat-modeling_tool.py | Runs STRIDE, PASTA, or LINDDUN threat modeling on DFDs; scores threat scenarios; maps to MITRE ATT&CK | `--model`, `--methodology`, `--output` |
| compliance-mapping_tool.py | risk-compliance/compliance-mapping/scripts/compliance-mapping_tool.py | Maps implemented controls to multiple regulatory frameworks; identifies gaps; produces cross-walk tables | `--frameworks`, `--control-inventory`, `--output` |
| regulatory-horizon_tool.py | risk-compliance/regulatory-horizon/scripts/regulatory-horizon_tool.py | Tracks emerging and enacted regulations; maps new requirements to existing control gaps; produces deadline register | `--region`, `--sector`, `--lookahead-days`, `--output` |
| privacy-dpia_tool.py | risk-compliance/privacy-dpia/scripts/privacy-dpia_tool.py | Conducts GDPR-aligned DPIA and PIA for data processing activities; scores residual risk; identifies consultation triggers | `--processing-activity`, `--data-categories`, `--output` |
| cyber-insurance_tool.py | risk-compliance/cyber-insurance/scripts/cyber-insurance_tool.py | Evaluates insurance coverage adequacy against incident scenario library; identifies coverage gaps and sublimit risks | `--policy`, `--scenario-set`, `--output` |
| internal-audit-assurance_tool.py | risk-compliance/internal-audit-assurance/scripts/internal-audit-assurance_tool.py | Collects and organizes controls evidence for audit; tests control operating effectiveness; identifies exceptions | `--framework`, `--control-domain`, `--period`, `--output` |
| quantum-security-readiness_tool.py | risk-compliance/quantum-security-readiness/scripts/quantum-security-readiness_tool.py | Assesses current cryptographic asset inventory against NIST PQC standards; scores migration readiness; prioritizes migration paths | `--scope`, `--nist-pqc-set`, `--output` |

---

## Regulatory Framework Coverage

The following matrix shows which skills contribute to each supported regulatory framework, where gap identification occurs, and whether deadline tracking is maintained.

| Framework | Contributing Skills | Gap Identification | Deadline Tracking |
|---|---|---|---|
| GDPR | compliance-mapping, privacy-dpia, regulatory-horizon | compliance-mapping (control gaps), privacy-dpia (residual risk) | regulatory-horizon (enforcement deadlines) |
| PCI DSS | compliance-mapping, internal-audit-assurance | compliance-mapping (requirement gaps), internal-audit-assurance (control exceptions) | regulatory-horizon (version transition deadlines) |
| HIPAA | compliance-mapping, internal-audit-assurance, privacy-dpia | compliance-mapping, privacy-dpia (PHI processing) | regulatory-horizon |
| SOC 2 | internal-audit-assurance, compliance-mapping | internal-audit-assurance (control exceptions), compliance-mapping (TSC gap mapping) | internal-audit-assurance (audit window tracking) |
| ISO 27001 | compliance-mapping, internal-audit-assurance, enterprise-risk-assessment | compliance-mapping (Annex A gaps), internal-audit-assurance (evidence gaps) | regulatory-horizon (certification renewal) |
| NIST CSF | compliance-mapping, enterprise-risk-assessment | compliance-mapping (function/category gaps) | regulatory-horizon |
| NIS2 | compliance-mapping, regulatory-horizon, enterprise-risk-assessment | regulatory-horizon (new requirement identification), compliance-mapping (control gaps) | regulatory-horizon (national transposition deadlines) |
| DORA | compliance-mapping, regulatory-horizon, internal-audit-assurance | regulatory-horizon, compliance-mapping (ICT risk management gaps) | regulatory-horizon (phased compliance deadlines) |
| CCPA / CPRA | compliance-mapping, privacy-dpia, regulatory-horizon | compliance-mapping (data rights gaps), privacy-dpia (processing risk) | regulatory-horizon (amendment deadlines) |
| SOX | internal-audit-assurance, enterprise-risk-assessment | internal-audit-assurance (IT general controls exceptions) | internal-audit-assurance (reporting period tracking) |
| FedRAMP | internal-audit-assurance, compliance-mapping | internal-audit-assurance (control evidence gaps), compliance-mapping (NIST 800-53 gaps) | regulatory-horizon (authorization renewal) |

---

## Risk Quantification Methods

The `enterprise-risk-assessment` skill supports three risk quantification approaches. Select the appropriate method based on the audience and decision context.

| Method | Description | Output Format | Best Used For |
|---|---|---|---|
| Qualitative (Likelihood x Impact) | 5x5 matrix; both axes scored 1–5; product gives risk score 1–25 | Heat map with risk zone overlay | Board-level briefings, initial risk triage, risk appetite alignment |
| Semi-quantitative (FAIR-lite) | Maps qualitative scores to frequency and magnitude ranges; produces annualized loss exposure bands | Risk register with ALE ranges (Low / Medium / High / Very High) | Risk treatment prioritization, investment justification, insurance sizing |
| Quantitative (FAIR) | Full Factor Analysis of Information Risk; produces annualized loss expectancy in monetary terms | Monte Carlo simulation range with 10th/50th/90th percentile ALE | Cyber insurance benchmarking, board risk committee reporting, M&A due diligence |

For organizations without a mature FAIR data model, semi-quantitative is the recommended default. The `enterprise-risk-assessment` tool accepts `--method qualitative`, `--method semi-quantitative`, or `--method fair` to select the appropriate model.

---

## DPIA Trigger Criteria

The `privacy-dpia` skill applies the following GDPR Article 35(3) mandatory trigger criteria. If any trigger is met, a full DPIA is legally required and must be completed before processing commences.

| Trigger | Description | Assessment Required | Supervisory Authority Consultation |
|---|---|---|---|
| Systematic evaluation / profiling | Automated processing to evaluate personal aspects, including profiling that produces legal or similarly significant effects | Full DPIA | If residual risk remains high after mitigation |
| Large-scale special category data | Processing special categories (health, biometric, racial origin, political opinion, etc.) at scale | Full DPIA | If residual risk remains high after mitigation |
| Systematic public area monitoring | Large-scale monitoring of publicly accessible areas (CCTV, location tracking) | Full DPIA | If residual risk remains high after mitigation |
| Innovative technology | New technology whose privacy impact is not yet well understood | DPIA recommended | If residual risk remains high after mitigation |
| Automated decision-making with legal effect | Solely automated processing producing legal or similarly significant effects | Full DPIA | Required in all cases |
| Cross-border transfer to high-risk third country | Transfer without an adequacy decision and without standard contractual clauses | Transfer Impact Assessment + DPIA if special categories involved | If transfer involves high-risk country |

The `privacy-dpia` tool evaluates the processing activity description against all six trigger criteria and produces a trigger verdict before proceeding to the full DPIA methodology. A negative trigger verdict (no DPIA required) is documented as a PIA record with the rationale for the negative determination.

---

## Threat Modeling Methodology Reference

The `risk-threat-modeling` skill supports three structured threat modeling methodologies. Select based on the system type and the primary threat concerns.

| Methodology | Primary Focus | Suitable For | Key Outputs |
|---|---|---|---|
| STRIDE | Spoofing, Tampering, Repudiation, Information Disclosure, Denial of Service, Elevation of Privilege | General software systems, APIs, microservices, data pipelines | Threat scenario list, per-component STRIDE matrix, mitigation register |
| PASTA | Process for Attack Simulation and Threat Analysis — business-impact-aligned, attacker-centric | Business-critical applications, payment systems, high-value targets | Attack tree, business impact alignment, risk-ranked threat scenarios |
| LINDDUN | Linkability, Identifiability, Non-repudiation, Detectability, Disclosure of information, Unawareness, Non-compliance | Privacy-sensitive systems, health data, consumer data processing | Privacy threat matrix, DFD-annotated findings, GDPR compliance implications |

All three methodologies produce outputs mapped to MITRE ATT&CK techniques for integration with `detection/detection-engineering` coverage analysis. Threat models must be re-run when any of the following changes occur: a new trust boundary is introduced, a new data store or data flow is added, a third-party integration is modified, or a prior threat scenario's stated mitigation is removed or downgraded.

---

## Domain Best Practices

1. **Risk heat maps require a calibrated risk appetite statement.** A heat map without an explicit risk appetite boundary is decorative. Before generating a heat map with `enterprise-risk-assessment`, obtain a signed risk appetite statement from the board or executive risk committee. Risk scenarios that fall within appetite are tracked; those that exceed appetite require immediate treatment plan assignment.

2. **Threat models must be anchored to a specific system boundary and version.** A threat model produced without a scoped data flow diagram and a system version identifier cannot be reused or updated. Every invocation of `risk-threat-modeling` must specify the DFD revision, the system version, and the date of the model. Generic threat models are not valid inputs to compliance or risk evidence packages.

3. **Compliance mapping is a point-in-time snapshot.** A compliance map produced from a control inventory that is 90 days or older is unreliable for audit purposes. The `compliance-mapping` tool must be re-run within 30 days before any audit evidence submission. Control inventory inputs must be timestamped and sourced from an authoritative configuration management or GRC system.

4. **DPIA triggers are non-negotiable.** Under GDPR Article 35, a DPIA is legally required before processing that is likely to result in a high risk to data subjects. The `privacy-dpia` skill embeds GDPR Article 35(3) trigger criteria. If the skill flags a mandatory DPIA trigger, processing must not commence until the DPIA is complete and, where required, prior consultation with the supervisory authority is obtained. This is a legal obligation, not a recommendation.

5. **Regulatory horizon outputs require a named owner for each tracked obligation.** A regulatory deadline without an assigned owner is an unmanaged risk. Every obligation produced by `regulatory-horizon` must be assigned to a named function (Legal, CISO, CTO, DPO) within five business days of identification. Unassigned obligations are flagged as governance exceptions in the next posture score computation.

6. **Cyber insurance gap analysis must use scenario-based assessment.** Coverage adequacy cannot be assessed by comparing policy limits to revenue figures alone. The `cyber-insurance` tool evaluates coverage against a library of incident scenarios (ransomware with business interruption, data breach with regulatory fine, SWIFT fraud, cloud outage) and identifies sublimit exposures and exclusion risks. Scenario-based assessments must be refreshed after every material change to the organization's technology footprint.

7. **Quantum readiness is a multi-year program, not a one-time assessment.** The `quantum-security-readiness` assessment establishes a cryptographic asset inventory baseline and maps current algorithms to NIST PQC standards (FIPS 203 ML-KEM, FIPS 204 ML-DSA, FIPS 205 SLH-DSA). The output is a migration priority register, not a pass/fail verdict. Reassess annually as NIST guidance evolves and as harvest-now-decrypt-later threat intelligence develops.

8. **Internal audit evidence must meet admissibility standards.** Evidence collected by `internal-audit-assurance` for SOC 2, ISO 27001, or FedRAMP audits must include: the control identifier, the evidence artifact, the collection timestamp, the collection method, and the name of the individual or automated process that produced the evidence. Evidence without complete provenance metadata will be rejected by external auditors as inadmissible.

---

## Audit Evidence Standards

The `internal-audit-assurance` skill enforces evidence quality standards aligned to the requirements of external auditors across the supported frameworks. The following table defines the minimum metadata requirements for each evidence artifact class.

| Evidence Class | Required Metadata | Admissibility Standard | Frameworks |
|---|---|---|---|
| System-generated log | Timestamp, system ID, log source, hash or checksum | Unaltered export with chain of custody statement | SOC 2, FedRAMP, SOX |
| Screenshot | Timestamp visible in screenshot, URL or system path visible, preparer name | Acceptable for supplemental only; not standalone for operating effectiveness | SOC 2, ISO 27001 |
| Policy document | Version number, approval date, approver name, effective date | Must be the version in force during the audit period | All frameworks |
| Configuration export | Export timestamp, system name, tool used for export, preparer name | Must be exported directly from the authoritative system; manual transcriptions are not acceptable | PCI DSS, FedRAMP, SOC 2 |
| Interview record | Interviewee name, role, date, interviewer name, questions asked | Signed by interviewee or recorded with consent | ISO 27001, SOC 2 |
| Test result | Test ID, test date, tester name, expected outcome, actual outcome, pass/fail verdict | Must include both expected and actual outcomes | SOC 2, FedRAMP |
| Third-party report | Report date, issuing firm, report type (SOC 2, pen test, etc.), scope statement | Must be within validity period; SOC 2 reports expire after 12 months | All frameworks |

Evidence gaps identified by `internal-audit-assurance` are automatically registered in the governance domain's `findings-tracker` with the audit framework, the control reference, the gap description, and a 14-day default remediation deadline before audit submission.

### Controls Testing Sampling Standards

For operating effectiveness testing, the `internal-audit-assurance` tool applies the following sample size guidance aligned to AICPA and ISO audit practice:

| Population Size | Minimum Sample Size | Sampling Method |
|---|---|---|
| 1–5 | 100% (all items) | Census |
| 6–25 | 5 items | Haphazard selection |
| 26–65 | 15 items | Random selection |
| 66–250 | 25 items | Random selection |
| 251+ | 40 items | Random or systematic selection |

For automated controls that execute identically for every transaction, one or two examples are sufficient to demonstrate design effectiveness. Operating effectiveness for automated controls is demonstrated through evidence that the control was enabled and functioning throughout the entire audit period rather than through population sampling.

---

## Workflow Patterns

### Quarterly Risk Review

A structured quarterly cadence that produces the enterprise risk posture for board consumption and feeds governance reporting.

```
risk-threat-modeling         (update threat models for material system changes in the quarter)
       |
       v
enterprise-risk-assessment   (aggregate risk scenarios; update heat map; check against risk appetite)
       |
       v
compliance-mapping           (refresh control-to-framework mapping; identify new gaps)
       |
       v
regulatory-horizon           (scan for new or amended regulations; update obligation register)
       |
       v
cyber-insurance              (validate coverage adequacy against current risk profile)
       |
       v
[outputs feed governance/security-posture-score and governance/ciso-brief-generator]
```

The quarterly risk review produces: an updated risk heat map, a control gap register by framework, a regulatory obligation register with deadlines and owners, and a coverage adequacy report. All outputs are structured JSON payloads formatted for direct consumption by governance skills.

---

### Regulatory Gap Assessment

An event-driven workflow triggered by a new regulation, a regulatory amendment, or a notification from `regulatory-horizon` that a compliance deadline is within 90 days.

```
regulatory-horizon           (identify specific new requirements; map to affected control domains)
       |
       v
compliance-mapping           (map new requirements to existing control inventory; identify gaps)
       |
       v
enterprise-risk-assessment   (score residual risk from identified compliance gaps)
       |
       v
internal-audit-assurance     (identify evidence gaps for the new requirements)
       |
       +--> [gaps identified]     --> create remediation plan with named owners and deadlines
       |
       +--> [no gaps identified]  --> document compliance attestation; archive evidence package
```

If a privacy-related regulation is in scope (GDPR, CCPA, HIPAA), `privacy-dpia` is invoked between `compliance-mapping` and `enterprise-risk-assessment` to assess data subject risk for any new processing requirements introduced by the regulation.

---

## Related Domains

### governance/

The `governance/` domain is the primary downstream consumer of risk-compliance outputs. Posture scores, compliance gap reports, and regulatory obligation registers produced in this domain feed directly into governance reporting and executive brief generation.

Key integration points:
- `risk-compliance/enterprise-risk-assessment` heat maps are included in the threat-landscape section of `governance/ciso-brief-generator` briefs
- `risk-compliance/compliance-mapping` gap registers feed `governance/security-policy-control` policy adequacy reviews and `governance/findings-tracker` for SLA assignment
- `risk-compliance/regulatory-horizon` obligation registers trigger `governance/security-architecture` architecture reviews when new requirements impose control design changes
- `risk-compliance/quantum-security-readiness` migration priority registers are surfaced in `governance/ciso-brief-generator` as a strategic risk section

Full domain reference: `governance/CLAUDE.md`

### detection/

The `detection/` domain provides operational finding data that informs risk quantification and compliance evidence in this domain.

Key integration points:
- `detection/attack-surface-management` and `detection/network-exposure` findings feed `risk-compliance/enterprise-risk-assessment` as external exposure risk scenarios
- `detection/threat-intelligence` actor attribution informs `risk-compliance/risk-threat-modeling` threat scenario calibration
- `detection/behavioral-analytics` insider threat risk scores are consumed by `risk-compliance/enterprise-risk-assessment` for people-risk heat map contributions
- Confirmed hunt findings from `detection/threat-hunting` register in `risk-compliance/compliance-mapping` as evidence of incident for frameworks requiring breach reporting (GDPR 72-hour notification, NIS2 Article 23)

Full domain reference: `detection/CLAUDE.md`

---

## Path Reference

All skill paths in this domain are relative from the repository root using the convention `risk-compliance/<slug>/`. Sub-paths within each skill follow the standard USAP skill layout:

```
risk-compliance/<slug>/
  README.md          -- skill overview and quick commands
  SKILL.md           -- full skill specification and methodology
  scripts/           -- executable Python tools
  references/        -- supporting documentation
  expected_outputs/  -- representative tool outputs for validation
  assets/            -- supporting data files
```

To invoke any tool directly from the repository root:

```bash
python risk-compliance/<slug>/scripts/<tool>.py --help
```

Example invocations:

```bash
python risk-compliance/enterprise-risk-assessment/scripts/enterprise-risk-assessment_tool.py --scope enterprise --risk-appetite board-approved-2024 --output json
python risk-compliance/compliance-mapping/scripts/compliance-mapping_tool.py --frameworks gdpr,pci-dss,iso27001 --control-inventory current --output json
python risk-compliance/regulatory-horizon/scripts/regulatory-horizon_tool.py --region eu,us --sector financial --lookahead-days 180 --output json
python risk-compliance/privacy-dpia/scripts/privacy-dpia_tool.py --processing-activity customer-analytics --data-categories personal,behavioral --output json
python risk-compliance/cyber-insurance/scripts/cyber-insurance_tool.py --policy current --scenario-set ransomware,data-breach,cloud-outage --output json
python risk-compliance/quantum-security-readiness/scripts/quantum-security-readiness_tool.py --scope enterprise --nist-pqc-set fips203,fips204,fips205 --output json
python risk-compliance/internal-audit-assurance/scripts/internal-audit-assurance_tool.py --framework soc2 --control-domain security --period 2024-q4 --output json
python risk-compliance/risk-threat-modeling/scripts/risk-threat-modeling_tool.py --model payment-service-dfd-v3 --methodology stride --output json
python risk-compliance/enterprise-risk-assessment/scripts/enterprise-risk-assessment_tool.py --scope enterprise --method semi-quantitative --risk-appetite board-approved-2024 --output json
```
