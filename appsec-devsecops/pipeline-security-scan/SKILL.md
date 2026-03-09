---
name: pipeline-security-scan
description: USAP agent skill for Pipeline Security Scan. Use for CI/CD pipeline security scanning — secrets in env vars, SAST integration, artifact signing check.
license: MIT
metadata:
  version: 1.0.0
  author: USAP Team
  category: usap-devsecops
  updated: 2026-03-08
  agent_slug: "pipeline-security-scan"
---

# Pipeline Security Scan

## Overview
Scan CI/CD pipeline configurations for security issues including secrets in environment variables, missing SAST/SCA integration, unsigned build artifacts, overly permissive pipeline permissions, and insecure third-party action usage. This skill complements devsecops-pipeline (which reviews existing gates) by actively scanning the pipeline YAML configuration for vulnerabilities and misconfigurations.

## Keywords
- usap
- security-agent
- devsecops
- pipeline
- ci-cd
- secrets
- artifact-signing
- operations

## Quick Start
```bash
python scripts/pipeline-security-scan_tool.py --help
python scripts/pipeline-security-scan_tool.py --output json
```

## Core Workflows
1. Scan pipeline YAML for secrets in environment variables and step definitions.
2. Verify SAST, SCA, and secrets scanning stages are configured.
3. Check artifact signing and provenance generation configuration.
4. Review third-party action versions and pinning.

---

## Skill Identity

| Field | Value |
|---|---|
| **Slug** | `pipeline-security-scan` |
| **Level** | L4 |
| **Plane** | work |
| **Phase** | phase1 |
| **Domain** | DevOps |
| **Role** | DevSecOps Engineer, Platform Security Engineer |
| **Authorization required** | no |

---

## Scan Categories

### Secrets in Pipeline
- Hardcoded secrets in env vars: `SECRET_KEY: "abc123"`
- Base64-encoded secrets in configuration values
- Secrets in pipeline step commands
- Secrets in container image arguments

### SAST/SCA Integration Gaps
- No SAST stage configured
- No SCA/dependency scanning stage
- No secrets scanning stage (trufflehog, gitleaks)
- Security stages that only run on main (should run on all PRs)

### Artifact Integrity
- No artifact signing stage (Sigstore/cosign)
- No SBOM generation step
- No provenance attestation
- Docker images pushed without digest pinning

### Pipeline Permissions
- `permissions: write-all` in GitHub Actions
- Missing explicit permission restrictions
- Pipeline tokens with repository admin scope

### Third-Party Actions
- Actions not pinned to commit hash (using mutable branch/tag)
- Actions from unverified publishers
- Actions with excessive permissions

---

## Output Contract

```json
{
  "agent_slug": "pipeline-security-scan",
  "intent_type": "analyze",
  "action": "Remove hardcoded API key from pipeline env vars. Pin all third-party actions to commit hashes. Add artifact signing stage.",
  "rationale": "Hardcoded API key exposed in pipeline YAML. 3 actions pinned to mutable tags — supply chain risk.",
  "confidence": 0.91,
  "severity": "high",
  "scan_results": {
    "secrets_found": 0,
    "missing_security_stages": [],
    "artifact_integrity_gaps": [],
    "permission_issues": [],
    "unpinned_actions": []
  },
  "key_findings": [],
  "evidence_references": [],
  "next_agents": ["secrets-exposure", "build-integrity"],
  "human_approval_required": false,
  "timestamp_utc": "2026-03-08T09:00:00Z"
}
```

---

## Related Skills

- `secrets-exposure` — receives hardcoded secret findings for blast radius analysis
- `build-integrity` — verifies artifact signing and provenance configuration
- `devsecops-pipeline` — reviews existing security gate configuration
- `supply-chain-risk` — assesses third-party action supply chain risk
