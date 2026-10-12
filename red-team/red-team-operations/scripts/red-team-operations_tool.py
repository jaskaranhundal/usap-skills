#!/usr/bin/env python3
"""red-team-operations_tool.py

Classifies red-team operational actions against the SKILL.md action table
(read-only planning vs. mutating execution directives) and flags the approvals
each needs. Planning is read-only; every execution directive requires human
approval, and exploitation additionally routes through the safe-exploitation
agent. Emits the USAP 11-field payload.

  python3 red-team-operations_tool.py --input op.json --output json
  python3 red-team-operations_tool.py --output json    # no input: informational, exit 0

Input (see tests/fixtures/red-team-operations-input.json):
{operation, actions[] (keys from the action table)}.

Exit codes: 0 planning only; 1 mutating directive present (approval required);
2 exploitation/C2/exfil execution directive present. Stdlib only.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

SLUG = "red-team-operations"
HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parents[2]
# action -> (classification, approvals, high_risk)
ACTION = {
    "generate_execution_plan": ("read_only", "", False),
    "document_c2_design": ("read_only", "", False),
    "produce_ioc_checklist": ("read_only", "", False),
    "recommend_opsec": ("read_only", "", False),
    "recon_directive": ("mutating", "human approval", False),
    "exploitation_directive": ("mutating", "human approval + safe-exploitation agent", True),
    "lateral_movement": ("mutating", "human approval", True),
    "c2_beacon_deployment": ("mutating", "human approval", True),
    "exfiltration_staging": ("mutating", "human approval", True),
}


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def analyse(t: dict, input_path: Optional[str] = None) -> Dict[str, Any]:
    rel = None
    if input_path:
        try:
            rel = Path(input_path).resolve().relative_to(REPO_ROOT).as_posix()
        except ValueError:
            rel = None
    raw = t.get("actions") or []
    if not t or not raw:
        return {"agent_slug": SLUG, "intent_type": "advise", "action": "Supply operational actions; nothing was provided.",
                "rationale": "No actions supplied.", "confidence": 0.30, "severity": "informational", "key_findings": ["No actions supplied"],
                "evidence_references": [{"source": "local://red-team/red-team-operations/SKILL.md", "ref": "action table (not applied)"}],
                "next_agents": [], "human_approval_required": False, "timestamp_utc": _now(), "actions": [], "_exit": 0}
    items: List[dict] = []
    for a in [str(x).lower() for x in raw]:
        cls, appr, hi = ACTION.get(a, ("read_only", "", False))
        items.append({"action": a, "classification": cls, "approvals": appr, "high_risk": hi})
    mutating = [x for x in items if x["classification"] == "mutating"]
    high_risk = [x for x in items if x["high_risk"]]
    severity = "high" if high_risk else "medium" if mutating else "low"
    exit_code = 2 if high_risk else 1 if mutating else 0
    op = t.get("operation", "the operation")
    needs_safe = any(x["action"] == "exploitation_directive" for x in items)
    action = (f"{op}: {len(mutating)} mutating execution directive(s) require human approval before execution — " + ", ".join(x["action"] for x in mutating)[:150] + (". Exploitation routes through safe-exploitation." if needs_safe else ".") if mutating else
              f"{op}: planning actions only; all read-only, no approval required.")
    key = [f"{op}: {len(items)} action(s); {len(mutating)} mutating ({len(high_risk)} high-risk)"]
    key += [f"{x['classification']} {x['action']}" + (f" [{x['approvals']}]" if x['approvals'] else "") for x in items[:7]]
    evidence = [{"source": f"local://{rel}" if rel else "local://red-team/red-team-operations/SKILL.md", "ref": "operation action list"},
                {"source": "local://red-team/red-team-operations/SKILL.md", "ref": "action classification and kill-chain table"}]
    return {"agent_slug": SLUG, "intent_type": "advise", "action": action,
            "rationale": ("Each action is classified against the SKILL.md table: plan generation, C2 design documentation, IOC checklists and OPSEC recommendations are read-only, while every "
                          "execution directive — recon, exploitation, lateral movement, C2 deployment, exfiltration staging — is mutating and requires human approval; exploitation additionally "
                          "routes through the safe-exploitation agent."),
            "confidence": 0.9, "severity": severity, "key_findings": key, "evidence_references": evidence,
            "next_agents": ["safe-exploitation"] if needs_safe else [], "human_approval_required": bool(mutating), "timestamp_utc": _now(),
            "actions": items, "mitre_ttps": [], "affected_assets": [str(op)], "_exit": exit_code}


def main() -> int:
    ap = argparse.ArgumentParser(description="USAP red-team-operations")
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
    print(json.dumps(p, indent=2) if args.output == "json" else f"red-team-operations: severity={p['severity']}")
    return code


if __name__ == "__main__":
    raise SystemExit(main())
