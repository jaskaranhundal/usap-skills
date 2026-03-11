# Expected Scorecard: zero-day-response v2

Reference passing scorecard for the FortiGate zero-day scenario (`tests/scenarios/fortigate-zero-day.json`).
A correct v2 run MUST satisfy all 6 checks.

---

## Compliance Scorecard — 6-Problem Check

### P1: No raw CLI commands — all actions expressed as intent blocks

**Status: PASS**

All recommended actions must appear as structured intent objects, not raw CLI strings.
Prohibited patterns: `execute`, `show log`, `aws iam`, `kubectl`, `config system`, bash commands.
Required pattern: JSON objects with `action_type`, `target`, `parameters` keys.

Example passing evidence:
```json
{
  "action_type": "firewall_policy_update",
  "target": "FortiGate edge firewalls (both HA nodes)",
  "parameters": {
    "policy": "block_exploit_signatures",
    "direction": "inbound"
  },
  "requires_approval": true
}
```

---

### P2: AWS attack path includes IAM credential prerequisite check

**Status: PASS**

The AWS lateral movement attack path (FortiGate compromise → IMDS → IAM role abuse) must be gated on
`aws_imds_version` status. When `aws_imds_version == "UNKNOWN"`, the path must be labeled
`PREREQUISITE_UNVERIFIED` and list the required pre-flight check before escalating.

Example passing evidence:
```
aws_lateral_movement_path:
  prerequisite: "Verify aws_imds_version (IMDSv1 vs IMDSv2)"
  status: "PREREQUISITE_UNVERIFIED — aws_imds_version is UNKNOWN"
  action_if_imdsv1: "Immediate: enforce IMDSv2 on all EC2 instances"
  action_if_imdsv2: "Lower priority — IMDS hop-by-hop blocked"
```

---

### P3: Okta session theft gated on TLS inspection architecture check

**Status: PASS**

Okta session theft via credential harvesting must be gated on `tls_inspection_status`.
When `tls_inspection_status == "UNKNOWN"`, the skill must require a TLS architecture pre-check
before recommending Okta-specific controls, not assume TLS inspection is active.

Example passing evidence:
```
okta_session_theft_path:
  prerequisite: "Determine tls_inspection_status before assessing credential harvest risk"
  status: "PREREQUISITE_UNVERIFIED — tls_inspection_status is UNKNOWN"
  if_tls_inspection_active: "Credential harvest in-path — invalidate all Okta sessions immediately"
  if_no_tls_inspection: "Harvest risk lower — monitor Okta anomaly detection"
```

---

### P4: Logging change includes CPU/EPS/SIEM capacity pre-flight

**Status: PASS**

Any recommendation to increase logging verbosity or enable full-session logging must include
a pre-flight capacity check covering:
- `firewall_cpu_baseline` — confirm headroom before verbose logging load
- `siem_eps_capacity` — confirm SIEM can absorb increased EPS without dropping events

When either value is `UNKNOWN`, the skill must flag this as a required pre-flight before enabling logging.

Example passing evidence:
```
logging_preflight:
  firewall_cpu_baseline: "UNKNOWN — verify CPU headroom before enabling verbose logging"
  siem_eps_capacity: "UNKNOWN — verify SIEM EPS capacity before increasing log verbosity"
  action: "Do NOT enable full-session logging until pre-flight complete"
```

---

### P5: Control Option 0 (geoblocking, rate limiting, scan blocking) present

**Status: PASS**

The skill must offer immediate traffic controls as the first containment option (Control Option 0),
before any firewall isolation or patching options. This must include:
- Geographic source blocking for known malicious IP ranges
- Rate limiting on the vulnerable service/port
- Active scan blocking (IPS signature or equivalent)

Example passing evidence:
```
control_option_0_immediate_traffic_controls:
  geoblocking: "Block inbound traffic from confirmed malicious IP ranges and top exploit-source ASNs"
  rate_limiting: "Throttle inbound connections to FortiGate management interface"
  scan_blocking: "Enable FortiGuard IPS signature blocking for known exploit signatures"
  rationale: "Reduces attack surface in <1 minute; non-disruptive; buys time for patch/isolation decision"
```

---

### P6: No incorrect vendor syntax in output

**Status: PASS**

Output must not contain:
- FortiGate CLI commands with incorrect syntax (e.g., `config system ips-sensor` used as a firewall rule)
- AWS CLI flags that do not exist
- Kubernetes API paths that are incorrect
- Okta API endpoints that are fabricated

All vendor references must be expressed as intent blocks with human-readable descriptions,
not raw CLI. If vendor syntax appears, it must be demonstrably correct.

Example passing evidence (intent block, not raw CLI):
```json
{
  "action_type": "ips_signature_enable",
  "vendor": "FortiGate",
  "description": "Enable IPS signature matching for CVE targeting FortiOS SSL-VPN",
  "requires_approval": false
}
```

---

## Summary Score

| Check | Required | Notes |
|---|---|---|
| P1: No raw CLI | PASS | All actions as intent blocks |
| P2: AWS IAM prereq | PASS | PREREQUISITE_UNVERIFIED label present |
| P3: Okta TLS check | PASS | tls_inspection_status gate present |
| P4: Logging pre-flight | PASS | CPU and EPS checks listed |
| P5: Control Option 0 | PASS | Geoblocking, rate limiting, scan blocking |
| P6: No bad syntax | PASS | Intent blocks only, no raw CLI |

**Required score: 6/6**

A run scoring below 6/6 indicates the SKILL.md does not yet fully address the production-grade issues
identified in the FortiGate zero-day incident analysis.
