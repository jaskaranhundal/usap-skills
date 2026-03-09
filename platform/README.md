# Platform Operations

Security-aware operational guidance for production system reliability, runbook review, and incident execution under SRE conditions.

---

## Domain Overview

The `platform/` domain applies security reasoning to site reliability engineering practice. The sre-runbook-advisor skill reviews production runbooks for security completeness, guides security-aware execution sequences during active incidents, and produces post-incident improvements that address security gaps surfaced under operational pressure.

---

## Skills

| Skill | Description | Key Use Case |
|---|---|---|
| sre-runbook-advisor | Applies security reasoning to SRE runbooks. Reviews runbooks for evidence preservation gaps, authorization requirements, and change logging completeness. Provides execution-mode guidance during active incidents with security checkpoints inserted at critical steps. | Quarterly runbook security review; security-aware incident execution guidance; post-incident runbook improvement |

---

## Quick Commands

```bash
# Review a runbook for security gaps
python platform/sre-runbook-advisor/scripts/sre-runbook-advisor_tool.py \
  --runbook path/to/runbook.md --mode review --output json

# Execution-mode guidance during an active incident
python platform/sre-runbook-advisor/scripts/sre-runbook-advisor_tool.py \
  --runbook path/to/runbook.md --mode execute --incident-type database-failover --output json

# Post-incident improvement recommendations
python platform/sre-runbook-advisor/scripts/sre-runbook-advisor_tool.py \
  --runbook path/to/runbook.md --mode improve --output json
```

---

## Directory Structure

```
platform/
├── CLAUDE.md                              # Authoritative domain guide
├── README.md                              # This file
└── sre-runbook-advisor/
    ├── SKILL.md
    ├── README.md
    ├── scripts/sre-runbook-advisor_tool.py
    ├── references/
    ├── assets/
    └── expected_outputs/
```

---

## Related Domains

- [response/](../response/) — Active incidents coordinate with response/incident-commander; sre-runbook-advisor provides the security-aware SRE execution layer
- [governance/](../governance/) — Runbook security gaps route to findings-tracker for lifecycle management and SLA enforcement

## Full Domain Guide

For complete methodology, runbook review workflow, best practices, and domain context, see [CLAUDE.md](./CLAUDE.md).
