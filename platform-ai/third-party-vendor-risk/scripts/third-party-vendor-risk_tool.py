#!/usr/bin/env python3
"""third-party-vendor-risk_tool.py

Assesses vendor security posture against the SKILL.md tiered evidence requirements
(SOC 2, ISO 27001, pen test, questionnaire, BCP, incident SLA, DPA) and regulatory
obligations. Read-only assessment; vendor suspension/offboarding is mutating and
requires approval. Emits the USAP 11-field payload.

  python3 third-party-vendor-risk_tool.py --input vendor.json --output json
  python3 third-party-vendor-risk_tool.py --output json    # no input: informational, exit 0

Input (see tests/fixtures/third-party-vendor-risk-input.json):
{vendor, tier (1|2|3), handles_pii, documents{soc2, iso27001, pentest,
questionnaire, bcp, incident_sla, dpa}}.

Exit codes: 0 compliant; 1 missing required docs; 2 tier-1 critical gap or a
missing DPA/BAA when PII/PCI is processed. Stdlib only.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

SLUG = "third-party-vendor-risk"
HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parents[2]
# document -> required by tier (True required, "pref" preferred, False not required, "pii" if PII/PCI)
MATRIX = {
    "soc2": {1: True, 2: True, 3: False},
    "iso27001": {1: "pref", 2: False, 3: False},
    "pentest": {1: True, 2: "pref", 3: False},
    "questionnaire": {1: True, 2: True, 3: "abbrev"},
    "bcp": {1: True, 2: True, 3: False},
    "incident_sla": {1: True, 2: True, 3: False},
    "dpa": {1: "pii", 2: "pii", 3: False},
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
    if not t or not t.get("vendor"):
        return {"agent_slug": SLUG, "intent_type": "advise", "action": "Supply a vendor descriptor; nothing was provided.",
                "rationale": "No vendor supplied.", "confidence": 0.30, "severity": "informational", "key_findings": ["No vendor supplied"],
                "evidence_references": [{"source": "local://platform-ai/third-party-vendor-risk/SKILL.md", "ref": "tiered evidence matrix (not applied)"}],
                "next_agents": [], "human_approval_required": False, "timestamp_utc": _now(), "gaps": [], "_exit": 0}
    vendor = t.get("vendor")
    try:
        tier = int(t.get("tier", 1))
    except (TypeError, ValueError):
        tier = 1
    tier = tier if tier in (1, 2, 3) else 1
    pii = bool(t.get("handles_pii"))
    docs = t.get("documents") or {}
    gaps: List[dict] = []
    for doc, byt in MATRIX.items():
        req = byt.get(tier, False)
        have = bool(docs.get(doc))
        if have:
            continue
        if req is True:
            sev = "critical" if (tier == 1 and doc in ("soc2", "pentest")) else "high"
            gaps.append({"document": doc, "requirement": "required", "severity": sev})
        elif req == "pii" and pii:
            gaps.append({"document": doc, "requirement": "required (PII/PCI)", "severity": "critical"})
        elif req == "abbrev":
            gaps.append({"document": doc, "requirement": "abbreviated required", "severity": "medium"})
        elif req == "pref":
            gaps.append({"document": doc, "requirement": "preferred", "severity": "low"})
    gaps.sort(key=lambda g: -SEV_RANK[g["severity"]])
    crit = [g for g in gaps if g["severity"] == "critical"]
    severity = gaps[0]["severity"] if gaps else "informational"
    exit_code = 2 if crit else 1 if gaps else 0
    action = (f"{vendor} (tier {tier}): {len(crit)} critical evidence gap(s) — " + ", ".join(g["document"] for g in crit)[:150] + ". Withhold onboarding or plan offboarding (mutating, approval required)." if crit else
              f"{vendor} (tier {tier}): {len(gaps)} evidence gap(s) to collect." if gaps else
              f"{vendor} (tier {tier}): evidence requirements met.")
    key = [f"{vendor}: tier {tier}, PII/PCI={pii}; {len(gaps)} gap(s) ({len(crit)} critical)"]
    key += [f"{g['severity']} missing {g['document']} ({g['requirement']})" for g in gaps[:6]]
    evidence = [{"source": f"local://{rel}" if rel else "local://platform-ai/third-party-vendor-risk/SKILL.md", "ref": "vendor documents"},
                {"source": "local://platform-ai/third-party-vendor-risk/SKILL.md", "ref": "tiered evidence and regulatory tables"}]
    return {"agent_slug": SLUG, "intent_type": "advise", "action": action,
            "rationale": ("Each document is checked against the SKILL.md tiered matrix; a missing tier-1 SOC 2 or pen test is critical, as is a missing data-processing agreement when the vendor "
                          "handles PII or PCI (GDPR Art. 28 / HIPAA BAA). Assessment is read-only; suspending or offboarding a vendor is a mutating action requiring approval."),
            "confidence": 0.85, "severity": severity, "key_findings": key, "evidence_references": evidence,
            "next_agents": ["findings-tracker"] if gaps else [], "human_approval_required": False, "timestamp_utc": _now(),
            "tier": tier, "gaps": gaps, "mitre_ttps": [], "affected_assets": [str(vendor)], "_exit": exit_code}


def main() -> int:
    ap = argparse.ArgumentParser(description="USAP third-party-vendor-risk")
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
    print(json.dumps(p, indent=2) if args.output == "json" else f"third-party-vendor-risk: severity={p['severity']}")
    return code


if __name__ == "__main__":
    raise SystemExit(main())
