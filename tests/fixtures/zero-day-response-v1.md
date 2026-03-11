---
name: zero-day-response
description: USAP agent skill for Zero-Day Response. Use for Coordinate compensating controls for zero-day risk.
license: MIT
metadata:
  version: 1.0.0
  author: USAP Team
  category: usap-operations
  updated: 2026-02-28
  agent_slug: "zero-day-response"
---

# Zero-Day Response

## Overview
Coordinate compensating controls for zero-day risk. This skill governs how the zero-day-response agent classifies a reported vulnerability as a true zero-day, scopes organizational exposure, implements compensating controls in the absence of a vendor patch, tracks the patch timeline, and determines when and how to communicate risk to leadership and customers. Monitoring is read-only; compensating control deployment requires human approval.

## Keywords
- usap
- security-agent
- mcp
- approval-gated
- evidence-chain
- operations

## Quick Start
```bash
python scripts/zero-day-response_tool.py --help
python scripts/zero-day-response_tool.py --output json
```

## Core Workflows
1. Validate input context and required fields.
2. Apply deterministic and policy-aligned reasoning for agent zero-day-response.
3. Emit structured recommendation payloads for orchestrator processing.
4. Enforce human approval gates for mutating actions.

---

## Zero-Day Classification

A vulnerability is classified as a true zero-day when ALL three conditions are met:

| Condition | Assessment Method |
|---|---|
| No vendor patch or official mitigation available | Check vendor advisory, NVD, vendor security portal |
| Active exploitation confirmed in the wild | CISA KEV, threat intel feeds, ISAC reports, vendor confirmation |
| The organization uses the affected product version | CMDB query, software inventory, cloud asset registry |

Classification matrix:

| Patch Available | Exploited in Wild | Classification |
|---|---|---|
| No | Yes | True Zero-Day — activate this playbook |
| No | No (PoC only) | N-Day / Pre-Patch — monitor; reduced urgency |
| Yes | Yes | Critical Patch — vulnerability management process |
| Yes | No | Standard Patch — normal vulnerability management |

A vulnerability must not be classified as a zero-day unless exploitation in the wild is confirmed. Proof-of-concept (PoC) code availability alone does not meet the threshold.

---

## Immediate Triage: 0-2 Hours

The first two hours are the highest-leverage window for limiting blast radius. Execute all triage steps in parallel where possible.

### Step 1: Scope Assessment (0-30 minutes)

Identify every asset in the environment that runs the affected product and version:
1. Query CMDB for software: `vendor=X AND product=Y AND version IN [affected_versions]`.
2. Query cloud asset inventory (AWS SSM Inventory, Azure Arc, GCP Asset Inventory).
3. Query EDR for running process version strings.
4. Query network scanners for externally reachable instances of the affected service.

Output: Asset inventory table with columns: hostname, IP, environment (prod/dev/test), internet-facing (Y/N), data classification of hosted data, business owner.

### Step 2: Exposure Scoring (30-60 minutes)

For each affected asset, compute an exposure score:
```
exposure_score = (internet_facing × 3) + (data_sensitivity × 2) + (patch_complexity × 1)
```

Prioritization tiers:
| Score | Tier | Action |
|---|---|---|
| >= 8 | Critical | Immediate compensating control; consider service isolation |
| 5-7 | High | Compensating control within 4 hours |
| 2-4 | Medium | Compensating control within 24 hours |
| < 2 | Low | Monitor; patch in next maintenance window |

### Step 3: Active Exploitation Evidence Check (60-120 minutes)

Search available telemetry for indicators of active exploitation targeting the organization:
- Review WAF logs for payloads matching the vulnerability's attack pattern.
- Review EDR for exploitation behaviors (process injection, reverse shell, unexpected child process of the affected service).
- Review SIEM for alerts correlated to the affected systems in the past 14 days.
- Query threat intelligence platform for targeting of the organization's IP ranges or domain.

If active exploitation is confirmed against the organization: immediately transition to the incident-commander agent. The zero-day-response agent remains active to coordinate compensating controls in parallel with incident response.

---

## Compensating Controls (No Patch Available)

Compensating controls are temporary risk reduction measures. They must be documented as temporary, with a defined expiry trigger (patch release or quarterly review). Each control requires human approval before deployment.

### Control Option 1: WAF Rule Deployment

Apply a web application firewall rule that blocks or sanitizes the attack payload pattern.

Requirements before deployment:
- Rule must be tested in detection-only mode for a minimum of 1 hour with no false-positive alerts against production traffic.
- Rule must have a rollback procedure documented.
- Rule must be assigned an expiry review date.

Limitations: WAF rules protect HTTP/HTTPS attack vectors only. They provide no protection for internal service-to-service exploitation or non-web protocol attacks.

### Control Option 2: Network Block / Segmentation

Block network access to the vulnerable service from untrusted networks or restrict to approved source IP ranges.

Implementation options (in order of preference):
1. Security group / firewall rule change to restrict access to the affected port and service.
2. Network ACL update at the perimeter firewall.
3. Service-level IP allowlist if the application supports it.

Risk: Blocking external access may disrupt legitimate users. Validate with the business owner before deployment.

### Control Option 3: Feature Disable or Killswitch

If the vulnerability is in a specific feature of the product, disable that feature at the application or configuration level without disabling the entire service.

