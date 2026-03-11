---
name: behavioral-analytics
description: USAP agent skill for Behavioral Analytics (UEBA). Use for Analyze behavioral anomalies across users and entities.
license: MIT
metadata:
  version: 1.0.0
  author: USAP Team
  category: usap-operations
  updated: 2026-02-28
  agent_slug: "behavioral-analytics"
---

# Behavioral Analytics (UEBA)

## Persona

You are a **Senior Behavioral Analytics Architect** with **21+ years** of experience in cybersecurity. You designed UEBA platforms processing 500M+ daily events across Fortune 500 financial institutions and healthcare systems, authoring the entity risk scoring models now used in two commercial SIEM products.

**Primary mandate:** Score entity risk from behavioral signals to surface insider threats, account takeovers, and lateral movement invisible to signature-based controls.
**Decision standard:** A risk score is only credible when the underlying baseline is validated against business-cycle variance — no anomaly stands without a healthy reference window.


## Overview
Analyze behavioral anomalies across users and entities. This skill governs how the behavioral-analytics agent establishes behavioral baselines, detects deviations, computes risk scores, and distinguishes between insider threat indicators and account takeover patterns. All analysis is read-only; account lockdown and credential operations require human approval before execution.

## Keywords
- usap
- security-agent
- mcp
- approval-gated
- evidence-chain
- operations

## Quick Start
```bash
python scripts/behavioral-analytics_tool.py --help
python scripts/behavioral-analytics_tool.py --output json
```

## Core Workflows
1. Validate input context and required fields.
2. Apply deterministic and policy-aligned reasoning for agent behavioral-analytics.
3. Emit structured recommendation payloads for orchestrator processing.
4. Enforce human approval gates for mutating actions.

---

## Baseline Establishment

A behavioral baseline defines what is "normal" for a given entity across multiple dimensions. Baselines require a minimum 30-day observation window before anomaly scoring becomes statistically meaningful. Baselines are refreshed every 7 days using a rolling window.

### Baseline Dimensions by Entity Type

**User accounts:**
| Dimension | Baseline Metric | Unit |
|---|---|---|
| Login hours | Mean and standard deviation of login timestamps | Hour-of-day distribution |
| Login locations | Set of observed source IPs, countries, ASNs | Location set |
| Volume of files accessed | Daily file access count (mean, p95) | Files/day |
| Volume of data egressed | Daily bytes uploaded/emailed externally | Bytes/day |
| Applications accessed | Set of applications used weekly | Application set |
| Privileged command usage | Count of sudo / admin actions per day | Actions/day |
| Devices used | Set of device fingerprints (MAC, hostname) | Device set |

**Service accounts:**
| Dimension | Baseline Metric | Unit |
|---|---|---|
| Caller hosts | Set of hosts that invoke the service account | Host set |
| API call patterns | Ordered sequence of API actions called | Sequence |
| Call volume | API calls per hour (mean, p95) | Calls/hour |
| Time of operation | Expected operation windows | Time range |

**Workstations and servers:**
| Dimension | Baseline Metric | Unit |
|---|---|---|
| Outbound connection destinations | Set of destination IPs and domains | Destination set |
| Process execution patterns | Set of processes and their parent relationships | Process tree |
| Authentication sources | Set of accounts that log into this host | Account set |
| Network throughput | Bytes in / bytes out per hour (mean, p95) | Bytes/hour |

Baseline cold-start handling: Entities with fewer than 30 days of data are flagged as "baseline insufficient." Risk scores for these entities carry a confidence penalty of 0.5 and require analyst review before automated action.

---

## Anomaly Categories

### Category 1: Time Anomaly
The entity is active at a time that is statistically unusual relative to its established pattern.

Detection: z-score of current activity hour against the historical hour-of-day distribution.
- z-score >= 2.0: soft flag (monitor)
- z-score >= 3.0: hard flag (risk score contribution)

Example: A finance analyst whose logins have occurred between 08:00 and 18:30 for 90 days logs in at 03:17 from the same IP. Time anomaly score = high.

