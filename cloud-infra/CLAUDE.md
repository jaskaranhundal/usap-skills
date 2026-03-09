# Cloud Infrastructure Security Domain — CLAUDE.md

This file is the authoritative domain guide for the `cloud-infra/` skill directory in the USAP skills repository. It documents all skills in this domain, their tooling, coverage scope, inter-skill workflows, domain best practices, and MITRE ATT&CK cloud matrix coverage.

---

## Purpose

The `cloud-infra/` domain addresses security across five interconnected coverage areas:

- **Cloud Security Posture (CSPM)**: Continuous evaluation of cloud resource configurations against CIS Benchmarks across AWS, Azure, and GCP. Detects misconfigurations, drift from known-good baselines, and maps findings to compliance frameworks (SOC 2, PCI DSS, HIPAA, NIST 800-53).
- **Infrastructure-as-Code (IaC) Security**: Static analysis of Terraform, CloudFormation, Pulumi, and Helm charts before deployment. Enforces security gates in CI/CD pipelines so misconfigurations are caught in code review, not in production.
- **Endpoint and OS Security**: Hardening assessment and EDR coverage evaluation for Windows, Linux, macOS, and containerized endpoints. Operates against CIS OS Benchmarks and DISA STIG standards.
- **OT/IoT Device Security**: Security posture assessment for operational technology, industrial control systems (ICS/SCADA), and IoT devices. Applies NIST SP 800-82, IEC 62443, NERC CIP, and the Purdue Enterprise Reference Architecture. Availability and safety take priority over confidentiality in this domain.
- **Cloud Workload Protection (CWPP)**: Runtime security for containers and serverless functions. Detects container escape indicators, anomalous process behavior in pods, serverless permission sprawl, and CWPP tool coverage gaps. Complements cloud-security-posture with a runtime focus.

All five skills are `read_only` for discovery and analysis. Configuration changes, remediation actions, and OT network changes are `mutating` and require explicit human approval. OT environment changes additionally require safety review and operations director co-approval.

---

## Skills Catalog

| Skill | Slug | Primary Tool | Coverage |
|---|---|---|---|
| Cloud Security Posture | `cloud-infra/cloud-security-posture` | `cloud-security-posture_tool.py` | CIS Benchmarks (AWS/Azure/GCP), CSPM, drift detection, compliance mapping |
| IaC Security | `cloud-infra/iac-security` | `iac-security_tool.py` | Terraform/CloudFormation misconfigs, Kubernetes RBAC, Helm hardening, CI/CD gate policy |
| Endpoint & OS Security | `cloud-infra/endpoint-os-security` | `endpoint-os-security_tool.py` | CIS OS Benchmarks, DISA STIG, EDR coverage, Windows/Linux/macOS hardening |
| OT/IoT Device Security | `cloud-infra/ot-iot-device-security` | `ot-iot-device-security_tool.py` | ICS/SCADA, NIST SP 800-82, IEC 62443, NERC CIP, Purdue Model, IoT baseline |
| Cloud Workload Protection | `cloud-infra/cloud-workload-protection` | `cloud-workload-protection_tool.py` | CWPP, container runtime security, serverless permission sprawl, escape detection |

---

## Python Tools Reference

| Tool | Location | Key Flags | Output |
|---|---|---|---|
| `cloud-security-posture_tool.py` | `cloud-security-posture/scripts/` | `--provider aws\|azure\|gcp`, `--account-id`, `--output json\|table` | CSPM findings with CIS check IDs, severity, compliance mapping, drift flag |
| `iac-security_tool.py` | `iac-security/scripts/` | `--target terraform\|cloudformation\|kubernetes\|helm`, `--dir`, `--output json` | Misconfiguration findings with `block_pr` flag, compliance score |
| `endpoint-os-security_tool.py` | `endpoint-os-security/scripts/` | `--os windows\|linux\|macos`, `--host`, `--output json` | Hardening score, EDR coverage status, CIS drift, patch priority matrix |
| `ot-iot-device-security_tool.py` | `ot-iot-device-security/scripts/` | `--zone 0-5`, `--env ot\|iot\|mixed`, `--output json` | Purdue zone risk assessment, segmentation gaps, compensating controls |
| `cloud-workload-protection_tool.py` | `cloud-workload-protection/scripts/` | `--target containers\|serverless`, `--cluster`, `--output json` | CWPP coverage gaps, runtime anomalies, escape indicators |

