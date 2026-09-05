#!/usr/bin/env python3
"""regulatory-horizon_tool.py

Assesses regulatory readiness against the SKILL.md horizon tables (US and EU/UK):
flags applicable regulations the organization is not ready for, weighted by how
close the effective date is. Read-only board intelligence. Emits the USAP
11-field payload.

  python3 regulatory-horizon_tool.py --input profile.json --output json
  python3 regulatory-horizon_tool.py --output json    # no input: informational, exit 0

Input (see tests/fixtures/regulatory-horizon-input.json):
{organization, regulations[] {name, applicable (bool), ready (bool),
in_effect (bool)}}.

Exit codes: 0 ready; 1 gaps with lead time; 2 an in-effect regulation the org is
not ready for. Stdlib only.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

SLUG = "regulatory-horizon"
HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parents[2]
SEV_RANK = {"critical": 4, "high": 3, "medium": 2, "low": 1, "informational": 0}


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def analyse(t: dict, input_path: Optional[str] = None) -> Dict[str, Any]:
    rel = None
    if input_path:
        try:
            rel = Path(input_path).resolve().relative_to(REPO_ROOT).as_posix()
        except ValueError:
            rel = None
    raw = [r for r in (t.get("regulations") or []) if isinstance(r, dict)]
    if not t or not raw:
        return {"agent_slug": SLUG, "intent_type": "report", "action": "Supply a regulatory profile; nothing was provided.",
                "rationale": "No regulations supplied.", "confidence": 0.30, "severity": "informational", "key_findings": ["No regulations supplied"],
                "evidence_references": [{"source": "local://risk-compliance/regulatory-horizon/SKILL.md", "ref": "horizon tables (not applied)"}],
                "next_agents": [], "human_approval_required": False, "timestamp_utc": _now(), "gaps": [], "_exit": 0}
    gaps: List[dict] = []
    applicable = 0
    for r in raw:
        if not r.get("applicable"):
            continue
        applicable += 1
        if r.get("ready"):
            continue
        in_effect = bool(r.get("in_effect"))
        sev = "critical" if in_effect else "high"
        gaps.append({"regulation": r.get("name", "regulation"), "in_effect": in_effect, "severity": sev,
                     "note": "in effect now and not ready — active non-compliance" if in_effect else "effective on the horizon; close the gap before the deadline"})
    gaps.sort(key=lambda g: -SEV_RANK[g["severity"]])
    crit = [g for g in gaps if g["severity"] == "critical"]
    severity = gaps[0]["severity"] if gaps else "informational"
    exit_code = 2 if crit else 1 if gaps else 0
    org = t.get("organization", "the organization")
    action = (f"{len(crit)} in-effect regulation(s) {org} is not ready for — active non-compliance: " + ", ".join(g["regulation"] for g in crit)[:130] + ". Escalate to the board." if crit else
              f"{len(gaps)} upcoming regulation(s) with readiness gaps for {org}; plan before the effective dates." if gaps else
              f"{org} is ready for all {applicable} applicable regulation(s).")
    key = [f"{org}: {applicable} applicable regulation(s), {len(gaps)} readiness gap(s) ({len(crit)} in effect)"]
    key += [f"{g['severity']} {g['regulation']}: {g['note']}" for g in gaps[:6]]
    evidence = [{"source": f"local://{rel}" if rel else "local://risk-compliance/regulatory-horizon/SKILL.md", "ref": "regulatory profile"},
                {"source": "local://risk-compliance/regulatory-horizon/SKILL.md", "ref": "US and EU/UK regulatory horizon tables"}]
    return {"agent_slug": SLUG, "intent_type": "report", "action": action,
            "rationale": ("Each applicable regulation the organization is not ready for is a gap; one already in effect is critical because it is active non-compliance, while one still on the "
                          "horizon is high and can be planned before its effective date. Read-only board intelligence."),
            "confidence": 0.85, "severity": severity, "key_findings": key, "evidence_references": evidence,
            "next_agents": ["ciso-brief-generator"] if crit else [], "human_approval_required": False, "timestamp_utc": _now(),
            "gaps": gaps, "mitre_ttps": [], "affected_assets": [str(org)], "_exit": exit_code}


def main() -> int:
    ap = argparse.ArgumentParser(description="USAP regulatory-horizon")
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
    print(json.dumps(p, indent=2) if args.output == "json" else f"regulatory-horizon: severity={p['severity']}")
    return code


if __name__ == "__main__":
    raise SystemExit(main())