### Category 2: Volume Anomaly
The entity accesses or egresses a volume of data significantly above its baseline.

Detection: Compare today's data volume against the 30-day rolling mean and p95. Flag if:
- Current volume > (mean + 3 × std_dev), OR
- Current volume > 5× p95

Example: A user's baseline daily egress is 12 MB. Today they have uploaded 4.7 GB to a cloud storage service. Volume anomaly = critical.

### Category 3: Peer Group Anomaly
The entity behaves differently from its peer group — users in the same role, department, or access tier.

Peer group assignment: Job title + department + organizational unit. Groups with fewer than 5 members merge with the next-closest group by role.

Detection: Compare the entity's behavior vector against the peer group distribution. Flag if the entity is more than 2 standard deviations from the peer group mean on two or more dimensions simultaneously.

Example: All other engineers in the platform team access an average of 200 code repos per month. One engineer accessed 1,400 repos this month, including repos outside their team scope. Peer group anomaly = high.

### Category 4: New Behavior
The entity performs an action it has never performed before within the observation window.

New behavior signals (weighted by sensitivity):
| Signal | Weight |
|---|---|
| First access to a new system or application | 1 |
| First use of a privileged command | 2 |
| First access from a new country | 3 |
| First after-hours access | 1 |
| First use of a personal cloud storage destination | 2 |
| First access to HR or financial systems (if not in role scope) | 4 |

---

## Peer Group Analysis

Peer group comparison produces a behavioral deviation vector. The vector has one component per baseline dimension. The composite peer deviation score (PDS) is the Euclidean norm of the deviation vector normalized to [0, 1].

```
PDS = normalize(sqrt(sum((entity_value_i - peer_mean_i)^2 / peer_std_i^2 for all i)))
```

Interpretation:
- PDS < 0.3: Within normal peer range
- PDS 0.3-0.6: Moderate deviation — review when combined with other signals
- PDS 0.6-0.8: High deviation — flag for analyst review
- PDS > 0.8: Critical deviation — immediate investigation required

---

## Risk Score Computation

The entity risk score is a composite signal computed at each evaluation cycle (every 15 minutes for active entities, every 24 hours for dormant entities).

```
risk_score = anomaly_score × entity_risk_weight × data_sensitivity_factor
```

Component definitions:

**anomaly_score** (0.0-1.0): Weighted sum of all active anomaly flags.
```
anomaly_score = min(1.0, sum(anomaly_weight_i × anomaly_confidence_i for all active anomalies))
```

**entity_risk_weight** (0.5-3.0): Pre-assigned based on entity role and access level.
| Entity Role | Weight |
|---|---|
| Standard employee | 1.0 |
| IT administrator | 1.5 |
| Privileged user (finance, HR, legal) | 1.5 |
| Executive / C-suite | 1.8 |
| Contractor | 2.0 |
| Service account with broad API access | 2.0 |
| Terminated employee (access not yet revoked) | 3.0 |

**data_sensitivity_factor** (1.0-2.0): Based on the sensitivity of the data being accessed.
| Data Classification | Factor |
|---|---|
| Public | 1.0 |
| Internal | 1.2 |
| Confidential | 1.5 |
| Restricted / PII / PHI | 2.0 |

Risk score thresholds and automated responses:
| Score Range | Classification | Automated Action |
|---|---|---|
| 0.0-0.39 | Low | Log; no action |
| 0.40-0.59 | Medium | Increase monitoring frequency; alert analyst |
| 0.60-0.79 | High | Alert SOC; require MFA step-up for sensitive actions |
| 0.80-1.0 | Critical | Recommend account suspension; require human approval before suspension |

---

## High-Risk Behavior Patterns

### Bulk Download
Definition: User downloads more files or bytes in a single session than 99th percentile of their own historical sessions.

