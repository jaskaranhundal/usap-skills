# AppSec & DevSecOps Domain — CLAUDE.md

This file is the authoritative domain guide for the `appsec-devsecops/` directory. It governs how Claude and cs-* agents understand, navigate, and apply the skills in this domain.

---

## Purpose

The AppSec & DevSecOps domain embeds security into every stage of the software development lifecycle (SDLC) — from requirements and design through code review, pipeline execution, artifact signing, and post-deployment monitoring. Skills in this domain operationalize shift-left security by placing automated gates at developer touchpoints (pre-commit, PR, CI/CD) and by providing structured analysis of code, dependencies, and build pipelines.

Core coverage areas:

- **Secure SDLC** — Security requirements, threat modeling, design review, and maturity assessment aligned to OWASP SAMM and BSIMM
- **SAST / DAST** — Coordinating static and dynamic analysis results across multiple scanners; deduplicating and prioritizing findings
- **DevSecOps Pipeline** — Assessing security gate completeness and correctness in CI/CD configurations
- **Build Integrity** — Verifying artifact provenance, signature validity, and SLSA compliance to prevent build-time compromise
- **Supply Chain Risk** — SBOM generation and analysis, malicious package detection, dependency risk scoring, and SLSA level assessment
- **AppSec Code Review** — OWASP Top 10 and CWE-focused static analysis of pull requests used as a merge gate
- **Pipeline Security Scan** — Active scanning of CI/CD YAML configurations for secrets exposure, SAST gaps, and insecure action pinning

The orchestrating agent for this domain is [cs-devsecops-engineer](../agents/devsecops/cs-devsecops-engineer.md).

---

## Skills Catalog

| Skill | Slug | Primary Tool | Coverage |
|---|---|---|---|
| Secure SDLC | `appsec-devsecops/secure-sdlc` | `secure-sdlc_tool.py` | OWASP SAMM, BSIMM |
| SAST/DAST Coordinator | `appsec-devsecops/sast-dast-coordinator` | `sast-dast-coordinator_tool.py` | CWE Top 25, OWASP Top 10 |
| DevSecOps Pipeline | `appsec-devsecops/devsecops-pipeline` | `devsecops-pipeline_tool.py` | CI/CD security gates |
| Build Integrity | `appsec-devsecops/build-integrity` | `build-integrity_tool.py` | SLSA L1-L4, Sigstore |
| Supply Chain Risk | `appsec-devsecops/supply-chain-risk` | `supply-chain-risk_tool.py` | SBOM, SLSA, Scorecard |
| Supply Chain Simulation | `appsec-devsecops/supply-chain-simulation` | `supply-chain-simulation_tool.py` | Attack simulation |
| AppSec Code Review | `appsec-devsecops/appsec-code-review` | `appsec-code-review_tool.py` | OWASP Top 10, CWE |
| Pipeline Security Scan | `appsec-devsecops/pipeline-security-scan` | `pipeline-security-scan_tool.py` | Secrets, SAST gaps |
| Security Requirements Review | `appsec-devsecops/security-requirements-review` | `security-requirements-review_tool.py` | Design doc intake, PRD/architecture/POA&M analysis |

Each skill directory follows the USAP Agent Skills Standard v1 layout:

```
<skill-slug>/
├── SKILL.md
├── README.md
├── scripts/
│   └── <skill-slug>_tool.py
├── references/
├── assets/
└── expected_outputs/
```

---

## Python Tools Reference

| Tool | Path | Primary Use Case | Output |
|---|---|---|---|
| `appsec-code-review_tool.py` | `appsec-code-review/scripts/` | PR security gate; OWASP Top 10 static analysis | JSON findings with CWE mappings |
| `pipeline-security-scan_tool.py` | `pipeline-security-scan/scripts/` | Scan pipeline YAML for secrets, SAST gaps, pinning issues | JSON scan report |
| `sast-dast-coordinator_tool.py` | `sast-dast-coordinator/scripts/` | Normalize and deduplicate multi-scanner results | Deduplicated finding set |
| `supply-chain-risk_tool.py` | `supply-chain-risk/scripts/` | SBOM analysis, malicious package detection, license audit | Risk-scored SBOM report |
| `build-integrity_tool.py` | `build-integrity/scripts/` | Artifact signature and SLSA provenance verification | Verification result + gate decision |
| `devsecops-pipeline_tool.py` | `devsecops-pipeline/scripts/` | Assess security gate coverage in CI/CD pipeline | Pipeline security score |
| `secure-sdlc_tool.py` | `secure-sdlc/scripts/` | SDLC maturity scoring and security requirements audit | Maturity score (0-5) + gap list |
| `supply-chain-simulation_tool.py` | `supply-chain-simulation/scripts/` | Simulate supply chain attack scenarios | Simulation report |
| `security-requirements-review_tool.py` | `security-requirements-review/scripts/` | Ingest design docs (PRD, arch, POA&M); extract security gaps; route findings | JSON output contract with document_metadata + design_analysis |

Invoke all tools with `--output json` for machine-readable output compatible with downstream aggregation.

---

## SDLC Phase Integration Matrix

