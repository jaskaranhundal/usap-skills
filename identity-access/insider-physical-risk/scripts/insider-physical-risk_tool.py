#!/usr/bin/env python3
"""insider-physical-risk_tool.py

Scores insider and physical risk per the SKILL.md behavioral indicators and
high-risk-period model, while respecting the privacy guardrail: individual-level
actions require HR and Legal co-approval. Read-only assessment. Emits the USAP
11-field payload.

  python3 insider-physical-risk_tool.py --input insider.json --output json
  python3 insider-physical-risk_tool.py --output json    # no input: informational, exit 0

Input (see tests/fixtures/insider-physical-risk-input.json): subjects[]:
{id, indicators[] (bulk_download|off_hours_access|data_staging|
usb_mass_storage|failed_badge|tailgating|access_after_resignation|
disabled_account_activity), high_risk_period (resignation|disciplinary|review|none),
role_sensitive}.

Exit codes: 0 low; 1 elevated; 2 high (active exfiltration signals in a
high-risk period). Stdlib only.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

SLUG = "insider-physical-risk"
HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parents[2]
INDICATOR_WEIGHT = {
    "bulk_download": 3, "data_staging": 3, "usb_mass_storage": 2, "off_hours_access": 1,
    "access_after_resignation": 4, "disabled_account_activity": 4, "failed_badge": 1, "tailgating": 2,
}
EXFIL_SIGNALS = {"bulk_download", "data_staging", "usb_mass_storage"}
PERIOD_MULT = {"resignation": 1.5, "disciplinary": 1.4, "review": 1.2, "none": 1.0}


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _score(s: dict) -> dict:
    inds = [str(i).lower() for i in (s.get("indicators") or [])]
    period = str(s.get("high_risk_period", "none")).lower()
    base = sum(INDICATOR_WEIGHT.get(i, 1) for i in inds)
    score = round(base * PERIOD_MULT.get(period, 1.0), 1)
    if s.get("role_sensitive"):
        score = round(score * 1.2, 1)
    exfil_active = bool(set(inds) & EXFIL_SIGNALS)
    if score >= 8 or (exfil_active and period != "none"):
        sev = "high"
    elif score >= 4:
        sev = "medium"
    elif score > 0:
        sev = "low"
    else:
        sev = "informational"
    return {"id": s.get("id"), "indicators": inds, "high_risk_period": period, "risk_score": score, "severity": sev, "exfil_signals": exfil_active}


def analyse(t: dict, input_path: Optional[str] = None) -> Dict[str, Any]:
    rel = None
    if input_path:
        try:
            rel = Path(input_path).resolve().relative_to(REPO_ROOT).as_posix()
        except ValueError:
            rel = None
    subjects = [s for s in (t.get("subjects") or []) if isinstance(s, dict)]
    if not t or not subjects:
        return {"agent_slug": SLUG, "intent_type": "analyze", "action": "Supply subject signals; nothing was provided.",
                "rationale": "No subjects supplied; no assessment.", "confidence": 0.30, "severity": "informational",
                "key_findings": ["No subjects supplied"], "evidence_references": [{"source": "local://identity-access/insider-physical-risk/SKILL.md", "ref": "behavioral indicators (not applied)"}],
                "next_agents": [], "human_approval_required": False, "timestamp_utc": _now(), "subjects": [], "_exit": 0}
    rank = {"critical": 4, "high": 3, "medium": 2, "low": 1, "informational": 0}
    scored = sorted((_score(s) for s in subjects), key=lambda r: -r["risk_score"])
    high = [r for r in scored if r["severity"] == "high"]
    severity = scored[0]["severity"] if scored else "informational"
    exit_code = 2 if high else 1 if any(r["severity"] == "medium" for r in scored) else 0
    action = (f"{len(high)} subject(s) at elevated insider risk (identifiers only). Any individual-level action requires HR and Legal co-approval; "
              "investigate the corroborating telemetry before contacting anyone." if high else
              f"{len([r for r in scored if r['severity']=='medium'])} medium-risk subject(s) to monitor." if any(r["severity"]=="medium" for r in scored) else
              "No subject above the low-risk threshold.")
    key = [f"{len(subjects)} subject(s): {len(high)} elevated; top risk score {scored[0]['risk_score']}"]
    key += [f"{r['severity']} {r['id']}: score {r['risk_score']} ({r['high_risk_period']} period), indicators {', '.join(r['indicators'])}" for r in scored[:6]]
    key.append("Privacy guardrail: this output ranks risk, it does not authorise surveillance or action; HR and Legal co-approve any individual measure.")
    evidence = [{"source": f"local://{rel}" if rel else "local://identity-access/insider-physical-risk/SKILL.md", "ref": "subject behavioral signals"},
                {"source": "local://identity-access/insider-physical-risk/SKILL.md", "ref": "behavioral risk indicators and high-risk-period model"}]
    return {"agent_slug": SLUG, "intent_type": "analyze", "action": action,
            "rationale": ("Each subject's indicators are weighted (data staging, bulk download and post-resignation activity heaviest) and multiplied by the high-risk-period and "
                          "role-sensitivity factors. Active exfiltration signals during a high-risk period raise severity to high. Read-only; individual action needs HR and Legal co-approval."),
            "confidence": 0.8, "severity": severity, "key_findings": key, "evidence_references": evidence,
            "next_agents": ["incident-classification"] if high else [], "human_approval_required": bool(high), "timestamp_utc": _now(),
            "approver_roles": ["hr_director", "legal", "ciso"] if high else [],
            "subjects": scored, "mitre_ttps": ["T1530"] if any(r["exfil_signals"] for r in scored) else [], "affected_assets": [str(r["id"]) for r in high], "_exit": exit_code}


def main() -> int:
    ap = argparse.ArgumentParser(description="USAP insider-physical-risk")
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
    print(json.dumps(p, indent=2) if args.output == "json" else f"insider-physical-risk: severity={p['severity']}")
    return code


if __name__ == "__main__":
    raise SystemExit(main())
