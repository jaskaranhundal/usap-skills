#!/usr/bin/env python3
"""secure-sdlc_tool.py

Scores an SDLC security programme against the SKILL.md maturity ladder (level 0
"no SDLC security" to level 5 "optimizing") from the gates in place, and names
the next gate to add. Read-only advisory. Emits the USAP 11-field payload.

  python3 secure-sdlc_tool.py --input program.json --output json
  python3 secure-sdlc_tool.py --output json    # no input: informational, exit 0

Input (see tests/fixtures/secure-sdlc-input.json):
{team, gates{secret_scanning, sast_on_pr, sca, dast, iac_scan, threat_modeling,
full_cicd_gates, continuous_red_team, chaos_testing}} (booleans),
target_level (0-5).

Exit codes: 0 at/above target; 1 one level below; 2 two or more below (or level
<= 1). Stdlib only.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

SLUG = "secure-sdlc"
HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parents[2]
# ordered maturity requirements; level = count of leading requirements satisfied
LADDER = [
    ("secret_scanning", "Level 1 (Ad-hoc): basic secret scanning"),
    ("sast_on_pr", "Level 2 (Developing): SAST on PR"),
    ("sca", "Level 2 (Developing): software composition analysis"),
    ("dast", "Level 3 (Defined): DAST"),
    ("iac_scan", "Level 3 (Defined): IaC scanning"),
    ("threat_modeling", "Level 4 (Managed): threat modeling"),
    ("full_cicd_gates", "Level 4 (Managed): full CI/CD gates"),
    ("continuous_red_team", "Level 5 (Optimizing): continuous red team"),
    ("chaos_testing", "Level 5 (Optimizing): chaos testing"),
]
# map count of satisfied leading requirements -> maturity level
def _level_from(gates: dict) -> tuple:
    satisfied = 0
    first_gap = None
    for key, label in LADDER:
        if gates.get(key):
            satisfied += 1
        else:
            first_gap = label
            break
    # bucket the satisfied count into the 0-5 ladder
    buckets = [0, 1, 2, 2, 3, 3, 4, 4, 5, 5]
    return buckets[satisfied], first_gap


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def analyse(t: dict, input_path: Optional[str] = None) -> Dict[str, Any]:
    rel = None
    if input_path:
        try:
            rel = Path(input_path).resolve().relative_to(REPO_ROOT).as_posix()
        except ValueError:
            rel = None
    gates = t.get("gates") or {}
    if not t or not gates:
        return {"agent_slug": SLUG, "intent_type": "advise", "action": "Supply the SDLC gates in place; nothing was provided.",
                "rationale": "No programme supplied.", "confidence": 0.30, "severity": "informational", "key_findings": ["No programme supplied"],
                "evidence_references": [{"source": "local://appsec-devsecops/secure-sdlc/SKILL.md", "ref": "maturity ladder (not applied)"}],
                "next_agents": [], "human_approval_required": False, "timestamp_utc": _now(), "level": None, "_exit": 0}
    level, first_gap = _level_from(gates)
    try:
        target = int(t.get("target_level", 4))
    except (TypeError, ValueError):
        target = 4
    gap = max(0, target - level)
    severity = "critical" if level <= 1 else "high" if gap >= 2 else "medium" if gap == 1 else "low"
    exit_code = 2 if (level <= 1 or gap >= 2) else 1 if gap == 1 else 0
    team = t.get("team", "the team")
    missing = [label for key, label in LADDER if not gates.get(key)]
    action = (f"{team} is at SDLC maturity level {level} (target {target}); add next: {first_gap}." if gap else
              f"{team} meets SDLC maturity target level {level}; sustain and measure.")
    key = [f"{team}: SDLC maturity level {level}/5 (target {target}, gap {gap}); {len(missing)} gate(s) missing"]
    key += [f"missing: {m}" for m in missing[:6]]
    evidence = [{"source": f"local://{rel}" if rel else "local://appsec-devsecops/secure-sdlc/SKILL.md", "ref": "gates in place"},
                {"source": "local://appsec-devsecops/secure-sdlc/SKILL.md", "ref": "SDLC maturity ladder"}]
    return {"agent_slug": SLUG, "intent_type": "advise", "action": action,
            "rationale": ("Maturity is scored by walking the SKILL.md ladder in order — secret scanning, SAST on PR and SCA, DAST and IaC scanning, threat modeling and full CI/CD gates, "
                          "then continuous red team and chaos testing — and bucketing the leading satisfied gates into levels 0 to 5. The next gate to add is the first gap. Read-only advisory."),
            "confidence": 0.85, "severity": severity, "key_findings": key, "evidence_references": evidence,
            "next_agents": ["devsecops-pipeline"] if gap else [], "human_approval_required": False, "timestamp_utc": _now(),
            "level": level, "target_level": target, "missing_gates": missing, "mitre_ttps": [], "affected_assets": [team] if t.get("team") else [], "_exit": exit_code}


def main() -> int:
    ap = argparse.ArgumentParser(description="USAP secure-sdlc")
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
    print(json.dumps(p, indent=2) if args.output == "json" else f"secure-sdlc: level={p.get('level')} severity={p['severity']}")
    return code


if __name__ == "__main__":
    raise SystemExit(main())
