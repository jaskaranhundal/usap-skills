# System Security Domain — CLAUDE.md

## Purpose

The System Security domain contains skills for assessing and hardening operating system and host configurations against recognized security baselines. Skills in this domain evaluate Linux, Windows, and macOS systems against CIS Benchmarks, DISA STIGs, and NSA hardening guides, classify configuration gaps by severity and MITRE ATT&CK technique, and produce prioritized, evidence-backed remediation.

System security skills are read-only assessors — they parse scanner output, score findings, and recommend exact remediation commands, but never execute changes. Every mutating remediation step is flagged for a human approval gate. All outputs are structured payloads consumable by downstream vulnerability-management, detection-engineering, and governance skills.

Subdomains covered by this domain:
- OS configuration hardening (CIS / STIG / NSA baselines)
- Host audit logging and integrity assessment
- Privilege-escalation surface review (SUID/SGID, sudo, cron)
- Kernel and mandatory-access-control hardening (ASLR, NX, Seccomp, SELinux, AppArmor)

---

## Skills Catalog

| Skill | Slug | Primary Tool | MITRE Coverage |
|---|---|---|---|
| os-hardening | system-security/os-hardening | os-hardening_tool.py | T1222, T1068, T1021.004, T1548.001, T1562.002 |

All skill paths are relative from the repository root as `system-security/<slug>/`.

---

## Python Tools Reference

| Tool | Path | Purpose | Key Args |
|---|---|---|---|
| os-hardening_tool.py | system-security/os-hardening/scripts/os-hardening_tool.py | Emits the skill status payload for orchestration | `--input`, `--output` |

```bash
python system-security/os-hardening/scripts/os-hardening_tool.py --output json
```

---

## Domain Best Practices

1. **Map every finding to a named baseline control.** A hardening finding without a CIS/STIG/NSA control ID is not actionable evidence. Tag each finding with the exact control reference (e.g. CIS Ubuntu 22.04 v1.0 — 5.2.7).

2. **Prioritize by exploitability × impact, not raw count.** A single unpatched local privilege-escalation CVE outranks a dozen cosmetic policy deviations. Order remediation by exploitability, blast radius, and ease of fix.

3. **Flag every mutating remediation for a human gate.** Remediation commands (disabling services, changing SSH config, enabling SELinux enforcing) are recommendations only. Set `human_approval_required` on any output whose action would change a running system.

4. **Confirm the system role before selecting a baseline profile.** CIS Level 1 vs Level 2 and STIG categories depend on whether the host is internet-facing, a workstation, or a hardened bastion. Selecting the wrong profile produces false findings.

5. **Route findings onward.** CVE-bearing findings go to `vulnerability-management`; audit-logging and detection gaps go to `detection-engineering`; compliance evidence goes to `compliance-mapping`.

---

## Related Domains

- `detection/` — audit-logging gaps found here become detection-engineering rule candidates
- `risk-compliance/` — hardening evidence maps to compliance-mapping control requirements
- `cloud-infra/` — host hardening complements endpoint-os-security and cloud-workload-protection

---

## Path Reference

```
system-security/<slug>/
  README.md          -- skill overview and quick commands
  SKILL.md           -- full skill specification and methodology
  scripts/           -- executable Python tools
  references/        -- supporting documentation
  expected_outputs/  -- representative tool outputs for validation
  assets/            -- supporting data files
```