Example: A zero-day in a SAML parsing library — disable SAML SSO and fall back to local authentication temporarily.

Decision criteria: Feature disable is preferred over full service shutdown when the disabled feature is not on the critical path for core business operations.

### Control Option 4: Service Isolation

For critical exploits with no viable WAF or network block option, isolate the affected service by removing it from the production network and switching to an alternative or degraded service mode.

This is the highest-impact compensating control and requires CISO approval.

### Control Option 5: Increase Detection Sensitivity

When the exploit cannot be blocked without unacceptable service disruption, increase detection sensitivity:
- Enable verbose logging on the affected service.
- Create custom SIEM detection rules for exploitation behaviors.
- Lower alerting thresholds for anomalies on affected hosts.
- Assign dedicated analyst monitoring for 24 hours.

This control does not prevent exploitation but reduces dwell time if exploitation occurs.

---

## Vendor Notification and Patch Timeline Tracking

### Vendor Engagement Protocol

If the zero-day was discovered internally (not by the vendor), follow Coordinated Vulnerability Disclosure (CVD):
1. Notify the vendor via their published security disclosure contact within 24 hours of internal confirmation.
2. Request a private confirmation and tracking number from the vendor.
3. Agree on a disclosure timeline — 90 days is the industry standard (Google Project Zero policy).
4. If the vendor does not respond within 7 days, escalate to CERT/CC or the relevant national CERT.

If the zero-day was publicly disclosed by a third party or is already public:
- Engage the vendor immediately for patch timeline.
- Check if a vendor emergency advisory is in progress.

### Patch Timeline Tracking

Maintain a running timeline record for each zero-day event:

| Milestone | Target | Actual | Status |
|---|---|---|---|
| Vulnerability reported to vendor | Day 0 | | |
| Vendor acknowledgment received | Day 2 | | |
| Vendor patch committed | Day 30 | | |
| Patch available for testing | Day 45 | | |
| Patch deployed to staging | Day 50 | | |
| Patch deployed to production | Day 60 | | |
| Compensating controls retired | Day 61 | | |

Update this timeline every 48 hours. Escalate to CISO if vendor patch commitment date slips by more than 14 days.

---

## Threat Actor Monitoring

Known APT groups and cybercriminal operators frequently exploit zero-days within hours of public disclosure. Monitor for targeting signals:

Monitoring sources:
- Threat intelligence platform: search for the CVE identifier across actor profiles.
- ISAC threat sharing: sector-specific early warning bulletins.
- CISA Emergency Directive or Known Exploited Vulnerabilities (KEV) catalog.
- Vendor threat intelligence team advisories.
- Dark web monitoring: exploit listings or access broker advertisements for the affected product.

Escalation trigger: If a nation-state APT is confirmed to be exploiting the vulnerability and targets organizations in the same sector, escalate compensating control priority to Critical regardless of exposure score.

---

## Emergency Change Management

Zero-day compensating controls bypass the standard Change Advisory Board (CAB) process under the Emergency Change procedure. Requirements for Emergency Change invocation:

| Criterion | Required |
|---|---|
| CVSS score >= 9.0 OR active exploitation confirmed in wild | Yes |
| CISO or deputy authorization | Yes |
| Rollback plan documented before deployment | Yes |
| Post-implementation review scheduled within 72 hours | Yes |
| Standard CAB retrospective within 5 business days | Yes |

The emergency change record must be created in the ITSM system even if approval is verbal — documentation follows within 2 hours.

---

## Communication Decision Matrix

| Condition | Notification Target | Timeline | Channel |
|---|---|---|---|
| True zero-day confirmed, Critical exposure | CISO + CTO | Within 1 hour | Secure call |
| Active exploitation confirmed against org | CEO + Board Chair | Within 2 hours | Secure call + written brief |
| Customer data at risk of exposure | Legal + DPO | Within 1 hour | Privileged communication |
| Vendor-required customer notification | Customers | Per contractual SLA (typically 72 hours) | Secure email or portal notice |
| Regulatory notification threshold met | DPO files with regulator | 72 hours (GDPR) | Regulatory portal |
| Compensating controls deployed successfully | C-level | Within 24 hours | Written executive summary |

Board-level communication must translate technical details into business impact: estimated financial exposure, reputational risk, regulatory exposure, and the specific control actions taken.

---

## Intent Classification

| Action | Intent Class | Approval Required |
|---|---|---|
| Query asset inventory for affected systems | read_only | None |
| Search telemetry for exploitation indicators | read_only | None |
| Review vendor advisories and CVE details | read_only | None |
| Generate compensating control recommendation | read_only | None |
| Monitor dark web and threat intel for targeting | read_only | None |
| Deploy WAF rule | mutating/device_config_change | Human approval required |
| Change firewall or security group rule | mutating/device_config_change | Human approval required |
| Disable a product feature or service | mutating/device_config_change | CISO approval required |
| Isolate a production service from the network | mutating/device_config_change | CISO approval required |
| Notify customers of potential exposure | mutating/external_communication | Legal + CISO approval required |

---

## Validation Checklist
- [ ] SKILL.md frontmatter is valid
- [ ] Script runs with --help
- [ ] references/ has at least one guide
- [ ] expected_outputs/ contains representative output
- [ ] Runtime contract link points to ../../agents/zero-day-response.yaml

## Runtime Contract
- ../../agents/zero-day-response.yaml
