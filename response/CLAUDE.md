# Response Domain — CLAUDE.md

This file is the authoritative domain guide for Claude agents operating within the `response/` skill domain of the USAP skills repository. It covers the purpose of the domain, the full skills catalog, Python tool references, incident response lifecycle procedures, severity matrices, regulatory deadline obligations, best practices, and cross-skill workflow sequences.

---

## Purpose

The response domain provides skills for the full incident lifecycle from the moment a security event is detected through triage, active containment, digital forensics, post-incident review, and board-level communication. It implements the Incident Command System (ICS) model adapted for cybersecurity operations, aligns with NIST SP 800-61 Rev 2, and integrates MITRE ATT&CK coverage across all response phases.

Domain responsibilities:

- **Incident command**: Severity declaration (SEV1–SEV4), response track assignment, regulatory clock activation, and decision authority coordination across all response agents.
- **Triage**: Universal first-triage classifying events into 14 incident types, severity scoring, false positive identification, and escalation routing.
- **Containment**: Blast-radius-aware containment strategy selection across 10 threat types with production impact assessment and human approval enforcement.
- **Forensics**: Legally defensible evidence collection, chain-of-custody compliance, DFRWS six-phase framework execution, and dwell time estimation.
- **Zero-day response**: Exposure scoring, compensating control selection (5 options), vendor timeline tracking, and emergency change management when no patch is available.
- **Zero-day governance**: Board and executive communication coordination, regulatory deadline tracking, and cross-organizational escalation matrix management.

Agents in this domain interact with the `detection/` domain (upstream signal sources), the `governance/` domain (regulatory notification and audit requirements), and the `risk-compliance/` domain (findings lifecycle and vulnerability tracking).

---

## Skills Catalog

| Skill | Slug | Primary Tool | MITRE Coverage |
|---|---|---|---|
| incident-commander | response/incident-commander | incident-commander_tool.py | All phases (command) |
| incident-classification | response/incident-classification | incident-classification_tool.py | TA0001–TA0010 (triage) |
| containment-advisor | response/containment-advisor | containment-advisor_tool.py | TA0005, TA0008 (containment) |
| forensics | response/forensics | forensics_tool.py | TA0009, TA0010 (collection) |
| zero-day-response | response/zero-day-response | zero-day-response_tool.py | T1190, T1203 (vuln exploitation) |
| zero-day-response-governance | response/zero-day-response-governance | zero-day-response-governance_tool.py | Governance layer |

### Skill Level and Plane Summary

| Skill | Level | Plane | Approval Required | Mutating Intents |
|---|---|---|---|---|
| incident-commander | L3 | work | CISO / security_director | network_change, credential_operation, device_config_change, remediation_action |
| incident-classification | L3 | work | None (read_only) | None |
| containment-advisor | L3 | work | soc_lead, ciso | remediation_action, network_change, credential_operation |
| forensics | L3 | work | incident_commander (for evidence actions) | remediation_action |
| zero-day-response | L3 | work | CISO (for isolation); human approval for all controls | device_config_change, external_communication |
| zero-day-response-governance | L2 | control | CISO + Legal (for external notifications) | external_communication |

---

## Python Tools Reference

| Tool File | Skill | Invocation | Output Format | Primary Use |
|---|---|---|---|---|
| `incident-commander_tool.py` | incident-commander | `python scripts/incident-commander_tool.py --output json` | JSON | SEV declaration, response track activation, regulatory clock |
| `incident-classification_tool.py` | incident-classification | `python scripts/incident-classification_tool.py --output json` | JSON | Event triage, type classification, false positive detection |
| `containment-advisor_tool.py` | containment-advisor | `python scripts/containment-advisor_tool.py --output json` | JSON | Containment strategy, blast radius, production impact |
| `forensics_tool.py` | forensics | `python scripts/forensics_tool.py --output json` | JSON | Evidence collection, timeline reconstruction, chain of custody |
| `zero-day-response_tool.py` | zero-day-response | `python scripts/zero-day-response_tool.py --output json` | JSON | Exposure scoring, compensating controls, patch tracking |
| `zero-day-response-governance_tool.py` | zero-day-response-governance | `python scripts/zero-day-response-governance_tool.py --output json` | JSON | Board communication, regulatory deadlines, escalation matrix |

All tools accept `--help` for parameter documentation. All tools emit structured JSON compatible with the USAP evidence chain schema.

---

## Incident Response Lifecycle

The response domain implements a seven-step procedure aligned with NIST SP 800-61 and the ICS model. Each step maps to one or more skills.

### Step 1: Detection and Initial Notification

An event arrives from the `detection/` domain (SIEM alert, EDR detection, threat intelligence feed, user report) or from an automated pipeline trigger. The `incident-classification` skill performs initial triage.

**Skill invoked:** `incident-classification`
**Output:** `incident_type`, `severity_assessment`, `false_positive_flag`, `escalation_recommendation`

### Step 2: Severity Declaration

Based on the classification output, `incident-commander` declares a severity level (SEV1–SEV4) and opens the incident command structure. The regulatory notification clock starts at this step.

