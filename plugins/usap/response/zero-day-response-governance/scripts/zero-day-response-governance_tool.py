#!/usr/bin/env python3
"""zero-day-response-governance_tool.py

Assesses a zero-day response programme's governance readiness per the SKILL.md:
disclosure policy, approval pathways, regulatory-communication readiness with
legal review, and compensating-control expiry governance. Read-only. Emits the
USAP 11-field payload.

  python3 zero-day-response-governance_tool.py --input program.json --output json
  python3 zero-day-response-governance_tool.py --output json    # no input: informational, exit 0

Input (see tests/fixtures/zero-day-response-governance-input.json): program{
disclosure_policy, approval_pathways_defined, regulatory_playbook,
legal_review_required, control_expiry_tracking, board_reporting}, open_zero_days,
controls_without_expiry.

Exit codes: 0 governed; 1 governance gaps; 2 a missing approval pathway or
regulatory communication with no legal review. Stdlib only.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

SLUG = "zero-day-response-governance"
HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parents[2]
# key -> (required, severity if missing, description)
REQUIREMENTS = [
    ("disclosure_policy", "high", "no documented vulnerability disclosure policy"),
    ("approval_pathways_defined", "critical", "compensating-control approval pathway not defined"),
    ("regulatory_playbook", "high", "no regulatory-communication playbook"),
    ("legal_review_required", "critical", "regulatory communication not gated behind legal review"),
    ("control_expiry_tracking", "high", "compensating-control expiry not tracked"),
    ("board_reporting", "medium", "no board reporting cadence for zero-day risk"),
]


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def analyse(t: dict, input_path: Optional[str] = None) -> Dict[str, Any]:
    rel = None
    if input_path:
        try:
            rel = Path(input_path).resolve().relative_to(REPO_ROOT).as_posix()
        except ValueError:
            rel = None
    prog = t.get("program") or {}
    if not t or not prog:
        return {"agent_slug": SLUG, "intent_type": "report", "action": "Supply a programme descriptor; nothing was provided.",
                "rationale": "No programme supplied.", "confidence": 0.30, "severity": "informational", "key_findings": ["No programme supplied"],
                "evidence_references": [{"source": "local://response/zero-day-response-governance/SKILL.md", "ref": "governance requirements (not applied)"}],
                "next_agents": [], "human_approval_required": False, "timestamp_utc": _now(), "gaps": [], "_exit": 0}
    rank = {"critical": 4, "high": 3, "medium": 2, "low": 1, "informational": 0}
    gaps = [{"requirement": k, "severity": sev, "description": desc} for k, sev, desc in REQUIREMENTS if not prog.get(k)]
    orphan = int(t.get("controls_without_expiry") or 0)
    if orphan:
        gaps.append({"requirement": "control_expiry_tracking", "severity": "high", "description": f"{orphan} compensating control(s) with no expiry trigger"})
    gaps.sort(key=lambda g: -rank[g["severity"]])
    crit = [g for g in gaps if g["severity"] == "critical"]
    severity = gaps[0]["severity"] if gaps else "informational"
    exit_code = 2 if crit else 1 if gaps else 0
    action = (f"{len(crit)} critical governance gap(s): " + "; ".join(g["description"] for g in crit[:2]) + ". Close before the next zero-day event." if crit else
              f"{len(gaps)} governance gap(s) to close." if gaps else "Zero-day response programme governance is complete.")
    key = [f"Programme governance: {len(gaps)} gap(s) ({len(crit)} critical); {t.get('open_zero_days', 0)} open zero-day(s), {orphan} control(s) without expiry"]
    key += [f"{g['severity'].upper()} {g['requirement']}: {g['description']}" for g in gaps[:6]]
    evidence = [{"source": f"local://{rel}" if rel else "local://response/zero-day-response-governance/SKILL.md", "ref": "programme descriptor"},
                {"source": "local://response/zero-day-response-governance/SKILL.md", "ref": "governance requirements and disclosure policy"}]
    return {"agent_slug": SLUG, "intent_type": "report", "action": action,
            "rationale": ("Each governance requirement is a gap unless present; a missing approval pathway or regulatory communication not gated behind legal review is critical. "
                          "Compensating controls without an expiry trigger are counted as a gap because every control is temporary by definition. Read-only."),
            "confidence": 0.85, "severity": severity, "key_findings": key, "evidence_references": evidence,
            "next_agents": ["ciso-brief-generator"] if crit else [], "human_approval_required": False, "timestamp_utc": _now(),
            "gaps": gaps, "mitre_ttps": [], "affected_assets": [], "_exit": exit_code}


def main() -> int:
    ap = argparse.ArgumentParser(description="USAP zero-day-response-governance")
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
    print(json.dumps(p, indent=2) if args.output == "json" else f"zero-day-response-governance: severity={p['severity']}")
    return code


if __name__ == "__main__":
    raise SystemExit(main())
