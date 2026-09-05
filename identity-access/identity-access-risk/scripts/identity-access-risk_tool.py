#!/usr/bin/env python3
"""identity-access-risk_tool.py

Classifies IAM events against the SKILL.md IAM Anomaly table, assigns blast
radius, and scores severity. Detection is read-only; a recommended credential
operation is gated. Emits the USAP 11-field payload.

  python3 identity-access-risk_tool.py --input iam.json --output json
  python3 identity-access-risk_tool.py --output json    # no input: informational, exit 0

Input (see tests/fixtures/identity-access-risk-input.json): events[]:
{principal, anomaly_type, detail, entitlements[] (e.g. AdministratorAccess,
s3:*, iam:*), mfa_present}.

Exit codes: 0 low; 1 medium/high; 2 critical. Stdlib only.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

SLUG = "identity-access-risk"
HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parents[2]
# anomaly -> (severity, mitre)
ANOMALY = {
    "privilege_escalation": ("critical", "T1078.004"), "mfa_bypass": ("critical", "T1556.006"), "root_account_usage": ("critical", "T1078.004"),
    "lateral_movement": ("high", "T1078.004"), "credential_stuffing": ("high", "T1110.004"), "impossible_travel": ("high", "T1078"),
    "service_account_interactive": ("high", "T1078.002"), "cross_account_anomaly": ("high", "T1550.001"), "data_enumeration_burst": ("high", "T1619"),
    "dormant_reactivation": ("medium", "T1078.004"), "unusual_api_call_volume": ("medium", "T1078.004"), "overprivileged_identity": ("medium", "T1078.004"),
}
FULL = ("administratoraccess", "poweruseraccess", "iam:*", "*:*")
EXFIL = ("s3:", "rds:", "dynamodb:", "secretsmanager:", "ssm:")
INFRA = ("ec2:", "eks:", "lambda:", "vpc:", "iam:createrole", "iam:passrole")


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _blast(ents: List[str]) -> str:
    e = [x.lower() for x in ents]
    if any(any(f in x for f in FULL) for x in e):
        return "full_account"
    if any(any(x.startswith(p) or p in x for p in EXFIL) for x in e):
        return "data_exfiltration_risk"
    if any(any(p in x for p in INFRA) for x in e):
        return "infrastructure_manipulation"
    if e:
        return "service_scoped"
    return "minimal"


def analyse(t: dict, input_path: Optional[str] = None) -> Dict[str, Any]:
    rel = None
    if input_path:
        try:
            rel = Path(input_path).resolve().relative_to(REPO_ROOT).as_posix()
        except ValueError:
            rel = None
    events = [e for e in (t.get("events") or []) if isinstance(e, dict)]
    if not t or not events:
        return {"agent_slug": SLUG, "intent_type": "detect", "action": "Supply IAM events; nothing was provided.",
                "rationale": "No IAM events supplied; no assessment.", "confidence": 0.30, "severity": "informational",
                "key_findings": ["No IAM events supplied"], "evidence_references": [{"source": "local://identity-access/identity-access-risk/SKILL.md", "ref": "anomaly table (not applied)"}],
                "next_agents": [], "human_approval_required": False, "timestamp_utc": _now(), "findings": [], "_exit": 0}
    rank = {"critical": 4, "high": 3, "medium": 2, "low": 1, "informational": 0}
    findings: List[dict] = []
    for e in events:
        at = str(e.get("anomaly_type", "")).lower()
        base_sev, mitre = ANOMALY.get(at, ("medium", "T1078"))
        blast = _blast([str(x) for x in (e.get("entitlements") or [])])
        sev = base_sev
        if blast == "full_account" and base_sev != "critical":
            sev = "critical"
        if at == "mfa_bypass" and e.get("mfa_present") is False:
            sev = "critical"
        findings.append({"principal": e.get("principal"), "anomaly_type": at, "severity": sev, "blast_radius": blast, "detail": e.get("detail", ""), "mitre": mitre})
    findings.sort(key=lambda f: -rank[f["severity"]])
    crit = [f for f in findings if f["severity"] == "critical"]
    severity = findings[0]["severity"] if findings else "informational"
    exit_code = 2 if crit else 1 if any(f["severity"] in ("high", "medium") for f in findings) else 0
    approval = bool(crit)  # a credential revocation would be recommended and is gated
    action = (f"{len(crit)} critical IAM anomaly(ies); recommend revoking sessions/credentials for "
              + ", ".join(f["principal"] for f in crit[:3]) + " (mutating, requires soc_lead approval)." if crit else
              f"{len(findings)} IAM anomaly(ies) to investigate." if findings else "No IAM anomaly.")
    key = [f"{len(events)} IAM event(s): {len(crit)} critical; top {findings[0]['principal']} {findings[0]['anomaly_type']} ({findings[0]['blast_radius']})" if findings else "no events"]
    key += [f"{f['severity']} {f['principal']}: {f['anomaly_type']} blast={f['blast_radius']} — {f['detail'][:80]}" for f in findings[:6]]
    evidence = [{"source": f"local://{rel}" if rel else "local://identity-access/identity-access-risk/SKILL.md", "ref": "IAM events"},
                {"source": "local://identity-access/identity-access-risk/SKILL.md", "ref": "IAM anomaly classification and blast-radius tables"}]
    return {"agent_slug": SLUG, "intent_type": "detect", "action": action,
            "rationale": ("Each event classified against the SKILL.md IAM anomaly table for base severity and MITRE technique, then raised to critical when the principal's "
                          "entitlements give a full-account blast radius or MFA was bypassed. Detection is read-only; a credential operation is gated for soc_lead approval."),
            "confidence": 0.85, "severity": severity, "key_findings": key, "evidence_references": evidence,
            "next_agents": (["incident-classification", "containment-advisor"] if crit else ["findings-tracker"] if findings else []),
            "human_approval_required": approval, "timestamp_utc": _now(),
            "findings": findings, "mutating_category": "credential_operation" if approval else None, "approver_roles": ["soc_lead", "ciso"] if approval else [],
            "mitre_ttps": sorted({f["mitre"] for f in findings}), "affected_assets": [str(f["principal"]) for f in findings], "_exit": exit_code}


def main() -> int:
    ap = argparse.ArgumentParser(description="USAP identity-access-risk")
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
    print(json.dumps(p, indent=2) if args.output == "json" else f"identity-access-risk: severity={p['severity']}")
    return code


if __name__ == "__main__":
    raise SystemExit(main())
