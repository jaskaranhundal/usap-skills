# Canonical Domain Slugs

Single source of truth for the 11 USAP domain slugs. The validator (`tools/validate_skill.py`) FAILs any SKILL.md whose first path segment is a known alias instead of the canonical slug listed below. Any new domain must be added here, in `tools/validate_skill.py`, and in `standards/frontmatter-spec.md` in the same commit.

---

## The 11 canonical slugs

| Canonical slug | What lives here |
|---|---|
| `appsec-devsecops` | Application security, SAST/DAST, devsecops pipeline, IaC scanning, dependency hygiene |
| `cloud-infra` | Cloud posture, IAM at the cloud-provider layer, container/K8s security |
| `detection` | Hunting, telemetry quality, behavioral analytics, secrets exposure, detection engineering |
| `governance` | Board reporting, executive briefings, security-program governance |
| `identity-access` | IAM beyond cloud — directory, SSO, MFA, privileged access, identity governance |
| `pentest` | Authorized offensive testing, bug-bounty triage, vulnerability validation |
| `platform-ai` | AI/ML platform security, model risk, prompt-injection, AI safety guardrails |
| `red-team` | Adversary emulation, purple-team, MITRE ATT&CK-aligned campaigns |
| `response` | Incident response, forensics, containment, post-incident review |
| `risk-compliance` | Risk register, regulatory horizon, compliance evidence, quantum-readiness |
| `system-security` | OS hardening, endpoint configuration, host-level controls |
| `webapp-security` | Web-application-specific findings (OWASP Top 10 classification, API posture, webapp triage) |

Total: 11. The legacy `engineering` and `platform` domains are excluded from validation scope; their skills are tracked but not counted toward the 79-skill inventory.

---

## Alias map

The validator rejects any of the aliases below as the first path segment of a SKILL.md. Use the canonical slug instead.

| Canonical slug | Rejected aliases |
|---|---|
| `appsec-devsecops` | `appsec`, `dev-sec-ops`, `devsecops`, `app-sec` |
| `cloud-infra` | `cloud`, `cloud-security`, `infra`, `infrastructure`, `cloud-infrastructure` |
| `detection` | `detect`, `detections`, `siem`, `soc` |
| `governance` | `gov`, `exec`, `executive`, `board` |
| `identity-access` | `iam`, `identity`, `idam`, `access` |
| `pentest` | `pentesting`, `penetration-testing`, `pen-test`, `pen-testing` |
| `platform-ai` | `ai-platform`, `ai`, `mlops`, `ml-platform`, `ml` |
| `red-team` | `red-teaming`, `offensive-security`, `redteam`, `adversary-emulation`, `offensive` |
| `response` | `ir`, `incident-response`, `dfir`, `forensics` |
| `risk-compliance` | `risk`, `compliance`, `grc`, `risk-and-compliance` |
| `system-security` | `endpoint`, `endpoint-security`, `host`, `host-security`, `os-security` |
| `webapp-security` | `web-application-security`, `webapp`, `appsec-web`, `web`, `web-security` |

---

## Adding a new domain

1. Add the canonical slug to the table above with a one-line scope.
2. Add the slug to `ACTIVE_DOMAINS` in `tools/validate_skill.py`.
3. Add an empty alias row in the alias map and back-fill aliases as misnamings appear.
4. Create the domain dir with `CLAUDE.md` and `README.md`.
5. Update `standards/frontmatter-spec.md` Category → Domain mapping if the new domain introduces a new category enum.
6. Open the PR with all of the above in one commit — partial domain rollouts break the validator.

---

## Why this exists

Domain slugs leak into SDK packaging, MCP routing, mappings/, and the agents catalog. A drift between the docs and the disk layout silently breaks `tools/framework_extractor.py` and the cs-agent skills index. This file lets the validator catch the drift in CI rather than at runtime.