**Skill invoked:** `incident-commander`
**Output:** `incident_severity`, `response_tracks`, `regulatory_notification_required`, `notification_deadline_utc`

### Step 3: Response Track Activation

The incident commander assigns parallel response tracks: containment, investigation, notification, and recovery. Each track is assigned to a USAP agent or human role.

**Skills involved:** All domain skills may be activated in parallel at this step depending on SEV level.

### Step 4: Containment

`containment-advisor` assesses blast radius and recommends the most targeted containment action for the confirmed threat type. All containment actions that modify system state are mutating and require human approval before execution.

**Skill invoked:** `containment-advisor`
**Output:** `recommended_strategy`, `blast_radius`, `production_impact`, `urgency`, `mutating_category`, `approver_roles`

### Step 5: Forensic Collection and Evidence Preservation

Concurrent with containment, `forensics` initiates evidence collection following the DFRWS six-phase framework. Volatile evidence (memory, network connections, running processes) is captured first. All evidence items are hashed (SHA-256) and logged in the chain of custody.

**Skill invoked:** `forensics`
**Output:** `timeline`, `iocs_identified`, `evidence_preservation_actions`, `dwell_time_estimate`, `legal_hold_required`

### Step 6: Zero-Day Handling (Conditional)

If the incident involves a CVE with no available vendor patch, `zero-day-response` computes exposure scores for affected assets and recommends compensating controls from a five-option control set. `zero-day-response-governance` manages executive communication and regulatory tracking.

**Skills invoked:** `zero-day-response`, `zero-day-response-governance`
**Output:** Exposure scoring table, compensating control plan, vendor timeline record, executive communication matrix

### Step 7: Post-Incident Review

Following eradication and recovery, the incident record is finalized. The forensics output provides the technical timeline and evidence inventory. `incident-commander` closes the incident and triggers handoff to `risk-compliance/` for findings tracking and lessons-learned integration.

**Skills involved:** `forensics` (final report), `incident-commander` (incident closure)

---

## SEV Level Matrix

| Level | Name | Criteria | Response SLA | Skills Invoked | Escalation Path |
|---|---|---|---|---|---|
| SEV1 | Critical | Confirmed ransomware or destructive malware in production; active exfiltration of PII/PHI/financial data (>10K records); full network compromise or domain controller breach; defense evasion detected (CloudTrail disabled, SIEM wiped); supply chain compromise (build system breach) | 15 min bridge call; war room immediate | incident-classification, incident-commander, containment-advisor, forensics (parallel) | SOC Lead → CISO → CEO → Board Chair (if data at risk) |
| SEV2 | High | Confirmed unauthorized access to sensitive systems; credential compromise with elevated privileges; lateral movement detected and confirmed; ransomware indicators without confirmed execution | 1 hour bridge; async coordination within 30 min | incident-classification, incident-commander, containment-advisor, forensics | SOC Lead → CISO |
| SEV3 | Medium | Suspected unauthorized access (unconfirmed); malware detected and contained (no spread evidence); single account compromise (no privilege escalation) | 4 hours; async coordination | incident-classification, incident-commander, containment-advisor | SOC Lead → Security Manager |
| SEV4 | Low | Security alert with no confirmed impact; informational indicator; policy violation with no data risk | 24 hours; ticket-based | incident-classification | L3 Analyst queue |

### SEV Escalation Triggers

An incident must be immediately re-declared at a higher SEV level when any of the following indicators are observed:

| Indicator | New Severity |
|---|---|
| Ransomware note found | Escalate to SEV1 |
| Active exfiltration confirmed | Escalate to SEV1 |
| CloudTrail or SIEM disabled | Escalate to SEV1 |
| Domain controller access confirmed | Escalate to SEV1 |
| Second system compromised | Escalate to SEV1 |
| Exfiltration volume exceeds 1 GB | Escalate to SEV2 minimum |
| C-suite account accessed | Escalate to SEV2 minimum |

---

## Regulatory Notification Deadlines

The `incident-commander` and `zero-day-response-governance` skills track regulatory deadlines from the moment an incident is declared. The notification clock starts at declaration, not at investigation completion.

| Framework | Incident Type | Deadline | Skills Used |
|---|---|---|---|
| GDPR (EU 2016/679) | Personal data breach | 72 hours after discovery | incident-commander, zero-day-response-governance |
| PCI-DSS v4.0 | Cardholder data breach | 24 hours after confirmation to acquirer | incident-commander |
| HIPAA (45 CFR Part 164) | PHI breach (>500 individuals) | 60 days after discovery; media notice if >500 in state | incident-commander, zero-day-response-governance |
| NY DFS 23 NYCRR 500 | Cybersecurity event | 72 hours to DFS; annual certification | incident-commander, zero-day-response-governance |
| SEC Cybersecurity Rule (17 CFR 229.106) | Material cybersecurity incident | 4 business days after materiality determination | zero-day-response-governance |
| CCPA / CPRA | Breach of sensitive personal information | Without unreasonable delay; notify AG if >500 CA residents | incident-commander, zero-day-response-governance |
| NIS2 (EU 2022/2555) | Significant incident (operator of essential services) | 24-hour early warning; 72-hour notification | zero-day-response-governance |
| SOX (for material incidents) | Financial system compromise | Immediate disclosure of material weakness | zero-day-response-governance |

