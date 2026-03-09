---
name: ai-ethics-governance
description: USAP agent skill for AI Ethics & Governance. Use for Govern ethical use and explainability of AI decisions.
license: MIT
metadata:
  version: 1.0.0
  author: USAP Team
  category: usap-executive
  updated: 2026-02-28
  agent_slug: "ai-ethics-governance"
---

# AI Ethics & Governance

## Overview

This skill governs the ethical use, transparency, and regulatory compliance of AI systems
deployed across USAP-managed environments. It operates at the L2 management plane, bridging
technical AI governance controls with executive policy requirements. The agent performs
read-only assessments of AI system behavior, fairness metrics, and documentation completeness.
Mutating actions — including AI system suspension or policy-level changes to permitted AI use
cases — require explicit human approval and are classified as `mutating/policy_change`.

## Keywords

- usap
- security-agent
- mcp
- approval-gated
- evidence-chain
- executive

## Quick Start

```bash
python scripts/ai-ethics-governance_tool.py --help
python scripts/ai-ethics-governance_tool.py --output json
```

## Governance Domain Map

### 1. Algorithmic Bias Detection

Algorithmic bias is a systematic and repeatable error in AI outputs that creates unfair outcomes
for individuals or groups sharing a protected characteristic (race, gender, age, disability,
national origin, and others depending on jurisdiction).

This agent evaluates bias across three measurement dimensions:

**Outcome fairness metrics:**
- Demographic parity: P(Y=1 | A=0) = P(Y=1 | A=1) across protected group A
- Equalized odds: equal true positive and false positive rates across groups
- Individual fairness: similar individuals receive similar predictions

**Process fairness:**
- Protected attribute exclusion verification — direct and proxy variable analysis
- Training data representativeness audit against known population distributions

**Impact assessment:**
- Disparate impact ratio: adverse outcome rate for disadvantaged group / advantaged group
  (legal threshold: less than 0.8 constitutes prima facie discrimination in US employment law)

Detection signals: statistical parity differences exceeding configured tolerance thresholds,
proxy variable detection through mutual information analysis of input features.

### 2. Fairness Metrics Framework

This agent maintains and evaluates the following fairness metrics for each registered AI system:

| Metric | Formula | Acceptable Threshold |
|---|---|---|
| Demographic Parity Difference | P(pos|A=0) - P(pos|A=1) | <= 0.05 |
| Equalized Odds Difference | max(TPR diff, FPR diff) | <= 0.05 |
| Disparate Impact Ratio | P(pos|A=0) / P(pos|A=1) | >= 0.80 |
| Calibration Error | max E[Y-hat - Y|A] across groups | <= 0.02 |

Metrics are computed per model version, per deployment environment, and per protected attribute
class. Results are persisted as time-series evidence for regulatory audit.

### 3. Explainability Requirements

High-risk AI systems must provide human-intelligible explanations for decisions affecting
individuals. This agent verifies compliance with explainability requirements:

**SHAP/LIME integration check**: model endpoints must expose a `/explain` interface or
equivalent side-channel producing feature attribution scores.

**Right to explanation**: any decision made about an individual must be explainable in plain
language within 72 hours of request (EU AI Act Article 13, GDPR Article 22).

**Counterfactual explanations**: systems making adverse decisions must be capable of generating
"what would need to change for a different outcome" responses.

This agent audits explanation quality using:
- Faithfulness: do explanations accurately reflect model internals, not post-hoc rationalizations
- Consistency: same input produces same explanation across invocations
- Completeness: explanation covers all features with material contribution (contribution > 1%)

### 4. Model Transparency

Model cards are mandatory documentation artifacts for every AI system in USAP scope. This agent
validates model card completeness against the following required sections:

- Model details: architecture, training approach, version, contact
- Intended uses and out-of-scope uses explicitly documented
- Training data: sources, collection methodology, preprocessing steps
- Evaluation results: performance metrics across demographic subgroups
- Ethical considerations: known limitations, potential harms, mitigation measures
- Caveats and recommendations: deployment constraints and monitoring requirements

Missing or stale model cards (last updated > 90 days before last model version change) generate
a HIGH severity finding requiring remediation before next deployment.

### 5. EU AI Act Compliance

The EU AI Act (Regulation (EU) 2024/1689) establishes a risk-tiered regulatory framework for AI
systems. This agent classifies systems into the appropriate tier and enforces corresponding
obligations.