All tools accept `--help` for full usage and `--output json` for machine-readable output.

```bash
# Quick invocation pattern for any tool in this domain
python <skill>/scripts/<skill>_tool.py --help
python <skill>/scripts/<skill>_tool.py --output json
```

---

## Cloud Provider Coverage Matrix

| Tool | AWS | Azure | GCP | On-Prem |
|---|---|---|---|---|
| `cloud-security-posture_tool.py` | Full (20+ CIS checks) | Full (10+ CIS checks) | Full (10+ CIS checks) | Not applicable |
| `iac-security_tool.py` | Full (Terraform AWS provider, CloudFormation) | Partial (Terraform AzureRM) | Partial (Terraform Google) | On-prem Kubernetes |
| `endpoint-os-security_tool.py` | EC2 / ECS task (agent-based) | Azure VM / AKS node | GCE instance / GKE node | Physical and VM endpoints |
| `ot-iot-device-security_tool.py` | Not applicable | Not applicable | Not applicable | Full (all Purdue zones) |
| `cloud-workload-protection_tool.py` | EKS, Lambda, ECS Fargate | AKS, Azure Functions | GKE, Cloud Run | Self-hosted Kubernetes |

**Coverage levels:**
- Full: All provider-specific checks implemented with benchmark IDs
- Partial: Core checks implemented; provider-specific hardening extensions in progress
- Not applicable: Tool is out of scope for that environment type

---

## IaC Security Scanning

### Supported IaC Formats

| Format | Toolchain | Scanner Backend | Notes |
|---|---|---|---|
| Terraform (HCL) | All providers | Checkov, tfsec | Modules analyzed recursively |
| CloudFormation (JSON/YAML) | AWS | Checkov, cfn-nag | SAM templates included |
| Pulumi | AWS, Azure, GCP | Checkov (Pulumi mode) | Python and TypeScript supported |
| Kubernetes manifests | All | Trivy config, kube-bench | Includes Kustomize overlays |
| Helm charts | All | Trivy config | Values file substitution applied before scan |

### Check Categories

| Category | Description | Severity Range | CI/CD Gate |
|---|---|---|---|
| Public exposure | Resources publicly accessible without authentication | Critical | Block PR |
| IAM wildcard | `Action: *` with `Resource: *` in any policy | Critical | Block PR |
| Encryption at rest | Missing encryption configuration on storage, database, secrets | High | Block PR |
| Secret in IaC | Hardcoded credentials, API keys, certificates in HCL/YAML | Critical | Block PR |
| Network segmentation | SSH/RDP open to 0.0.0.0/0, unrestricted security groups | Critical–High | Block PR |
| Kubernetes pod security | `privileged: true`, `hostPID`, `allowPrivilegeEscalation` | Critical–High | Block PR |
| Kubernetes RBAC | Service accounts bound to `cluster-admin` | High | Block PR |
| Audit logging | CloudTrail, Azure Monitor, GCP Audit Logs disabled | High | Warn |
| Backup and versioning | Versioning disabled on object storage | Medium | Warn |
| Least privilege | Overly permissive RBAC, inline IAM policies | Medium | Warn |

### Automated Scanner Commands

```bash
# Checkov — Terraform and CloudFormation
checkov -d ./terraform --framework terraform --output json
checkov -d ./cloudformation --framework cloudformation --output json

# Trivy — Kubernetes manifests and Helm charts
trivy config ./kubernetes/ --format json --severity HIGH,CRITICAL
trivy config ./helm-chart/ --format json --severity HIGH,CRITICAL

# tfsec — Terraform focused
tfsec . --format json

# kube-bench — CIS Kubernetes Benchmark (run on cluster node)
kube-bench run --targets node,master --json
```

---

## Domain Best Practices

1. **Never scope a posture scan to a single region or account.** Cloud footprints span multiple regions, accounts, subscriptions, and projects. Cross-account S3 replication targets, VPC peering partners, and shared service accounts are all in scope. Single-region scans produce false confidence.

2. **Use configuration data no older than 24 hours for active posture assessments.** Stale scan data masks drift. Drift events (unauthorized configuration changes) are themselves a High finding and must be reported separately from the configuration state.

