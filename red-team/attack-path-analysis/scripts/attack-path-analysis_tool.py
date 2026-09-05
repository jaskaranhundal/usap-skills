#!/usr/bin/env python3
"""attack-path-analysis_tool.py

Scores attack paths by likelihood x impact per the SKILL.md, identifies choke
points, and produces hardening recommendations. Read-only graph analysis;
issuing a lateral-movement or credential-harvesting directive is mutating and
requires approval. Emits the USAP 11-field payload.

  python3 attack-path-analysis_tool.py --input paths.json --output json
  python3 attack-path-analysis_tool.py --output json    # no input: informational, exit 0

Input (see tests/fixtures/attack-path-analysis-input.json):
{source, paths[] {name, category (credential_theft|lateral_movement|
privilege_escalation|data_access), likelihood (0-1), impact (0-1),
choke_point (bool), hardening}}.

Exit codes: 0 low risk; 1 high; 2 critical (score >= 0.75). Stdlib only.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

SLUG = "attack-path-analysis"
HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parents[2]
MITRE = {"credential_theft": "TA0006", "lateral_movement": "TA0008", "privilege_escalation": "TA0004", "data_access": "TA0009"}
SEV_RANK = {"critical": 4, "high": 3, "medium": 2, "low": 1, "informational": 0}


def _sev(score: float) -> str:
    return "critical" if score >= 0.75 else "high" if score >= 0.5 else "medium" if score >= 0.25 else "low"


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def analyse(t: dict, input_path: Optional[str] = None) -> Dict[str, Any]:
    rel = None
    if input_path:
        try:
            rel = Path(input_path).resolve().relative_to(REPO_ROOT).as_posix()
        except ValueError:
            rel = None
    raw = [p for p in (t.get("paths") or []) if isinstance(p, dict)]
    if not t or not raw:
        return {"agent_slug": SLUG, "intent_type": "analyze", "action": "Supply attack-path graph data; nothing was provided.",
                "rationale": "No paths supplied.", "confidence": 0.30, "severity": "informational", "key_findings": ["No paths supplied"],
                "evidence_references": [{"source": "local://red-team/attack-path-analysis/SKILL.md", "ref": "scoring model (not applied)"}],
                "next_agents": [], "human_approval_required": False, "timestamp_utc": _now(), "paths": [], "_exit": 0}
    paths: List[dict] = []
    for p in raw:
        try:
            like = max(0.0, min(1.0, float(p.get("likelihood", 0.5))))
            imp = max(0.0, min(1.0, float(p.get("impact", 0.5))))
        except (TypeError, ValueError):
            like, imp = 0.5, 0.5
        score = round(like * imp, 3)
        cat = str(p.get("category", "")).lower()
        paths.append({"name": p.get("name", "path"), "category": cat, "mitre": MITRE.get(cat, "TA0008"),
                      "likelihood": like, "impact": imp, "score": score, "severity": _sev(score),
                      "choke_point": bool(p.get("choke_point")), "hardening": p.get("hardening")})
    paths.sort(key=lambda x: -x["score"])
    counts = {k: sum(1 for x in paths if x["severity"] == k) for k in SEV_RANK}
    chokes = [x for x in paths if x["choke_point"]]
    severity = paths[0]["severity"] if paths else "informational"
    exit_code = 2 if counts["critical"] else 1 if counts["high"] else 0
    src = t.get("source", "the entry point")
    action = (f"{counts['critical']} critical attack path(s) from {src}; harden the {len(chokes)} choke point(s) first: " + "; ".join(x["name"] for x in chokes[:3])[:150] + "." if (counts["critical"] and chokes) else
              f"{counts['critical']} critical attack path(s) from {src}; prioritise the highest-scoring path for hardening." if counts["critical"] else
              f"{counts['high']} high attack path(s) from {src} to harden." if counts["high"] else
              f"No attack path above medium risk from {src}.")
    key = [f"{len(paths)} path(s) from {src}: {counts['critical']} critical, {counts['high']} high; {len(chokes)} choke point(s)"]
    key += [f"{x['severity']} {x['name']} [{x['mitre']}] score {x['score']}" + (" (choke point)" if x['choke_point'] else "") for x in paths[:6]]
    evidence = [{"source": f"local://{rel}" if rel else "local://red-team/attack-path-analysis/SKILL.md", "ref": "attack-path graph"},
                {"source": "local://red-team/attack-path-analysis/SKILL.md", "ref": "path scoring and category table"}]
    return {"agent_slug": SLUG, "intent_type": "analyze", "action": action,
            "rationale": ("Each path is scored as likelihood x impact and bucketed (>= 0.75 critical, >= 0.5 high); choke points that appear on multiple paths are the highest-leverage "
                          "hardening targets. Analysis is read-only; issuing a lateral-movement or credential-harvesting directive is a mutating action requiring human approval."),
            "confidence": 0.85, "severity": severity, "key_findings": key, "evidence_references": evidence,
            "next_agents": ["red-team-planner"] if counts["critical"] else [], "human_approval_required": False, "timestamp_utc": _now(),
            "paths": paths, "choke_points": [x["name"] for x in chokes], "mitre_ttps": sorted({x["mitre"] for x in paths}), "affected_assets": [], "_exit": exit_code}


def main() -> int:
    ap = argparse.ArgumentParser(description="USAP attack-path-analysis")
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
    print(json.dumps(p, indent=2) if args.output == "json" else f"attack-path-analysis: severity={p['severity']}")
    return code


if __name__ == "__main__":
    raise SystemExit(main())
