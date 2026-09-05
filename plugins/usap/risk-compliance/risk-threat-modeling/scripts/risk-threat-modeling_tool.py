#!/usr/bin/env python3
"""risk-threat-modeling_tool.py

Classifies threats against the SKILL.md STRIDE table (security property violated)
and scores each by likelihood x impact to prioritise mitigations. Read-only.
Emits the USAP 11-field payload.

  python3 risk-threat-modeling_tool.py --input model.json --output json
  python3 risk-threat-modeling_tool.py --output json    # no input: informational, exit 0

Input (see tests/fixtures/risk-threat-modeling-input.json):
{system, threats[] {name, category (spoofing|tampering|repudiation|
information_disclosure|denial_of_service|elevation_of_privilege), likelihood
(0-1), impact (0-1), mitigation}}.

Exit codes: 0 low; 1 high; 2 critical (score >= 0.75). Stdlib only.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

SLUG = "risk-threat-modeling"
HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parents[2]
# STRIDE category -> (property violated, MITRE tactic)
STRIDE = {
    "spoofing": ("Authentication", "TA0006"),
    "tampering": ("Integrity", "TA0040"),
    "repudiation": ("Non-repudiation", "TA0005"),
    "information_disclosure": ("Confidentiality", "TA0009"),
    "denial_of_service": ("Availability", "TA0040"),
    "elevation_of_privilege": ("Authorization", "TA0004"),
}
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
    raw = [x for x in (t.get("threats") or []) if isinstance(x, dict)]
    if not t or not raw:
        return {"agent_slug": SLUG, "intent_type": "analyze", "action": "Supply a threat model; nothing was provided.",
                "rationale": "No threats supplied.", "confidence": 0.30, "severity": "informational", "key_findings": ["No threats supplied"],
                "evidence_references": [{"source": "local://risk-compliance/risk-threat-modeling/SKILL.md", "ref": "STRIDE table (not applied)"}],
                "next_agents": [], "human_approval_required": False, "timestamp_utc": _now(), "threats": [], "_exit": 0}
    threats: List[dict] = []
    for x in raw:
        cat = str(x.get("category", "")).lower().replace(" ", "_")
        prop, mitre = STRIDE.get(cat, ("unclassified", "TA0000"))
        try:
            like = max(0.0, min(1.0, float(x.get("likelihood", 0.5))))
            imp = max(0.0, min(1.0, float(x.get("impact", 0.5))))
        except (TypeError, ValueError):
            like, imp = 0.5, 0.5
        score = round(like * imp, 3)
        threats.append({"name": x.get("name", "threat"), "category": cat, "property": prop, "mitre": mitre,
                        "score": score, "severity": _sev(score), "mitigation": x.get("mitigation")})
    threats.sort(key=lambda x: -x["score"])
    counts = {k: sum(1 for x in threats if x["severity"] == k) for k in SEV_RANK}
    severity = threats[0]["severity"] if threats else "informational"
    exit_code = 2 if counts["critical"] else 1 if counts["high"] else 0
    system = t.get("system", "the system")
    action = (f"{counts['critical']} critical threat(s) in {system}; mitigate first: " + "; ".join(f"{x['name']} ({x['mitigation'] or 'no mitigation'})" for x in threats if x['severity']=='critical')[:150] + "." if counts["critical"] else
              f"{counts['high']} high threat(s) in {system} to mitigate." if counts["high"] else
              f"No threat above medium in {system}.")
    key = [f"{system}: {len(threats)} threat(s) ({counts['critical']} critical, {counts['high']} high)"]
    key += [f"{x['severity']} {x['category']} '{x['name']}' violates {x['property']} [{x['mitre']}] score {x['score']}" for x in threats[:6]]
    evidence = [{"source": f"local://{rel}" if rel else "local://risk-compliance/risk-threat-modeling/SKILL.md", "ref": "threat model"},
                {"source": "local://risk-compliance/risk-threat-modeling/SKILL.md", "ref": "STRIDE classification table"}]
    return {"agent_slug": SLUG, "intent_type": "analyze", "action": action,
            "rationale": ("Each threat is classified by STRIDE to name the security property it violates, then scored as likelihood x impact and bucketed (>= 0.75 critical, >= 0.5 high) to "
                          "order mitigations. Read-only modeling."),
            "confidence": 0.85, "severity": severity, "key_findings": key, "evidence_references": evidence,
            "next_agents": ["risk-prioritization"] if counts["critical"] else [], "human_approval_required": False, "timestamp_utc": _now(),
            "threats": threats, "mitre_ttps": sorted({x["mitre"] for x in threats}), "affected_assets": [str(system)], "_exit": exit_code}


def main() -> int:
    ap = argparse.ArgumentParser(description="USAP risk-threat-modeling")
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
    print(json.dumps(p, indent=2) if args.output == "json" else f"risk-threat-modeling: severity={p['severity']}")
    return code


if __name__ == "__main__":
    raise SystemExit(main())
