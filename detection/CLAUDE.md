# Detection Domain — CLAUDE.md

## Purpose

The Detection domain contains skills for identifying adversary presence, surfacing exposure, and maintaining the quality of security telemetry. Skills in this domain span the full detection lifecycle: from proactive threat hunting and behavioral anomaly analysis through secrets exposure, network and attack surface enumeration, threat intelligence enrichment, detection rule engineering, and deception technology deployment.

Detection skills are primarily read-only analysts — they query, score, correlate, and report. Mutating actions (blocking indicators, isolating hosts, deploying deceptive assets) require explicit human approval gates. All detection outputs are structured payloads consumable by downstream response, governance, and risk skills.

Subdomains covered by this domain:
- Threat hunting (hypothesis-driven, IOC-driven, anomaly-driven)
- Secrets and credential exposure
- Behavioral analytics and user/entity risk scoring (UEBA)
- Telemetry signal quality and data source health
- Network exposure and open service enumeration
- Attack surface management and external asset discovery
- Threat intelligence enrichment and actor attribution
- Detection engineering (rule authoring, coverage gap analysis, alert quality)
- Deception technology (honeypots, canary tokens, lateral movement traps)

---

## Skills Catalog

| Skill | Slug | Primary Tool | MITRE Coverage |
|---|---|---|---|
| threat-hunting | detection/threat-hunting | threat-hunting_tool.py | TA0009, TA0006, TA0007 |
| secrets-exposure | detection/secrets-exposure | secrets-exposure_tool.py | T1552, T1078 |
| behavioral-analytics | detection/behavioral-analytics | behavioral-analytics_tool.py | TA0006, T1078, T1133 |
| telemetry-signal-quality | detection/telemetry-signal-quality | telemetry-signal-quality_tool.py | (Data Quality) |
| network-exposure | detection/network-exposure | network-exposure_tool.py | T1046, T1595, T1590 |
| attack-surface-management | detection/attack-surface-management | attack-surface-management_tool.py | T1595, T1591, T1596 |
| threat-intelligence | detection/threat-intelligence | threat-intelligence_tool.py | All ATT&CK phases |
| detection-engineering | detection/detection-engineering | detection-engineering_tool.py | All ATT&CK phases |
| deception-honeypot | detection/deception-honeypot | deception-honeypot_tool.py | TA0001, TA0003, TA0007 |

All skill paths are relative from the repository root as `detection/<slug>/`. For example, the threat-hunting skill lives at `detection/threat-hunting/`.

---

## Python Tools Reference

| Tool | Path | Purpose | Key Args |
|---|---|---|---|
| threat-hunting_tool.py | detection/threat-hunting/scripts/threat-hunting_tool.py | Executes hunt playbooks, scores hypotheses, estimates dwell time | `--playbook`, `--lookback-days`, `--output` |
| secrets-exposure_tool.py | detection/secrets-exposure/scripts/secrets-exposure_tool.py | Scans for 15 secret types, entropy scoring, blast radius estimation | `--scope`, `--entropy-threshold`, `--output` |
| scan_for_secrets.py | detection/secrets-exposure/scripts/scan_for_secrets.py | Raw secrets scan runner invoked by secrets-exposure_tool | `--path`, `--format` |
| pre_analysis.py | detection/secrets-exposure/scripts/pre_analysis.py | Pre-scan validation and context setup for secrets exposure | `--target`, `--config` |
| behavioral-analytics_tool.py | detection/behavioral-analytics/scripts/behavioral-analytics_tool.py | UEBA entity risk scoring, insider threat pattern detection, account takeover identification | `--entity`, `--baseline-days`, `--risk-threshold`, `--output` |
| telemetry-signal-quality_tool.py | detection/telemetry-signal-quality/scripts/telemetry-signal-quality_tool.py | Assesses data source health, dedup confidence, normalization error rates | `--source`, `--window`, `--output` |
| network-exposure_tool.py | detection/network-exposure/scripts/network-exposure_tool.py | Open port enumeration, firewall rule analysis, internet-facing service inventory | `--target`, `--ports`, `--output` |
| attack-surface-management_tool.py | detection/attack-surface-management/scripts/attack-surface-management_tool.py | Discovers public-facing assets: domains, IPs, ports, web properties | `--org`, `--scope`, `--output` |
| threat-intelligence_tool.py | detection/threat-intelligence/scripts/threat-intelligence_tool.py | IOC enrichment, actor attribution, TTP mapping to ATT&CK | `--ioc`, `--type`, `--output` |
| detection-engineering_tool.py | detection/detection-engineering/scripts/detection-engineering_tool.py | Rule authoring, coverage gap analysis, alert fidelity scoring | `--rule`, `--coverage-map`, `--output` |
| deception-honeypot_tool.py | detection/deception-honeypot/scripts/deception-honeypot_tool.py | Honeypot placement strategy, canary token generation, lateral movement trap design | `--environment`, `--density`, `--output` |