| SDLC Phase | Skills Active | Gates | Artifacts Produced |
|---|---|---|---|
| Requirements & Design | `secure-sdlc`, `security-requirements-review` | Threat model sign-off required for high-risk features; document security review before design freeze | Threat model, abuse case register, security requirements doc, design gap report |
| Development (pre-commit) | `appsec-code-review`, `pipeline-security-scan` | Pre-commit hook: secrets scan + lint (<30 s) | Pre-commit finding log |
| Pull Request | `appsec-code-review`, `sast-dast-coordinator`, `supply-chain-risk` | Block merge on Critical/High findings | PR security gate report, CWE-mapped findings |
| CI/CD Build | `devsecops-pipeline`, `pipeline-security-scan`, `build-integrity` | Fail pipeline on missing SAST gate or unsigned artifact | Pipeline scan report, artifact signature |
| Pre-Production | `sast-dast-coordinator`, `supply-chain-risk`, `build-integrity` | Deployment gate: SLSA L2+ required; no Critical CVEs | SBOM, SLSA provenance, pentest sign-off |
| Operations | `supply-chain-risk`, `supply-chain-simulation` | Continuous dependency monitoring; quarterly simulation | Dependency diff report, simulation results |

---

## OWASP Top 10 Coverage (2021)

| Category | Skills | Detection Method |
|---|---|---|
| A01 — Broken Access Control | `appsec-code-review`, `sast-dast-coordinator` | Static pattern matching; DAST auth bypass probes |
| A02 — Cryptographic Failures | `appsec-code-review`, `secure-sdlc` | Algorithm allowlist check; TLS version scan |
| A03 — Injection | `appsec-code-review`, `sast-dast-coordinator` | Parameterized query enforcement; DAST injection payloads |
| A04 — Insecure Design | `secure-sdlc` | Threat model review; abuse case analysis |
| A05 — Security Misconfiguration | `pipeline-security-scan`, `devsecops-pipeline` | Pipeline YAML audit; default credential checks |
| A06 — Vulnerable and Outdated Components | `supply-chain-risk`, `sast-dast-coordinator` | SBOM diff against CVE database; SCA results coordination |
| A07 — Identification and Auth Failures | `appsec-code-review`, `secure-sdlc` | Session management pattern review; JWT validation check |
| A08 — Software and Data Integrity Failures | `build-integrity`, `supply-chain-risk` | Artifact signing verification; SLSA provenance check |
| A09 — Security Logging and Monitoring Failures | `secure-sdlc`, `appsec-code-review` | Logging coverage review; sensitive data in logs pattern |
| A10 — Server-Side Request Forgery | `appsec-code-review`, `sast-dast-coordinator` | URL validation pattern check; DAST SSRF probes |

---

## Domain Best Practices

1. **Shift left without blocking velocity.** Place the fastest, highest-signal gates earliest (pre-commit: <30 s, PR gate: <5 min). Reserve longer scans (DAST, full SCA) for CI/CD after commit, not before.

2. **Gate on severity, not volume.** Only Critical and High findings block merge or deployment. Medium findings create tracked issues. Low and Informational findings are comments only. Tuning gates to this threshold keeps false-positive-driven bypasses below 15%.

3. **Every artifact must have a cryptographic chain of custody.** From source commit hash to deployed container digest, there must be no unsigned gaps. Enforce SLSA L2 as the minimum for production deployments; target SLSA L3 for internet-facing services.

4. **SBOM is a first-class release artifact.** Generate a CycloneDX or SPDX SBOM for every software release. Store it alongside the build provenance. Make it available to security and legal before release sign-off.

5. **Deduplicate before escalating.** Run `sast-dast-coordinator` before routing findings to developers. A single SQL injection finding reported by three scanners must appear once, with the highest confidence and clearest remediation.

6. **Pin and verify all third-party CI actions.** Pipeline configurations that reference mutable action tags (`@main`, `@v2`) are supply chain attack vectors. Require SHA pinning (`@<full-commit-sha>`) for all external actions and verify with `pipeline-security-scan`.

7. **Threat model before you build.** Use `secure-sdlc` to assess security requirements at the design phase for any change touching authentication, authorization, cryptography, PII storage, or new external integrations. A missed threat model is a debt that compounds through every downstream gate.

8. **Simulate to validate.** Run `supply-chain-simulation` quarterly and after significant dependency tree changes to validate that detection controls (SBOM diff, package hash verification, build anomaly detection) catch realistic supply chain attack scenarios before a real attacker does.

---

## Workflow: PR Security Gate

This is the primary daily workflow. It executes on every pull request before merge is permitted.