**Operational rule:** If the incident scope is unclear at declaration time, assume the most restrictive applicable deadline until scope is confirmed. Document the assumption in the incident record.

---

## Domain Best Practices

1. **Decisiveness over perfection under time pressure.** During a SEV1 incident, a good decision made at T+15 minutes outweighs a perfect decision made at T+45 minutes. All decisions must be logged in the evidence chain, including decisions made under uncertainty.

2. **Volatile evidence first.** Memory, running processes, and active network connections are lost on system shutdown. The forensics skill must be invoked in parallel with containment — never sequentially after containment completes.

3. **Containment approval is non-negotiable.** No containment action that modifies system state (network isolation, credential revocation, firewall rule change) may be executed without explicit human approval. The `containment-advisor` recommends; humans authorize; the tool-execution-broker executes.

4. **The notification clock starts at declaration.** Regulatory deadlines run from the moment the incident is declared, not from investigation completion. When in doubt about regulatory scope, start the clock and confirm scope within the first response window.

5. **Chain of custody is established at evidence collection, not at report time.** Every evidence item must be SHA-256 hashed at the moment of acquisition. Timestamps must be UTC with timezone offset. Tool provenance (FTK Imager, Volatility, AWS CloudTrail export) must be recorded per item.

6. **False positive verification before escalation.** The `incident-classification` skill applies five false positive filters before escalating: known-safe automation, test environment activity, expected batch jobs, whitelisted identities, and scanner activity. Skipping these filters inflates SEV1 declaration rates and degrades SOC credibility.

7. **Zero-day compensating controls are temporary by definition.** Every compensating control deployed in the absence of a vendor patch must carry a documented expiry trigger (patch release date or a specified quarterly review date). Controls that outlive their justification become permanent attack surface.

8. **Regulatory communication is privileged until legal review.** All external communications related to a confirmed breach — to regulators, customers, or media — must be reviewed by Legal and CISO before transmission. `zero-day-response-governance` enforces this gate and must not be bypassed to meet a notification deadline; prepare draft notifications in advance and hold them pending approval.

---

## Cross-Skill Workflow: SEV1 Response Track

The following sequence documents the canonical skill invocation order for a SEV1 incident. Steps 3 and 4 run in parallel.

```
T+0   Detection event arrives from detection/ domain
        |
        v
T+5   [incident-classification]
        Classify event type, score severity, check false positives
        Output: incident_type=ransomware, severity=critical, false_positive=false
        |
        v
T+10  [incident-commander]
        Declare SEV1, open war room, start regulatory clock
        Assign response tracks: containment / investigation / notification / recovery
        Output: incident_severity=sev1, regulatory_deadline=T+72h (GDPR), response_tracks=[...]
        |
        |-----------------------------------------------|
        v                                               v
T+15  [containment-advisor]                     [forensics]
        Identify blast radius                     Acquire volatile evidence (memory, netstat)
        Recommend isolation strategy              Start chain of custody log
        Requires approval: soc_lead + ciso        Hash all evidence at acquisition time
        Output: containment_plan, urgency=immediate    Output: timeline (partial), iocs_identified
        |                                               |
        v                                               v
T+30  [Human approval gate]                     [forensics — continued]
        Operator reviews containment plan         Disk image, CloudTrail, log export
        Approves or modifies                      Reconstruct attacker timeline
        |
        v
T+45  [tool-execution-broker]
        Executes approved containment actions
        |
        v
T+60  [incident-commander]
        Assess containment effectiveness
        Update regulatory notification status
        Brief Legal if PCI/GDPR scope confirmed
        |
        v
     [If zero-day involved]
        |
        v
     [zero-day-response]
        Score exposure for unpatched assets
        Select compensating control option (WAF / network block / feature disable / isolation / detection sensitivity)
        Track vendor patch timeline
        |
        v
     [zero-day-response-governance]
        Prepare board communication
        File regulatory notification (if required)
        Open emergency change record in ITSM
        |
        v
T+4h  Post-containment assessment
        [forensics] final evidence package, dwell time estimate
        [incident-commander] incident status update, next SLA checkpoint
        |
        v
      Eradication and recovery
        [incident-commander] close incident
        Handoff to risk-compliance/ for findings tracking
```

---

## Related Domains

- **detection/**: Upstream signal source. Provides SIEM alerts, EDR detections, and telemetry events that trigger `incident-classification`. The `telemetry-signal-quality` skill in `detection/` assesses the fidelity of incoming signals before classification.
- **governance/**: Downstream consumer of incident records. The `compliance-mapping` and `internal-audit-assurance` skills in `governance/` receive incident summaries for regulatory reporting, audit evidence packages, and policy violation tracking.
- **risk-compliance/**: Receives post-incident findings for vulnerability lifecycle management, lessons-learned integration, and recurrence prevention tracking.
- **agents/security/cs-incident-responder.md**: The orchestrator agent that manages the full SEV1–SEV4 lifecycle by coordinating all skills in this domain.
