---
name: threat-hunting
description: USAP agent skill for Threat Hunting. Use for Perform hypothesis-driven threat hunting across telemetry.
license: MIT
metadata:
  version: 1.0.0
  author: USAP Team
  category: usap-operations
  updated: 2026-02-28
  agent_slug: "threat-hunting"
---

# Threat Hunting

## Overview
Perform hypothesis-driven threat hunting across telemetry. This skill governs how the threat-hunting agent identifies adversary presence that has bypassed automated controls, determines dwell time, and escalates confirmed active threats to the incident-commander agent. Every hunt produces a structured evidence package regardless of outcome — a clean hunt is as valuable as a finding.

## Keywords
- usap
- security-agent
- mcp
- approval-gated
- evidence-chain
- operations

## Quick Start
```bash
python scripts/threat-hunting_tool.py --help
python scripts/threat-hunting_tool.py --output json
```

## Core Workflows
1. Validate input context and required fields.
2. Apply deterministic and policy-aligned reasoning for agent threat-hunting.
3. Emit structured recommendation payloads for orchestrator processing.
4. Enforce human approval gates for mutating actions.

---

## Hunt Methodology

### Three Methodology Tracks

**Track 1: Hypothesis-Driven Hunting**
Begin with a written hypothesis derived from threat intelligence, MITRE ATT&CK TTPs, or recent industry incidents. The hypothesis must be falsifiable. Structure: "Threat actor using [TTP] would produce [observable] in [data source] between [time bounds]."

Hypothesis lifecycle:
1. Draft hypothesis based on threat landscape and known actor preferences.
2. Identify the minimum data sources needed to confirm or refute.
3. Define what a positive finding looks like before querying.
4. Execute queries and collect evidence.
5. Record verdict: confirmed / not observed / inconclusive (data gap).

**Track 2: IOC-Driven Hunting**
Consume threat intelligence feeds (IP addresses, file hashes, domain names, YARA signatures). Sweep telemetry for exact or fuzzy matches. IOC-driven hunts have a shorter shelf life because indicators age quickly — always record the indicator confidence level and expiry date.

IOC sweep checklist:
- Hash matches in EDR process creation logs (exact match).
- Domain matches in DNS query logs (exact + subdomain wildcard).
- IP matches in firewall and proxy egress logs.
- Registry key or file path matches in endpoint telemetry.
- Email header matches in mail gateway logs.

**Track 3: Anomaly-Driven Hunting**
Use statistical outliers or ML-generated anomaly scores as hunt leads. Anomaly-driven hunts are higher-noise but find novel attacker behaviors not captured by known TTPs or IOCs.

Anomaly signals worth hunting:
- Spike in outbound data volume from a single host (>2 standard deviations from 30-day baseline).
- Process executing from a non-standard path (AppData, Temp, or recycler directories).
- First-ever connection from an internal host to an external IP in a new ASN.
- Service account authenticating interactively (logon type 2 or 10).
- Scheduled task created by a non-privileged process.

---

## Hunt Hypothesis Generation

Before each hunt cycle, generate a prioritized hypothesis list. Inputs:

| Input | Source | Weight |
|---|---|---|
| Recent threat intelligence reports | ISAC, vendor intel | High |
| Active campaigns targeting the sector | CISA KEV, FS-ISAC | High |
| MITRE ATT&CK Navigator heat map | Internal ATT&CK coverage gaps | Medium |
| Previous hunt findings and near-misses | Hunt log | Medium |
| Red team exercise outcomes | Penetration test reports | Medium |
| Newly deployed infrastructure changes | Change management records | Low |

Hypothesis scoring formula (rank order):
```
hypothesis_priority = (actor_relevance × 3) + (control_gap × 2) + (data_availability × 1)
```
Pursue hypotheses with priority >= 5 in the current sprint. Document lower-priority hypotheses for future sprints.

---

## Required Data Sources

