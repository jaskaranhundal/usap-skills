# Engineering Security

Expert-level security review skills for code and system architecture, designed to complement automated scanning with structured security reasoning.

---

## Domain Overview

The `engineering/` domain provides two advisory skills that apply security expertise to the software delivery lifecycle. code-reviewer evaluates pull requests and code changes for logic flaws, OWASP Top 10 vulnerabilities, and CWE-classified weaknesses that automated SAST tools are likely to miss. architecture-advisor evaluates system designs, architectural decision records, and infrastructure blueprints for systemic risk, zero trust alignment, and long-horizon security debt.

These skills are expert advisory layers, not pipeline automation tools. For automated SAST/DAST gate execution, see the `appsec-devsecops/` domain.

---

## Skills

| Skill | Description | Key Use Case |
|---|---|---|
| code-reviewer | Security-focused code review applying OWASP Top 10, CWE Top 25, and logic flaw analysis to pull requests and code changes. Produces line-precise structured findings with remediation guidance. | Expert PR review gate; logic flaw analysis on authentication and authorization code |
| architecture-advisor | Security review of system designs and ADRs. Evaluates zero trust alignment, threat model completeness, blast radius of design decisions, and architectural security debt. | Pre-implementation architecture gate; post-incident architectural risk assessment |

---

## Quick Commands

**code-reviewer**
```bash
python engineering/code-reviewer/scripts/code-reviewer_tool.py --help
python engineering/code-reviewer/scripts/code-reviewer_tool.py --pr 1234 --lang python --severity-threshold medium --output json
```

**architecture-advisor**
```bash
python engineering/architecture-advisor/scripts/architecture-advisor_tool.py --help
python engineering/architecture-advisor/scripts/architecture-advisor_tool.py --design-doc path/to/adr.md --review-type full --output json
```

---

## Directory Structure

```
engineering/
├── CLAUDE.md                              # Authoritative domain guide
├── README.md                              # This file
├── code-reviewer/
│   ├── SKILL.md
│   ├── README.md
│   ├── scripts/code-reviewer_tool.py
│   ├── references/
│   ├── assets/
│   └── expected_outputs/
└── architecture-advisor/
    ├── SKILL.md
    ├── README.md
    ├── scripts/architecture-advisor_tool.py
    ├── references/
    ├── assets/
    └── expected_outputs/
```

---

## Finding Severity Reference

| Severity | code-reviewer Action | architecture-advisor Action |
|---|---|---|
| Critical | Block merge immediately; security team sign-off required | Block design progression; mandatory remediation before implementation |
| High | Block merge; security team sign-off required to override | Flag for architectural remediation; track in security-architecture |
| Medium | Warn; allow merge with tracked finding | Track as security debt; address in next architectural review cycle |
| Low / Informational | Comment only; no gate impact | Note for awareness; no required action |

---

## Related Domains

- [appsec-devsecops/](../appsec-devsecops/) — Automated SAST/DAST gate execution; code-reviewer expert findings supplement appsec-code-review automated output
- [governance/](../governance/) — Critical findings route to findings-tracker; architecture risk findings route to security-architecture

## Full Domain Guide

For complete methodology, skill differentiation matrix, workflow patterns, best practices, and standards coverage, see [CLAUDE.md](./CLAUDE.md).
