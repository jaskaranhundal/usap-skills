# Detection Domain

Skills in this domain focus on identifying adversary presence, monitoring telemetry quality, and surfacing anomalies across the environment.

## Skills

| Slug | Level | Description |
|---|---|---|
| `threat-hunting` | L3 | Hypothesis-driven, IOC-driven, and anomaly-driven threat hunting with 4 built-in playbooks |
| `secrets-exposure` | L4 | Credential exposure analysis: 15 secret types, entropy scoring, blast radius, attacker timeline |
| `behavioral-analytics` | L3 | UEBA: entity risk scoring, insider threat pattern detection, account takeover identification |
| `telemetry-signal-quality` | L3 | Assesses telemetry data quality, dedup confidence, normalization errors, data source health |
| `network-exposure` | L3 | Network exposure assessment: open ports, firewall rule analysis, internet-facing service inventory |
| `attack-surface-management` | L3 | Discovers and inventories public-facing attack surface: domains, IPs, ports, web assets |
| `threat-intelligence` | L3 | Threat intelligence enrichment: IOC analysis, actor attribution, TTP mapping |
| `deception-honeypot` | L4 | Deception technology strategy: honeypot placement, canary token deployment, lateral movement traps |

## Workflow: Detection Pipeline

```
threat-intelligence → threat-hunting → behavioral-analytics → incident-classification
```

## Key MITRE ATT&CK Phases Covered

- Initial Access (TA0001)
- Execution (TA0002)
- Persistence (TA0003)
- Defense Evasion (TA0005)
- Discovery (TA0007)
- Lateral Movement (TA0008)
- Collection (TA0009)
- Exfiltration (TA0010)

## Orchestrator Agent

[cs-security-analyst](../agents/security/cs-security-analyst.md) — coordinates detection skills for Tier 2 SOC workflows.