3. **Apply severity modifiers consistently.** Base severity from CIS Benchmarks is a starting point, not a final verdict. Internet-facing resources, production environment, and regulated data stores each warrant a severity upgrade. Verified compensating controls are the only valid basis for a severity downgrade.

4. **Shift IaC security left — block at PR, not at deployment.** The `iac-security` skill is most effective as a CI/CD gate. A Critical IaC finding that reaches production is five to ten times more expensive to remediate than one caught in a PR comment.

5. **Treat unauthorized drift as an independent finding.** A configuration change that has no associated change management ticket is a process violation regardless of whether the resulting configuration is secure. Log it, alert on it, and require a retrospective ticket.

6. **Maintain separate OT and IT security procedures.** Standard IT patching and hardening timelines do not apply to OT environments. In ICS/SCADA zones, availability and safety take priority over confidentiality. All recommendations for OT environments must include a compensating control path for cases where patching is not operationally feasible.

7. **Require co-approval for all OT environment changes.** Any mutating action in an OT environment requires three approvals: security engineer (originator), CISO, and operations director. Safety-critical systems additionally require a safety review before any change window opens. This is enforced in the `ot-iot-device-security` runtime contract.

8. **Measure CWPP coverage as a percentage.** A CWPP coverage gap — workloads running without a runtime protection agent — is a High finding when below 80% and a Critical finding when below 50% in production. Coverage percentage should be tracked as a domain KPI and reported in `security-posture-score`.

9. **Link cloud posture findings to IaC policies.** When the `cloud-security-posture` skill detects a misconfiguration that originates from a Terraform or CloudFormation resource, it cascades to the `iac-security` skill for policy-as-code rule creation. This prevents the same misconfiguration from reappearing after the next deployment.

10. **Document remediation commands; never auto-execute them.** All CLI remediation commands (AWS CLI, Azure CLI, `gsutil`, `kubectl`) are included in skill output as reference for human engineers. The skills in this domain are read-only analyzers — no skill autonomously modifies cloud resources, OS configurations, or OT systems.

---

## Workflow: Cloud Posture Assessment

This cross-skill workflow represents a complete infrastructure security assessment cycle. Each step may run independently or as part of the full sequence.

```
iac-security  →  cloud-security-posture  →  cloud-workload-protection  →  endpoint-os-security
```

### Step-by-Step

**Step 1 — IaC Security Gate (iac-security)**
Trigger: PR opened or IaC file changed in CI/CD pipeline.
Action: Scan Terraform, CloudFormation, Kubernetes manifests, and Helm charts for misconfigurations. Block the PR if any Critical finding (public S3, IAM wildcard, secret in code, SSH open to 0.0.0.0/0) is present. Cascade passing results with compliance score to `findings-tracker`.

```bash
python cloud-infra/iac-security/scripts/iac-security_tool.py \
  --target terraform --dir ./infrastructure --output json
```

**Step 2 — Cloud Posture Scan (cloud-security-posture)**
Trigger: Deployment event, daily scheduled scan, or IaC drift detected.
Action: Collect current cloud resource configurations for all accounts, subscriptions, and projects. Run all CIS Benchmark checks. Apply severity modifiers. Detect drift against last baseline. Map findings to CIS, NIST 800-53, SOC 2, PCI DSS, HIPAA. Cascade Critical production findings to the USAP orchestrator immediately.

```bash
python cloud-infra/cloud-security-posture/scripts/cloud-security-posture_tool.py \
  --provider aws --account-id 123456789012 --output json
```

**Step 3 — Workload Runtime Assessment (cloud-workload-protection)**
Trigger: Completion of Step 2 or new container workload deployed.
Action: Assess CWPP tool coverage across all pods and serverless functions. Detect runtime anomalies and container escape indicators. Evaluate Lambda/Function permission sprawl. Escalate container escape events to `incident-commander` (SEV1) immediately.

```bash
python cloud-infra/cloud-workload-protection/scripts/cloud-workload-protection_tool.py \
  --target containers --cluster prod-eks --output json
```

**Step 4 — Endpoint Hardening Check (endpoint-os-security)**
Trigger: Completion of Step 3 or new endpoint enrolled.
Action: Evaluate hardening baseline compliance (CIS Level 1/2, DISA STIG). Assess EDR coverage and alert on gaps. Identify missing patches by CVSS score and CISA KEV status. Produce patch priority matrix with SLA windows.

