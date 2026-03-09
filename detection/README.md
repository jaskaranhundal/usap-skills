# Detection Domain

Skills in the Detection domain identify adversary presence, surface exposure across credentials and network assets, and maintain the quality of security telemetry. The domain spans proactive threat hunting, behavioral anomaly analysis, secrets and credential exposure, external attack surface enumeration, threat intelligence enrichment, detection rule engineering, and deception technology. Detection skills are optimized for structured, corroborated findings that feed directly into downstream response and governance workflows.

---

## Skills Index

| Skill | Description | Key Use Case |
|---|---|---|
| threat-hunting | Hypothesis-driven, IOC-driven, and anomaly-driven hunting across endpoint, network, and cloud telemetry. Produces formal hunt verdicts for both confirmed findings and clean hunts. | Proactive hunt sprint, post-incident lateral movement sweep, TTP-triggered investigation |
| secrets-exposure | Scans codebases, configuration stores, and pipeline artifacts for 15 secret types using entropy scoring, pattern matching, and blast radius estimation. | Developer credential leak in a repository, API key exposed in CI/CD logs |
| behavioral-analytics | UEBA entity risk scoring, insider threat pattern detection, and account takeover identification using baseline deviation analysis. | Anomalous privileged account activity, after-hours data access spike |
| telemetry-signal-quality | Assesses data source health across EDR, DNS, proxy, authentication, and cloud audit logs. Flags dedup failures, normalization errors, and data gaps. | Pre-hunt telemetry gate, data coverage audit for compliance reporting |
| network-exposure | Enumerates open ports, analyzes firewall rules, and inventories internet-facing services. Scores exposure by criticality and business justification. | Quarterly external exposure review, post-change firewall audit |
| attack-surface-management | Discovers and inventories public-facing assets: domains, subdomains, IP ranges, web applications, and cloud-exposed services. | M&A due diligence asset discovery, shadow IT enumeration |
| threat-intelligence | Enriches IOCs with context, maps indicators to ATT&CK TTPs, and attributes activity to known threat actors. Maintains IOC expiry and confidence scoring. | Alert enrichment, actor attribution for a targeted intrusion, feed integration |
| detection-engineering | Authors SIEM/EDR detection rules, measures ATT&CK coverage gaps, and scores alert fidelity against production telemetry. | New rule development from a hunt finding, coverage gap remediation |
| deception-honeypot | Designs honeypot placement strategies, generates canary tokens, and models lateral movement traps for high-value asset protection. | Deception layer design for a data center segment, canary token seeding in file shares |

---

## Agent Links

The primary orchestrator for this domain is the [cs-security-analyst](../agents/security/cs-security-analyst.md) agent, which coordinates detection skills for Tier 2 SOC workflows. It sequences skills based on alert type, manages approval gates for mutating actions, and routes confirmed findings to the response domain.

Typical orchestration patterns:
- Incoming SIEM alert: `threat-intelligence` -> `behavioral-analytics` -> `threat-hunting`
- Scheduled sprint: `telemetry-signal-quality` -> `threat-hunting` -> `detection-engineering`
- New asset change: `attack-surface-management` -> `network-exposure` -> `detection-engineering`

---

## Quick Commands

Run any skill tool directly from the repository root. All tools accept `--help` and `--output json` for structured output.

**threat-hunting**
```bash
python detection/threat-hunting/scripts/threat-hunting_tool.py --help
python detection/threat-hunting/scripts/threat-hunting_tool.py --playbook wmi-lateral-movement --lookback-days 30 --output json
```

**secrets-exposure**
```bash
python detection/secrets-exposure/scripts/secrets-exposure_tool.py --help
python detection/secrets-exposure/scripts/secrets-exposure_tool.py --scope repo --entropy-threshold 4.5 --output json
```

**behavioral-analytics**
```bash
python detection/behavioral-analytics/scripts/behavioral-analytics_tool.py --help
python detection/behavioral-analytics/scripts/behavioral-analytics_tool.py --entity svc-account-01 --baseline-days 30 --risk-threshold 75 --output json
```

**telemetry-signal-quality**
```bash
python detection/telemetry-signal-quality/scripts/telemetry-signal-quality_tool.py --help
python detection/telemetry-signal-quality/scripts/telemetry-signal-quality_tool.py --source all --window 24h --output json
```

**network-exposure**
```bash
python detection/network-exposure/scripts/network-exposure_tool.py --help
python detection/network-exposure/scripts/network-exposure_tool.py --target 10.0.0.0/16 --ports 0-65535 --output json
```

**attack-surface-management**
```bash
python detection/attack-surface-management/scripts/attack-surface-management_tool.py --help
python detection/attack-surface-management/scripts/attack-surface-management_tool.py --org example.com --scope external --output json
```

**threat-intelligence**
```bash
python detection/threat-intelligence/scripts/threat-intelligence_tool.py --help
python detection/threat-intelligence/scripts/threat-intelligence_tool.py --ioc 198.51.100.42 --type ip --output json
```

**detection-engineering**
```bash
python detection/detection-engineering/scripts/detection-engineering_tool.py --help
python detection/detection-engineering/scripts/detection-engineering_tool.py --coverage-map current --output json
```

**deception-honeypot**
```bash
python detection/deception-honeypot/scripts/deception-honeypot_tool.py --help
python detection/deception-honeypot/scripts/deception-honeypot_tool.py --environment datacenter --density medium --output json
```

---

## Full Domain Guide

For complete methodology, cross-skill workflow patterns, MITRE ATT&CK coverage tables, Python tools reference, and domain best practices, see [CLAUDE.md](./CLAUDE.md).
