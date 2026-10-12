#!/usr/bin/env python3
"""supply-chain-simulation_tool.py

Analyses a supply-chain attack simulation per the SKILL.md detection-point table:
computes detection coverage, flags undetected points with their MITRE technique,
and rates mean time to detect. Read-only analysis of simulation results. Emits
the USAP 11-field payload.

  python3 supply-chain-simulation_tool.py --input sim.json --output json
  python3 supply-chain-simulation_tool.py --output json    # no input: informational, exit 0

Input (see tests/fixtures/supply-chain-simulation-input.json):
{scenario, detection_points[] {point, detected, time_to_detect_min}}.

Exit codes: 0 full coverage; 1 partial gaps; 2 a critical detection point missed
(build intrusion, malicious artifact, or no SIEM alert). Stdlib only.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

SLUG = "supply-chain-simulation"
HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parents[2]
# point key -> (label, MITRE, critical-if-missed)
POINTS = {
    "build_system_intrusion": ("Build system intrusion", "T0802/T0806", True),
    "malicious_artifact_registry": ("Malicious artifact in registry", "T1195.001", True),
    "anomalous_dependency_binary": ("Anomalous binary in dependency", "T1195.002", False),
    "unexpected_network_connection": ("Unexpected network connection", "T1041", False),
    "siem_alert_fired": ("SIEM alert fired", "detection-quality", True),
}
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
    raw = [p for p in (t.get("detection_points") or []) if isinstance(p, dict)]
    if not t or not raw:
        return {"agent_slug": SLUG, "intent_type": "analyze", "action": "Supply simulation detection points; nothing was provided.",
                "rationale": "No simulation supplied.", "confidence": 0.30, "severity": "informational", "key_findings": ["No simulation supplied"],
                "evidence_references": [{"source": "local://appsec-devsecops/supply-chain-simulation/SKILL.md", "ref": "detection-point table (not applied)"}],
                "next_agents": [], "human_approval_required": False, "timestamp_utc": _now(), "gaps": [], "_exit": 0}
    total = len(raw)
    detected = 0
    gaps: List[dict] = []
    times: List[float] = []
    for p in raw:
        key = str(p.get("point", "")).lower()
        label, mitre, crit = POINTS.get(key, (p.get("point", key), "n/a", False))
        is_det = bool(p.get("detected"))
        if is_det:
            detected += 1
            try:
                times.append(float(p.get("time_to_detect_min")))
            except (TypeError, ValueError):
                pass
        else:
            gaps.append({"point": label, "mitre": mitre, "critical": crit, "severity": "critical" if crit else "high"})
    coverage = round(100.0 * detected / total, 1)
    gaps.sort(key=lambda g: -SEV_RANK[g["severity"]])
    crit_gaps = [g for g in gaps if g["critical"]]
    severity = "critical" if crit_gaps else "high" if gaps else "low"
    exit_code = 2 if crit_gaps else 1 if gaps else 0
    mttd = round(sum(times) / len(times), 1) if times else None
    scenario = t.get("scenario", "the scenario")
    action = (f"{len(crit_gaps)} critical detection point(s) missed in {scenario}: " + "; ".join(g["point"] for g in crit_gaps)[:150] + ". Build detections before closing the exercise." if crit_gaps else
              f"{len(gaps)} detection gap(s) in {scenario}; add coverage." if gaps else
              f"Full detection coverage in {scenario}.")
    key = [f"{scenario}: coverage {coverage}% ({detected}/{total}); {len(gaps)} gap(s) ({len(crit_gaps)} critical); MTTD {mttd if mttd is not None else 'n/a'} min"]
    key += [f"{g['severity']} MISSED {g['point']} [{g['mitre']}]" for g in gaps[:6]]
    evidence = [{"source": f"local://{rel}" if rel else "local://appsec-devsecops/supply-chain-simulation/SKILL.md", "ref": "simulation detection points"},
                {"source": "local://appsec-devsecops/supply-chain-simulation/SKILL.md", "ref": "detection-point and MITRE table"}]
    return {"agent_slug": SLUG, "intent_type": "analyze", "action": action,
            "rationale": ("Detection coverage is the share of simulated attack points the defenders caught; a missed build-system intrusion, malicious artifact in the registry, or a SIEM "
                          "that never alerted is a critical gap because it means the whole scenario would have gone unseen. Read-only analysis of a simulation run in an isolated environment."),
            "confidence": 0.85, "severity": severity, "key_findings": key, "evidence_references": evidence,
            "next_agents": ["detection-engineering"] if gaps else [], "human_approval_required": False, "timestamp_utc": _now(),
            "coverage_percent": coverage, "mttd_min": mttd, "gaps": gaps, "mitre_ttps": sorted({g["mitre"] for g in gaps if g["mitre"] != "n/a"}), "affected_assets": [], "_exit": exit_code}


def main() -> int:
    ap = argparse.ArgumentParser(description="USAP supply-chain-simulation")
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
    print(json.dumps(p, indent=2) if args.output == "json" else f"supply-chain-simulation: severity={p['severity']}")
    return code


if __name__ == "__main__":
    raise SystemExit(main())
