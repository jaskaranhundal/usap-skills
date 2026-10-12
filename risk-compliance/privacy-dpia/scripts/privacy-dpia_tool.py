#!/usr/bin/env python3
"""privacy-dpia_tool.py

Assesses a processing activity for GDPR DPIA readiness per the SKILL.md: lawful
basis, high-risk-processing DPIA requirement, and data-subject-rights
implementation gaps. Read-only. Emits the USAP 11-field payload.

  python3 privacy-dpia_tool.py --input processing.json --output json
  python3 privacy-dpia_tool.py --output json    # no input: informational, exit 0

Input (see tests/fixtures/privacy-dpia-input.json):
{activity, lawful_basis (consent|contract|legal_obligation|vital_interests|
public_task|legitimate_interests|none), high_risk (bool), dpia_completed (bool),
rights{access, rectification, erasure, restriction} (booleans),
special_category (bool)}.

Exit codes: 0 compliant; 1 gaps; 2 high-risk processing without a DPIA, or no
lawful basis. Stdlib only.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

SLUG = "privacy-dpia"
HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parents[2]
LAWFUL = {"consent", "contract", "legal_obligation", "vital_interests", "public_task", "legitimate_interests"}
RIGHTS = {"access": "Art 15", "rectification": "Art 16", "erasure": "Art 17", "restriction": "Art 18"}
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
    if not t or not t.get("activity"):
        return {"agent_slug": SLUG, "intent_type": "report", "action": "Supply a processing activity; nothing was provided.",
                "rationale": "No activity supplied.", "confidence": 0.30, "severity": "informational", "key_findings": ["No activity supplied"],
                "evidence_references": [{"source": "local://risk-compliance/privacy-dpia/SKILL.md", "ref": "lawful-basis and rights tables (not applied)"}],
                "next_agents": [], "human_approval_required": False, "timestamp_utc": _now(), "gaps": [], "_exit": 0}
    activity = t.get("activity")
    basis = str(t.get("lawful_basis", "none")).lower()
    high_risk = bool(t.get("high_risk"))
    gaps: List[dict] = []
    if basis not in LAWFUL:
        gaps.append({"gap": "no_lawful_basis", "severity": "critical", "note": "no valid Art. 6 lawful basis for processing"})
    if high_risk and not t.get("dpia_completed"):
        gaps.append({"gap": "dpia_missing", "severity": "critical", "note": "high-risk processing requires a completed DPIA (Art. 35)"})
    if t.get("special_category") and basis == "legitimate_interests":
        gaps.append({"gap": "special_category_basis", "severity": "high", "note": "special-category data needs an Art. 9 condition, not legitimate interests alone"})
    rights = t.get("rights") or {}
    for r, art in RIGHTS.items():
        if r in rights and not rights.get(r):
            sev = "high" if r in ("access", "erasure") else "medium"
            gaps.append({"gap": f"right_{r}", "severity": sev, "note": f"data-subject right to {r} not implemented ({art})"})
    gaps.sort(key=lambda g: -SEV_RANK[g["severity"]])
    crit = [g for g in gaps if g["severity"] == "critical"]
    severity = gaps[0]["severity"] if gaps else "informational"
    exit_code = 2 if crit else 1 if gaps else 0
    action = (f"{activity}: {len(crit)} critical privacy gap(s) — " + "; ".join(g["note"] for g in crit[:2])[:180] + ". Do not proceed until resolved." if crit else
              f"{activity}: {len(gaps)} privacy gap(s) to close." if gaps else
              f"{activity}: DPIA and rights requirements met for basis '{basis}'.")
    key = [f"{activity}: lawful basis '{basis}', high_risk={high_risk}; {len(gaps)} gap(s) ({len(crit)} critical)"]
    key += [f"{g['severity']} {g['gap']}: {g['note']}" for g in gaps[:6]]
    evidence = [{"source": f"local://{rel}" if rel else "local://risk-compliance/privacy-dpia/SKILL.md", "ref": "processing activity"},
                {"source": "local://risk-compliance/privacy-dpia/SKILL.md", "ref": "lawful-basis and data-subject-rights tables"}]
    return {"agent_slug": SLUG, "intent_type": "report", "action": action,
            "rationale": ("The activity is checked for an Art. 6 lawful basis, the Art. 35 DPIA requirement when processing is high-risk, and the implementation of data-subject rights. No "
                          "lawful basis and high-risk processing without a DPIA are critical because they make the processing itself unlawful. Read-only assessment."),
            "confidence": 0.85, "severity": severity, "key_findings": key, "evidence_references": evidence,
            "next_agents": ["findings-tracker"] if gaps else [], "human_approval_required": False, "timestamp_utc": _now(),
            "gaps": gaps, "mitre_ttps": [], "affected_assets": [str(activity)], "_exit": exit_code}


def main() -> int:
    ap = argparse.ArgumentParser(description="USAP privacy-dpia")
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
    print(json.dumps(p, indent=2) if args.output == "json" else f"privacy-dpia: severity={p['severity']}")
    return code


if __name__ == "__main__":
    raise SystemExit(main())
