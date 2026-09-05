#!/usr/bin/env python3
"""behavioral-analytics_tool.py

UEBA over supplied entity baselines and current activity per the SKILL.md
anomaly categories: time (z-score), volume (mean + 3*std or > 5x p95), peer-group
deviation, and new-behavior signals with their weights. Emits the USAP 11-field
payload. Read-only detection.

  python3 behavioral-analytics_tool.py --input ueba.json --output json
  python3 behavioral-analytics_tool.py --output json    # no input: informational, exit 0

Input (see tests/fixtures/behavioral-analytics-input.json): entities[]:
  entity, baseline{active_hours_mean, active_hours_std, volume_mean_mb,
  volume_std_mb, volume_p95_mb, observation_days}, current{active_hour,
  volume_mb}, new_behaviors[] (labels from the SKILL.md weight table),
  peer_deviation_sigmas (number of dimensions > 2 sigma).

Exit codes: 0 no anomaly above low; 1 medium/high anomalies; 2 critical
(cold-start entity flagged or composite critical). Stdlib only.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

SLUG = "behavioral-analytics"
HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parents[2]
NEW_BEHAVIOR_WEIGHT = {
    "new_system": 1, "new_application": 1, "privileged_command": 2, "new_country": 3,
    "after_hours": 1, "personal_cloud_storage": 2, "hr_or_finance_out_of_role": 4,
}
MIN_BASELINE_DAYS = 30
SEV_RANK = {"critical": 4, "high": 3, "medium": 2, "low": 1, "informational": 0}


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _score_entity(e: dict) -> dict:
    ent = e.get("entity", "?")
    b = e.get("baseline") or {}
    cur = e.get("current") or {}
    anomalies: List[str] = []
    cold = int(b.get("observation_days") or 0) < MIN_BASELINE_DAYS
    # Time anomaly
    if cur.get("active_hour") is not None and b.get("active_hours_std"):
        z = abs(float(cur["active_hour"]) - float(b.get("active_hours_mean", 0))) / max(float(b["active_hours_std"]), 0.5)
        if z >= 3:
            anomalies.append(f"time anomaly (z={z:.1f})")
    # Volume anomaly
    if cur.get("volume_mb") is not None:
        v = float(cur["volume_mb"]); mean = float(b.get("volume_mean_mb", 0)); std = float(b.get("volume_std_mb", 0)); p95 = float(b.get("volume_p95_mb", 0))
        if (std and v > mean + 3 * std) or (p95 and v > 5 * p95):
            anomalies.append(f"volume anomaly ({v}MB vs mean {mean}MB)")
    # Peer group
    if int(e.get("peer_deviation_sigmas") or 0) >= 2:
        anomalies.append(f"peer-group deviation on {e.get('peer_deviation_sigmas')} dimensions (>2 sigma)")
    # New behavior weighted score
    nb = [str(x) for x in (e.get("new_behaviors") or [])]
    nb_score = sum(NEW_BEHAVIOR_WEIGHT.get(x, 1) for x in nb)
    if nb:
        anomalies.append(f"new behavior: {', '.join(nb)} (weight {nb_score})")
    composite = len([a for a in anomalies if "new behavior" not in a]) * 2 + nb_score
    if any("hr_or_finance_out_of_role" in nb for _ in [0]) or composite >= 6 or (cold and anomalies):
        sev = "critical" if composite >= 6 or "hr_or_finance_out_of_role" in nb else "high"
    elif composite >= 3:
        sev = "high"
    elif composite >= 1 or anomalies:
        sev = "medium"
    else:
        sev = "informational"
    return {"entity": ent, "anomalies": anomalies, "new_behavior_score": nb_score, "composite": composite,
            "cold_start": cold, "severity": sev}


def analyse(t: dict, input_path: Optional[str] = None) -> Dict[str, Any]:
    rel = None
    if input_path:
        try:
            rel = Path(input_path).resolve().relative_to(REPO_ROOT).as_posix()
        except ValueError:
            rel = None
    entities = [e for e in (t.get("entities") or []) if isinstance(e, dict)]
    if not t or not entities:
        return {"agent_slug": SLUG, "intent_type": "detect", "action": "Supply entity baselines and current activity; nothing was provided.",
                "rationale": "No entities supplied; no anomaly detection.", "confidence": 0.30, "severity": "informational",
                "key_findings": ["No entities supplied"], "evidence_references": [{"source": "local://detection/behavioral-analytics/SKILL.md", "ref": "anomaly categories (not applied)"}],
                "next_agents": [], "human_approval_required": False, "timestamp_utc": _now(), "entities": [], "_exit": 0}
    scored = sorted((_score_entity(e) for e in entities), key=lambda r: -SEV_RANK[r["severity"]])
    flagged = [r for r in scored if r["severity"] != "informational"]
    severity = scored[0]["severity"] if scored else "informational"
    exit_code = 2 if severity == "critical" else 1 if severity in ("high", "medium") else 0
    cold = [r["entity"] for r in scored if r["cold_start"] and r["anomalies"]]
    action = (f"{len(flagged)} entity/entities with behavioral anomalies; investigate {scored[0]['entity']} first ({scored[0]['severity']})."
              if flagged else "No entity deviates from its baseline beyond threshold.")
    if cold:
        action += f" Baselines under 30 days for {', '.join(cold)}: treat verdicts as low-confidence."
    key = [f"{len(entities)} entity/entities analysed, {len(flagged)} anomalous; top {scored[0]['entity']} ({scored[0]['severity']}, composite {scored[0]['composite']})"]
    key += [f"{r['severity']} {r['entity']}: {'; '.join(r['anomalies']) or 'within baseline'}" + (" [cold start <30d]" if r['cold_start'] else "") for r in scored[:6]]
    evidence = [{"source": f"local://{rel}" if rel else "local://detection/behavioral-analytics/SKILL.md", "ref": "entity baselines and current activity"},
                {"source": "local://detection/behavioral-analytics/SKILL.md", "ref": "anomaly categories and new-behavior weights"}]
    return {"agent_slug": SLUG, "intent_type": "detect", "action": action,
            "rationale": ("Each entity scored against the SKILL.md anomaly categories: time by z-score >= 3, volume by mean+3sigma or >5x p95, peer-group by >2 sigma on two or more "
                          "dimensions, and weighted new-behavior signals (HR/finance out of role is the heaviest). A baseline under 30 days is cold-start and caps confidence. Read-only."),
            "confidence": 0.6 if cold else 0.85, "severity": severity, "key_findings": key, "evidence_references": evidence,
            "next_agents": ["threat-hunting"] if severity in ("critical", "high") else [], "human_approval_required": False, "timestamp_utc": _now(),
            "entities": scored, "mitre_ttps": ["T1078"] + (["T1110"] if any("volume" in a for r in scored for a in r["anomalies"]) else []),
            "affected_assets": [r["entity"] for r in flagged], "_exit": exit_code}


def main() -> int:
    ap = argparse.ArgumentParser(description="USAP behavioral-analytics")
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
    print(json.dumps(p, indent=2) if args.output == "json" else f"behavioral-analytics: severity={p['severity']}")
    return code


if __name__ == "__main__":
    raise SystemExit(main())