```bash
python cloud-infra/endpoint-os-security/scripts/endpoint-os-security_tool.py \
  --os linux --host prod-bastion-01 --output json
```

**Step 5 — OT Environment Assessment (ot-iot-device-security)** (if in scope)
Trigger: Scheduled quarterly OT assessment or OT incident.
Action: Map all Purdue model zones. Identify segmentation gaps in the IT/OT DMZ. Assess default credentials on IoT devices. Flag safety-system risks as Critical regardless of other severity modifiers. All recommended actions include compensating controls and require co-approval.

```bash
python cloud-infra/ot-iot-device-security/scripts/ot-iot-device-security_tool.py \
  --zone 3 --env ot --output json
```

**Step 6 — Aggregate and Report**
Downstream: `findings-tracker` aggregates all findings. `compliance-mapping` generates framework-specific evidence packages. `security-posture-score` rolls up the domain posture score for executive reporting via `ciso-brief-generator`.

---

## MITRE ATT&CK Cloud Matrix Coverage

The skills in this domain map to the MITRE ATT&CK Enterprise and ICS matrices as follows.

### Initial Access

| Technique | ID | Detecting Skill |
|---|---|---|
| Valid Accounts — Cloud | T1078.004 | cloud-security-posture (IAM anomaly → cascade to identity-access-risk) |
| Exploit Public-Facing Application | T1190 | cloud-security-posture (internet-facing resources), cloud-workload-protection |
| Drive-by Compromise (HMI) | T1817 (ICS) | ot-iot-device-security |
| Default Credentials (IoT) | T1812 (ICS) | ot-iot-device-security |

### Execution

| Technique | ID | Detecting Skill |
|---|---|---|
| Command and Scripting Interpreter — PowerShell | T1059.001 | endpoint-os-security (PS Script Block logging) |
| Container Administration Command | T1609 | cloud-workload-protection |
| Deploy Container | T1610 | cloud-workload-protection, iac-security |
| Modify Control Logic | T0833 (ICS) | ot-iot-device-security |

### Persistence

| Technique | ID | Detecting Skill |
|---|---|---|
| Valid Accounts — Cloud | T1078.004 | cloud-security-posture, cloud-workload-protection |
| Implant Container Image | T1525 | cloud-workload-protection (image scanning) |
| Registry Run Keys / Startup Folder | T1547.001 | endpoint-os-security |
| Scheduled Task/Job | T1053.005 | endpoint-os-security |

### Privilege Escalation

| Technique | ID | Detecting Skill |
|---|---|---|
| Abuse Elevation Control Mechanism | T1548 | endpoint-os-security |
| Container Escape | T1611 | cloud-workload-protection |
| Escape to Host | T1611 | cloud-workload-protection (privileged container detection) |
| Exploitation for Privilege Escalation | T1068 | endpoint-os-security (patch priority matrix) |

### Defense Evasion

| Technique | ID | Detecting Skill |
|---|---|---|
| Modify Cloud Compute Infrastructure | T1578 | cloud-security-posture (drift detection) |
| Impair Defenses — Disable Cloud Logs | T1562.008 | cloud-security-posture (CloudTrail / Azure Monitor checks) |
| Impair Defenses — Disable or Modify Tools | T1562.001 | endpoint-os-security (EDR agent offline detection) |

### Credential Access

| Technique | ID | Detecting Skill |
|---|---|---|
| OS Credential Dumping — LSASS | T1003.001 | endpoint-os-security (Credential Guard check) |
| Steal Application Access Token | T1528 | cloud-security-posture (IAM key rotation checks) |
| Forge Web Credentials | T1606 | cloud-security-posture (IAM policy analysis) |

### Discovery

| Technique | ID | Detecting Skill |
|---|---|---|
| Cloud Service Discovery | T1526 | cloud-security-posture |
| Cloud Infrastructure Discovery | T1580 | cloud-security-posture |
| Container and Resource Discovery | T1613 | cloud-workload-protection |
| Network Service Discovery (OT) | T0840 (ICS) | ot-iot-device-security |

### Lateral Movement

