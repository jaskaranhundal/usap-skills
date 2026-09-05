#!/usr/bin/env python3
"""cyber-insurance_tool.py

Assesses cyber-insurance coverage adequacy against the SKILL.md coverage tables:
flags missing coverages and dangerous exclusions/sublimits. Read-only advisory.
Emits the USAP 11-field payload.

  python3 cyber-insurance_tool.py --input policy.json --output json
  python3 cyber-insurance_tool.py --output json    # no input: informational, exit 0

Input (see tests/fixtures/cyber-insurance-input.json):
{policy, coverages{business_interruption, extra_expense, ransomware,
data_recovery, cyber_crime, crisis_management, regulatory_defense,
privacy_liability, network_security, media_liability} (booleans),
exclusions{gdpr_fines, unencrypted_data, nation_state} (booleans),
sublimits{social_engineering, ransomware} (numbers, optional)}.

Exit codes: 0 adequate; 1 gaps; 2 a critical gap (no ransomware or no privacy
liability, or unencrypted-data exclusion). Stdlib only.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

SLUG = "cyber-insurance"
HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parents[2]
# coverage key -> (severity if missing, label)
COVERAGE = {
    "ransomware": ("critical", "Cyber extortion / ransomware"),
    "privacy_liability": ("critical", "Privacy liability (customer breach claims)"),
    "business_interruption": ("high", "Business interruption"),
    "network_security": ("high", "Network security liability"),
    "regulatory_defense": ("high", "Regulatory defense and fines"),
    "cyber_crime": ("high", "Cyber crime (funds transfer / social engineering)"),
    "data_recovery": ("medium", "Data recovery"),
    "crisis_management": ("medium", "Crisis management (PR, notification)"),
    "extra_expense": ("medium", "Extra expense"),
    "media_liability": ("low", "Media liability"),
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
    cov = t.get("coverages")
    if not t or cov is None:
        return {"agent_slug": SLUG, "intent_type": "advise", "action": "Supply a policy descriptor; nothing was provided.",
                "rationale": "No policy supplied.", "confidence": 0.30, "severity": "informational", "key_findings": ["No policy supplied"],
                "evidence_references": [{"source": "local://risk-compliance/cyber-insurance/SKILL.md", "ref": "coverage tables (not applied)"}],
                "next_agents": [], "human_approval_required": False, "timestamp_utc": _now(), "gaps": [], "_exit": 0}
    cov = cov or {}
    excl = t.get("exclusions") or {}
    subl = t.get("sublimits") or {}
    gaps: List[dict] = []
    for key, (sev, label) in COVERAGE.items():
        if not cov.get(key):
            gaps.append({"item": key, "type": "missing_coverage", "severity": sev, "note": f"no coverage: {label}"})
    if excl.get("unencrypted_data"):
        gaps.append({"item": "unencrypted_data_exclusion", "type": "exclusion", "severity": "critical", "note": "privacy liability excludes unencrypted data — a common denial trigger"})
    if excl.get("gdpr_fines"):
        gaps.append({"item": "gdpr_fines_exclusion", "type": "exclusion", "severity": "high", "note": "regulatory fines (GDPR/CCPA) excluded"})
    if excl.get("nation_state"):
        gaps.append({"item": "war_exclusion", "type": "exclusion", "severity": "high", "note": "nation-state / war exclusion on network security liability"})
    try:
        if subl.get("social_engineering") is not None and float(subl["social_engineering"]) < 250000:
            gaps.append({"item": "social_engineering_sublimit", "type": "sublimit", "severity": "high", "note": f"social-engineering sublimit is low (${subl['social_engineering']:,.0f})"})
    except (TypeError, ValueError):
        pass
    gaps.sort(key=lambda g: -SEV_RANK[g["severity"]])
    crit = [g for g in gaps if g["severity"] == "critical"]
    severity = gaps[0]["severity"] if gaps else "informational"
    exit_code = 2 if crit else 1 if gaps else 0
    policy = t.get("policy", "the policy")
    action = (f"{policy}: {len(crit)} critical coverage gap(s) — " + "; ".join(g["note"] for g in crit[:2])[:180] + ". Address before renewal." if crit else
              f"{policy}: {len(gaps)} coverage gap(s) to raise at renewal." if gaps else
              f"{policy}: coverage adequate against the reference tables.")
    key = [f"{policy}: {len(gaps)} gap(s) ({len(crit)} critical)"]
    key += [f"{g['severity']} {g['note']}" for g in gaps[:6]]
    evidence = [{"source": f"local://{rel}" if rel else "local://risk-compliance/cyber-insurance/SKILL.md", "ref": "policy descriptor"},
                {"source": "local://risk-compliance/cyber-insurance/SKILL.md", "ref": "first-party and third-party coverage tables"}]
    return {"agent_slug": SLUG, "intent_type": "advise", "action": action,
            "rationale": ("Each coverage is checked against the SKILL.md tables; missing ransomware or privacy liability is critical, and an unencrypted-data exclusion is critical because it "
                          "voids the privacy cover when it is most needed. Sublimits and war/nation-state exclusions are flagged as the common claim-denial triggers. Read-only advisory."),
            "confidence": 0.85, "severity": severity, "key_findings": key, "evidence_references": evidence,
            "next_agents": ["enterprise-risk-assessment"] if crit else [], "human_approval_required": False, "timestamp_utc": _now(),
            "gaps": gaps, "mitre_ttps": [], "affected_assets": [str(policy)], "_exit": exit_code}


def main() -> int:
    ap = argparse.ArgumentParser(description="USAP cyber-insurance")
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
    print(json.dumps(p, indent=2) if args.output == "json" else f"cyber-insurance: severity={p['severity']}")
    return code


if __name__ == "__main__":
    raise SystemExit(main())
