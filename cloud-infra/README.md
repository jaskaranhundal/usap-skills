# Cloud & Infrastructure Security Domain

Five skill packages covering cloud security posture, infrastructure-as-code security, endpoint and OS hardening, OT/IoT device security, and cloud workload protection. All skills are read-only analyzers; configuration changes and remediation actions require explicit human approval.

---

## Skills

| Skill | Slug | Level | Intent | Description |
|---|---|---|---|---|
| [Cloud Security Posture](cloud-security-posture/SKILL.md) | `cloud-security-posture` | L4 | `read_only` + `mutating/device_config_change` | CSPM across AWS, Azure, and GCP. 40+ CIS Benchmark checks, drift detection, compliance mapping to CIS, NIST 800-53, SOC 2, PCI DSS, HIPAA. |
| [IaC Security](iac-security/SKILL.md) | `iac-security` | L3 | `read_only` | Static analysis of Terraform, CloudFormation, Kubernetes manifests, Pulumi, and Helm charts. CI/CD gate with Critical-finding PR block policy. |
| [Endpoint & OS Security](endpoint-os-security/SKILL.md) | `endpoint-os-security` | L4 | `read_only` + `mutating/device_config_change` | Hardening assessment for Windows, Linux, and macOS against CIS Level 1/2 and DISA STIG. EDR coverage gaps and patch priority matrix. |
| [OT/IoT Device Security](ot-iot-device-security/SKILL.md) | `ot-iot-device-security` | L4 | `read_only` + `mutating/network_change` + `mutating/device_config_change` | ICS/SCADA and IoT posture using the Purdue model. NIST SP 800-82, IEC 62443, NERC CIP. All OT changes require safety review and operations director co-approval. |
| [Cloud Workload Protection](cloud-workload-protection/SKILL.md) | `cloud-workload-protection` | L4 | `read_only` | Runtime security for containers and serverless functions. CWPP coverage gaps, container escape detection, pod anomaly analysis, serverless permission sprawl. |

---

## Quick Commands

```bash
# Cloud Security Posture — AWS account scan
python cloud-infra/cloud-security-posture/scripts/cloud-security-posture_tool.py \
  --provider aws --account-id <ACCOUNT_ID> --output json

# Cloud Security Posture — Azure subscription scan
python cloud-infra/cloud-security-posture/scripts/cloud-security-posture_tool.py \
  --provider azure --output json

# IaC Security — Terraform directory
python cloud-infra/iac-security/scripts/iac-security_tool.py \
  --target terraform --dir ./infrastructure --output json

# IaC Security — Kubernetes manifests
python cloud-infra/iac-security/scripts/iac-security_tool.py \
  --target kubernetes --dir ./k8s --output json

# Endpoint & OS Security — Linux host
python cloud-infra/endpoint-os-security/scripts/endpoint-os-security_tool.py \
  --os linux --host <HOSTNAME> --output json

# OT/IoT Device Security — IT/OT DMZ zone
python cloud-infra/ot-iot-device-security/scripts/ot-iot-device-security_tool.py \
  --zone 3 --env ot --output json

# Cloud Workload Protection — EKS cluster
python cloud-infra/cloud-workload-protection/scripts/cloud-workload-protection_tool.py \
  --target containers --cluster <CLUSTER_NAME> --output json
```

---

## Cross-Skill Workflow: Cloud Posture Assessment

```
iac-security  →  cloud-security-posture  →  cloud-workload-protection  →  endpoint-os-security
```

1. `iac-security` runs as a CI/CD PR gate. Critical findings block the PR.
2. `cloud-security-posture` runs on deployment and daily. Detects misconfigurations and unauthorized drift.
3. `cloud-workload-protection` assesses runtime container and serverless security.
4. `endpoint-os-security` evaluates hardening and EDR coverage on enrolled endpoints.
5. All findings flow to `findings-tracker`, `compliance-mapping`, and `security-posture-score`.

---

## Orchestrator Agent

[`cs-devsecops-engineer`](../agents/devsecops/cs-devsecops-engineer.md) — includes `iac-security` and `cloud-security-posture` as pipeline security gates alongside SAST, DAST, and supply chain checks.

---

## Cloud Provider Coverage

| Skill | AWS | Azure | GCP | On-Prem |
|---|---|---|---|---|
| cloud-security-posture | Full | Full | Full | Not applicable |
| iac-security | Full | Partial | Partial | Kubernetes |
| endpoint-os-security | EC2 / ECS | Azure VM / AKS | GCE / GKE | Physical and VM |
| ot-iot-device-security | Not applicable | Not applicable | Not applicable | Full |
| cloud-workload-protection | EKS, Lambda, Fargate | AKS, Azure Functions | GKE, Cloud Run | Self-hosted K8s |

---

## Compliance Frameworks

| Framework | Skill |
|---|---|
| CIS AWS / Azure / GCP Benchmarks | cloud-security-posture, iac-security |
| CIS Kubernetes Benchmark | iac-security, cloud-workload-protection |
| CIS Windows / Linux / macOS Benchmarks | endpoint-os-security |
| NIST SP 800-53 | cloud-security-posture, iac-security, endpoint-os-security |
| NIST SP 800-82 / 800-213 | ot-iot-device-security |
| IEC 62443 / NERC CIP | ot-iot-device-security |
| DISA STIG | endpoint-os-security |
| PCI DSS / HIPAA / SOC 2 | cloud-security-posture, iac-security |

---

## Downstream Integrations

| Finding Type | Cascades To |
|---|---|
| Public cloud resource (S3, GCS, blob) | `attack-surface-management` |
| Security group 0.0.0.0/0 | `network-exposure` |
| IAM wildcard policy | `identity-access-risk`, `vulnerability-management` |
| Container escape detected | `incident-commander` (SEV1 immediate) |
| OT safety system risk | `incident-commander` (safety escalation) |
| IaC resource drifted from Terraform state | `iac-security` (policy-as-code rule creation) |
| EDR coverage gap or agent offline | `detection-engineering` |

---

## Domain Guide

See [`CLAUDE.md`](CLAUDE.md) for the full domain guide, including the MITRE ATT&CK cloud matrix coverage, detailed IaC check categories, OT environment workflows, authoring notes, and the complete cascade and integration map.