| Technique | ID | Detecting Skill |
|---|---|---|
| Use Alternate Authentication Material | T1550 | cloud-security-posture, endpoint-os-security |
| Lateral Tool Transfer | T1570 | endpoint-os-security |
| Remote Services — SSH | T1021.004 | endpoint-os-security, iac-security (SSH open check) |
| Lateral Movement — OT Network | T0812 (ICS) | ot-iot-device-security |

### Impact

| Technique | ID | Detecting Skill |
|---|---|---|
| Data Destruction | T1485 | cloud-security-posture (S3 versioning, backup checks) |
| Defacement | T1491 | cloud-workload-protection |
| Endpoint Denial of Service | T1499 | endpoint-os-security |
| Modify Safety System | T0838 (ICS) | ot-iot-device-security (safety system impact flag) |
| Loss of Safety | T0879 (ICS) | ot-iot-device-security |

---

## Compliance Framework Coverage

| Framework | Skills with Explicit Mapping |
|---|---|
| CIS AWS Foundations Benchmark | cloud-security-posture, iac-security |
| CIS Azure Benchmark | cloud-security-posture, iac-security |
| CIS Google Cloud Platform Benchmark | cloud-security-posture, iac-security |
| CIS Kubernetes Benchmark | iac-security, cloud-workload-protection |
| CIS Windows / Linux / macOS Benchmarks | endpoint-os-security |
| NIST SP 800-53 | cloud-security-posture, iac-security, endpoint-os-security |
| NIST SP 800-82 | ot-iot-device-security |
| NIST SP 800-213 (IoT) | ot-iot-device-security |
| IEC 62443 | ot-iot-device-security |
| NERC CIP | ot-iot-device-security |
| DISA STIG | endpoint-os-security |
| PCI DSS | cloud-security-posture, iac-security, endpoint-os-security |
| HIPAA | cloud-security-posture |
| SOC 2 | cloud-security-posture, iac-security |

---

## Cascade and Integration Map

```
                    ┌─────────────────────┐
                    │   iac-security      │ ◄── CI/CD pipeline trigger
                    └────────┬────────────┘
                             │ IaC drift detected
                             ▼
                    ┌─────────────────────┐
                    │ cloud-security-     │ ◄── daily scan / deployment event
                    │ posture             │
                    └─────┬──────┬────────┘
                          │      │ public resource
                          │      └──► attack-surface-management
                          │ workload
                          ▼
                    ┌─────────────────────┐
                    │ cloud-workload-     │
                    │ protection          │ ──► incident-commander (escape)
                    └─────┬───────────────┘
                          │ endpoint in scope
                          ▼
                    ┌─────────────────────┐
                    │ endpoint-os-        │
                    │ security            │ ──► detection-engineering
                    └─────────────────────┘

                    ┌─────────────────────┐
                    │ ot-iot-device-      │ ◄── scheduled OT assessment
                    │ security            │ ──► incident-commander (safety)
                    └─────────────────────┘

All skills ──► findings-tracker, compliance-mapping, security-posture-score
```

---

## Related Domains

- **[appsec-devsecops/](../appsec-devsecops/)**: Supplies IaC scan triggers from CI/CD pipeline events (`devsecops-pipeline`, `pipeline-security-scan`). The `iac-security` skill consumes pipeline context and returns findings back to the AppSec domain's `sast-dast-coordinator` for deduplication.
- **[identity-access/](../identity-access/)**: The `cloud-security-posture` skill cascades IAM anomalies and wildcard policy findings to `identity-access-risk`. The `endpoint-os-security` skill cascades local admin proliferation and credential guard gap findings to `identity-access-risk` and `cryptography-key-management`.

---

## Authoring Notes

When adding a new skill to this domain:

1. Place the skill directory under `cloud-infra/<slug>/`.
2. Reference the domain's Python tool naming convention: `<slug>_tool.py` in `scripts/`.
3. Update this CLAUDE.md Skills Catalog table and Cloud Provider Coverage Matrix.
4. Update the root `README.md` Domain Index table entry for `Cloud & Infra`.
5. Update `domains/cloud-infra.md` with the new skill slug and level.
6. Ensure all MITRE ATT&CK technique mappings relevant to the new skill are added to the coverage section above.
7. Add cascade rules to the Cascade and Integration Map.