| Data Source | Minimum Retention | Key Fields |
|---|---|---|
| EDR process telemetry | 90 days | process_name, parent_process, command_line, user, host, timestamp |
| DNS query logs | 30 days | query_name, query_type, response_ip, source_ip, timestamp |
| Proxy / web gateway logs | 90 days | url, destination_ip, bytes_out, user_agent, source_ip |
| Firewall flow logs | 30 days | src_ip, dst_ip, dst_port, protocol, bytes, action |
| Windows authentication logs (4624/4625/4648) | 90 days | logon_type, source_ip, account_name, target_server |
| CloudTrail / cloud audit logs | 365 days | api_action, principal_arn, source_ip, region, user_agent |
| Email gateway logs | 30 days | sender, recipient, subject, attachment_hash, delivery_status |

Data source health check: Before executing a hunt, verify that each required source has data within the last 24 hours. A data gap invalidates the hunt verdict for that time period — document the gap explicitly.

---

## Hunt Playbooks

### Playbook 1: Lateral Movement via WMI

Hypothesis: Attacker has established a foothold and is moving laterally using WMI remote execution, a technique commonly used to avoid spawning cmd.exe or PowerShell directly on the target.

Data sources required: EDR process creation events, Windows Security Event Log (4688).

Detection logic:
```
process_name = "wmiprvse.exe"
AND parent_process = "svchost.exe"
AND child_process NOT IN ["scrcons.exe"]  -- expected WMI children
AND child_process IN ["cmd.exe", "powershell.exe", "wscript.exe", "cscript.exe", "mshta.exe", "rundll32.exe"]
```

Triage steps:
1. Identify the initiating account that triggered the WMI call (Security Event 4688, 4648).
2. Determine the source host that made the remote WMI request (Security Event 4624 on target, logon type 3).
3. Map source host to user — is this expected admin activity?
4. Review the full command line argument of the spawned child process.
5. Check if the same pattern appears on multiple hosts within the same time window (indicates automated lateral movement).

Escalation trigger: Pattern on 3+ hosts within 60 minutes OR command line contains encoded payload or download cradle.

### Playbook 2: Living-Off-the-Land Binary Abuse

Hypothesis: Attacker is using trusted Windows binaries (LOLBins) to execute malicious code and evade detection by avoiding custom malware.

Detection logic:
```
process_name IN ["powershell.exe", "pwsh.exe"]
AND (
  command_line CONTAINS "-enc" OR
  command_line CONTAINS "-EncodedCommand" OR
  command_line CONTAINS "-nop" OR
  command_line CONTAINS "-NonInteractive" OR
  command_line CONTAINS "IEX" OR
  command_line CONTAINS "DownloadString" OR
  command_line CONTAINS "WebClient"
)
AND hour(timestamp) NOT IN [7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17]  -- outside business hours
AND parent_process NOT IN ["explorer.exe", "wmiprvse.exe"]  -- unexpected parent
```

After-hours threshold: Executions outside 07:00-17:00 local time increase base anomaly score by 2.

Decode encoded commands: Extract the base64 payload from `-EncodedCommand` argument and decode. Record decoded payload verbatim in the hunt evidence package.

### Playbook 3: Beaconing Detection

Hypothesis: A compromised host is communicating with a C2 server at regular intervals, a pattern that differs from human-driven browsing behavior.

Data sources: DNS query logs, proxy egress logs, firewall flow logs.

Statistical beaconing signature:
- Jitter less than 10% of mean interval (e.g., queries every 60 seconds +/- 3 seconds).
- Consistent small payload size per request (C2 keep-alive packets are typically small).
- Destination domain registered within the last 90 days (WHOIS lookup).
- Destination domain has no Alexa/Tranco top-1M entry.
- Communication continues across overnight and weekend hours (not human-driven).

Detection approach:
```
For each (source_ip, destination_domain) pair:
  intervals = [timestamps[i+1] - timestamps[i] for all i]
  jitter_coefficient = std(intervals) / mean(intervals)
  if jitter_coefficient < 0.1 AND count(intervals) > 20:
    flag as potential beacon
```

Escalation trigger: Confirmed beacon pattern to a domain less than 90 days old with no legitimate business purpose.

### Playbook 4: Pass-the-Hash Detection

Hypothesis: Attacker has harvested NTLM hashes from memory and is authenticating using the hash rather than the plaintext credential — no keyboard activity required on the originating workstation.

Data sources: Windows Security Event Log (4624, 4648), EDR, physical access / endpoint activity logs.

