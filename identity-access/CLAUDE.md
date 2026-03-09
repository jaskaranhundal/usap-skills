# Identity & Access Security Domain — CLAUDE.md

This file is the authoritative domain guide for the `identity-access/` skill directory in the USAP skills repository. It documents all skills in this domain, their tooling, coverage scope, inter-skill workflows, domain best practices, and MITRE ATT&CK technique coverage.

---

## Purpose

The `identity-access/` domain contains skills for assessing, detecting, and managing risk across the full identity and access lifecycle. Skills in this domain address IAM anomaly detection, privilege escalation analysis, data sensitivity classification, cryptographic key lifecycle management, and insider/physical threat assessment.

Subdomains covered:

- Identity and access risk (IAM anomalies, privilege escalation, CloudTrail behavioral analysis)
- Data security classification (DLP posture, sensitivity labeling, regulatory mapping)
- Cryptography and key management (PKI assessment, key rotation gaps, HSM coverage, algorithm risk)
- Insider and physical threat (UEBA-driven insider risk, physical security posture, behavioral indicators)

All skills in this domain are `read_only` analysts. They query, score, correlate, and produce structured recommendations. Mutating actions — revoking credentials, disabling accounts, rotating keys — require explicit human approval gates. All skill outputs are structured payloads consumable by downstream detection, response, governance, and risk-compliance skills.

---

## Skills Catalog

| Skill | Slug | Primary Tool | Coverage |
|---|---|---|---|
| identity-access-risk | `identity-access/identity-access-risk` | `identity-access-risk_tool.py` | IAM risk scoring, CloudTrail anomaly detection, privilege escalation patterns, over-permissioned roles |
| data-security-classification | `identity-access/data-security-classification` | `data-security-classification_tool.py` | DLP posture, data classification (L1-L4), sensitivity labeling, regulatory control mapping |
| cryptography-key-management | `identity-access/cryptography-key-management` | `cryptography-key-management_tool.py` | PKI health, key rotation compliance, HSM coverage gaps, weak algorithm detection |
| insider-physical-risk | `identity-access/insider-physical-risk` | `insider-physical-risk_tool.py` | UEBA-driven insider threat scoring, physical access anomalies, privileged user behavioral indicators |

All skill paths are relative from the repository root as `identity-access/<slug>/`. For example, the identity-access-risk skill lives at `identity-access/identity-access-risk/`.

---

## Python Tools Reference

| Tool | Path | Purpose | Key Args |
|---|---|---|---|
| `identity-access-risk_tool.py` | `identity-access/identity-access-risk/scripts/identity-access-risk_tool.py` | IAM anomaly detection, privilege escalation scoring, CloudTrail pattern matching (5 patterns), over-permissioned role analysis | `--account-id`, `--lookback-days`, `--provider aws\|azure\|gcp`, `--output` |
| `data-security-classification_tool.py` | `identity-access/data-security-classification/scripts/data-security-classification_tool.py` | Classifies data assets by sensitivity level (L1-L4), maps to GDPR/HIPAA/PCI DSS/SOC 2, recommends DLP controls | `--scope`, `--regulatory-framework`, `--output` |
| `cryptography-key-management_tool.py` | `identity-access/cryptography-key-management/scripts/cryptography-key-management_tool.py` | Assesses cryptographic key lifecycle: weak algorithms, key rotation age, HSM coverage gaps, certificate expiry | `--provider aws\|azure\|gcp\|on-prem`, `--key-store`, `--rotation-threshold-days`, `--output` |
| `insider-physical-risk_tool.py` | `identity-access/insider-physical-risk/scripts/insider-physical-risk_tool.py` | UEBA entity risk scoring for insider threat, physical access anomaly detection, privileged user behavioral baseline deviation | `--entity`, `--baseline-days`, `--risk-threshold`, `--include-physical`, `--output` |

All tools accept `--help` for full usage and `--output json` for machine-readable output.

```bash
# Quick invocation pattern for any tool in this domain
python identity-access/<slug>/scripts/<slug>_tool.py --help
python identity-access/<slug>/scripts/<slug>_tool.py --output json
```

---

## Cloud IAM Coverage Matrix

