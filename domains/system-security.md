# System Security Domain

Skills in this domain assess and harden operating system and host configurations against recognized security baselines (CIS Benchmarks, DISA STIGs, NSA hardening guides).

## Skills

| Slug | Level | Description |
|---|---|---|
| `os-hardening` | L4 | OS configuration assessment against CIS Benchmarks, DISA STIGs, and NSA guides with prioritized, evidence-backed remediation |

## Workflow: Hardening Assessment

```
os-hardening → vulnerability-management → detection-engineering
```

## Key MITRE ATT&CK Phases Covered

- Persistence (TA0003)
- Privilege Escalation (TA0004)
- Defense Evasion (TA0005)

## Orchestrator Agent

[cs-blue-team-analyst](../agents/security/cs-blue-team-analyst.md) — incorporates host-hardening findings into blue-team detection and response workflows.