Detection logic:
```
Event 4624 on target host:
  LogonType = 3 (network logon)
  AuthenticationPackage = "NTLM"
  Source host = workstation (not a server or DC)

AND on source host at same timestamp:
  No keyboard or mouse activity for 10+ minutes (EDR idle indicator)
  No interactive user session (Event 4624 type 2 absent)
```

Triage steps:
1. Confirm the source workstation was locked or had no active user session at the time of the NTLM auth event.
2. Check if the authenticating account has recently been used on a host where Mimikatz or LSASS dumping tools have run (cross-reference with EDR behavioral alerts).
3. Verify the target resource being accessed — is it a high-value server (DC, file share, HRMS)?

---

## Dwell Time Estimation

Dwell time is the period between initial compromise and detection. Accurate dwell time estimation informs blast radius assessment and evidence collection scope.

Estimation method:
1. Identify the earliest observed malicious artifact (file write, process, network connection).
2. Scan backwards from that timestamp in all data sources for related indicators.
3. Check CloudTrail, authentication logs, and email logs for initial access vectors.
4. Cross-reference with threat actor infrastructure registration dates (WHOIS, Shodan).

Dwell time brackets and implications:

| Dwell Time | Blast Radius Assumption | Evidence Collection Scope |
|---|---|---|
| < 24 hours | Limited — likely early stage | 7-day lookback |
| 1-7 days | Moderate — reconnaissance complete | 30-day lookback |
| 7-30 days | High — lateral movement likely | 90-day lookback + backup media |
| > 30 days | Critical — full environment compromise assumed | Full historical + offline media |

Document dwell time estimate with confidence level (high / medium / low) and the earliest observed indicator that anchors the estimate.

---

## Hunt Success Criteria

A hunt is successful under two conditions:

**Condition A — Finding Confirmed:**
A finding is confirmed when two or more independent data sources corroborate the same malicious activity. Single-source observations are flagged as unconfirmed and require additional investigation. A confirmed finding triggers immediate escalation to incident-commander.

**Condition B — Clean Hunt (No Compromise Confirmed):**
A clean hunt result is equally valid and must be documented formally. A clean hunt report must state:
- Hypothesis tested.
- Data sources searched.
- Time period covered.
- Data quality verdict (gaps noted).
- Conclusion: no indicators observed within the scope of this hunt.

A clean hunt without data quality verification is not a valid clean hunt — it may simply be a data gap.

Hunt sprint cadence: One sprint = 2 weeks. Each sprint should close at least 3 hypotheses with formal verdicts.

---

## Escalation and Cascade Rules

| Finding Severity | Action |
|---|---|
| Confirmed active threat | Immediately escalate to incident-commander agent via structured alert payload |
| Unconfirmed indicator (single source) | Elevate to monitored watchlist; re-hunt within 48 hours |
| IOC match (no active behavior) | Add to blocked list; document in threat intel platform |
| Clean hunt | Archive evidence package; update ATT&CK coverage map |

Cascade payload to incident-commander must include:
```json
{
  "finding_id": "HUNT-YYYY-NNN",
  "hypothesis": "...",
  "confidence": "high|medium|low",
  "earliest_indicator_timestamp": "ISO8601",
  "estimated_dwell_days": N,
  "affected_hosts": ["host1", "host2"],
  "affected_accounts": ["account1"],
  "data_sources_searched": ["EDR", "DNS", "proxy"],
  "mitre_techniques": ["T1047", "T1059.001"],
  "evidence_artifacts": [...]
}
```

---

## Intent Classification

| Action | Intent Class | Approval Required |
|---|---|---|
| Query telemetry data sources | read_only | None |
| Generate hunt hypothesis list | read_only | None |
| Decode suspicious command-line payloads | read_only | None |
| Tag an indicator in the threat intel platform | read_only | None |
| Block an IP or domain at the firewall | mutating/network_change | Human approval |
| Isolate a suspected compromised host | mutating/endpoint_isolation | Human approval |
| Escalate to incident-commander | mutating/alert_dispatch | Automated (policy-defined) |

---

## Validation Checklist
- [ ] SKILL.md frontmatter is valid
- [ ] Script runs with --help
- [ ] references/ has at least one guide
- [ ] expected_outputs/ contains representative output
- [ ] Runtime contract link points to ../../agents/threat-hunting.yaml

## Runtime Contract
- ../../agents/threat-hunting.yaml