| Tool | AWS IAM | Azure AD / Entra ID | GCP IAM | On-Prem AD |
|---|---|---|---|---|
| `identity-access-risk_tool.py` | Full (CloudTrail, IAM Analyzer, Access Advisor) | Full (Sign-in logs, Entra ID audit, PIM) | Full (Cloud Audit Logs, IAM recommender) | Partial (AD event log patterns, GPO analysis) |
| `data-security-classification_tool.py` | Full (S3 Macie integration, Lake Formation labels) | Full (Azure Purview, Information Protection) | Partial (DLP API, BigQuery metadata) | Full (file server classification, SharePoint) |
| `cryptography-key-management_tool.py` | Full (KMS, ACM, Secrets Manager rotation) | Full (Key Vault, certificate lifecycle) | Full (Cloud KMS, Secret Manager) | Full (on-prem PKI, AD CS, HSM via PKCS#11) |
| `insider-physical-risk_tool.py` | Partial (CloudTrail behavioral, no physical) | Partial (Entra sign-in risk, no physical) | Partial (Cloud audit behavioral, no physical) | Full (AD logon patterns, physical badge data) |

**Coverage levels:**
- Full: All provider-specific checks implemented with audit source integration
- Partial: Core behavioral checks implemented; provider-specific extensions or physical data integrations in progress
- Not applicable: Tool is out of scope for that environment type

---

## Privilege Escalation Patterns

This domain tracks five common IAM misconfigurations that enable privilege escalation. Each pattern includes detection signals used by `identity-access-risk_tool.py`.

### Pattern 1: Policy Attachment by Unprivileged Principal

**Description:** A principal without explicit administrative privileges attaches a managed or inline policy that grants elevated permissions to themselves or another principal.

**Detection signals:**
- CloudTrail event: `AttachUserPolicy`, `AttachRolePolicy`, or `PutUserPolicy` initiated by a non-admin principal
- The attached policy contains `iam:*` or `sts:AssumeRole` with `Resource: *`
- Event occurs outside a change management window or from an unexpected source IP

**Severity modifier:** Critical if the target principal has production access or access to cryptographic key stores.

---

### Pattern 2: Role Assumption Chain to Elevated Trust Boundary

**Description:** An attacker pivots through a chain of role assumptions (`sts:AssumeRole`) to reach a role with broader permissions than their starting identity, exploiting overly permissive trust policies.

**Detection signals:**
- CloudTrail sequence: multiple `AssumeRole` events within a short window (default: 10 minutes) from a single source identity
- Destination role in the chain has significantly higher privilege level than the originating principal
- Cross-account role assumption from an account not in the approved federation list

**Severity modifier:** High. Escalate to Critical if the destination role has IAM write or KMS key access.

---

### Pattern 3: Bulk Permission Grant to Service Accounts

**Description:** A large number of service accounts or programmatic principals receive new permission grants simultaneously, indicating a misconfiguration push, compromised automation pipeline, or insider action.

**Detection signals:**
- CloudTrail: five or more `AttachRolePolicy`, `PutRolePolicy`, or `CreatePolicyVersion` events within a 15-minute window affecting service account principals
- The granted permissions include data plane actions (`s3:GetObject`, `kms:Decrypt`, `secretsmanager:GetSecretValue`)
- Events originate from a CI/CD pipeline identity rather than a human admin

**Severity modifier:** High. Correlate with `data-security-classification` findings to assess data exposure scope.

---

### Pattern 4: Root Account Usage Outside Maintenance Window

**Description:** AWS root account credentials are used for console login or API calls outside of a defined maintenance window, indicating either a compromised root credential or a process control failure.

**Detection signals:**
- CloudTrail: `userIdentity.type = Root` in any event outside the defined maintenance window (default: none defined — every root event is flagged)
- MFA not present on the root account login event
- Source IP not in the organizational egress range

**Severity modifier:** Critical regardless of the action taken. Root credential usage is a P1 finding.

---

### Pattern 5: Access Key Creation for Dormant or Off-Boarded Accounts

**Description:** A new programmatic access key is created for a principal that has had no recorded activity for more than 90 days, or for a principal whose HR record indicates departure.

**Detection signals:**
- CloudTrail: `CreateAccessKey` event for a principal with no `GetCallerIdentity`, login, or data plane event in the preceding 90-day lookback window
- The key creation event is performed by a principal other than the key owner (administrative creation for a dormant account)
- No associated ticket or approved change record in the audit log

**Severity modifier:** High. Dormant accounts used for key issuance are a common persistence mechanism (T1098).

---

## Domain Best Practices

1. **Enforce least privilege at the role level, not the individual level.** Avoid attaching policies directly to IAM users. Role-based access control (RBAC) with time-bound role assumption reduces the blast radius of a compromised credential and provides a clean audit trail. Every direct user policy attachment is a finding until it is migrated to a role.

2. **Rotate access keys on a defined schedule regardless of usage.** Access keys that are never rotated become permanent credentials that survive employee offboarding, vendor relationship changes, and organizational restructuring. Set a maximum key age of 90 days and flag any key older than 60 days as a warning-level finding. Keys older than 90 days without documented exception are a High finding.

3. **Classify data before assigning access controls.** Access controls designed without data classification context produce over-permissioned roles by default. Run `data-security-classification` before designing any IAM policy for a new data store. L3 (Confidential) and L4 (Restricted) data stores require MFA-protected access, audit logging, and explicit deny rules as a baseline.

4. **Treat HSM gaps as a High finding for any L4 key material.** Cryptographic key material classified as L4 (root CA keys, code signing keys, data encryption master keys) that is stored in software-only key stores rather than HSMs is a High finding. HSM coverage is a control objective, not an advisory.

5. **Score insider threat risk before revoking access.** When `behavioral-analytics` or `insider-physical-risk` flags a high-risk entity, the structured risk score must be reviewed by a human before any account action is taken. False positives in UEBA systems affect legitimate employees. The skill produces a risk score and recommended action; a human security engineer makes the final call.

6. **Require MFA for all human identities accessing L3 and above data.** Service accounts are exempt from interactive MFA but must use short-lived tokens (maximum 12-hour lifetime). Human identities with standing access to any Confidential or Restricted data store without MFA enforcement is a Critical IAM control gap.

7. **Eliminate standing privilege; use just-in-time (JIT) access for privileged roles.** Permanent membership in privileged groups (Domain Admins, Organization Admin, Global Administrator) is acceptable only for break-glass accounts. All routine privileged access should be time-bound via PIM (Azure AD), AWS IAM Identity Center, or equivalent. Every standing privileged account without JIT enforcement is a Medium finding and a target for insider and external threat actors.

8. **Cross-reference data classification findings with IAM access grants quarterly.** As data classification levels change, the access control boundaries must change with them. A quarterly reconciliation between `data-security-classification` outputs and `identity-access-risk` IAM grant analysis identifies access creep: principals who retain access to data they no longer require. Access creep is the leading cause of excessive blast radius during a credential compromise.

---

## Workflow: IAM Risk Assessment

This cross-skill workflow represents a complete identity risk assessment cycle. It connects all four skills in this domain and feeds structured output to downstream response and compliance consumers.

```
insider-physical-risk   →   identity-access-risk   →   data-security-classification   →   cryptography-key-management
```

### Step-by-Step

**Step 1 — Baseline Behavioral Risk (insider-physical-risk)**

Trigger: Scheduled weekly assessment or alert from UEBA/SIEM on entity anomaly.

Action: Score all privileged entities against behavioral baselines for the past 30 days. Flag entities with a risk score above threshold (default: 75). Identify after-hours access patterns, unusual data volume downloads, or physical access to restricted zones outside normal patterns. Pass high-risk entity list to Step 2 as scope context.

```bash
python identity-access/insider-physical-risk/scripts/insider-physical-risk_tool.py \
  --baseline-days 30 --risk-threshold 75 --include-physical true --output json
```

**Step 2 — IAM Anomaly and Privilege Escalation Scan (identity-access-risk)**

Trigger: Completion of Step 1, deployment event, or scheduled daily scan.

Action: Analyze IAM configurations and CloudTrail events for the five privilege escalation patterns. Apply elevated scrutiny to entities flagged in Step 1. Score all IAM principals for over-permissioning using Access Advisor or equivalent. Cascade Critical findings (root usage, escalation chain, dormant key creation) to `incident-commander` immediately.

```bash
python identity-access/identity-access-risk/scripts/identity-access-risk_tool.py \
  --account-id 123456789012 --lookback-days 7 --provider aws --output json
```

**Step 3 — Data Exposure Scope (data-security-classification)**

Trigger: Completion of Step 2 or new data store provisioned.

Action: Classify all data stores accessible by the over-permissioned or anomalous principals identified in Step 2. Quantify the maximum data exposure scope by classification level. Map findings to applicable regulatory frameworks (GDPR, HIPAA, PCI DSS). Output a data exposure impact matrix.

```bash
python identity-access/data-security-classification/scripts/data-security-classification_tool.py \
  --scope cloud-storage --regulatory-framework gdpr,hipaa --output json
```

**Step 4 — Cryptographic Key Risk (cryptography-key-management)**

Trigger: Completion of Step 3 or key rotation policy audit.

Action: Assess the cryptographic key lifecycle for all key stores protecting L3 and L4 data identified in Step 3. Flag overdue rotations, weak algorithms (RSA < 2048-bit, DES, MD5 signing), missing HSM backing, and expiring certificates within a 30-day window. Produce a key risk register.

```bash
python identity-access/cryptography-key-management/scripts/cryptography-key-management_tool.py \
  --provider aws --key-store kms --rotation-threshold-days 90 --output json
```

**Step 5 — Aggregate and Report**

Downstream: All findings from Steps 1-4 flow to `findings-tracker`. `compliance-mapping` generates framework-specific evidence. `security-posture-score` rolls up domain IAM posture for executive reporting via `ciso-brief-generator`.

---

## MITRE ATT&CK Technique Coverage

| Technique | ID | Description | Covering Skills |
|---|---|---|---|
| Valid Accounts | T1078 | Use of legitimate credentials for unauthorized access | identity-access-risk, insider-physical-risk |
| Create Account | T1136 | Creation of new accounts to establish persistence | identity-access-risk |
| Account Manipulation | T1098 | Modification of account settings, group membership, or credentials | identity-access-risk |
| Unsecured Credentials | T1552 | Credentials stored in accessible locations (files, environment variables, key stores) | cryptography-key-management, data-security-classification |
| Steal Application Access Token | T1528 | Stealing OAuth tokens, API keys, or cloud access tokens | identity-access-risk, cryptography-key-management |

Specific sub-technique coverage:

| Sub-Technique | ID | Covering Skill |
|---|---|---|
| Valid Accounts — Cloud Accounts | T1078.004 | identity-access-risk |
| Valid Accounts — Domain Accounts | T1078.002 | insider-physical-risk, identity-access-risk |
| Account Manipulation — Additional Cloud Credentials | T1098.001 | identity-access-risk |
| Account Manipulation — SSH Authorized Keys | T1098.004 | cryptography-key-management |
| Credentials in Files | T1552.001 | cryptography-key-management |
| Private Keys | T1552.004 | cryptography-key-management |

---

## Related Domains

### detection/

Skills in `detection/` are the primary behavioral data source for this domain's insider threat and anomaly analysis:

- `detection/behavioral-analytics` — UEBA entity risk scores feed `insider-physical-risk` as primary behavioral signal. The structured risk payload from `insider-physical-risk` is the authoritative insider threat score consumed by `detection/behavioral-analytics` for alert correlation.
- `detection/secrets-exposure` — exposed credential findings from `secrets-exposure` cascade to `identity-access-risk` for IAM impact scoping and `cryptography-key-management` for key revocation planning.
- `detection/threat-hunting` — hunt findings involving credential theft or account manipulation (T1078, T1098, T1552) trigger a full IAM Risk Assessment workflow.

Full domain reference: `detection/CLAUDE.md`

### cloud-infra/

Skills in `cloud-infra/` are a primary source of IAM findings that cascade into this domain:

- `cloud-infra/cloud-security-posture` cascades IAM wildcard policy findings and over-permissioned role detections to `identity-access-risk` for full principal risk scoring.
- `cloud-infra/endpoint-os-security` cascades local admin proliferation findings and Credential Guard gap findings to `identity-access-risk` and `cryptography-key-management` for on-premises identity risk assessment.
- `identity-access-risk` output feeds back to `cloud-infra/cloud-security-posture` to annotate CSPM findings with the full identity risk context of each misconfigured resource's owner.

Full domain reference: `cloud-infra/CLAUDE.md`

---

## Path Reference

All skill paths in this domain are relative from the repository root using the convention `identity-access/<slug>/`. Sub-paths within each skill follow the standard USAP skill layout:

```
identity-access/<slug>/
  README.md          -- skill overview and quick commands
  SKILL.md           -- full skill specification and methodology
  scripts/           -- executable Python tools
  references/        -- supporting documentation
  expected_outputs/  -- representative tool outputs for validation
  assets/            -- supporting data files
```

To invoke any tool directly from the repository root:

```bash
python identity-access/<slug>/scripts/<tool>.py --help
```

Examples:

```bash
python identity-access/identity-access-risk/scripts/identity-access-risk_tool.py \
  --account-id 123456789012 --lookback-days 7 --provider aws --output json

python identity-access/data-security-classification/scripts/data-security-classification_tool.py \
  --scope all --regulatory-framework gdpr --output json

python identity-access/cryptography-key-management/scripts/cryptography-key-management_tool.py \
  --provider aws --key-store kms --rotation-threshold-days 90 --output json

python identity-access/insider-physical-risk/scripts/insider-physical-risk_tool.py \
  --entity jsmith --baseline-days 30 --risk-threshold 75 --output json
```

---

## Authoring Notes

When adding a new skill to this domain:

1. Place the skill directory under `identity-access/<slug>/`.
2. Follow the domain Python tool naming convention: `<slug>_tool.py` in `scripts/`.
3. Update this CLAUDE.md Skills Catalog table and Cloud IAM Coverage Matrix.
4. Update the root `README.md` Domain Index table entry for `Identity & Access`.
5. Update `domains/identity-access.md` with the new skill slug and level.
6. Ensure all MITRE ATT&CK technique mappings relevant to the new skill are added to the coverage section above.
7. Confirm cascade rules to and from `detection/` and `cloud-infra/` are documented.
