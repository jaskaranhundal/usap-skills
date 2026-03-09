# Response Domain

The response domain provides skills for the complete security incident lifecycle: from initial triage and severity declaration through active containment, digital forensics, post-incident review, and board-level communication. It implements the Incident Command System (ICS) model adapted for cybersecurity operations and aligns with NIST SP 800-61 Rev 2.

Skills in this domain are designed to be invoked in coordinated sequences by the `cs-incident-responder` orchestrator agent, or individually by SOC analysts for standalone triage, containment, and forensics workflows.

---

## Skills

| Skill | Slug | Level | Description |
|---|---|---|---|
| [incident-commander](incident-commander/README.md) | `response/incident-commander` | L3 | ICS-model incident command: SEV1–SEV4 declaration, response track assignment, regulatory deadline tracking, decision authority coordination |
| [incident-classification](incident-classification/README.md) | `response/incident-classification` | L3 | Universal first-triage: classifies events into 14 incident types, scores severity, identifies false positives, routes escalation |
| [containment-advisor](containment-advisor/README.md) | `response/containment-advisor` | L3 | Blast-radius-aware containment strategies across 10 threat types; production impact assessment; human approval enforcement |
| [forensics](forensics/README.md) | `response/forensics` | L3 | Legally defensible digital forensics: DFRWS six-phase framework, chain-of-custody compliance, dwell time estimation, IOC extraction |
| [zero-day-response](zero-day-response/README.md) | `response/zero-day-response` | L3 | Zero-day compensating controls: exposure scoring, 5 control options (WAF, network block, feature disable, isolation, detection sensitivity), vendor patch timeline tracking |
| [zero-day-response-governance](zero-day-response-governance/README.md) | `response/zero-day-response-governance` | L2 | Board and executive coordination for zero-day events: communication matrix, regulatory notification deadlines, emergency change management |

---

## Orchestrator Agent

**[cs-incident-responder](../agents/security/cs-incident-responder.md)** — Full incident lifecycle manager that coordinates all response domain skills from initial triage through post-incident closure. Designed for SOC leads and incident commanders managing active SEV1–SEV4 events.

The cs-incident-responder agent runs the following skills in sequence and in parallel depending on incident severity:

```
incident-classification
  -> incident-commander
     -> containment-advisor  (parallel)
     -> forensics            (parallel)
     -> zero-day-response    (if no patch available)
        -> zero-day-response-governance
```

---

## Quick Command Reference

Run any skill tool individually from its script directory:

```bash
# Initial triage — classify the incoming event
python response/incident-classification/scripts/incident-classification_tool.py --output json

# Declare severity and activate ICS response tracks
python response/incident-commander/scripts/incident-commander_tool.py --output json

# Assess containment options with blast radius
python response/containment-advisor/scripts/containment-advisor_tool.py --output json

# Start forensic evidence collection
python response/forensics/scripts/forensics_tool.py --output json

# Score zero-day exposure and select compensating controls
python response/zero-day-response/scripts/zero-day-response_tool.py --output json

# Coordinate board and regulatory communication
python response/zero-day-response-governance/scripts/zero-day-response-governance_tool.py --output json
```

All tools support `--help` for full parameter documentation and emit structured JSON compatible with the USAP evidence chain schema.

---

## Incident Response Lifecycle

```
1. Detection      incident-classification   — Classify event type, score severity
2. Declaration    incident-commander        — Declare SEV level, start regulatory clock
3. Tracks         incident-commander        — Assign containment / investigation / notification / recovery
4. Containment    containment-advisor       — Recommend strategy, assess blast radius (human approval required)
5. Forensics      forensics                 — Collect volatile evidence, establish chain of custody
6. Zero-Day       zero-day-response         — Compensating controls if no patch available
7. Governance     zero-day-response-governance — Executive communication, regulatory filing
```

---

## SEV Level Summary

| Level | Name | Response SLA | Bridge Call |
|---|---|---|---|
| SEV1 | Critical | 15 minutes | Immediate war room |
| SEV2 | High | 1 hour | Within 30 minutes |
| SEV3 | Medium | 4 hours | Async coordination |
| SEV4 | Low | 24 hours | Ticket-based |

---

## Related Domains

- [detection/](../detection/) — Upstream signal source; provides alerts and telemetry that trigger incident-classification
- [governance/](../governance/) — Downstream consumer; compliance-mapping and audit-assurance skills receive incident records
- [risk-compliance/](../risk-compliance/) — Post-incident findings tracking and vulnerability lifecycle management

---

## Domain Guide

For full domain documentation including Python tool reference, regulatory notification deadlines, cross-skill workflow sequences, and best practices, see **[CLAUDE.md](CLAUDE.md)**.
