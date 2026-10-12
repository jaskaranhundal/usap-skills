#!/usr/bin/env python3
"""detection-engineering_tool.py

Reviews detection coverage and rule fidelity per the SKILL.md: required
techniques versus production rules (coverage gaps), the Detection Fidelity
Matrix (precision x recall -> deploy / document gaps / tune / redesign), the
Telemetry Requirements Matrix, and rule designs from the SKILL.md templates
for the gaps they cover. Production deployment is a mutating recommendation
that requires approval; this tool deploys nothing. Emits the USAP 11-field
payload.

  python3 detection-engineering_tool.py --input coverage.json --output json
  python3 detection-engineering_tool.py --output json     # no input: informational, exit 0

Input (see tests/fixtures/detection-engineering-input.json): review_id,
techniques_required[]: {technique, priority}, telemetry_available[],
existing_rules[]: {rule_id, title, technique, format, precision, recall,
fp_rate_7d, status (draft|testing|production), telemetry[]}

Exit codes: 0 no gaps above medium; 1 high-priority gap or a rule to redesign;
2 critical-priority technique with no production coverage. Stdlib only.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

SLUG = "detection-engineering"
HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parents[2]
SEV_RANK = {"critical": 4, "high": 3, "medium": 2, "low": 1, "informational": 0}
FIDELITY_HIGH = 0.80
FP_SLA = 0.05

# SKILL.md Detection Templates
TEMPLATES = {
    "T1098.001": {"title": "IAM User Created Then Given Admin Policy", "format": "sigma", "telemetry": ["CloudTrail"],
                  "logic": "eventName=CreateUser followed by eventName=AttachUserPolicy with policyArn contains AdministratorAccess within 5m by the same actor", "level": "critical",
                  "precision": 0.9, "recall": 0.8},
    "T1562.008": {"title": "CloudTrail Logging Stopped", "format": "sigma", "telemetry": ["CloudTrail"],
                  "logic": "eventName in (StopLogging, DeleteTrail); false positives: authorised infrastructure changes (verify with change management)", "level": "critical",
                  "precision": 0.85, "recall": 0.95},
    "T1110": {"title": "Multiple Failed Logins Followed by Success", "format": "sigma", "telemetry": ["Windows Security Log", "SIEM"],
              "logic": "EventID 4625 count > 5 in 5m followed by EventID 4624 for the same account within 10m", "level": "high",
              "precision": 0.75, "recall": 0.85},
    "T1059.001": {"title": "Encoded PowerShell Spawned by WMI or Office", "format": "sigma", "telemetry": ["EDR"],
                  "logic": "process powershell.exe with -enc/-EncodedCommand where parent in (wmiprvse.exe, winword.exe, excel.exe)", "level": "high",
                  "precision": 0.8, "recall": 0.7},
}
# Telemetry Requirements Matrix (target keyword -> required telemetry)
TELEMETRY_FOR = {"process": ["EDR"], "network": ["NetFlow", "DNS"], "auth": ["Windows Security Log", "CloudTrail", "SIEM"], "cloud": ["CloudTrail", "SIEM"], "memory": ["EDR"]}


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _fidelity(p: Optional[float], r: Optional[float]) -> Dict[str, str]:
    if p is None or r is None:
        return {"assessment": "unmeasured", "action": "Measure precision and recall against a clean baseline and an attack replay before production"}
    hp, hr = p >= FIDELITY_HIGH, r >= FIDELITY_HIGH
    if hp and hr:
        return {"assessment": "excellent", "action": "Deploy immediately (approval required for production)"}
    if hp and not hr:
        return {"assessment": "partial coverage", "action": "Deploy, document the recall gap"}
    if not hp and hr:
        return {"assessment": "noisy but complete", "action": "Tune precision first"}
    return {"assessment": "useless", "action": "Redesign"}


def analyse(target: dict, input_path: Optional[str] = None) -> Dict[str, Any]:
    required = [t for t in (target.get("techniques_required") or []) if isinstance(t, dict) and t.get("technique")]
    rules = [r for r in (target.get("existing_rules") or []) if isinstance(r, dict)]
    telemetry = {str(t) for t in (target.get("telemetry_available") or [])}
    if not required and not rules:
        return {"agent_slug": SLUG, "intent_type": "analyze", "action": "Supply required techniques and existing rules to review; nothing was provided.",
                "rationale": "No coverage request supplied. Absence of input, never a clean result.", "confidence": 0.30, "severity": "informational",
                "key_findings": ["No detection review content supplied"],
                "evidence_references": [{"source": "local://detection/detection-engineering/SKILL.md", "ref": "fidelity matrix (not applied: no input)"}],
                "next_agents": [], "human_approval_required": False, "timestamp_utc": _now(), "detection_rules_designed": [], "coverage_gaps": []}

    prod_by_tech: Dict[str, List[dict]] = {}
    for r in rules:
        prod_by_tech.setdefault(str(r.get("technique")), []).append(r)

    reviews: List[dict] = []
    tuning: List[str] = []
    for r in rules:
        f = _fidelity(r.get("precision"), r.get("recall"))
        fp = r.get("fp_rate_7d")
        note = f"{r.get('rule_id')} ({r.get('technique')}, {r.get('status')}): {f['assessment']} -> {f['action']}"
        if fp is not None and float(fp) > FP_SLA:
            tuning.append(f"{r.get('rule_id')}: false-positive rate {float(fp):.0%} over 7 days exceeds the 5% SLA; add exclusions for documented automation and re-baseline")
        missing_tel = [t for t in (r.get("telemetry") or []) if t not in telemetry]
        if missing_tel:
            tuning.append(f"{r.get('rule_id')}: required telemetry not available: {', '.join(missing_tel)}; rule cannot fire")
        reviews.append({"rule_id": r.get("rule_id"), "technique": r.get("technique"), "status": r.get("status"), "precision": r.get("precision"), "recall": r.get("recall"),
                        "fp_rate_7d": fp, "fidelity": f["assessment"], "recommended_action": f["action"], "missing_telemetry": missing_tel, "note": note})

    gaps: List[dict] = []
    designed: List[dict] = []
    for t in required:
        tech = str(t["technique"]); prio = str(t.get("priority", "medium")).lower()
        prod = [r for r in prod_by_tech.get(tech, []) if str(r.get("status")) == "production" and not [x for x in (r.get("telemetry") or []) if x not in telemetry]]
        if prod:
            continue
        reason = "no rule" if not prod_by_tech.get(tech) else "rules exist but none in production with available telemetry"
        gaps.append({"technique": tech, "gap_description": f"{reason} for {tech}", "priority": prio})
        tpl = TEMPLATES.get(tech)
        if tpl:
            missing = [x for x in tpl["telemetry"] if x not in telemetry]
            designed.append({"rule_id": f"DE-{tech.replace('.', '-')}", "title": tpl["title"], "technique": tech, "format": tpl["format"], "logic": tpl["logic"],
                             "precision_estimate": tpl["precision"], "recall_estimate": tpl["recall"], "telemetry_required": tpl["telemetry"],
                             "telemetry_missing": missing, "deployment_status": "draft" if missing else "testing",
                             "requires_approval": True, "note": "production deployment is a mutating change (device_config_change); approval by soc_lead"})
    crit_gap = any(g["priority"] == "critical" for g in gaps)
    high_gap = any(g["priority"] == "high" for g in gaps)
    redesign = any(r["fidelity"] == "useless" for r in reviews)
    severity = "critical" if crit_gap else "high" if high_gap or redesign else "medium" if gaps or tuning else "low" if reviews else "informational"

    parts = []
    if designed:
        parts.append(f"{len(designed)} rule(s) designed from the SKILL.md templates for uncovered techniques; validate against a clean baseline and an attack replay, then request approval to deploy")
    if gaps and len(gaps) > len(designed):
        parts.append(f"{len(gaps) - len(designed)} gap(s) need a new design (no template): " + ", ".join(g["technique"] for g in gaps if g["technique"] not in TEMPLATES))
    if tuning:
        parts.append(f"{len(tuning)} tuning item(s)")
    action = ("; ".join(parts) + ".") if parts else "Coverage and fidelity meet the SKILL.md bar; no action."

    key = [f"{target.get('review_id', 'review')}: {len(required)} technique(s) required, {len(rules)} rule(s) reviewed, {len(gaps)} coverage gap(s) "
           f"({sum(1 for g in gaps if g['priority'] == 'critical')} critical), {len(designed)} designed, {len(tuning)} tuning item(s)"]
    key += [f"GAP {g['priority']}: {g['gap_description']}" + (f" -> template '{TEMPLATES[g['technique']]['title']}'" if g["technique"] in TEMPLATES else "") for g in gaps]
    key += [r["note"] for r in reviews[:5]]
    key += tuning[:4]

    rel = None
    if input_path:
        try:
            rel = Path(input_path).resolve().relative_to(REPO_ROOT).as_posix()
        except ValueError:
            rel = None
    evidence = [{"source": f"local://{rel}" if rel else "local://detection/detection-engineering/SKILL.md", "ref": target.get("review_id", "review"), "quote": f"{len(rules)} rules, {len(required)} required techniques"}]
    evidence += [{"source": f"https://attack.mitre.org/techniques/{g['technique'].replace('.', '/')}/", "ref": g["technique"]} for g in gaps[:4]]
    evidence.append({"source": "local://detection/detection-engineering/SKILL.md", "ref": "detection templates, fidelity matrix, telemetry requirements"})

    conf, factors = 0.60, ["base 0.60"]
    if telemetry:
        conf += 0.12; factors.append("telemetry inventory supplied (+0.12)")
    if rules and all(r.get("precision") is not None and r.get("recall") is not None for r in rules):
        conf += 0.15; factors.append("precision and recall measured on every rule (+0.15)")
    elif rules:
        conf += 0.05; factors.append("some rules unmeasured (+0.05)")
    conf = round(min(conf, 0.92), 2)

    next_agents = []
    if any(d["telemetry_missing"] for d in designed) or any(r["missing_telemetry"] for r in reviews):
        next_agents.append("telemetry-signal-quality")
    if gaps:
        next_agents.append("threat-hunting")
    return {
        "agent_slug": SLUG, "intent_type": "analyze", "action": action,
        "rationale": (f"A technique is covered only by a production rule whose telemetry is available. Fidelity per the matrix: precision and recall at or above {FIDELITY_HIGH:.0%} "
                      f"is excellent; low precision tunes first; low both redesigns. False-positive SLA {FP_SLA:.0%} over the first week. Designs come from the SKILL.md "
                      f"templates and start in draft or testing; production deployment is mutating and needs approval. Confidence factors: {', '.join(factors)}."),
        "confidence": conf, "severity": severity, "key_findings": key, "evidence_references": evidence,
        "next_agents": next_agents, "human_approval_required": bool(designed) or any(r["recommended_action"].startswith("Deploy") for r in reviews),
        "timestamp_utc": _now(), "detection_rules_designed": designed, "rule_reviews": reviews, "coverage_gaps": gaps, "tuning_recommendations": tuning,
        "mitre_ttps": sorted({g["technique"] for g in gaps} | {str(r.get("technique")) for r in rules if r.get("technique")}), "affected_assets": [],
    }


def _exit(p: dict) -> int:
    return {"critical": 2, "high": 1}.get(p["severity"], 0)


def main() -> int:
    ap = argparse.ArgumentParser(description="USAP detection-engineering: coverage and fidelity review")
    ap.add_argument("--input"); ap.add_argument("--output", choices=["json", "text"], default="text")
    args = ap.parse_args()
    if args.input:
        try:
            target = json.loads(Path(args.input).read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            print(f"error: cannot read --input: {exc}", file=sys.stderr); return 2
    else:
        raw = "" if sys.stdin.isatty() else sys.stdin.read()
        try:
            target = json.loads(raw) if raw.strip() else {}
        except json.JSONDecodeError:
            target = {}
    p = analyse(target, args.input)
    if args.output == "json":
        print(json.dumps(p, indent=2))
    else:
        print(f"detection-engineering: severity={p['severity']} gaps={len(p.get('coverage_gaps', []))}")
        for f in p["key_findings"]:
            print(f"  - {f}")
    return _exit(p)


if __name__ == "__main__":
    raise SystemExit(main())
