# Identity & Access Domain

Skills in this domain detect IAM anomalies, assess privilege escalation risk, and classify data sensitivity.

## Skills

| Slug | Level | Description |
|---|---|---|
| `identity-access-risk` | L4 | IAM anomaly detection, privilege escalation analysis, CloudTrail pattern matching (5 patterns) |
| `data-security-classification` | L3 | Classifies data assets by sensitivity, maps to regulatory requirements, recommends controls |
| `cryptography-key-management` | L3 | Assesses cryptographic key lifecycle risk: weak algorithms, key rotation gaps, HSM gaps |
| `insider-physical-risk` | L3 | Insider threat and physical security risk assessment combining behavioral and physical indicators |

## Workflow: Identity Risk Assessment

```
behavioral-analytics → identity-access-risk → data-security-classification → compliance-mapping
```

## IAM Anomaly Patterns

1. Root account usage outside maintenance windows
2. IAM role assumption from unexpected geographic region
3. Bulk permission grants to service accounts
4. Privilege escalation via policy attachment
5. Access key creation for dormant accounts

## Data Classification Levels

| Level | Name | Examples |
|---|---|---|
| L1 | Public | Marketing materials, open-source code |
| L2 | Internal | Internal wikis, meeting notes |
| L3 | Confidential | Customer PII, financial data |
| L4 | Restricted | Cryptographic keys, credentials, board materials |

## Related Domains

- [Detection](detection.md) — behavioral-analytics feeds identity risk
- [Response](response.md) — identity incidents escalate to incident-commander
- [Risk & Compliance](risk-compliance.md) — identity findings map to compliance frameworks