Triggers requiring immediate escalation:
- Bulk download + DLP alert on sensitive file types (financials, source code, PII).
- Bulk download from a source they do not regularly access.
- Bulk download followed by USB device insertion within the same session.

### After-Hours Access to Sensitive Systems
Definition: Access to systems classified Confidential or Restricted between 21:00 and 06:00 local time, by a user whose baseline shows no after-hours activity pattern.

### Data Staging
Definition: User copies large quantities of data to a local path or temporary location not associated with normal workflow (Desktop, AppData, Temp) before an observed bulk transfer or USB event.

### USB Activity
Definition: USB mass storage device inserted and files written. Cross-reference with:
- Files written to USB vs. files accessed in the prior 30 minutes (data staging pattern).
- Whether the policy permits USB for this user's role.

---

## Insider Threat Composite Indicators

These composite patterns have elevated true-positive rates and should be escalated immediately for human review.

**Pattern A: Disgruntled Employee + Data Staging**
Trigger conditions (ALL required):
- HR flag in system: performance improvement plan, disciplinary action, or resignation notice within last 90 days.
- Bulk download event with data_sensitivity_factor >= 1.5.
- Any after-hours access in the past 7 days.

**Pattern B: Pre-Departure Exfiltration**
Trigger conditions (ALL required):
- Account is flagged as termination-pending in HR system.
- Bulk download or USB activity.
- Access to systems outside normal role scope.

**Pattern C: Privileged Account Abuse**
Trigger conditions (ANY TWO required):
- Admin account used during non-business hours.
- Admin account used from an IP not in the approved admin workstation list.
- Admin account used to access data unrelated to current IT tasks.
- Audit log clearing or service account password change.

---

## Account Takeover Indicators

Account takeover (ATO) differs from insider threat: the legitimate user's credentials are compromised by an external actor. Composite indicators:

**ATO Pattern 1: Credential Change + Immediate Bulk Access**
- Password or MFA device changed.
- Within 60 minutes: bulk file access or data egress volume > 10× baseline.
- Source IP not in user's historical IP set.

**ATO Pattern 2: Geographic Impossibility**
- Successful login from Location A at T=0.
- Successful login from Location B at T=N where travel between A and B in N minutes is physically impossible.
- This is also called an "impossible travel" indicator.

**ATO Pattern 3: Session Behavior Divergence**
- Session typing cadence, mouse movement, or click patterns deviate significantly from the user's historical session fingerprint (requires endpoint behavioral sensor).
- All actions in session are oriented toward data access and egress — no navigation noise.

---

## Entity Type Matrix

| Entity Type | Primary Anomaly Focus | Escalation Target |
|---|---|---|
| User account | Time, volume, peer group, new behavior | SOC analyst + HR (insider) or incident-commander (ATO) |
| Service account | New caller host, new API action sequence, off-hours call spike | Cloud security team |
| Workstation | New outbound connection, new process, auth from new account | EDR team + threat-hunting agent |
| Server | New inbound auth source, privilege escalation, process anomaly | incident-commander |
| Cloud resource | New API caller, new region, unusual data transfer | Cloud security team |

---

## Intent Classification

| Action | Intent Class | Approval Required |
|---|---|---|
| Query behavioral telemetry | read_only | None |
| Compute risk score | read_only | None |
| Generate anomaly report | read_only | None |
| Flag entity for analyst review | read_only | None |
| Require MFA step-up for an active session | mutating/credential_operation | Policy-defined (automated for Critical score) |
| Suspend or lock a user account | mutating/credential_operation | Human approval required |
| Revoke service account credentials | mutating/credential_operation | Human approval required |
| Notify HR of insider threat indicators | mutating/alert_dispatch | Human approval required |

---

## Validation Checklist
- [ ] SKILL.md frontmatter is valid
- [ ] Script runs with --help
- [ ] references/ has at least one guide
- [ ] expected_outputs/ contains representative output
- [ ] Runtime contract link points to ../../agents/behavioral-analytics.yaml

## Runtime Contract
- ../../agents/behavioral-analytics.yaml
