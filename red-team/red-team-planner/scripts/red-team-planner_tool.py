#!/usr/bin/env python3
"""red-team-planner_tool.py

Builds a red-team campaign target-prioritisation matrix from the SKILL.md asset
tiers and classifies planning vs. execution actions. Planning is read-only;
execution directives require approval, and modifying an active engagement's scope
requires CISO plus sponsor sign-off. Emits the USAP 11-field payload.

  python3 red-team-planner_tool.py --input engagement.json --output json
  python3 red-team-planner_tool.py --output json    # no input: informational, exit 0

Input (see tests/fixtures/red-team-planner-input.json):
{engagement, targets[] {name, tier (crown_jewels|tier1|tier2|tier3)},
actions[] (keys from the action table)}.

Exit codes: 0 planning only; 1 mutating directive present; 2 an active-scope
modification is requested. Stdlib only.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

SLUG = "red-team-planner"
HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parents[2]
TIER = {
    "crown_jewels": ("Maximum — objective in every campaign", 4),
    "tier1": ("High — secondary objectives", 3),
    "tier2": ("Medium", 2),
    "tier3": ("Low", 1),
}
ACTION = {
    "campaign_plan": ("read_only", ""),
    "target_prioritization": ("read_only", ""),
    "roe_document": ("read_only", ""),
    "recommend_attack_techniques": ("read_only", ""),
    "social_engineering_scripts": ("read_only", ""),
    "execution_directive_safe_exploitation": ("mutating", "human approval"),
    "execution_directive_red_team_ops": ("mutating", "human approval"),
    "modify_scope_active": ("mutating", "CISO + sponsor sign-off"),
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
    targets = [x for x in (t.get("targets") or []) if isinstance(x, dict)]
    actions = t.get("actions") or []
    if not t or (not targets and not actions):
        return {"agent_slug": SLUG, "intent_type": "advise", "action": "Supply targets and/or actions; nothing was provided.",
                "rationale": "No engagement supplied.", "confidence": 0.30, "severity": "informational", "key_findings": ["No engagement supplied"],
                "evidence_references": [{"source": "local://red-team/red-team-planner/SKILL.md", "ref": "tier matrix (not applied)"}],
                "next_agents": [], "human_approval_required": False, "timestamp_utc": _now(), "matrix": [], "_exit": 0}
    matrix: List[dict] = []
    for x in targets:
        tier = str(x.get("tier", "tier2")).lower()
        prio, rank = TIER.get(tier, ("Medium", 2))
        matrix.append({"name": x.get("name"), "tier": tier, "priority": prio, "rank": rank})
    matrix.sort(key=lambda x: -x["rank"])
    items: List[dict] = []
    for a in [str(x).lower() for x in actions]:
        cls, appr = ACTION.get(a, ("read_only", ""))
        items.append({"action": a, "classification": cls, "approvals": appr})
    mutating = [x for x in items if x["classification"] == "mutating"]
    scope_change = [x for x in items if x["action"] == "modify_scope_active"]
    crown = [x for x in matrix if x["tier"] == "crown_jewels"]
    severity = "high" if scope_change else "medium" if mutating else "low"
    exit_code = 2 if scope_change else 1 if mutating else 0
    eng = t.get("engagement", "the engagement")
    action = (f"{eng}: active-scope modification requested — requires CISO + sponsor sign-off before any change." if scope_change else
              f"{eng}: {len(mutating)} execution directive(s) require human approval." if mutating else
              f"{eng}: campaign plan ready; {len(crown)} crown-jewel objective(s), all planning actions read-only.")
    key = [f"{eng}: {len(matrix)} target(s) ({len(crown)} crown jewels), {len(items)} action(s), {len(mutating)} mutating"]
    key += [f"{x['priority'].split(' ')[0]} {x['name']} ({x['tier']})" for x in matrix[:4]]
    key += [f"{x['classification']} {x['action']}" + (f" [{x['approvals']}]" if x['approvals'] else "") for x in items[:4]]
    evidence = [{"source": f"local://{rel}" if rel else "local://red-team/red-team-planner/SKILL.md", "ref": "engagement targets and actions"},
                {"source": "local://red-team/red-team-planner/SKILL.md", "ref": "asset-tier and action tables"}]
    return {"agent_slug": SLUG, "intent_type": "advise", "action": action,
            "rationale": ("Targets are ranked by the SKILL.md asset tiers — crown jewels are an objective in every campaign, tier 1 are secondary objectives — and actions are classified: "
                          "planning, ROE and technique recommendations are read-only, execution directives require human approval, and modifying an active engagement's scope requires CISO "
                          "and sponsor sign-off."),
            "confidence": 0.88, "severity": severity, "key_findings": key, "evidence_references": evidence,
            "next_agents": ["red-team-operations"] if mutating and not scope_change else [], "human_approval_required": bool(mutating), "timestamp_utc": _now(),
            "matrix": matrix, "actions": items, "mitre_ttps": [], "affected_assets": [str(x["name"]) for x in matrix if x.get("name")], "_exit": exit_code}


def main() -> int:
    ap = argparse.ArgumentParser(description="USAP red-team-planner")
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
    print(json.dumps(p, indent=2) if args.output == "json" else f"red-team-planner: severity={p['severity']}")
    return code


if __name__ == "__main__":
    raise SystemExit(main())
