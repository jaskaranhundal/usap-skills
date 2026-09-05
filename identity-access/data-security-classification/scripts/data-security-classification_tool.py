#!/usr/bin/env python3
"""data-security-classification_tool.py

Classifies data assets into the SKILL.md 4-tier scheme (Public / Internal /
Confidential / Top Secret) from their data categories, assigns the required
handling controls, and flags assets whose current protection is below their
tier. Read-only. Emits the USAP 11-field payload.

  python3 data-security-classification_tool.py --input assets.json --output json
  python3 data-security-classification_tool.py --output json    # no input: informational, exit 0

Input (see tests/fixtures/data-security-classification-input.json): assets[]:
{id, name, data_categories[] (pii|pci|phi|encryption_keys|source_code|
financial|trade_secret|employee_directory|marketing|public), location,
encrypted_at_rest, encrypted_in_transit, access (public|restricted|internal)}.

Exit codes: 0 all adequately protected; 1 a control gap; 2 a Top Secret or
Confidential asset publicly accessible or unencrypted. Stdlib only.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

SLUG = "data-security-classification"
HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parents[2]
# category -> tier (L4 highest)
CATEGORY_TIER = {"encryption_keys": 4, "trade_secret": 4, "ma_data": 4,
                 "pii": 3, "pci": 3, "phi": 3, "source_code": 3, "financial": 3,
                 "employee_directory": 2, "internal_policy": 2,
                 "marketing": 1, "public": 1}
TIER_LABEL = {4: "Top Secret / Restricted", 3: "Confidential", 2: "Internal", 1: "Public"}
TIER_CONTROLS = {
    4: ["encryption at rest and in transit (dedicated keys)", "access on explicit approval only", "full audit logging", "no third-party sharing"],
    3: ["encryption at rest and in transit", "role-based least-privilege access", "audit logging", "DLP monitoring"],
    2: ["access limited to employees", "transport encryption"],
    1: ["integrity controls; no confidentiality requirement"],
}


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _assess(a: dict) -> dict:
    cats = [str(c).lower() for c in (a.get("data_categories") or [])]
    tier = max((CATEGORY_TIER.get(c, 1) for c in cats), default=1)
    gaps: List[str] = []
    if tier >= 3:
        if not a.get("encrypted_at_rest"):
            gaps.append("not encrypted at rest")
        if not a.get("encrypted_in_transit"):
            gaps.append("not encrypted in transit")
        if str(a.get("access", "internal")).lower() == "public":
            gaps.append("publicly accessible")
    if tier == 2 and str(a.get("access", "internal")).lower() == "public":
        gaps.append("internal data publicly accessible")
    if tier >= 3 and str(a.get("access", "")).lower() not in ("restricted", "internal", "private"):
        pass
    if tier == 4 and gaps:
        sev = "critical"
    elif tier >= 3 and ("publicly accessible" in gaps or "not encrypted at rest" in gaps):
        sev = "critical"
    elif gaps:
        sev = "high"
    else:
        sev = "informational"
    return {"id": a.get("id"), "name": a.get("name"), "tier": f"L{tier}", "label": TIER_LABEL[tier], "categories": cats,
            "required_controls": TIER_CONTROLS[tier], "gaps": gaps, "severity": sev}


def analyse(t: dict, input_path: Optional[str] = None) -> Dict[str, Any]:
    rel = None
    if input_path:
        try:
            rel = Path(input_path).resolve().relative_to(REPO_ROOT).as_posix()
        except ValueError:
            rel = None
    assets = [a for a in (t.get("assets") or []) if isinstance(a, dict)]
    if not t or not assets:
        return {"agent_slug": SLUG, "intent_type": "analyze", "action": "Supply data assets; nothing was provided.",
                "rationale": "No assets supplied; no classification.", "confidence": 0.30, "severity": "informational",
                "key_findings": ["No data assets supplied"], "evidence_references": [{"source": "local://identity-access/data-security-classification/SKILL.md", "ref": "classification framework (not applied)"}],
                "next_agents": [], "human_approval_required": False, "timestamp_utc": _now(), "assets": [], "_exit": 0}
    rank = {"critical": 4, "high": 3, "medium": 2, "low": 1, "informational": 0}
    scored = sorted((_assess(a) for a in assets), key=lambda r: -rank[r["severity"]])
    gapped = [r for r in scored if r["gaps"]]
    crit = [r for r in scored if r["severity"] == "critical"]
    severity = scored[0]["severity"] if scored else "informational"
    exit_code = 2 if crit else 1 if gapped else 0
    action = (f"{len(crit)} high-sensitivity asset(s) under-protected: " + "; ".join(f"{r['id']} ({r['label']}: {', '.join(r['gaps'])})" for r in crit[:3]) + "."
              if crit else f"{len(gapped)} control gap(s) to close." if gapped else "All assets meet their tier's handling controls.")
    key = [f"{len(assets)} asset(s) classified: " + ", ".join(f"{r['tier']}={sum(1 for x in scored if x['tier']==r['tier'])}" for r in sorted({s['tier'] for s in scored}) if isinstance(r, str)) if False else
           f"{len(assets)} asset(s) classified; {len(gapped)} with control gaps, {len(crit)} critical"]
    key += [f"{r['severity']} {r['id']} {r['tier']} ({r['label']}): {', '.join(r['gaps']) or 'controls adequate'}" for r in scored[:6]]
    evidence = [{"source": f"local://{rel}" if rel else "local://identity-access/data-security-classification/SKILL.md", "ref": "data asset inventory"},
                {"source": "local://identity-access/data-security-classification/SKILL.md", "ref": "4-tier classification and handling controls"}]
    return {"agent_slug": SLUG, "intent_type": "analyze", "action": action,
            "rationale": ("Each asset takes the highest tier of its data categories (encryption keys and trade secrets are L4; PII/PCI/PHI/source/financial are L3), the tier's "
                          "handling controls are required, and any missing control is a gap; a Confidential or Top Secret asset that is public or unencrypted is critical. Read-only."),
            "confidence": 0.88, "severity": severity, "key_findings": key, "evidence_references": evidence,
            "next_agents": (["compliance-mapping"] if crit else []) + (["findings-tracker"] if gapped else []), "human_approval_required": False, "timestamp_utc": _now(),
            "assets": scored, "mitre_ttps": ["T1530"] if crit else [], "affected_assets": [str(r["id"]) for r in gapped], "_exit": exit_code}


def main() -> int:
    ap = argparse.ArgumentParser(description="USAP data-security-classification")
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
    print(json.dumps(p, indent=2) if args.output == "json" else f"data-security-classification: severity={p['severity']}")
    return code


if __name__ == "__main__":
    raise SystemExit(main())
