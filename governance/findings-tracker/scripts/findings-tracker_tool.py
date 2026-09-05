#!/usr/bin/env python3
"""findings-tracker_tool.py

Maintains the findings registry per the SKILL.md: composite risk score,
severity SLA matrix, lifecycle-state validity, and the SLA escalation matrix.
Read-only reporting; auto-closing a false positive is the only mutating
operation and it requires approval. Emits the USAP 11-field payload.

  python3 findings-tracker_tool.py --input registry.json --output json
  python3 findings-tracker_tool.py --output json      # no input: informational, exit 0

Input (see tests/fixtures/findings-tracker-input.json): as_of_utc, findings[]:
  finding_id, title, severity, cvss_base, status, owner, affected_resource,
  exploit (kev|poc|module|none), business (internet_pii|internal_sensitive|
  standard|dev), opened_utc, due_utc, source_agent, verification (for closed).

Exit codes: 0 all on track; 1 overdue findings; 2 critically overdue (>150%)
or a closed finding without verification. Stdlib only.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

SLUG = "findings-tracker"
HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parents[2]
SLA_DAYS = {"critical": 1, "high": 7, "medium": 30, "low": 90, "informational": 180}
EXPLOIT_F = {"kev": 2.0, "poc": 1.5, "module": 1.2, "none": 1.0}
BUSINESS_F = {"internet_pii": 2.0, "internal_sensitive": 1.5, "standard": 1.0, "dev": 0.5}
PRIORITY = [(400, "P0"), (250, "P1"), (120, "P2"), (40, "P3"), (0, "P4")]
VALID_STATUS = {"new", "triaged", "assigned", "in_progress", "pending_verification", "closed", "false_positive", "accepted_risk"}
SEV_RANK = {"critical": 4, "high": 3, "medium": 2, "low": 1, "informational": 0}


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _parse(ts: Optional[str]) -> Optional[datetime]:
    try:
        return datetime.fromisoformat(str(ts).replace("Z", "+00:00")).astimezone(timezone.utc)
    except (ValueError, TypeError):
        return None


def _priority(score: float) -> str:
    for floor, p in PRIORITY:
        if score >= floor:
            return p
    return "P4"


def analyse(t: dict, input_path: Optional[str] = None) -> Dict[str, Any]:
    rel = None
    if input_path:
        try:
            rel = Path(input_path).resolve().relative_to(REPO_ROOT).as_posix()
        except ValueError:
            rel = None
    if not t:
        return {"agent_slug": SLUG, "intent_type": "report", "action": "Supply a findings registry; nothing was provided.",
                "rationale": "No registry supplied; nothing tracked.", "confidence": 0.30, "severity": "informational",
                "key_findings": ["No findings supplied"], "evidence_references": [{"source": "local://governance/findings-tracker/SKILL.md", "ref": "SLA and risk-score model (not applied)"}],
                "next_agents": [], "human_approval_required": False, "timestamp_utc": _now(), "registry": {"findings": []}, "_exit": 0}
    as_of = _parse(t.get("as_of_utc")) or datetime.now(timezone.utc)
    rows: List[dict] = []
    invalid_status: List[str] = []
    unverified_closed: List[str] = []
    for f in [x for x in (t.get("findings") or []) if isinstance(x, dict)]:
        sev = str(f.get("severity", "medium")).lower()
        status = str(f.get("status", "new")).lower()
        if status not in VALID_STATUS:
            invalid_status.append(f"{f.get('finding_id')}: {status}")
        cvss = float(f.get("cvss_base") or 0)
        due = _parse(f.get("due_utc")) or (_parse(f.get("opened_utc")) or as_of).__class__.fromtimestamp((_parse(f.get("opened_utc")) or as_of).timestamp())
        sla = SLA_DAYS.get(sev, 30)
        opened = _parse(f.get("opened_utc")) or as_of
        due = _parse(f.get("due_utc")) or opened
        days_over = (as_of - due).total_seconds() / 86400
        pct = (days_over / sla * 100) if sla else 0
        aging = min(2.0, 1.0 + (max(0, days_over) / sla * 0.5)) if sla else 1.0
        risk = round(cvss * 10 * EXPLOIT_F.get(str(f.get("exploit", "none")).lower(), 1.0) * BUSINESS_F.get(str(f.get("business", "standard")).lower(), 1.0) * aging, 1)
        if days_over <= 0:
            sla_status = "on_track"
        elif pct <= 50:
            sla_status = "warning"
        elif pct <= 100:
            sla_status = "overdue"
        else:
            sla_status = "critically_overdue"
        if status == "closed" and not f.get("verification"):
            unverified_closed.append(str(f.get("finding_id")))
        rows.append({"finding_id": f.get("finding_id"), "title": f.get("title"), "severity": sev, "status": status,
                     "risk_score": risk, "priority": _priority(risk), "owner": f.get("owner"), "affected_resource": f.get("affected_resource"),
                     "days_overdue": round(max(0, days_over), 1), "sla_status": sla_status, "source_agent": f.get("source_agent")})
    rows.sort(key=lambda r: (-r["risk_score"], r["finding_id"] or ""))
    open_rows = [r for r in rows if r["status"] not in ("closed", "false_positive", "accepted_risk")]
    overdue = [r for r in open_rows if r["sla_status"] in ("overdue", "critically_overdue")]
    crit_over = [r for r in open_rows if r["sla_status"] == "critically_overdue"]

    if crit_over or unverified_closed:
        severity, exit_code = "critical", 2
    elif overdue:
        severity, exit_code = "high", 1
    elif any(r["sla_status"] == "warning" for r in open_rows):
        severity, exit_code = "medium", 0
    else:
        severity, exit_code = "low" if rows else "informational", 0

    esc = []
    for r in open_rows:
        if r["sla_status"] == "critically_overdue":
            esc.append(f"{r['finding_id']} executive escalation / risk acceptance ({r['days_overdue']}d overdue)")
        elif r["sla_status"] == "overdue":
            esc.append(f"{r['finding_id']} escalate to security lead")
    action = (f"{len(overdue)} overdue finding(s) ({len(crit_over)} critically): " + "; ".join(esc[:3]) + ".") if overdue else \
             ("Register clean; monitor the warning-band items." if rows else "No findings to track.")
    if unverified_closed:
        action = f"Reopen {len(unverified_closed)} finding(s) closed without verification: {', '.join(unverified_closed)}. " + action

    key = [f"{len(rows)} finding(s): {len(open_rows)} open, {len(overdue)} overdue, {len(crit_over)} critically overdue; top risk score {rows[0]['risk_score'] if rows else 0}"]
    key += [f"{r['priority']} {r['finding_id']} {r['severity']} risk {r['risk_score']} {r['sla_status']} ({r['days_overdue']}d over) owner={r['owner']}" for r in rows[:6]]
    if unverified_closed:
        key.append(f"Closed without verification (treated as open): {', '.join(unverified_closed)}")
    if invalid_status:
        key.append(f"Invalid lifecycle status: {'; '.join(invalid_status)}")

    evidence = [{"source": f"local://{rel}" if rel else "local://governance/findings-tracker/SKILL.md", "ref": "findings registry"},
                {"source": "local://governance/findings-tracker/SKILL.md", "ref": "composite risk score, severity SLA matrix, escalation matrix"}]
    return {"agent_slug": SLUG, "intent_type": "report", "action": action,
            "rationale": ("Each finding scored by the SKILL.md formula (cvss*10 * exploit * business * aging, aging capped at 2.0), SLA and escalation band from the "
                          "severity matrix. A closed finding without a verification record is treated as open. Read-only; auto-closing a false positive would require approval."),
            "confidence": 0.9 if rows else 0.4, "severity": severity, "key_findings": key, "evidence_references": evidence,
            "next_agents": (["metrics-reporting"] if rows else []) + (["ciso-brief-generator"] if crit_over else []),
            "human_approval_required": False, "timestamp_utc": _now(),
            "registry": {"total": len(rows), "open": len(open_rows), "overdue": len(overdue), "critically_overdue": len(crit_over),
                         "unverified_closed": unverified_closed, "findings": rows},
            "mitre_ttps": [], "affected_assets": sorted({str(r["affected_resource"]) for r in rows if r["affected_resource"]}), "_exit": exit_code}


def main() -> int:
    ap = argparse.ArgumentParser(description="USAP findings-tracker")
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
    print(json.dumps(p, indent=2) if args.output == "json" else f"findings-tracker: severity={p['severity']}")
    return code


if __name__ == "__main__":
    raise SystemExit(main())