---

## Domain Best Practices

1. **Verify telemetry health before acting on absence of evidence.** A clean hunt result is only valid when the underlying data sources are confirmed healthy. Always run `telemetry-signal-quality` before drawing conclusions from negative hunt findings. An absence of evidence in a broken data pipeline is not evidence of absence.

2. **Every hypothesis must be falsifiable.** Hypothesis-driven hunting requires a pre-stated definition of what a positive finding looks like before any queries are executed. Vague hypotheses produce vague results. Structure every hypothesis as: "Threat actor using [TTP] would produce [observable] in [data source] between [time bounds]."

3. **Corroborate findings across at least two independent data sources.** Single-source observations are flagged as unconfirmed and must not trigger escalation or remediation. If two sources cannot corroborate, document the finding as an unconfirmed indicator and schedule a re-hunt within 48 hours.

4. **Document clean hunts formally.** A hunt sprint that finds nothing is as operationally valuable as one that finds an active threat — if documented correctly. A clean hunt without explicit data scope, time bounds, and data quality attestation is not a valid clean hunt.

5. **Scope blast radius before blocking.** When a secrets-exposure or threat-hunting finding produces a candidate for blocking or revocation, always pass the finding through blast-radius assessment. A legitimate service account may be sharing a credential with production workloads — revocation without scoping can cause an outage.

6. **Entropy alone does not confirm a secret.** Entropy scoring is a signal, not a verdict. High-entropy strings appear in base64-encoded images, compressed data, and UUIDs. Combine entropy thresholds with pattern matching (regex for AWS key format, PEM header presence, known secret prefixes) before classifying a finding as an exposed credential.

7. **ATT&CK coverage maps are living documents.** After each detection-engineering sprint or hunt campaign, update the ATT&CK Navigator coverage map to reflect newly authored rules and confirmed detection gaps. Coverage maps that are more than 90 days stale are unreliable for risk reporting.

8. **Deception assets require maintenance schedules.** Honeypots and canary tokens that are deployed and forgotten become background noise. Establish a 30-day review cycle for deception asset inventory — verify tokens are still reachable, confirm alerting integrations are functional, and rotate credentials to prevent legitimization by attackers who discover the deception.

9. **Threat intelligence has an expiry.** IOC feeds degrade over time as attacker infrastructure rotates. Tag every imported IOC with a confidence level and expiry date (default: 30 days for IP addresses, 90 days for domains, 180 days for file hashes). Expired IOCs in active block lists create false positives and erode analyst trust.

10. **Behavioral baselines must account for business cycles.** UEBA anomaly detection that compares weekday behavior against holiday periods will generate high false-positive rates. Ensure behavioral baselines are segmented by day-of-week, business quarter, and known organizational event calendars (earnings periods, product launches, open enrollment) before scoring anomalies.

---

## Workflow Patterns

### Workflow 1: Alert to Evidence

This workflow converts a raw SIEM alert or threat intelligence report into a structured, escalation-ready evidence package. It moves from enrichment through behavioral context to hunt confirmation.

```
threat-intelligence          (enrich IOC, map to ATT&CK TTPs, attribute to actor)
       |
       v
behavioral-analytics         (score impacted entities, check for related anomalies)
       |
       v
threat-hunting               (run targeted playbook against relevant data sources)
       |
       v
telemetry-signal-quality     (validate data source coverage for the hunt period)
       |
       v
[escalate to response/incident-commander if confirmed]
```

Skills invoked in sequence. Output of each skill is passed as context to the next. The telemetry-signal-quality check at the end validates the evidentiary basis before escalation. If data quality is insufficient, return to threat-hunting with an updated scope that excludes the degraded sources.

---

### Workflow 2: Proactive Hunt Campaign

A scheduled two-week hunt sprint. Starts with intelligence-driven hypothesis generation, executes structured playbooks across all relevant data sources, and closes with detection engineering improvements for any gaps found.

```
threat-intelligence          (generate TTP-aligned hypotheses from current actor reports)
       |
       v
attack-surface-management    (confirm which assets are in scope and exposed)
       |
       v
network-exposure             (identify internet-facing services relevant to the TTP)
       |
       v
threat-hunting               (execute hypothesis-driven playbooks, document verdicts)
       |
       v
behavioral-analytics         (check entity anomaly scores for hosts/accounts in scope)
       |
       v
detection-engineering        (author new rules for gaps identified; update coverage map)
```

All skill outputs feed into a single Hunt Sprint Report. Clean hunt verdicts are archived. Confirmed findings escalate to response. Detection gaps produce new rule candidates.

---

### Workflow 3: Telemetry Quality Gate

