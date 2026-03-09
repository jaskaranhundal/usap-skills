# Identity & Access Security Domain

Four skill packages covering IAM risk detection, data security classification, cryptographic key lifecycle management, and insider/physical threat assessment. All skills are read-only analyzers. Credential revocation, account disablement, and key rotation actions require explicit human approval.

---

## Skills

| Skill | Slug | Level | Intent | Description |
|---|---|---|---|---|
| [Identity Access Risk](identity-access-risk/SKILL.md) | `identity-access-risk` | L4 | `read_only` | IAM anomaly detection across AWS, Azure, and GCP. Identifies five privilege escalation patterns, over-permissioned roles, and dormant credential risks using CloudTrail and equivalent audit logs. |
| [Data Security Classification](data-security-classification/SKILL.md) | `data-security-classification` | L3 | `read_only` | Classifies data assets by sensitivity level (L1 Public through L4 Restricted). Maps findings to GDPR, HIPAA, PCI DSS, and SOC 2 control requirements. Recommends DLP controls by classification level. |
| [Cryptography Key Management](cryptography-key-management/SKILL.md) | `cryptography-key-management` | L3 | `read_only` | Assesses cryptographic key lifecycle health: weak algorithm detection, key rotation age, HSM coverage gaps, certificate expiry windows. Covers AWS KMS, Azure Key Vault, GCP Cloud KMS, and on-premises PKI. |
| [Insider Physical Risk](insider-physical-risk/SKILL.md) | `insider-physical-risk` | L3 | `read_only` | UEBA-driven insider threat scoring combining digital behavioral indicators with physical access anomalies. Produces per-entity risk scores and recommended review actions for human approval. |

---

## Agent Links

No dedicated orchestrator agent exists for this domain. The primary agent that uses identity-access skills is the [cs-security-analyst](../agents/security/cs-security-analyst.md), which incorporates `identity-access-risk` and `insider-physical-risk` into Tier 2 SOC workflows when investigating alerts involving credential anomalies, privilege escalation, or account manipulation.

Typical orchestration patterns:

- Credential alert from SIEM: `identity-access-risk` -> `data-security-classification` (scope blast radius) -> `cryptography-key-management` (assess key exposure)
- UEBA anomaly: `insider-physical-risk` -> `identity-access-risk` (privilege check on flagged entity)
- Cloud posture cascade: `cloud-infra/cloud-security-posture` -> `identity-access-risk` -> `compliance-mapping`

---

## Quick Commands

Run any skill tool directly from the repository root. All tools accept `--help` and `--output json` for structured output.

**identity-access-risk**
```bash
python identity-access/identity-access-risk/scripts/identity-access-risk_tool.py --help

# AWS account IAM risk scan, 7-day lookback
python identity-access/identity-access-risk/scripts/identity-access-risk_tool.py \
  --account-id 123456789012 --lookback-days 7 --provider aws --output json

# Azure Entra ID scan
python identity-access/identity-access-risk/scripts/identity-access-risk_tool.py \
  --provider azure --lookback-days 14 --output json
```

**data-security-classification**
```bash
python identity-access/data-security-classification/scripts/data-security-classification_tool.py --help

# Classify all cloud storage with GDPR and HIPAA framework mapping
python identity-access/data-security-classification/scripts/data-security-classification_tool.py \
  --scope cloud-storage --regulatory-framework gdpr,hipaa --output json

# Full scope scan with PCI DSS mapping
python identity-access/data-security-classification/scripts/data-security-classification_tool.py \
  --scope all --regulatory-framework pci-dss --output json
```

**cryptography-key-management**
```bash
python identity-access/cryptography-key-management/scripts/cryptography-key-management_tool.py --help

# AWS KMS key rotation audit
python identity-access/cryptography-key-management/scripts/cryptography-key-management_tool.py \
  --provider aws --key-store kms --rotation-threshold-days 90 --output json

# On-premises PKI and HSM assessment
python identity-access/cryptography-key-management/scripts/cryptography-key-management_tool.py \
  --provider on-prem --key-store pki --rotation-threshold-days 365 --output json
```

**insider-physical-risk**
```bash
python identity-access/insider-physical-risk/scripts/insider-physical-risk_tool.py --help

# Score all privileged entities against 30-day baseline
python identity-access/insider-physical-risk/scripts/insider-physical-risk_tool.py \
  --baseline-days 30 --risk-threshold 75 --output json

# Score a specific entity with physical access data included
python identity-access/insider-physical-risk/scripts/insider-physical-risk_tool.py \
  --entity jsmith --baseline-days 30 --risk-threshold 60 --include-physical true --output json
```

---

## Cross-Skill Workflow: IAM Risk Assessment

```
insider-physical-risk  →  identity-access-risk  →  data-security-classification  →  cryptography-key-management
```

1. `insider-physical-risk` establishes behavioral risk scores for all privileged entities.
2. `identity-access-risk` analyzes IAM configurations and audit logs for escalation patterns, applying elevated scrutiny to high-risk entities from Step 1.
3. `data-security-classification` scopes the maximum data exposure for over-permissioned or anomalous principals.
4. `cryptography-key-management` assesses key lifecycle risk for all cryptographic stores protecting data identified in Step 3.
5. All findings flow to `findings-tracker`, `compliance-mapping`, and `security-posture-score`.

---

## IAM Anomaly Patterns Detected

| Pattern | Technique | Severity |
|---|---|---|
| Root account usage outside maintenance window | T1078 | Critical |
| Role assumption chain to elevated trust boundary | T1078.004, T1098 | High-Critical |
| Bulk permission grant to service accounts | T1098.001 | High |
| Policy attachment by unprivileged principal | T1098 | Critical |
| Access key creation for dormant accounts | T1098 | High |

---

## Data Classification Levels

| Level | Name | Examples | DLP Baseline |
|---|---|---|---|
| L1 | Public | Marketing materials, open-source code | No restrictions |
| L2 | Internal | Internal wikis, meeting notes, runbooks | Access logging recommended |
| L3 | Confidential | Customer PII, financial records, HR data | MFA required, audit logging mandatory |
| L4 | Restricted | Cryptographic key material, board materials, credentials | HSM backing, explicit deny rules, JIT access |

---

## Downstream Integrations

| Finding Type | Cascades To |
|---|---|
| Root account usage | `incident-commander` (SEV1 immediate) |
| Privilege escalation confirmed | `incident-commander`, `containment-advisor` |
| L3/L4 data exposure scoped | `compliance-mapping`, `ciso-brief-generator` |
| Key rotation overdue (>90 days) | `findings-tracker`, `compliance-mapping` |
| Insider risk score above threshold | `behavioral-analytics` (corroboration), human security engineer review |
| IAM wildcard policy detected | `vulnerability-management`, `security-posture-score` |

---

## Full Domain Guide

For complete methodology, cross-skill workflow patterns, MITRE ATT&CK technique coverage tables, Python tools reference, privilege escalation pattern details, cloud IAM coverage matrix, and domain best practices, see [CLAUDE.md](./CLAUDE.md).
