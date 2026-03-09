# Response Domain

Skills in this domain manage the full incident lifecycle from triage through forensic collection and post-incident review.

## Skills

| Slug | Level | Description |
|---|---|---|
| `incident-commander` | L2 | Active incident command (ICS model): SEV1-4 declaration, response tracks, regulatory deadlines |
| `incident-classification` | L3 | Universal first-triage: classifies events into 14 types, assigns severity, identifies false positives |
| `containment-advisor` | L3 | Recommends containment strategies across 10 threat types; assesses blast radius and production impact |
| `forensics` | L3 | Legally defensible digital forensics: DFRWS six-phase framework, chain-of-custody, dwell time |
| `zero-day-response` | L3 | Zero-day compensating controls: exposure scoring, 5 control options, vendor timeline tracking |
| `zero-day-response-governance` | L2 | Board/executive coordination for zero-day events: communication matrix, regulatory deadlines |

## Workflow: Incident Response Lifecycle

```
incident-classification → incident-commander → containment-advisor → forensics → compliance-mapping
```

## ICS Severity Levels

| Level | Name | Response SLA |
|---|---|---|
| SEV1 | Critical | 15 min |
| SEV2 | High | 1 hour |
| SEV3 | Medium | 4 hours |
| SEV4 | Low | 24 hours |

## Orchestrator Agent

[cs-incident-responder](../agents/security/cs-incident-responder.md) — manages full incident lifecycle across response skills.
