# Cloud & Infrastructure Domain

Skills in this domain assess cloud security posture, infrastructure configuration, and endpoint hardening.

## Skills

| Slug | Level | Description |
|---|---|---|
| `cloud-security-posture` | L4 | CSPM: AWS/Azure/GCP posture evaluation against CIS Benchmarks, drift detection, compliance mapping |
| `iac-security` | L3 | Infrastructure-as-Code security analysis: Terraform, CloudFormation, Kubernetes manifests |
| `endpoint-os-security` | L4 | Endpoint and OS security assessment: patch status, EDR coverage, hardening baselines |
| `ot-iot-device-security` | L4 | OT/ICS/IoT device security: protocol analysis, firmware assessment, network segmentation gaps |
| `cloud-workload-protection` | L4 | Container and serverless runtime security: anomaly detection, escape detection, CSPM gap analysis |

## Workflow: Cloud Posture Assessment

```
iac-security → cloud-security-posture → cloud-workload-protection → vulnerability-management
```

## Supported Cloud Platforms

- AWS (CIS AWS Foundations Benchmark)
- Microsoft Azure (CIS Azure Benchmark)
- Google Cloud Platform (CIS GCP Benchmark)
- Kubernetes (CIS Kubernetes Benchmark)

## Container & Serverless Coverage

- Docker / OCI container images
- Kubernetes pod security
- AWS Lambda runtime security
- Azure Functions security
- GCP Cloud Run security

## Orchestrator Agent

[cs-devsecops-engineer](../agents/devsecops/cs-devsecops-engineer.md) — includes cloud workload protection in pipeline security gates.
