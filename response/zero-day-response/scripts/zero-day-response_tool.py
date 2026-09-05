#!/usr/bin/env python3
"""zero-day-response_tool.py

Classifies a reported vulnerability per the SKILL.md zero-day matrix
(patch-available x exploited-in-wild x org-uses-it) and recommends compensating
controls as intent blocks, each with an expiry trigger. Controls are gated;
this tool advises. Emits the USAP 11-field payload.

  python3 zero-day-response_tool.py --input vuln.json --output json
  python3 zero-day-response_tool.py --output json    # no input: informational, exit 0

Input (see tests/fixtures/zero-day-response-input.json): cve_id, product,
patch_available, exploited_in_wild, org_uses, internet_facing, affected_assets[],
available_controls[] (waf|segmentation|ids_signature|feature_disable|
enhanced_monitoring).

Exit codes: 0 not applicable / n-day; 1 org uses it, no active exploitation;
2 true zero-day in use. Stdlib only.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

SLUG = "zero-day-response"
HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parents[2]
CONTROL_ORDER = ["waf", "segmentation", "ids_signature", "feature_disable", "enhanced_monitoring"]
CONTROL_TEXT = {"waf": "Deploy a virtual-patch WAF rule for the exploit pattern",
                "segmentation": "Restrict network reachability to the affected service",
                "ids_signature": "Add an IDS/IPS signature for the exploit",
                "feature_disable": "Disable the affected feature or module",
                "enhanced_monitoring": "Raise logging and alerting around the affected asset"}


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def analyse(t: dict, input_path: Optional[str] = None) -> Dict[str, Any]:
    rel = None
    if input_path:
        try:
            rel = Path(input_path).resolve().relative_to(REPO_ROOT).as_posix()
        except ValueError:
            rel = None
    if not t or not t.get("cve_id") and not t.get("product"):
        return {"agent_slug": SLUG, "intent_type": "advise", "action": "Supply a vulnerability descriptor; nothing was provided.",
                "rationale": "No vulnerability supplied.", "confidence": 0.30, "severity": "informational", "key_findings": ["No vulnerability supplied"],
                "evidence_references": [{"source": "local://response/zero-day-response/SKILL.md", "ref": "zero-day classification (not applied)"}],
                "next_agents": [], "human_approval_required": False, "timestamp_utc": _now(), "controls": [], "_exit": 0}
    patch = bool(t.get("patch_available")); wild = bool(t.get("exploited_in_wild")); uses = bool(t.get("org_uses"))
    internet = bool(t.get("internet_facing"))
    if not uses:
        classification, severity, exit_code = "not_applicable", "informational", 0
    elif not patch and wild:
        classification, severity, exit_code = "true_zero_day", "critical", 2
    elif not patch and not wild:
        classification, severity, exit_code = "n_day_pre_patch", "high" if internet else "medium", 1
    else:  # patch available
        classification, severity, exit_code = "critical_patch", "high" if wild else "medium", 1

    avail = [c for c in (t.get("available_controls") or []) if c in CONTROL_TEXT] or CONTROL_ORDER
    chosen = [c for c in CONTROL_ORDER if c in avail]
    expiry = (datetime.now(timezone.utc) + timedelta(days=30)).strftime("%Y-%m-%d")
    controls = [] if classification in ("not_applicable", "critical_patch") else [
        {"containment_intent": CONTROL_TEXT[c], "intent_type": "mutating", "mutating_category": "device_config_change",
         "reversibility": "immediate", "expiry_trigger": f"remove when the vendor patch is applied (review by {expiry})",
         "requires_approval": True, "approver_roles": ["soc_lead", "ciso"], "executor": "tool-execution-broker"}
        for c in chosen[:3]]
    action = ({"true_zero_day": f"True zero-day in {t.get('product', 'the product')} exploited in the wild with no patch: deploy compensating controls now (virtual-patch order), each expiring on patch. Gated for approval.",
               "n_day_pre_patch": f"Pre-patch exposure in {t.get('product', 'the product')}: apply reduced-urgency compensating controls; monitor for exploitation.",
               "critical_patch": f"Patch is available for {t.get('cve_id', 'the CVE')}: route to vulnerability-management for expedited patching, not this playbook.",
               "not_applicable": "The organization does not use the affected product; no action."}[classification])
    key = [f"{t.get('cve_id', 'vuln')} in {t.get('product', 'n/a')}: classification {classification} (patch={patch}, exploited={wild}, uses={uses}, internet={internet})"]
    key += [f"control: {c['containment_intent']} (expires on patch)" for c in controls]
    if classification == "critical_patch":
        key.append("Patch exists: hand to vulnerability-management")
    evidence = [{"source": f"local://{rel}" if rel else "local://response/zero-day-response/SKILL.md", "ref": "vulnerability descriptor"}]
    if t.get("cve_id"):
        evidence.append({"source": f"https://nvd.nist.gov/vuln/detail/{str(t['cve_id']).upper()}", "ref": t["cve_id"]})
        if wild:
            evidence.append({"source": "https://www.cisa.gov/known-exploited-vulnerabilities-catalog", "ref": "exploited in the wild"})
    evidence.append({"source": "local://response/zero-day-response/SKILL.md", "ref": "zero-day classification and virtual-patching order"})
    return {"agent_slug": SLUG, "intent_type": "advise", "action": action,
            "rationale": ("Classified on the SKILL.md matrix: no patch and active exploitation while the org uses the product is a true zero-day (critical); no patch and PoC-only is "
                          "n-day; a patch existing routes to vulnerability management. Compensating controls follow the virtual-patching order and each carries an expiry tied to the "
                          "patch. Every control is a gated intent block; nothing is executed."),
            "confidence": 0.85, "severity": severity, "key_findings": key, "evidence_references": evidence,
            "next_agents": (["vulnerability-management"] if classification == "critical_patch" else ["containment-advisor"] if controls else []),
            "human_approval_required": bool(controls), "timestamp_utc": _now(),
            "classification": classification, "controls": controls,
            "mitre_ttps": ["T1190"] if internet else ["T1203"], "affected_assets": [str(a) for a in (t.get("affected_assets") or [])], "_exit": exit_code}


def main() -> int:
    ap = argparse.ArgumentParser(description="USAP zero-day-response")
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
    print(json.dumps(p, indent=2) if args.output == "json" else f"zero-day-response: {p.get('classification')} {p['severity']}")
    return code


if __name__ == "__main__":
    raise SystemExit(main())
