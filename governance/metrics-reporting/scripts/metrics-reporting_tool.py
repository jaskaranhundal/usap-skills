#!/usr/bin/env python3
"""metrics-reporting_tool.py

Computes the SKILL.md security KPIs from raw metric inputs against their
targets, translates breaches into business language, and states the decisions
needed. Read-only. Emits the USAP 11-field payload.

  python3 metrics-reporting_tool.py --input metrics.json --output json
  python3 metrics-reporting_tool.py --output json      # no input: informational, exit 0

Input (see tests/fixtures/metrics-reporting-input.json): period, report_type,
metrics{mttd_min, mttr_hours_critical, false_positive_rate, patch_coverage_pct,
sla_compliance_pct, phishing_click_rate, training_completion_pct,
critical_open_count, approval_completion_rate, evidence_chain_integrity}.

Exit codes: 0 all KPIs on target; 1 one or more breached; 2 a critical KPI
breached (critical_open_count>0 or approval/evidence integrity<100). Stdlib only.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

SLUG = "metrics-reporting"
HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parents[2]

# (key, label, target_text, ok predicate, critical?)
KPIS: List[Tuple[str, str, str, Callable[[float], bool], bool]] = [
    ("mttd_min", "Mean time to detect", "< 30 min", lambda v: v < 30, False),
    ("mttr_hours_critical", "Mean time to remediate (critical)", "< 4 h", lambda v: v < 4, False),
    ("false_positive_rate", "False-positive rate", "< 0.40", lambda v: v < 0.40, False),
    ("patch_coverage_pct", "Patch coverage (critical)", ">= 95%", lambda v: v >= 95, False),
    ("sla_compliance_pct", "SLA compliance", ">= 90%", lambda v: v >= 90, False),
    ("phishing_click_rate", "Phishing click rate", "< 0.05", lambda v: v < 0.05, False),
    ("training_completion_pct", "Training completion", ">= 95%", lambda v: v >= 95, False),
    ("critical_open_count", "Open critical incidents", "0", lambda v: v == 0, True),
    ("approval_completion_rate", "Approval completion", "100%", lambda v: v >= 100, True),
    ("evidence_chain_integrity", "Evidence-chain integrity", "100%", lambda v: v >= 100, True),
]
TRANSLATE = {
    "false_positive_rate": "Signal quality is low — the team spends time on noise, not real threats.",
    "phishing_click_rate": "Staff are clicking simulated phishing above target — human attack surface is elevated.",
    "patch_coverage_pct": "Critical systems remain unpatched beyond the coverage target — exploitable exposure.",
    "critical_open_count": "Unresolved critical incidents remain open — active business risk.",
    "evidence_chain_integrity": "Some security decisions are not fully auditable — audit and regulatory risk.",
    "approval_completion_rate": "Mutating actions occurred without a recorded approval — governance gap.",
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
    m = t.get("metrics") or {}
    if not t or not m:
        return {"agent_slug": SLUG, "intent_type": "report", "action": "Supply a metrics object; nothing was provided.",
                "rationale": "No metrics supplied; no KPIs computed.", "confidence": 0.30, "severity": "informational",
                "key_findings": ["No metrics supplied"], "evidence_references": [{"source": "local://governance/metrics-reporting/SKILL.md", "ref": "KPI definitions (not applied)"}],
                "next_agents": [], "human_approval_required": False, "timestamp_utc": _now(), "kpis": [], "_exit": 0}
    results: List[dict] = []
    breached: List[dict] = []
    crit_breach = False
    for key, label, target, ok, is_crit in KPIS:
        if key not in m or m[key] is None:
            continue
        v = float(m[key])
        on = ok(v)
        r = {"kpi": key, "label": label, "value": v, "target": target, "on_target": on, "critical": is_crit}
        results.append(r)
        if not on:
            breached.append(r)
            if is_crit:
                crit_breach = True
    severity = "critical" if crit_breach else "high" if breached else "low" if results else "informational"
    exit_code = 2 if crit_breach else 1 if breached else 0
    decisions = [TRANSLATE.get(b["kpi"], f"{b['label']} is off target ({b['value']} vs {b['target']}).") for b in breached] or ["No decisions required at this time."]
    action = (f"{len(breached)} KPI(s) off target for {t.get('period', 'the period')}: " + "; ".join(f"{b['label']} {b['value']} (target {b['target']})" for b in breached[:4]) + ".") if breached else \
             f"All {len(results)} KPIs on target for {t.get('period', 'the period')}."
    key = [f"{t.get('report_type', 'operational_kpi_report')} for {t.get('period', 'n/a')}: {len(results)} KPI(s), {len(breached)} off target"]
    key += [f"{'OFF' if not r['on_target'] else 'ok '} {r['label']}: {r['value']} (target {r['target']})" for r in results[:8]]
    key.append("Decisions needed: " + "; ".join(decisions[:3]))
    evidence = [{"source": f"local://{rel}" if rel else "local://governance/metrics-reporting/SKILL.md", "ref": "metrics inputs"},
                {"source": "local://governance/metrics-reporting/SKILL.md", "ref": "KPI definitions and targets"}]
    return {"agent_slug": SLUG, "intent_type": "report", "action": action,
            "rationale": ("Each KPI computed from the supplied metric and compared to its SKILL.md target; breaches of critical KPIs (open criticals, approval completion, "
                          "evidence-chain integrity) drive critical severity. Breaches are translated to business language for the decisions-needed section. Read-only."),
            "confidence": round(min(0.9, 0.5 + 0.05 * len(results)), 2), "severity": severity, "key_findings": key, "evidence_references": evidence,
            "next_agents": ["security-posture-score"] + (["ciso-brief-generator"] if crit_breach else []), "human_approval_required": False, "timestamp_utc": _now(),
            "kpis": results, "decisions_needed": decisions, "regulatory_relevance": "Assess GDPR/PCI/HIPAA obligations if a breach KPI reflects a reportable incident.",
            "mitre_ttps": [], "affected_assets": [], "_exit": exit_code}


def main() -> int:
    ap = argparse.ArgumentParser(description="USAP metrics-reporting")
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
    print(json.dumps(p, indent=2) if args.output == "json" else f"metrics-reporting: severity={p['severity']}")
    return code


if __name__ == "__main__":
    raise SystemExit(main())
