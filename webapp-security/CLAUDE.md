# Webapp Security Domain — CLAUDE.md

## Purpose

The `webapp-security/` domain holds skills that triage, classify, and assess web-application and API security findings. Scope is the runtime surface — production webapps and API endpoints — and the OWASP Top 10 2025 + OWASP API Security Top 10 are the primary taxonomies. Build-time AppSec (SAST, dependency analysis, supply-chain) lives in `appsec-devsecops/` and is not duplicated here.

Skills in this domain produce structured triage payloads, not remediation actions. Mutating recommendations (WAF rule changes, account disablement, schema-rewrite proposals) are surfaced via `human_approval_required: true` and routed to `cs-appsec-engineer` (the orchestrator) or `cs-incident-responder` (active-exploit case).

Subdomains covered:
- Webapp finding triage (which OWASP category, what severity, who consumes it next)
- OWASP Top 10 2025 classification with confidence scoring
- API security posture assessment (OWASP API Top 10, BOLA / mass assignment / broken auth)

---

## Skills Catalog

| Skill | Slug | Primary Tool | Frameworks (frontmatter) |
|---|---|---|---|
| webapp-risk-triage | webapp-security/webapp-risk-triage | `webapp-risk-triage_tool.py` | OWASP A01, A03, A05, A07; MITRE T1190 |
| owasp-top10-classifier | webapp-security/owasp-top10-classifier | `owasp-top10-classifier_tool.py` | OWASP A01–A10 (full set) |
| api-security-posture | webapp-security/api-security-posture | `api-security-posture_tool.py` | OWASP A01, A03, A07; MITRE T1078, T1190 |

All paths are relative from the repository root.

---

## Python Tools Reference

| Tool | Path | Purpose | Key Args |
|---|---|---|---|
| `webapp-risk-triage_tool.py` | `webapp-security/webapp-risk-triage/scripts/webapp-risk-triage_tool.py` | Map a webapp finding to OWASP + severity, recommend the next USAP skill | `--input <finding.json>`, `--output {json,human}` |
| `owasp-top10-classifier_tool.py` | `webapp-security/owasp-top10-classifier/scripts/owasp-top10-classifier_tool.py` | Classify a finding description into OWASP Top 10 2025 categories with confidence | `--input <finding.json>`, `--output {json,human}` |
| `api-security-posture_tool.py` | `webapp-security/api-security-posture/scripts/api-security-posture_tool.py` | Score an API surface (auth, rate limits, identification, mass-assignment) against OWASP API Top 10 | `--input <api-spec.json>`, `--output {json,human}` |

All three are stdlib-only and emit USAP's 11-field output contract.

---

## Domain Best Practices

1. **Triage before scanning.** A webapp finding without context (target URL, environment, auth state) cannot be prioritised. Always run `webapp-risk-triage` before invoking a deeper scanner or pentest skill. The triage output names the right downstream skill.

2. **OWASP category is a routing decision, not a verdict.** `owasp-top10-classifier` returns ranked category candidates with confidence. Treat the top match as the routing key, not as a finding statement. The eventual finding statement still requires evidence corroboration.

3. **API auth failures dominate the threat model.** OWASP API Top 10's "Broken Object Level Authorization" (BOLA) is the most common real-world issue. `api-security-posture` scores BOLA visibility first and weights it heaviest in the posture score.

4. **Always emit a `next_agents` recommendation.** Triage skills must point to the next concrete USAP skill — `appsec-devsecops/sast-dast-coordinator` for build-time, `response/incident-classification` for production exploit, `risk-compliance/risk-threat-modeling` for design-stage. Empty `next_agents` is an anti-pattern in this domain.

5. **`human_approval_required: true` on any control change.** WAF rule injection, schema rewrites, and account state changes are mutating actions — never auto-trigger. Surface them with confidence, evidence references, and a clear escalation owner role.

---

## Workflow Patterns

### Workflow 1: Production webapp alert → routing

```
webapp-risk-triage           (classify finding, score severity, scope blast radius)
       |
       v
owasp-top10-classifier       (refine OWASP category with confidence)
       |
       +--> [A01/A07 + production exploit]  --> response/incident-classification
       |
       +--> [A03/A08 + design issue]        --> risk-compliance/risk-threat-modeling
       |
       +--> [build-time gap]                --> appsec-devsecops/sast-dast-coordinator
```

### Workflow 2: API security review

```
api-security-posture         (score API surface against OWASP API Top 10)
       |
       v
[posture below threshold]
       |
       +--> appsec-devsecops/secure-sdlc        (design changes)
       +--> appsec-devsecops/security-requirements-review  (PRD updates)
       +--> identity-access/identity-access-risk  (auth model review)
```

---

## Related Domains

### appsec-devsecops/

Build-time AppSec is upstream of this domain. The SAST/DAST coordinator, supply-chain risk, and secure-SDLC skills run in CI; this domain handles their runtime equivalents. Findings flow both ways: a runtime triage may demand a build-time gate, and a CI finding may require runtime monitoring.

### response/

Production exploit cases escalate from `webapp-risk-triage` straight into `response/incident-classification`. The triage output is structured exactly so the incident-classification skill consumes it without translation.

### risk-compliance/

Design-stage webapp issues (architecture, threat-modelling gaps) route to `risk-compliance/risk-threat-modeling` rather than to incident response. The triage skill chooses which based on the finding's evidence references.

---

## Path Reference

```
webapp-security/<slug>/
  SKILL.md
  README.md
  references/workflow.md
  assets/templates/output-template.json
  expected_outputs/sample_output.json
  scripts/<slug>_tool.py
```

Invoke any tool from the repo root:

```bash
python3 webapp-security/webapp-risk-triage/scripts/webapp-risk-triage_tool.py --output json
python3 webapp-security/owasp-top10-classifier/scripts/owasp-top10-classifier_tool.py --output json
python3 webapp-security/api-security-posture/scripts/api-security-posture_tool.py --output json
```

Each tool emits a USAP 11-field contract payload by default. Pass `--input <finding.json>` to drive the analysis from real data.
