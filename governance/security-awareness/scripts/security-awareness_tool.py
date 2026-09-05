#!/usr/bin/env python3
"""security-awareness_tool.py

Measures human-risk posture against the SKILL.md Human Risk Metrics Framework:
phishing click / credential / reporting / repeat-clicker rates, training
completion, and high-risk segment coverage, each versus its target. Read-only.
Emits the USAP 11-field payload.

  python3 security-awareness_tool.py --input awareness.json --output json
  python3 security-awareness_tool.py --output json     # no input: informational, exit 0

Input (see tests/fixtures/security-awareness-input.json): period, baseline_click_rate,
metrics{click_rate, privileged_click_rate, credential_submission_rate,
reporting_rate, training_completion_pct, repeat_clicker_pct}, segments[]:
{name, click_rate}.

Exit codes: 0 all on target; 1 a target breached; 2 credential submission rate
above target (direct compromise path). Stdlib only.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

SLUG = "security-awareness"
HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parents[2]
# (key, label, target text, ok predicate, critical?)
KPIS: List[Tuple[str, str, str, Callable[[float], bool], bool]] = [
    ("click_rate", "Phishing click rate", "< 0.05", lambda v: v < 0.05, False),
    ("privileged_click_rate", "Privileged-user click rate", "< 0.03", lambda v: v < 0.03, False),
    ("credential_submission_rate", "Credential submission rate", "< 0.01", lambda v: v < 0.01, True),
    ("reporting_rate", "Suspicious-email reporting rate", ">= 0.30", lambda v: v >= 0.30, False),
    ("training_completion_pct", "Training completion", ">= 95%", lambda v: v >= 95, False),
    ("repeat_clicker_pct", "Repeat clickers (90d)", "< 0.02", lambda v: v < 0.02, False),
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
    m = t.get("metrics") or {}
    if not t or not m:
        return {"agent_slug": SLUG, "intent_type": "report", "action": "Supply awareness metrics; nothing was provided.",
                "rationale": "No metrics supplied; no human-risk assessment.", "confidence": 0.30, "severity": "informational",
                "key_findings": ["No awareness metrics supplied"], "evidence_references": [{"source": "local://governance/security-awareness/SKILL.md", "ref": "human risk metrics (not applied)"}],
                "next_agents": [], "human_approval_required": False, "timestamp_utc": _now(), "human_risk": {}, "_exit": 0}
    results, breached, crit = [], [], False
    for key, label, target, ok, is_crit in KPIS:
        if key not in m or m[key] is None:
            continue
        v = float(m[key]); on = ok(v)
        r = {"kpi": key, "label": label, "value": v, "target": target, "on_target": on, "critical": is_crit}
        results.append(r)
        if not on:
            breached.append(r)
            crit = crit or is_crit
    segs = [s for s in (t.get("segments") or []) if isinstance(s, dict)]
    high_segs = sorted([s for s in segs if float(s.get("click_rate", 0)) >= 0.05], key=lambda s: -float(s.get("click_rate", 0)))
    baseline = t.get("baseline_click_rate")
    cur = m.get("click_rate")
    trend = None
    if baseline is not None and cur is not None:
        trend = "improving" if float(cur) < float(baseline) else "worsening" if float(cur) > float(baseline) else "flat"
    severity = "critical" if crit else "high" if breached else "low" if results else "informational"
    exit_code = 2 if crit else 1 if breached else 0
    action = (f"{len(breached)} human-risk target(s) breached for {t.get('period', 'the period')}: " +
              "; ".join(f"{b['label']} {b['value']} (target {b['target']})" for b in breached[:4]) +
              (f". Enhanced training for high-click segments: {', '.join(s['name'] for s in high_segs[:3])}." if high_segs else ".")) if breached else \
             f"All human-risk targets met for {t.get('period', 'the period')}" + (f"; click rate {trend} vs baseline." if trend else ".")
    key = [f"Human-risk review {t.get('period', 'n/a')}: {len(results)} KPI(s), {len(breached)} breached" + (f"; click rate {trend} vs baseline {baseline}" if trend else "")]
    key += [f"{'BREACH' if not r['on_target'] else 'ok '} {r['label']}: {r['value']} (target {r['target']})" for r in results]
    if high_segs:
        key.append("High-risk segments (>=5% click): " + ", ".join(f"{s['name']} {float(s['click_rate']):.0%}" for s in high_segs[:5]))
    evidence = [{"source": f"local://{rel}" if rel else "local://governance/security-awareness/SKILL.md", "ref": "awareness metrics"},
                {"source": "local://governance/security-awareness/SKILL.md", "ref": "human risk metrics framework and targets"}]
    return {"agent_slug": SLUG, "intent_type": "report", "action": action,
            "rationale": ("Each behavioral KPI compared to its SKILL.md target; a credential submission rate above target is critical because it is a direct account-compromise "
                          "path. Segments clicking at or above 5% are surfaced for enhanced training (remediation, not punishment). Read-only."),
            "confidence": round(min(0.9, 0.55 + 0.06 * len(results)), 2), "severity": severity, "key_findings": key, "evidence_references": evidence,
            "next_agents": ["metrics-reporting"], "human_approval_required": False, "timestamp_utc": _now(),
            "human_risk": {"kpis": results, "breached": [b["kpi"] for b in breached], "high_risk_segments": [s["name"] for s in high_segs], "trend": trend},
            "mitre_ttps": ["T1566"], "affected_assets": [], "_exit": exit_code}


def main() -> int:
    ap = argparse.ArgumentParser(description="USAP security-awareness")
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
    print(json.dumps(p, indent=2) if args.output == "json" else f"security-awareness: severity={p['severity']}")
    return code


if __name__ == "__main__":
    raise SystemExit(main())
