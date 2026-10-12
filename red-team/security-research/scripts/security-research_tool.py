#!/usr/bin/env python3
"""security-research_tool.py

Scores emerging-threat research items per the SKILL.md: a confidence level from
the evidence basis and an action priority (P0-P3) from the timeframe table.
Read-only. Emits the USAP 11-field payload.

  python3 security-research_tool.py --input items.json --output json
  python3 security-research_tool.py --output json    # no input: informational, exit 0

Input (see tests/fixtures/security-research-input.json):
{items[] {title, cve, poc (bool), cisa_kev (bool), active_exploitation (bool),
in_our_stack (bool), vendor_advisory (bool)}}.

Exit codes: 0 no P0/P1; 1 P1; 2 P0 (KEV + active exploitation in our stack).
Stdlib only.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

SLUG = "security-research"
HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parents[2]
PRIO_RANK = {"P0": 3, "P1": 2, "P2": 1, "P3": 0}


def _confidence(it: dict) -> float:
    if it.get("cve") and it.get("poc") and it.get("cisa_kev"):
        return 0.9
    if it.get("cve") and it.get("vendor_advisory"):
        return 0.7
    if it.get("cve"):
        return 0.5
    return 0.35


def _priority(it: dict) -> str:
    stack = bool(it.get("in_our_stack"))
    if it.get("cisa_kev") and it.get("active_exploitation") and stack:
        return "P0"
    if it.get("poc") and stack:
        return "P1"
    if stack:
        return "P2"
    return "P3"


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def analyse(t: dict, input_path: Optional[str] = None) -> Dict[str, Any]:
    rel = None
    if input_path:
        try:
            rel = Path(input_path).resolve().relative_to(REPO_ROOT).as_posix()
        except ValueError:
            rel = None
    raw = [i for i in (t.get("items") or []) if isinstance(i, dict)]
    if not t or not raw:
        return {"agent_slug": SLUG, "intent_type": "report", "action": "Supply research items; nothing was provided.",
                "rationale": "No items supplied.", "confidence": 0.30, "severity": "informational", "key_findings": ["No items supplied"],
                "evidence_references": [{"source": "local://red-team/security-research/SKILL.md", "ref": "confidence/priority tables (not applied)"}],
                "next_agents": [], "human_approval_required": False, "timestamp_utc": _now(), "items": [], "_exit": 0}
    TF = {"P0": "< 24 hours", "P1": "< 7 days", "P2": "< 30 days", "P3": "< 90 days"}
    SEVMAP = {"P0": "critical", "P1": "high", "P2": "medium", "P3": "low"}
    items: List[dict] = []
    for it in raw:
        prio = _priority(it)
        items.append({"title": it.get("title", "item"), "cve": it.get("cve"), "confidence": _confidence(it),
                      "priority": prio, "timeframe": TF[prio], "severity": SEVMAP[prio]})
    items.sort(key=lambda x: (-PRIO_RANK[x["priority"]], -x["confidence"]))
    counts = {p: sum(1 for x in items if x["priority"] == p) for p in PRIO_RANK}
    p0 = counts["P0"]; p1 = counts["P1"]
    severity = items[0]["severity"] if items else "informational"
    exit_code = 2 if p0 else 1 if p1 else 0
    action = (f"{p0} P0 item(s) — act within 24 hours: " + "; ".join(x["title"] for x in items if x["priority"] == "P0")[:150] + "." if p0 else
              f"{p1} P1 item(s) — act within 7 days." if p1 else
              "No P0/P1 research item; track P2/P3 on the planned cadence.")
    key = [f"{len(items)} item(s): {p0} P0, {p1} P1, {counts['P2']} P2, {counts['P3']} P3"]
    key += [f"{x['priority']} {x['title']} ({x['cve'] or 'no CVE'}) conf {x['confidence']:.2f} -> {x['timeframe']}" for x in items[:6]]
    evidence = [{"source": f"local://{rel}" if rel else "local://red-team/security-research/SKILL.md", "ref": "research items"},
                {"source": "https://www.cisa.gov/known-exploited-vulnerabilities-catalog", "ref": "CISA KEV catalog"},
                {"source": "local://red-team/security-research/SKILL.md", "ref": "confidence and priority tables"}]
    return {"agent_slug": SLUG, "intent_type": "report", "action": action,
            "rationale": ("Each item's confidence is set from its evidence basis (CVE + PoC + KEV is high, CVE + vendor advisory is medium) and its action priority from the timeframe table: "
                          "KEV plus active exploitation in our stack is P0 within 24 hours, a released PoC affecting our stack is P1 within 7 days. Read-only."),
            "confidence": 0.85, "severity": severity, "key_findings": key, "evidence_references": evidence,
            "next_agents": ["vulnerability-management"] if p0 else [], "human_approval_required": False, "timestamp_utc": _now(),
            "items": items, "mitre_ttps": [], "affected_assets": [], "_exit": exit_code}


def main() -> int:
    ap = argparse.ArgumentParser(description="USAP security-research")
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
    print(json.dumps(p, indent=2) if args.output == "json" else f"security-research: severity={p['severity']}")
    return code


if __name__ == "__main__":
    raise SystemExit(main())
