#!/usr/bin/env python3
"""os-hardening_tool.py

Classifies OS configuration findings against the SKILL.md classification table
(CIS Benchmarks / DISA STIG signals) with severity, intent and MITRE mapping,
and prioritises remediation. Read-only detection. Emits the USAP 11-field payload.

  python3 os-hardening_tool.py --input host.json --output json
  python3 os-hardening_tool.py --output json    # no input: informational, exit 0

Input (see tests/fixtures/os-hardening-input.json): os (linux|windows), role,
cis_profile (L1|L2), findings[] (signal keys from the SKILL.md table, or
{signal, detail}).

Exit codes: 0 no finding above medium; 1 high; 2 critical. Stdlib only.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

SLUG = "os-hardening"
HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parents[2]
# signal -> (severity, intent, mitre, remediation)
TABLE = {
    "world_writable_system_files": ("critical", "detect", "T1222", "Correct permissions on system files (remove world-write)"),
    "unpatched_lpe_cve": ("critical", "respond", "T1068", "Patch the local privilege-escalation CVE immediately"),
    "weak_ssh_config": ("high", "detect", "T1021.004", "Harden sshd: disable root login and password auth, restrict ciphers"),
    "missing_audit_logging": ("high", "detect", "T1562.002", "Enable auditd / Windows Event Logging with a shipped baseline"),
    "suid_sgid_outside_baseline": ("high", "detect", "T1548.001", "Remove or justify SUID/SGID binaries outside the baseline"),
    "missing_kernel_hardening": ("high", "detect", "T1055", "Enable ASLR, NX and seccomp"),
    "cleartext_protocol_services": ("high", "detect", "T1040", "Disable Telnet/FTP/rsh; use SSH/SFTP"),
    "selinux_apparmor_disabled": ("high", "detect", "T1068", "Enforce SELinux/AppArmor (enforcing mode)"),
    "cron_writable_by_nonroot": ("high", "detect", "T1053.003", "Restrict cron directories to root"),
    "unneeded_services_running": ("medium", "analyze", "T1203", "Disable services not required by the system role"),
    "password_policy_below_cis": ("medium", "detect", "T1110", "Set password policy to the CIS minimum"),
}


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def analyse(t: dict, input_path: Optional[str] = None) -> Dict[str, Any]:
    rel = None
    if input_path:
        try:
            rel = Path(input_path).resolve().relative_to(REPO_ROOT).as_posix()
        except ValueError:
            rel = None
    raw = t.get("findings") or []
    findings = []
    for f in raw:
        sig = f if isinstance(f, str) else str(f.get("signal", ""))
        detail = "" if isinstance(f, str) else f.get("detail", "")
        if sig in TABLE:
            sev, intent, mitre, rem = TABLE[sig]
            findings.append({"signal": sig, "severity": sev, "intent": intent, "mitre": mitre, "remediation": rem, "detail": detail})
    if not t or not raw:
        return {"agent_slug": SLUG, "intent_type": "detect", "action": "Supply OS findings; nothing was provided.",
                "rationale": "No findings supplied.", "confidence": 0.30, "severity": "informational", "key_findings": ["No OS findings supplied"],
                "evidence_references": [{"source": "local://system-security/os-hardening/SKILL.md", "ref": "classification table (not applied)"}],
                "next_agents": [], "human_approval_required": False, "timestamp_utc": _now(), "findings": [], "_exit": 0}
    rank = {"critical": 4, "high": 3, "medium": 2, "low": 1, "informational": 0}
    findings.sort(key=lambda x: -rank[x["severity"]])
    counts = {k: sum(1 for x in findings if x["severity"] == k) for k in rank}
    severity = findings[0]["severity"] if findings else "informational"
    exit_code = 2 if counts["critical"] else 1 if counts["high"] else 0
    action = (f"{counts['critical']} critical and {counts['high']} high hardening finding(s) on {t.get('os', 'the host')} ({t.get('role', 'role n/a')}); "
              + (findings[0]["remediation"] + " first." if findings else "")) if findings else "No hardening finding against the CIS/STIG table."
    key = [f"{t.get('os', 'os')} {t.get('role', '')} (CIS {t.get('cis_profile', 'L1')}): {len(findings)} finding(s) ({counts['critical']} critical, {counts['high']} high, {counts['medium']} medium)"]
    key += [f"{x['severity']} {x['signal']} [{x['mitre']}]: {x['remediation']}" + (f" ({x['detail']})" if x['detail'] else "") for x in findings[:7]]
    evidence = [{"source": f"local://{rel}" if rel else "local://system-security/os-hardening/SKILL.md", "ref": "OS configuration findings"},
                {"source": "https://www.cisecurity.org/cis-benchmarks", "ref": "CIS Benchmarks"},
                {"source": "local://system-security/os-hardening/SKILL.md", "ref": "OS hardening classification table"}]
    return {"agent_slug": SLUG, "intent_type": "detect", "action": action,
            "rationale": ("Each configuration signal is scored against the SKILL.md CIS/STIG classification table for severity, intent and MITRE technique; world-writable system "
                          "files and an unpatched local-privilege-escalation CVE are critical. Read-only detection."),
            "confidence": 0.88, "severity": severity, "key_findings": key, "evidence_references": evidence,
            "next_agents": (["vulnerability-management"] if any(x["signal"] == "unpatched_lpe_cve" for x in findings) else []) + (["findings-tracker"] if findings else []),
            "human_approval_required": False, "timestamp_utc": _now(),
            "findings": findings, "mitre_ttps": sorted({x["mitre"] for x in findings}), "affected_assets": [t.get("host")] if t.get("host") else [], "_exit": exit_code}


def main() -> int:
    ap = argparse.ArgumentParser(description="USAP os-hardening")
    ap.add_argument("--input"); ap.add_argument("--output", choices=["json", "text"], default="text")
    args = ap.parse_args()
    if args.input:
        try:
            t = json.loads(Path(args.input).read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            print(f"error: {exc}", file=sys.stderr); return 2
    else:
        raw = "" if sys.stdin.isatty() else sys.stdin.read()
        t = json.loads(raw) if raw.strip() else {}
    p = analyse(t, args.input); code = p.pop("_exit", 0)
    print(json.dumps(p, indent=2) if args.output == "json" else f"os-hardening: severity={p['severity']}")
    return code


if __name__ == "__main__":
    raise SystemExit(main())
