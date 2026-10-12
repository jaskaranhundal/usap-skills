#!/usr/bin/env python3
"""enterprise-risk-assessment_tool.py

Quantifies enterprise cyber risk with FAIR-style Annual Loss Expectancy and tiers
each scenario per the SKILL.md ALE table (Critical > $10M ... Low < $100K) with
its board-attention and response. Read-only. Emits the USAP 11-field payload.

  python3 enterprise-risk-assessment_tool.py --input risk.json --output json
  python3 enterprise-risk-assessment_tool.py --output json    # no input: informational, exit 0

Input (see tests/fixtures/enterprise-risk-assessment-input.json):
{organization, scenarios[] {name, ale} OR {name, tef, plm} (annualised loss =
threat event frequency x probable loss magnitude)}.

Exit codes: 0 all low; 1 medium/high top tier; 2 a critical scenario (> $10M).
Stdlib only.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

SLUG = "enterprise-risk-assessment"
HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parents[2]


def _tier(ale: float) -> tuple:
    if ale > 10_000_000:
        return "critical", "Immediate board escalation", "Emergency remediation plan"
    if ale >= 1_000_000:
        return "high", "Quarterly board reporting", "Risk owner + timeline"
    if ale >= 100_000:
        return "medium", "Annual board reporting", "Risk register entry"
    return "low", "Internal tracking", "Accept or mitigate"


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
    raw = [s for s in (t.get("scenarios") or []) if isinstance(s, dict)]
    if not t or not raw:
        return {"agent_slug": SLUG, "intent_type": "report", "action": "Supply risk scenarios; nothing was provided.",
                "rationale": "No scenarios supplied.", "confidence": 0.30, "severity": "informational", "key_findings": ["No scenarios supplied"],
                "evidence_references": [{"source": "local://risk-compliance/enterprise-risk-assessment/SKILL.md", "ref": "ALE tier table (not applied)"}],
                "next_agents": [], "human_approval_required": False, "timestamp_utc": _now(), "scenarios": [], "_exit": 0}
    scenarios: List[dict] = []
    for s in raw:
        try:
            if s.get("ale") is not None:
                ale = float(s["ale"])
            else:
                ale = float(s.get("tef", 0)) * float(s.get("plm", 0))
        except (TypeError, ValueError):
            ale = 0.0
        tier, board, resp = _tier(ale)
        scenarios.append({"name": s.get("name", "scenario"), "ale": ale, "tier": tier, "board_attention": board, "response": resp})
    scenarios.sort(key=lambda x: -x["ale"])
    counts = {k: sum(1 for x in scenarios if x["tier"] == k) for k in SEV_RANK}
    total_ale = sum(x["ale"] for x in scenarios)
    severity = scenarios[0]["tier"] if scenarios else "informational"
    exit_code = 2 if counts["critical"] else 1 if (counts["high"] or counts["medium"]) else 0
    org = t.get("organization", "the organization")
    action = (f"{counts['critical']} critical risk scenario(s) (> $10M ALE) for {org}; immediate board escalation and an emergency remediation plan for: " + "; ".join(x["name"] for x in scenarios if x["tier"]=="critical")[:130] + "." if counts["critical"] else
              f"Top risk for {org} is {scenarios[0]['tier']} (${scenarios[0]['ale']:,.0f} ALE); {scenarios[0]['board_attention'].lower()}." if scenarios else
              "No material risk scenario.")
    key = [f"{org}: {len(scenarios)} scenario(s), aggregate ALE ${total_ale:,.0f} ({counts['critical']} critical, {counts['high']} high)"]
    key += [f"{x['tier']} {x['name']}: ALE ${x['ale']:,.0f} -> {x['board_attention']}" for x in scenarios[:6]]
    evidence = [{"source": f"local://{rel}" if rel else "local://risk-compliance/enterprise-risk-assessment/SKILL.md", "ref": "risk scenarios"},
                {"source": "local://risk-compliance/enterprise-risk-assessment/SKILL.md", "ref": "FAIR ALE tier table"}]
    return {"agent_slug": SLUG, "intent_type": "report", "action": action,
            "rationale": ("Each scenario's Annual Loss Expectancy (supplied, or threat-event frequency x probable loss magnitude) is placed on the SKILL.md tier table: above $10M is critical "
                          "with immediate board escalation, $1M-$10M high with quarterly reporting. Read-only quantification."),
            "confidence": 0.85, "severity": severity, "key_findings": key, "evidence_references": evidence,
            "next_agents": ["ciso-brief-generator"] if counts["critical"] else [], "human_approval_required": False, "timestamp_utc": _now(),
            "aggregate_ale": total_ale, "scenarios": scenarios, "mitre_ttps": [], "affected_assets": [str(org)], "_exit": exit_code}


def main() -> int:
    ap = argparse.ArgumentParser(description="USAP enterprise-risk-assessment")
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
    print(json.dumps(p, indent=2) if args.output == "json" else f"enterprise-risk-assessment: severity={p['severity']}")
    return code


if __name__ == "__main__":
    raise SystemExit(main())
