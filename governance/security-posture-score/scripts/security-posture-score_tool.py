#!/usr/bin/env python3
"""security-posture-score_tool.py

Computes the 0-100 composite posture score per the SKILL.md scoring
methodology: per-domain (controls passing / total * 100 * maturity multiplier),
weighted composite, rating band, and trend versus the prior period. Read-only.
Emits the USAP 11-field payload.

  python3 security-posture-score_tool.py --input posture.json --output json
  python3 security-posture-score_tool.py --output json     # no input: informational, exit 0

Input (see tests/fixtures/security-posture-score-input.json): period,
prior_composite, domains[]: {name, controls_passing, controls_total,
maturity (ad_hoc|defined|managed|optimized)}.

Exit codes: 0 Good or better (>=75); 1 Fair (60-74); 2 Poor/Critical (<60).
Stdlib only.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

SLUG = "security-posture-score"
HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parents[2]
WEIGHTS = {"detection": 0.20, "response": 0.20, "cloud_infra": 0.15, "appsec_devsecops": 0.15,
           "identity_access": 0.10, "risk_compliance": 0.10, "governance": 0.10}
MATURITY = {"ad_hoc": 0.6, "defined": 0.75, "managed": 0.9, "optimized": 1.0}


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _rating(score: float) -> str:
    return ("excellent" if score >= 90 else "good" if score >= 75 else "fair" if score >= 60 else "poor" if score >= 40 else "critical")


def analyse(t: dict, input_path: Optional[str] = None) -> Dict[str, Any]:
    rel = None
    if input_path:
        try:
            rel = Path(input_path).resolve().relative_to(REPO_ROOT).as_posix()
        except ValueError:
            rel = None
    domains = [d for d in (t.get("domains") or []) if isinstance(d, dict)]
    if not t or not domains:
        return {"agent_slug": SLUG, "intent_type": "report", "action": "Supply domain control data; nothing was provided.",
                "rationale": "No domains supplied; no score computed.", "confidence": 0.30, "severity": "informational",
                "key_findings": ["No domain data supplied"], "evidence_references": [{"source": "local://governance/security-posture-score/SKILL.md", "ref": "scoring methodology (not applied)"}],
                "next_agents": [], "human_approval_required": False, "timestamp_utc": _now(), "scorecard": {}, "_exit": 0}
    scored: List[dict] = []
    composite = 0.0
    weight_sum = 0.0
    for d in domains:
        name = str(d.get("name", "?")).lower().replace(" ", "_").replace("&", "").replace("/", "_")
        total = int(d.get("controls_total") or 0)
        passing = int(d.get("controls_passing") or 0)
        mult = MATURITY.get(str(d.get("maturity", "defined")).lower(), 0.75)
        ds = round((passing / total * 100 * mult) if total else 0.0, 1)
        w = WEIGHTS.get(name, 0.0)
        composite += ds * w
        weight_sum += w
        scored.append({"domain": d.get("name"), "score": ds, "weight": w, "controls": f"{passing}/{total}", "maturity": d.get("maturity")})
    composite = round(composite / weight_sum, 1) if weight_sum else round(sum(s["score"] for s in scored) / len(scored), 1)
    rating = _rating(composite)
    prior = t.get("prior_composite")
    if prior is None:
        trend = "no prior period"
        delta = None
    else:
        delta = round(composite - float(prior), 1)
        trend = "rising" if delta > 0 else "falling" if delta < 0 else "flat"
    scored.sort(key=lambda s: s["score"])
    weak = [s for s in scored if s["score"] < 60]
    severity = "low" if composite >= 75 else "medium" if composite >= 60 else "high" if composite >= 40 else "critical"
    exit_code = 0 if composite >= 75 else 1 if composite >= 60 else 2

    action = (f"Composite {composite}/100 ({rating}), {trend}" + (f" {delta:+}" if delta is not None else "") +
              (f". Prioritise remediation in {', '.join(s['domain'] for s in weak[:3])} (below 60)." if weak else ". No domain below 60."))
    key = [f"Composite posture {composite}/100 — {rating}; trend {trend}" + (f" ({delta:+} vs {prior})" if delta is not None else "")]
    key += [f"{s['domain']}: {s['score']}/100 (controls {s['controls']}, {s['maturity']}, weight {int(s['weight']*100)}%)" for s in scored]
    if abs(delta or 0) >= 10:
        key.append(f"Anomalous {abs(delta)}-point swing this period — root-cause explanation required in the brief")

    evidence = [{"source": f"local://{rel}" if rel else "local://governance/security-posture-score/SKILL.md", "ref": "domain control data"},
                {"source": "local://governance/security-posture-score/SKILL.md", "ref": "domain weights, maturity multipliers, score bands"}]
    return {"agent_slug": SLUG, "intent_type": "report", "action": action,
            "rationale": ("Each domain scored as controls-passing/total * 100 * maturity multiplier (ad_hoc 0.6 .. optimized 1.0), composite as the weighted sum of the SKILL.md "
                          "domain weights, rating from the score bands, trend against the prior composite. A swing of 10 points or more is flagged as anomalous. Read-only."),
            "confidence": 0.88, "severity": severity, "key_findings": key, "evidence_references": evidence,
            "next_agents": ["ciso-brief-generator", "metrics-reporting"], "human_approval_required": False, "timestamp_utc": _now(),
            "scorecard": {"composite": composite, "rating": rating, "trend": trend, "delta": delta, "domains": scored, "weak_domains": [s["domain"] for s in weak]},
            "mitre_ttps": [], "affected_assets": [], "_exit": exit_code}


def main() -> int:
    ap = argparse.ArgumentParser(description="USAP security-posture-score")
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
    print(json.dumps(p, indent=2) if args.output == "json" else f"security-posture-score: {p['scorecard'].get('composite')}/100 {p['severity']}")
    return code


if __name__ == "__main__":
    raise SystemExit(main())
