# AppSec & DevSecOps

Skills for securing the software development lifecycle from code review through build pipeline validation and supply chain risk assessment.

## Domain Overview

The `appsec-devsecops/` domain provides eight USAP skill packages that collectively enforce security from the earliest developer touchpoint (pre-commit) to the final release gate (artifact signing and SBOM delivery). Each skill is self-contained and executable as a standalone module; the [cs-devsecops-engineer](../agents/devsecops/cs-devsecops-engineer.md) agent orchestrates them into coherent security gate workflows.

This domain directly addresses the OWASP Top 10 (2021), CWE Top 25, SLSA Framework levels 1-4, OWASP SAMM maturity model, and NIST SSDF secure development practice areas.

## Skills

| Slug | Level | Description |
|---|---|---|
| `secure-sdlc` | L3 | Secure software development lifecycle: security requirements, design review, threat modeling, and SDLC maturity assessment aligned to OWASP SAMM and BSIMM |
| `sast-dast-coordinator` | L3 | Coordinates and interprets SAST, DAST, and SCA scan results from multiple scanners; deduplicates findings and normalizes severity |
| `devsecops-pipeline` | L3 | Security gate assessment for CI/CD pipelines: evaluates coverage of secrets scanning, SAST, DAST, SCA, and IaC scanning stages |
| `build-integrity` | L3 | Verifies software build pipeline integrity: artifact signing validation, SLSA provenance check, reproducible build assessment, and anomaly detection |
| `supply-chain-risk` | L3 | SBOM analysis, malicious package detection across five attack categories, dependency risk scoring, and SLSA build integrity assessment |
| `supply-chain-simulation` | L3 | Simulates supply chain attack scenarios (typosquatting, dependency confusion, compromised maintainer, CI poisoning) to validate detection controls |
| `appsec-code-review` | L4 | Security-focused static code analysis: OWASP Top 10, logic flaws, cryptographic misuse, and dependency audits — used as a PR merge gate |
| `pipeline-security-scan` | L4 | Active CI/CD pipeline configuration scanning: secrets in environment variables, missing SAST/SCA stages, unpinned third-party actions, unsigned artifacts |

## Orchestrator Agent

[cs-devsecops-engineer](../agents/devsecops/cs-devsecops-engineer.md) — coordinates AppSec and DevSecOps skills into PR security gates, pipeline hardening assessments, and SBOM/release workflows.

## DevSecOps Security Gate Workflow

```
secure-sdlc
    |
    | (security requirements, threat model)
    v
appsec-code-review  ──────────────────────────────────┐
    |                                                   |
    | (OWASP Top 10 findings)                           |
    v                                                   |
sast-dast-coordinator  <── (scanner results)           |
    |                                                   |
    | (deduplicated finding set)                        |
    v                                                   |
supply-chain-risk                                       |
    |                                                   |
    | (SBOM, dependency risk score)                     |
    v                                                   |
devsecops-pipeline                                      |
    |                                                   |
    | (pipeline gate coverage score)                    |
    v                                                   |
pipeline-security-scan  <──────────────────────────────┘
    |
    | (pipeline config findings)
    v
build-integrity
    |
    | (artifact verification: pass / block)
    v
Release Gate Decision
```

## Directory Structure

```
appsec-devsecops/
├── CLAUDE.md                         # Domain guide for Claude and cs-* agents
├── README.md                         # This file
├── appsec-code-review/
│   ├── SKILL.md
│   ├── README.md
│   ├── scripts/appsec-code-review_tool.py
│   ├── references/
│   ├── assets/
│   └── expected_outputs/
├── build-integrity/
│   ├── SKILL.md
│   └── scripts/build-integrity_tool.py
├── devsecops-pipeline/
│   ├── SKILL.md
│   └── scripts/devsecops-pipeline_tool.py
├── pipeline-security-scan/
│   ├── SKILL.md
│   └── scripts/pipeline-security-scan_tool.py
├── sast-dast-coordinator/
│   ├── SKILL.md
│   └── scripts/sast-dast-coordinator_tool.py
├── secure-sdlc/
│   ├── SKILL.md
│   └── scripts/secure-sdlc_tool.py
├── supply-chain-risk/
│   ├── SKILL.md
│   └── scripts/supply-chain-risk_tool.py
└── supply-chain-simulation/
    ├── SKILL.md
    └── scripts/supply-chain-simulation_tool.py
```

## Quick Start

Run a PR security gate against the current working directory:

```bash
# Step 1: Static code review for OWASP Top 10
python appsec-devsecops/appsec-code-review/scripts/appsec-code-review_tool.py --output json

# Step 2: Coordinate scanner results
python appsec-devsecops/sast-dast-coordinator/scripts/sast-dast-coordinator_tool.py --output json

# Step 3: Dependency and supply chain audit
python appsec-devsecops/supply-chain-risk/scripts/supply-chain-risk_tool.py --output json
```

Run a release security gate:

```bash
# Build integrity and artifact signing
python appsec-devsecops/build-integrity/scripts/build-integrity_tool.py --output json

# Pipeline configuration scan
python appsec-devsecops/pipeline-security-scan/scripts/pipeline-security-scan_tool.py --output json
```

## Gate Severity Reference

| Finding Severity | PR Gate | Deployment Gate |
|---|---|---|
| Critical | Block merge immediately | Block deployment; require CISO sign-off to override |
| High | Block merge; security team sign-off required to override | Block deployment; security director sign-off required |
| Medium | Warn; allow merge with tracked finding | Warn; allow deployment with tracked finding |
| Low / Informational | Comment only | No gate impact |

## Related Domains

- [detection/](../detection/) — AppSec findings that reach production become detection use cases; SSRF and injection patterns produce WAF rules and SIEM detections
- [red-team/](../red-team/) — Supply chain simulation outputs feed red team attack scenarios; red team validates AppSec gate coverage
- [risk-compliance/](../risk-compliance/) — SBOM and SLSA provenance feed compliance evidence packages; OWASP SAMM maturity scores feed the risk register
- [response/](../response/) — Critical build integrity failures and confirmed supply chain compromises trigger incident response workflows

## Standards Coverage

| Standard | Covered By |
|---|---|
| OWASP Top 10 (2021) | `appsec-code-review`, `sast-dast-coordinator`, `secure-sdlc` |
| CWE Top 25 | `appsec-code-review`, `sast-dast-coordinator` |
| OWASP SAMM 2.0 | `secure-sdlc` |
| BSIMM 14 | `secure-sdlc` |
| SLSA L1-L4 | `build-integrity`, `supply-chain-risk` |
| Sigstore / cosign | `build-integrity` |
| SPDX / CycloneDX SBOM | `supply-chain-risk` |
| OpenSSF Scorecard | `supply-chain-risk` |
| NIST SP 800-218 (SSDF) | `secure-sdlc` |