```
Step 1 — Code Review (appsec-code-review)
  python appsec-code-review/scripts/appsec-code-review_tool.py --output json
  Gate: Block on Critical or High findings

Step 2 — Scanner Coordination (sast-dast-coordinator)
  python sast-dast-coordinator/scripts/sast-dast-coordinator_tool.py --output json
  Gate: Deduplicate and re-score; re-apply Critical/High block rule

Step 3 — Dependency Audit (supply-chain-risk)
  python supply-chain-risk/scripts/supply-chain-risk_tool.py --output json
  Gate: Block if new dependency has Critical CVE or is flagged malicious

Step 4 — Decision
  PASS  → Approve PR; route Medium/Low findings to tracking system
  BLOCK → Return findings to developer with CWE mappings and remediation steps
          Require security team sign-off for any override of High findings
          Require CISO sign-off for any override of Critical findings

Step 5 — Tracking
  Route all findings to findings-tracker for lifecycle and SLA management
```

Expected output: A structured PR security gate decision (pass/block) with severity-sorted findings, CWE mappings, and developer-actionable remediation guidance.

---

## Workflow: Release Security Checklist

This workflow gates a software release before production deployment.

```
Step 1 — Pipeline Integrity Review
  python pipeline-security-scan/scripts/pipeline-security-scan_tool.py --output json
  python devsecops-pipeline/scripts/devsecops-pipeline_tool.py --output json
  Requirement: No secrets in pipeline env vars; all stages present

Step 2 — Build Artifact Verification
  python build-integrity/scripts/build-integrity_tool.py --output json
  Requirement: Signature valid; SLSA L2 minimum; provenance present

Step 3 — SBOM Generation and Risk Scoring
  python supply-chain-risk/scripts/supply-chain-risk_tool.py --output json
  Requirement: No Critical CVEs in SBOM; no malicious packages; license compliance confirmed

Step 4 — SDLC Maturity Check
  python secure-sdlc/scripts/secure-sdlc_tool.py --output json
  Requirement: Maturity score >= 2 (SAST + SCA in place)

Step 5 — Release Decision
  ALL PASS → Release approved; attach SBOM and provenance to release artifact
  ANY FAIL → Release blocked; create incident ticket; notify release manager

Artifacts produced: SBOM (CycloneDX or SPDX), build provenance (SLSA .intoto.jsonl),
                   pipeline scan report, release gate decision record
```

---

## Cascade Intelligence (Cross-Skill Routing)

```
security-requirements-review ──► risk-threat-modeling (architecture docs)
                              ──► compliance-mapping (regulated data detected)
                              ──► appsec-code-review (PRD / requirements)
                              ──► pipeline-security-scan (pipeline/CI references)
                              ──► cs-security-analyst (critical gaps: no auth, hardcoded creds)

appsec-code-review ──► sast-dast-coordinator ──► findings-tracker
                                                 └──► secrets-exposure (hardcoded credential findings)

supply-chain-risk ──► build-integrity ──► incident-commander (Critical integrity failures)

devsecops-pipeline ──► pipeline-security-scan ──► secure-sdlc

supply-chain-simulation ──► red-team/ (validated attack scenarios)
```

When a Critical finding is produced by any skill in this domain, route immediately to `cs-security-analyst` for triage. Do not wait for the full gate pipeline to complete.

---

## Related Domains

| Domain | Directory | Relationship |
|---|---|---|
| Detection | `detection/` | AppSec findings that survive to production become detection use cases (e.g., SSRF patterns become WAF rules and SIEM detections) |
| Red Team | `red-team/` | Supply chain simulation outputs feed red team attack scenarios; red team validates AppSec gate effectiveness |
| Risk & Compliance | `risk-compliance/` | SBOM and SLSA provenance feed compliance evidence; OWASP SAMM maturity scores feed risk register |
| Response | `response/` | Critical build integrity failures and confirmed supply chain compromises trigger incident response |

---

## Skill Level Reference

| Level | Meaning | Skills at this Level |
|---|---|---|
| L3 | Practitioner — structured analysis, defined output | `secure-sdlc`, `sast-dast-coordinator`, `devsecops-pipeline`, `build-integrity`, `supply-chain-risk`, `supply-chain-simulation`, `security-requirements-review` |
| L4 | Expert — blocking gate authority, CWE mapping, high-confidence decisions | `appsec-code-review`, `pipeline-security-scan` |

L4 skills have authority to produce `block_required: true` decisions. L3 skills produce findings and recommendations that feed into gate decisions made by L4 skills or the orchestrating agent.

---

## Standards and Frameworks Referenced

| Standard | Application in this Domain |
|---|---|
| OWASP SAMM 2.0 | Secure SDLC maturity model; `secure-sdlc` maturity scoring |
| BSIMM 14 | Observed security practices benchmark; gap analysis for `secure-sdlc` |
| OWASP Top 10 (2021) | Primary vulnerability taxonomy for `appsec-code-review` and `sast-dast-coordinator` |
| CWE Top 25 | Secondary finding classification; CWE IDs attached to all findings |
| SLSA Framework (L1-L4) | Build integrity and provenance requirements; `build-integrity` assessment |
| Sigstore / cosign | Artifact signing mechanism referenced in `build-integrity` |
| SPDX 2.3 / CycloneDX 1.5 | SBOM format standards; `supply-chain-risk` output formats |
| OpenSSF Scorecard | Dependency health scoring; referenced in `supply-chain-risk` |
| NIST SP 800-218 (SSDF) | Secure Software Development Framework; aligns with `secure-sdlc` phases |
