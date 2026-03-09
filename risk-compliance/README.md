# Risk & Compliance Domain

Skills in the Risk & Compliance domain quantify enterprise risk, model threats at the design and architecture level, map security controls to regulatory frameworks, track emerging regulatory obligations, conduct privacy impact assessments, evaluate cyber insurance coverage adequacy, gather internal audit evidence, and assess readiness for post-quantum cryptography migration. Risk and compliance skills produce structured, auditable outputs that feed executive governance reporting, regulatory submission packages, and operational security prioritization decisions.

---

## Skills Index

| Skill | Description | Key Use Case |
|---|---|---|
| enterprise-risk-assessment | Aggregates risk scenarios into board-level heat maps using Likelihood × Impact scoring aligned to the organization's risk appetite statement. Identifies risks that exceed appetite and require treatment plans. | Quarterly board risk review, M&A target risk assessment, post-incident risk re-rating |
| risk-threat-modeling | Runs structured threat modeling using STRIDE, PASTA, or LINDDUN methodologies on data flow diagrams. Scores threat scenarios by Likelihood × Impact and maps findings to MITRE ATT&CK techniques. | New system design review, architecture threat model update, secure SDLC gate |
| compliance-mapping | Maps implemented security controls to multiple regulatory frameworks simultaneously. Generates cross-walk tables, identifies control gaps by framework, and produces evidence-ready compliance gap registers. | Pre-audit compliance gap assessment, multi-framework control cross-walk, new framework adoption baseline |
| regulatory-horizon | Tracks enacted and emerging regulations and maps new requirements to existing control gaps. Maintains a deadline register with named obligation owners for upcoming compliance milestones. | NIS2 / DORA readiness tracking, state privacy law amendment monitoring, sector-specific regulatory watch |
| privacy-dpia | Conducts GDPR-aligned Data Protection Impact Assessments (DPIA) and Privacy Impact Assessments (PIA) for data processing activities. Applies Article 35(3) trigger criteria and produces a scored residual risk output. | New product feature involving personal data, third-party data processing agreement, AI-driven profiling use case |
| cyber-insurance | Evaluates cyber insurance policy coverage adequacy against a library of incident scenarios. Identifies sublimit exposures, exclusion risks, and coverage gaps relative to the organization's current risk profile. | Annual policy renewal preparation, post-incident coverage review, M&A insurance due diligence |
| internal-audit-assurance | Collects, organizes, and validates controls evidence for audit engagements. Tests control operating effectiveness and identifies exceptions for SOC 2, ISO 27001, SOX IT general controls, and FedRAMP. | SOC 2 Type II audit evidence package, ISO 27001 surveillance audit prep, FedRAMP annual assessment |
| quantum-security-readiness | Assesses the organization's cryptographic asset inventory against NIST PQC standards (FIPS 203, FIPS 204, FIPS 205). Scores migration readiness and produces a prioritized cryptographic migration register. | PQC migration program initiation, cryptographic inventory baseline, board-level quantum risk brief |

---

## Agent Links

The primary orchestrator for this domain is the [cs-ciso-advisor](../agents/executive/cs-ciso-advisor.md) agent, which coordinates risk and compliance skills for executive advisory workflows, board-level risk reporting, and regulatory compliance readiness assessments.

The `cs-ciso-advisor` agent specifically orchestrates the following risk-compliance skills for its core workflow:

- `enterprise-risk-assessment` — produces the board risk heat map and risk appetite alignment analysis that anchors quarterly executive risk presentations
- `compliance-mapping` — supplies the regulatory control gap register that informs program investment priorities and audit readiness status
- `cyber-insurance` — provides the coverage adequacy assessment that is surfaced in board risk discussions and D&O insurance context

Typical orchestration patterns:

- Quarterly board risk package: `risk-threat-modeling` -> `enterprise-risk-assessment` -> `compliance-mapping` -> `cyber-insurance`
- Regulatory gap response: `regulatory-horizon` -> `compliance-mapping` -> `enterprise-risk-assessment` -> `internal-audit-assurance`
- New processing activity: `privacy-dpia` -> `compliance-mapping` -> `enterprise-risk-assessment`

---

## Quick Commands

Run any skill tool directly from the repository root. All tools accept `--help` and `--output json` for structured output.

**enterprise-risk-assessment**
```bash
python risk-compliance/enterprise-risk-assessment/scripts/enterprise-risk-assessment_tool.py --help
python risk-compliance/enterprise-risk-assessment/scripts/enterprise-risk-assessment_tool.py --scope enterprise --risk-appetite board-approved-2024 --output json
```

**risk-threat-modeling**
```bash
python risk-compliance/risk-threat-modeling/scripts/risk-threat-modeling_tool.py --help
python risk-compliance/risk-threat-modeling/scripts/risk-threat-modeling_tool.py --model payment-service-dfd-v3 --methodology stride --output json
```

**compliance-mapping**
```bash
python risk-compliance/compliance-mapping/scripts/compliance-mapping_tool.py --help
python risk-compliance/compliance-mapping/scripts/compliance-mapping_tool.py --frameworks gdpr,pci-dss,iso27001 --control-inventory current --output json
```

**regulatory-horizon**
```bash
python risk-compliance/regulatory-horizon/scripts/regulatory-horizon_tool.py --help
python risk-compliance/regulatory-horizon/scripts/regulatory-horizon_tool.py --region eu,us --sector financial --lookahead-days 180 --output json
```

**privacy-dpia**
```bash
python risk-compliance/privacy-dpia/scripts/privacy-dpia_tool.py --help
python risk-compliance/privacy-dpia/scripts/privacy-dpia_tool.py --processing-activity customer-analytics --data-categories personal,behavioral --output json
```

**cyber-insurance**
```bash
python risk-compliance/cyber-insurance/scripts/cyber-insurance_tool.py --help
python risk-compliance/cyber-insurance/scripts/cyber-insurance_tool.py --policy current --scenario-set ransomware,data-breach,cloud-outage --output json
```

**internal-audit-assurance**
```bash
python risk-compliance/internal-audit-assurance/scripts/internal-audit-assurance_tool.py --help
python risk-compliance/internal-audit-assurance/scripts/internal-audit-assurance_tool.py --framework soc2 --control-domain security --period 2024-q4 --output json
```

**quantum-security-readiness**
```bash
python risk-compliance/quantum-security-readiness/scripts/quantum-security-readiness_tool.py --help
python risk-compliance/quantum-security-readiness/scripts/quantum-security-readiness_tool.py --scope enterprise --nist-pqc-set fips203,fips204,fips205 --output json
```

---

## Full Domain Guide

For complete methodology, cross-skill workflow patterns, the Regulatory Framework Coverage matrix, Domain Best Practices, Python tools reference, and workflow documentation, see [CLAUDE.md](./CLAUDE.md).
