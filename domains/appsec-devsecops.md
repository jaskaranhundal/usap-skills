# AppSec & DevSecOps Domain

Skills in this domain secure the software development lifecycle from code review through pipeline integrity and supply chain validation.

## Skills

| Slug | Level | Description |
|---|---|---|
| `secure-sdlc` | L3 | Secure software development lifecycle: security requirements, design review, code review guidance |
| `sast-dast-coordinator` | L3 | Coordinates and interprets SAST, DAST, and SCA scan results; deduplicates findings |
| `devsecops-pipeline` | L3 | Security gate assessment for CI/CD pipelines: secrets scanning, SAST, DAST, SCA integration |
| `build-integrity` | L3 | Verifies software build pipeline integrity: artifact signing, provenance, reproducibility |
| `supply-chain-risk` | L3 | SBOM analysis, malicious package detection (5 categories), SLSA build integrity assessment |
| `supply-chain-simulation` | L3 | Simulates supply chain attack scenarios to test detection and response capabilities |
| `appsec-code-review` | L4 | Security-focused static code analysis: OWASP Top 10, logic flaws, dependency audits |
| `pipeline-security-scan` | L4 | CI/CD pipeline security scanning: secrets in env vars, SAST integration, artifact signing check |

## Workflow: DevSecOps Security Gate

```
secure-sdlc → appsec-code-review → sast-dast-coordinator → devsecops-pipeline → build-integrity → supply-chain-risk
```

## OWASP Top 10 Coverage (2021)

- A01: Broken Access Control
- A02: Cryptographic Failures
- A03: Injection
- A04: Insecure Design
- A05: Security Misconfiguration
- A06: Vulnerable and Outdated Components
- A07: Identification and Authentication Failures
- A08: Software and Data Integrity Failures
- A09: Security Logging and Monitoring Failures
- A10: Server-Side Request Forgery

## Orchestrator Agent

[cs-devsecops-engineer](../agents/devsecops/cs-devsecops-engineer.md) — coordinates AppSec and DevSecOps skills for pipeline security gates.