**Prohibited AI practices** (Article 5 — blanket prohibition):
- Real-time remote biometric identification in public spaces by law enforcement (with exceptions)
- Social scoring systems by public authorities
- Manipulation using subliminal techniques
- Exploitation of vulnerabilities of specific groups

**High-risk AI systems** (Annex III — mandatory conformity assessment):
- Biometric categorization and identification systems
- Critical infrastructure management
- Education and vocational training access
- Employment and workforce management
- Essential private and public services access
- Law enforcement, migration, and border control
- Administration of justice

High-risk system obligations enforced by this agent:
- Conformity assessment completed before deployment
- Technical documentation maintained and current
- Automatic event logging for traceability
- Human oversight measures implemented and tested
- Accuracy, robustness, and cybersecurity requirements met
- Post-market monitoring plan in place

**GPAI Model obligations** (Chapter V):
- Models with systemic risk (>10^25 FLOPs training compute) require additional evaluation
  including adversarial testing and incident reporting

### 6. Responsible AI Framework

This agent maps AI system assessments to the organization's internal Responsible AI principles:

- **Fairness**: AI systems treat all individuals and groups equitably
- **Reliability and Safety**: AI systems perform reliably within defined operational parameters
- **Privacy and Security**: AI systems protect personal data and resist adversarial manipulation
- **Inclusiveness**: AI systems are designed to benefit all users, including those with disabilities
- **Transparency**: stakeholders understand AI system capabilities, limitations, and decisions
- **Accountability**: clear human ownership exists for every AI system in production

Each principle maps to measurable controls assessed on a quarterly basis.

### 7. High-Risk AI System Classification Workflow

When a new AI system is proposed for deployment, this agent executes the following classification
workflow:

1. Collect system description, intended use case, affected population, and deployment context
2. Apply EU AI Act Annex III checklist — any match triggers high-risk designation
3. Apply NIST AI RMF (AI 100-1) risk framing: Govern, Map, Measure, Manage
4. Generate risk tier assignment with supporting rationale
5. Emit required governance artifacts: model card template, conformity assessment checklist,
   human oversight plan
6. Block deployment pathway until all required artifacts are complete and approved

### 8. Human Oversight Requirements

Automated AI decisions in high-risk domains must include meaningful human oversight. This agent
enforces:

- **Human-in-the-loop**: human reviews every individual AI decision before it takes effect
- **Human-on-the-loop**: human monitors AI decisions in real time with ability to intervene
- **Human-in-command**: human retains ability to shut down the AI system at any time

Oversight tier assignment is based on risk classification and consequence severity of incorrect
decisions. The agent monitors override rates — if humans override AI decisions at a rate above
30%, this triggers a model performance review.

## Intent and Action Classification

| Action Type | Classification | Approval Required |
|---|---|---|
| Compute fairness metrics for a model | read_only | No |
| Audit model card completeness | read_only | No |
| Classify AI system risk tier | read_only | No |
| Generate EU AI Act compliance report | read_only | No |
| Flag high-risk system for review | read_only | No |
| Suspend an AI system from production | mutating/policy_change | Yes |
| Change AI system risk tier designation | mutating/policy_change | Yes |
| Enforce mandatory retraining | mutating/policy_change | Yes |

## Core Workflows

1. Validate input context and required fields.
2. Apply deterministic and policy-aligned reasoning for agent ai-ethics-governance.
3. Emit structured recommendation payloads for orchestrator processing.
4. Enforce human approval gates for mutating actions.

## Evidence Chain Requirements

Every governance finding must include:

- `system_id`: registered AI system identifier
- `model_version`: semantic version of evaluated model
- `assessment_date`: ISO 8601 UTC
- `risk_tier`: prohibited | high-risk | limited-risk | minimal-risk | gpai
- `fairness_metrics`: computed metric table with values and pass/fail status
- `compliance_gaps`: list of unmet obligations with regulatory citation
- `recommended_action`: action slug from classification table
- `approval_status`: `pending` | `approved` | `rejected`

## Script Reference

- `scripts/ai-ethics-governance_tool.py`: CLI helper with --help and JSON output.

## Validation Checklist

- [ ] SKILL.md frontmatter is valid
- [ ] Script runs with --help
- [ ] references/ has at least one guide
- [ ] expected_outputs/ contains representative output
- [ ] Runtime contract link points to ../../agents/ai-ethics-governance.yaml

## Runtime Contract

- ../../agents/ai-ethics-governance.yaml
