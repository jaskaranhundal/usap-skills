# Engineering Security Domain — CLAUDE.md

This file is the authoritative domain guide for the `engineering/` directory. It governs how Claude and cs-* agents understand, navigate, and apply the skills in this domain.

---

## Purpose

The Engineering Security domain provides structured security review capabilities for two foundational activities in the software delivery process: code review and architecture advisory. These skills are not pipeline automation tools — they are expert-level analytical skills that apply security reasoning to code and system design, producing structured findings and remediation guidance consumable by engineering teams and downstream security workflows.

Unlike the `appsec-devsecops/` domain, which focuses on automated pipeline gate execution and supply chain integrity, the Engineering domain provides the expert advisory layer. It answers the questions that automated scanners cannot: Is the design sound? Are there logic flaws that pattern matching will miss? Does this architecture introduce systemic risk beyond the vulnerability at hand?

Core coverage areas:

- **Code Review** — Security-focused analysis of pull requests and code changes. Applies OWASP Top 10, CWE classifications, and logic flaw analysis. Produces structured findings with remediation guidance, not just scanner output.
- **Architecture Advisory** — Security review of system design proposals, architectural decision records (ADRs), and infrastructure blueprints. Evaluates zero trust alignment, defense-in-depth, blast radius of design choices, and long-horizon security debt introduced by architectural decisions.

The primary orchestrating agent for this domain is cs-security-analyst when the task involves a specific code finding, and cs-ciso-advisor when the request is a strategic architecture review with executive risk implications.

---

## Skills Catalog

| Skill | Slug | Primary Tool | Coverage |
|---|---|---|---|
| code-reviewer | `engineering/code-reviewer` | `code-reviewer_tool.py` | OWASP Top 10, CWE Top 25, logic flaw analysis, secure coding patterns |
| architecture-advisor | `engineering/architecture-advisor` | `architecture-advisor_tool.py` | Zero trust assessment, threat modeling, architectural risk, security debt quantification |

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

| Tool | Path | Key Flags | Output |
|---|---|---|---|
| `code-reviewer_tool.py` | `code-reviewer/scripts/` | `--pr`, `--lang`, `--severity-threshold`, `--output json` | Structured findings with CWE ID, severity, line reference, remediation guidance |
| `architecture-advisor_tool.py` | `architecture-advisor/scripts/` | `--design-doc`, `--review-type`, `--threat-model`, `--output json` | Architecture risk assessment, design recommendations, security debt register |

All tools accept `--help` and `--output json` for machine-readable structured output.

```bash
python engineering/code-reviewer/scripts/code-reviewer_tool.py --help
python engineering/architecture-advisor/scripts/architecture-advisor_tool.py --help
```

---

## Skill Differentiation

The two skills in this domain are complementary and address different points in the engineering lifecycle.

| Attribute | code-reviewer | architecture-advisor |
|---|---|---|
| Primary input | Pull request diff, code file, snippet | Design document, ADR, architecture diagram, RFC |
| Evaluation scope | Implementation-level: specific lines, functions, data flows | Design-level: system components, trust boundaries, data classification |
| Finding granularity | Line-precise findings with CWE ID | Architectural risk themes with blast radius estimation |
| Primary consumer | Developer who wrote the code | Engineering lead, architect, security architect |
| Lifecycle stage | PR / code review stage | Design and planning stage; post-incident architectural review |
| Automation role | Can serve as a PR review gate with `--severity-threshold` | Primarily advisory; not suited to fully automated gate decisions |

---

## Domain Best Practices

1. **Apply code-reviewer to logic, not just patterns.** Automated SAST tools catch known vulnerability patterns. The code-reviewer skill's value is in applying security reasoning to logic: authentication bypass paths, TOCTOU race conditions, error handling that leaks state, business logic flaws in multi-step workflows. Do not use this skill solely to re-surface findings that a SAST tool would already catch. Configure `appsec-devsecops/appsec-code-review` for automated pattern scanning; use `engineering/code-reviewer` for expert logic review.

2. **Architecture reviews must precede implementation, not follow it.** An architecture-advisor review conducted after a system is built is a post-mortem, not a gate. Schedule architecture security reviews during the design phase, before significant implementation effort is invested. The cost of an architectural security finding at the design stage is substantially lower than the same finding post-deployment.

3. **Findings must be CWE-classified and severity-graded before routing.** All code-reviewer outputs must carry CWE identifiers and severity grades (Critical, High, Medium, Low) before being routed to developers or aggregated into findings trackers. Unclassified findings create ambiguity in prioritization and SLA tracking. Use `--output json` to ensure structured output is always produced.

4. **Architecture risk findings must include blast radius estimates.** An architecture-advisor finding that identifies a design flaw without estimating the blast radius — how many systems, data classes, or user populations are affected if the flaw is exploited — is incomplete. Blast radius estimates are required for prioritizing architectural remediation against feature work in engineering planning cycles.

5. **Cross-domain routing is the expected outcome for Critical findings.** A Critical finding from code-reviewer should be routed to `appsec-devsecops/sast-dast-coordinator` for deduplication against scanner results, then to `governance/findings-tracker` for lifecycle management and SLA enforcement. An architecture-advisor finding that identifies a systemic design weakness should be routed to `governance/security-architecture` for program-level tracking. Engineering domain skills are producers of findings, not lifecycle managers of them.

---

## Workflow: Pull Request Security Review

This workflow applies code-reviewer as an expert advisory layer on top of automated SAST results.

```
Step 1 — Automated Gate (appsec-devsecops/appsec-code-review)
  Run the automated SAST-based gate first. Block on Critical/High pattern findings.

Step 2 — Expert Logic Review (engineering/code-reviewer)
  python engineering/code-reviewer/scripts/code-reviewer_tool.py \
    --pr <pr-id> --lang <language> --severity-threshold medium --output json
  Focus: Authentication/authorization logic, session management, input handling edge cases,
         business logic flaws that scanner pattern matching does not cover.

Step 3 — Finding Consolidation (appsec-devsecops/sast-dast-coordinator)
  Merge expert review findings with automated scan results.
  Deduplicate; apply unified severity grades.

Step 4 — Decision
  Critical / High (any source) --> Block merge; require security team sign-off
  Medium --> Track; allow merge with finding registered
  Low / Informational --> Comment; no gate impact
```

---

## Related Domains

| Domain | Directory | Relationship |
|---|---|---|
| AppSec & DevSecOps | `appsec-devsecops/` | code-reviewer expert findings supplement automated SAST output from appsec-code-review; architecture-advisor design reviews inform secure-sdlc threat modeling |
| Governance | `governance/` | Critical findings from both skills route to findings-tracker; architecture risk findings route to security-architecture for program-level tracking |
| Detection | `detection/` | Logic flaw findings that survive to production become use cases for detection-engineering rule authoring |

---

## Standards and Frameworks Referenced

| Standard | Application in this Domain |
|---|---|
| OWASP Top 10 (2021) | Primary vulnerability taxonomy for code-reviewer findings |
| CWE Top 25 | Finding classification; CWE IDs required on all code-reviewer output |
| OWASP SAMM 2.0 | Architecture security maturity reference for architecture-advisor |
| NIST SP 800-53 (rev 5) | Control framework reference for architecture-advisor gap analysis |
| Zero Trust Architecture (NIST SP 800-207) | Design evaluation framework for architecture-advisor |
| STRIDE Threat Modeling | Threat modeling methodology referenced in architecture-advisor |
