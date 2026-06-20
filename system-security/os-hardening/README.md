# os-hardening

**Level:** L4 (Technical / Expert) | **Category:** System Security | **Intent:** `detect` / `analyze` (read-only assessment)

Assesses Linux, Windows, and macOS system configurations against CIS Benchmarks, DISA STIGs, and NSA hardening guides. Ingests scanner output (Lynis, OpenSCAP, CIS-CAT), classifies each failed control by severity and MITRE ATT&CK technique, and produces prioritized remediation with exact CLI commands or GPO paths. Never executes changes — every mutating step is flagged for a human approval gate.

---

## When to trigger

- New server or golden image hardening review before production promotion
- Scheduled CIS Benchmark configuration-drift assessment
- Lynis / OpenSCAP / CIS-CAT scan output needs triage and prioritization
- Audit or compliance evidence request (CIS, STIG, ISO 27001 A.8)
- Post-incident host hardening after a privilege-escalation finding

---

## Key outputs

| Field | Type | Description |
|---|---|---|
| `action` | string | Prioritized remediation summary (e.g. disable Telnet, enforce SSH key-only auth, enable auditd) |
| `intent_type` | string | `detect`, `analyze`, `advise`, `respond`, or `escalate` |
| `severity` | string | Highest finding severity across the assessed baseline |
| `key_findings` | array | Failed controls with CIS/STIG ID and MITRE technique |
| `evidence_references` | array | Scanner source, control ID, and exact remediation command |
| `next_agents` | array | Downstream skills (e.g. `vulnerability-management`, `detection-engineering`) |

---

## Finding classification (excerpt)

| Input signal | Severity | MITRE |
|---|---|---|
| World-writable system files | Critical | T1222 |
| Unpatched local privilege-escalation CVE | Critical | T1068 |
| Weak SSH configuration | High | T1021.004 |
| Missing audit logging (auditd / Windows Event Log) | High | T1562.002 |
| SUID/SGID binary outside baseline | High | T1548.001 |
| Cleartext protocol service (Telnet, FTP, rsh) | High | T1040 |
| SELinux / AppArmor disabled or permissive | High | T1068 |

---

## Works with

**Upstream:** scanner output from Lynis, OpenSCAP, CIS-CAT; `attack-surface-management` (exposed hosts to prioritize)

**Downstream:** `vulnerability-management` (when CVEs are present), `detection-engineering` (when audit-logging gaps are found)

---

## Standalone use

```bash
cat system-security/os-hardening/SKILL.md
# Paste into system prompt, then send an assessment request:

{
  "event_type": "hardening_assessment",
  "severity": "high",
  "raw_payload": {
    "os": "Ubuntu 22.04 LTS",
    "role": "internet-facing web server",
    "scanner": "Lynis 3.0.9",
    "profile": "CIS Level 1"
  }
}
```

Run the helper tool:

```bash
python system-security/os-hardening/scripts/os-hardening_tool.py --output json
```

---

## Runtime Contract

- ../../agents/os-hardening.yaml