A pre-hunt gate run at the start of every sprint to confirm that required data sources are healthy enough to support valid hunt verdicts.

```
telemetry-signal-quality     (assess all required sources: EDR, DNS, proxy, auth logs, cloud audit)
       |
       +--> [source healthy]      --> proceed with threat-hunting sprint
       |
       +--> [source degraded]     --> alert to engineering, document gap, narrow hunt scope
       |
       +--> [source missing]      --> halt sprint for that data source, escalate as data risk
```

This gate runs before every scheduled hunt sprint and before any reactive hunt triggered by a threat intelligence alert. A hunt that begins without a telemetry health check produces verdicts of unknown validity.

---

## MITRE ATT&CK Phase Coverage

| ATT&CK Tactic | ID | Covering Skills |
|---|---|---|
| Reconnaissance | TA0043 | attack-surface-management, network-exposure, threat-intelligence |
| Resource Development | TA0042 | threat-intelligence |
| Initial Access | TA0001 | deception-honeypot, threat-hunting, behavioral-analytics |
| Execution | TA0002 | threat-hunting, behavioral-analytics, detection-engineering |
| Persistence | TA0003 | deception-honeypot, threat-hunting, behavioral-analytics |
| Privilege Escalation | TA0004 | behavioral-analytics, secrets-exposure, threat-hunting |
| Defense Evasion | TA0005 | threat-hunting, detection-engineering, behavioral-analytics |
| Credential Access | TA0006 | secrets-exposure, threat-hunting, behavioral-analytics |
| Discovery | TA0007 | threat-hunting, deception-honeypot, network-exposure |
| Lateral Movement | TA0008 | threat-hunting, behavioral-analytics, deception-honeypot |
| Collection | TA0009 | threat-hunting, behavioral-analytics |
| Command and Control | TA0011 | threat-hunting, network-exposure, threat-intelligence |
| Exfiltration | TA0010 | threat-hunting, behavioral-analytics, network-exposure |
| Impact | TA0040 | detection-engineering, threat-intelligence |

Specific technique coverage (non-exhaustive):

| Technique | ID | Skill |
|---|---|---|
| Valid Accounts | T1078 | secrets-exposure, behavioral-analytics |
| Credentials in Files | T1552 | secrets-exposure |
| External Remote Services | T1133 | behavioral-analytics, network-exposure |
| Network Service Discovery | T1046 | network-exposure |
| Active Scanning | T1595 | attack-surface-management, network-exposure |
| Gather Victim Network Information | T1590 | attack-surface-management, network-exposure |
| Search Open Technical Databases | T1596 | attack-surface-management, threat-intelligence |
| Gather Victim Org Information | T1591 | attack-surface-management, threat-intelligence |

---

## Related Domains

### response/

Skills in `response/` are the primary downstream consumers of confirmed detection findings. When threat-hunting escalates a confirmed active threat, or when behavioral-analytics flags a high-risk entity, the structured payload is consumed by:

- `response/incident-classification` — first triage, severity assignment, false positive ruling
- `response/incident-commander` — active incident command for SEV1-3 events
- `response/containment-advisor` — containment strategy and blast radius scoping
- `response/forensics` — legally defensible evidence collection and chain-of-custody

Full domain reference: `response/CLAUDE.md`

### appsec-devsecops/

Skills in `appsec-devsecops/` share telemetry and findings with detection in both directions:

- `appsec-devsecops/pipeline-security-scan` produces secrets findings that feed `detection/secrets-exposure` for post-deployment validation
- `detection/detection-engineering` coverage maps inform `appsec-devsecops/devsecops-pipeline` on which detection rules are active for a given application stack
- `appsec-devsecops/sast-dast-coordinator` findings inform behavioral-analytics entity risk scores for application-layer accounts

Full domain reference: `appsec-devsecops/CLAUDE.md`

---

## Path Reference

All skill paths in this domain are relative from the repository root using the convention `detection/<slug>/`. Sub-paths within each skill follow the standard USAP skill layout:

```
detection/<slug>/
  README.md          -- skill overview and quick commands
  SKILL.md           -- full skill specification and methodology
  scripts/           -- executable Python tools
  references/        -- supporting documentation
  expected_outputs/  -- representative tool outputs for validation
  assets/            -- supporting data files
```

To invoke any tool directly from the repository root:

```bash
python detection/<slug>/scripts/<tool>.py --help
```

Example:

```bash
python detection/threat-hunting/scripts/threat-hunting_tool.py --playbook wmi-lateral-movement --lookback-days 30 --output json
python detection/secrets-exposure/scripts/secrets-exposure_tool.py --scope repo --entropy-threshold 4.5 --output json
python detection/telemetry-signal-quality/scripts/telemetry-signal-quality_tool.py --source all --window 24h --output json
```
