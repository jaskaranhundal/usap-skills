#!/usr/bin/env python3
"""ciso-brief-generator_tool.py

Synthesises a board-ready CISO brief from a posture score, KPI metrics and
incident summaries, structured on the SKILL.md Executive Communication
Framework (Headline / So What / What We Are Doing / Ask) in plain language.
Read-only; the brief itself is gated for human approval before it goes to a
board. Emits the USAP 11-field payload.

  python3 ciso-brief-generator_tool.py --input brief.json --output json
  python3 ciso-brief-generator_tool.py --output json     # no input: informational, exit 0

Input (see tests/fixtures/ciso-brief-generator-input.json): brief_type,
period, posture{composite, rating, trend}, metrics{}, incidents[]:
{id, severity, summary, status}, regulatory_gaps[], asks[].

Exit codes: 0 always (advisory). Stdlib only.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

SLUG = "ciso-brief-generator"
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
    if not t:
        return {"agent_slug": SLUG, "intent_type": "report", "action": "Supply posture, metrics and incidents; nothing was provided.",
                "rationale": "No inputs supplied; no brief generated.", "confidence": 0.30, "severity": "informational",
                "key_findings": ["No brief inputs supplied"], "evidence_references": [{"source": "local://governance/ciso-brief-generator/SKILL.md", "ref": "communication framework (not applied)"}],
                "next_agents": [], "human_approval_required": False, "timestamp_utc": _now(), "brief": {}, "_exit": 0}
    posture = t.get("posture") or {}
    incidents = [i for i in (t.get("incidents") or []) if isinstance(i, dict)]
    gaps = [str(g) for g in (t.get("regulatory_gaps") or [])]
    asks = [str(a) for a in (t.get("asks") or [])]
    notable = sorted(incidents, key=lambda i: -SEV_RANK.get(str(i.get("severity", "low")).lower(), 0))
    open_crit = [i for i in incidents if str(i.get("severity", "")).lower() in ("critical", "high") and str(i.get("status", "")).lower() not in ("closed", "resolved")]
    composite = posture.get("composite")
    rating = posture.get("rating", "n/a")

    headline = (f"Security posture is {rating} at {composite}/100 ({posture.get('trend', 'n/a')})"
                if composite is not None else "Security posture summary")
    so_what = ("Open critical work and regulatory deadlines carry direct business and compliance risk."
               if open_crit or gaps else "No material new risk this period; the programme is operating within tolerance.")
    doing = []
    if notable:
        doing.append(f"Responding to {len(incidents)} incident(s); {len(open_crit)} high or critical still open.")
    if gaps:
        doing.append(f"Closing {len(gaps)} regulatory gap(s).")
    if not doing:
        doing.append("Sustaining controls and the monthly measurement cycle.")
    ask = asks or (["Approve remediation investment for the weakest domains."] if composite is not None and composite < 75 else ["No decision required at this time."])

    sections = {"headline": headline, "so_what": so_what, "what_we_are_doing": doing, "ask": ask}
    key_messages = [headline] + [f"{i.get('id', 'incident')}: {i.get('summary', '')[:90]} ({i.get('severity')}, {i.get('status')})" for i in notable[:3]]
    if gaps:
        key_messages.append("Regulatory gaps: " + "; ".join(gaps[:3]))

    severity = "high" if open_crit or gaps else "medium" if composite is not None and composite < 75 else "informational"
    action = f"Review and approve the {t.get('brief_type', 'board')} brief for {t.get('period', 'the period')} before it goes to the board."
    key = [f"{t.get('brief_type', 'board_quarterly')} brief for {t.get('period', 'n/a')}: {len(incidents)} incident(s), {len(open_crit)} open critical/high, {len(gaps)} regulatory gap(s)",
           f"Headline: {headline}", f"So what: {so_what}", "What we are doing: " + " ".join(doing), "Ask: " + "; ".join(ask)]

    evidence = [{"source": f"local://{rel}" if rel else "local://governance/ciso-brief-generator/SKILL.md", "ref": "posture, metrics and incident inputs"},
                {"source": "local://governance/ciso-brief-generator/SKILL.md", "ref": "executive communication framework and plain-language rules"}]
    return {"agent_slug": SLUG, "intent_type": "report", "action": action,
            "rationale": ("Brief assembled on the SKILL.md Headline / So What / What We Are Doing / Ask framework in plain language from the posture score, KPI metrics and "
                          "incident summaries. The brief is gated for human approval before it reaches a board; the tool drafts, it does not send."),
            "confidence": 0.85, "severity": severity, "key_findings": key, "evidence_references": evidence,
            "next_agents": ["security-posture-score", "metrics-reporting"], "human_approval_required": True, "timestamp_utc": _now(),
            "brief": {"brief_type": t.get("brief_type", "board_quarterly"), "period": t.get("period"), "sections": sections, "key_messages": key_messages},
            "mitre_ttps": [], "affected_assets": [], "_exit": 0}


def main() -> int:
    ap = argparse.ArgumentParser(description="USAP ciso-brief-generator")
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
    print(json.dumps(p, indent=2) if args.output == "json" else f"ciso-brief-generator: severity={p['severity']}")
    return code


if __name__ == "__main__":
    raise SystemExit(main())
