#!/usr/bin/env python3
"""quantum-security-readiness_tool.py

Tiers assets for post-quantum migration per the SKILL.md table (CRITICAL:
long-lived data on RSA/ECC ... LOW: short-lived/expired) with target migration
dates. Read-only assessment; updating a priority tier or re-issuing a certificate
with PQC is a mutating policy change requiring approval. Emits the USAP 11-field
payload.

  python3 quantum-security-readiness_tool.py --input inventory.json --output json
  python3 quantum-security-readiness_tool.py --output json    # no input: informational, exit 0

Input (see tests/fixtures/quantum-security-readiness-input.json):
{assets[] {name, algorithm (rsa|ecc|aes|pqc), data_sensitivity_years,
internet_exposed (bool), internal (bool)}}.

Exit codes: 0 no critical/high; 1 high (18-month window); 2 critical (6-month
window). Stdlib only.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

SLUG = "quantum-security-readiness"
HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parents[2]
QUANTUM_VULN = {"rsa", "ecc", "ecdsa", "ecdh", "dh"}
SEV_RANK = {"critical": 4, "high": 3, "medium": 2, "low": 1, "informational": 0}


def _tier(asset: dict) -> tuple:
    algo = str(asset.get("algorithm", "")).lower()
    vuln = algo in QUANTUM_VULN
    try:
        years = float(asset.get("data_sensitivity_years", 0))
    except (TypeError, ValueError):
        years = 0.0
    if not vuln:
        return "low", "During normal refresh", "not quantum-vulnerable"
    if years > 10:
        return "critical", "Within 6 months", "long-lived data (>10y) on RSA/ECC — harvest-now-decrypt-later risk"
    if asset.get("internet_exposed"):
        return "high", "Within 18 months", "internet-exposed key exchange on RSA/ECC"
    if asset.get("internal"):
        return "medium", "Within 36 months", "internal service on RSA/ECC"
    return "medium", "Within 36 months", "RSA/ECC in use"


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def analyse(t: dict, input_path: Optional[str] = None) -> Dict[str, Any]:
    rel = None
    if input_path:
        try:
            rel = Path(input_path).resolve().relative_to(REPO_ROOT).as_posix()
        except ValueError:
            rel = None
    raw = [a for a in (t.get("assets") or []) if isinstance(a, dict)]
    if not t or not raw:
        return {"agent_slug": SLUG, "intent_type": "report", "action": "Supply a crypto asset inventory; nothing was provided.",
                "rationale": "No assets supplied.", "confidence": 0.30, "severity": "informational", "key_findings": ["No assets supplied"],
                "evidence_references": [{"source": "local://risk-compliance/quantum-security-readiness/SKILL.md", "ref": "migration tier table (not applied)"}],
                "next_agents": [], "human_approval_required": False, "timestamp_utc": _now(), "assets": [], "_exit": 0}
    assets: List[dict] = []
    for a in raw:
        tier, target, why = _tier(a)
        assets.append({"name": a.get("name"), "algorithm": a.get("algorithm"), "tier": tier, "target": target, "reason": why})
    order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
    assets.sort(key=lambda x: order[x["tier"]])
    counts = {k: sum(1 for x in assets if x["tier"] == k) for k in SEV_RANK}
    severity = assets[0]["tier"] if assets else "informational"
    exit_code = 2 if counts["critical"] else 1 if counts["high"] else 0
    action = (f"{counts['critical']} asset(s) need PQC migration within 6 months: " + ", ".join(x["name"] for x in assets if x["tier"]=="critical")[:130] + ". Tier updates and re-issuance are mutating (approval required)." if counts["critical"] else
              f"{counts['high']} asset(s) on an 18-month PQC migration window." if counts["high"] else
              "No asset on a critical or high PQC migration window.")
    key = [f"{len(assets)} asset(s): {counts['critical']} critical, {counts['high']} high, {counts['medium']} medium quantum-migration tier(s)"]
    key += [f"{x['tier']} {x['name']} ({x['algorithm']}) -> {x['target']}: {x['reason']}" for x in assets[:6]]
    evidence = [{"source": f"local://{rel}" if rel else "local://risk-compliance/quantum-security-readiness/SKILL.md", "ref": "crypto asset inventory"},
                {"source": "https://csrc.nist.gov/projects/post-quantum-cryptography", "ref": "NIST PQC standards"},
                {"source": "local://risk-compliance/quantum-security-readiness/SKILL.md", "ref": "migration tier table"}]
    return {"agent_slug": SLUG, "intent_type": "report", "action": action,
            "rationale": ("Each asset is tiered against the SKILL.md table: long-lived data (>10 years) protected by RSA/ECC is critical on a 6-month window because of harvest-now-decrypt-later, "
                          "internet-exposed key exchange is high on 18 months, internal RSA/ECC is medium on 36 months. Assessment is read-only; changing a tier or re-issuing a certificate with "
                          "a PQC algorithm is a mutating policy change requiring approval."),
            "confidence": 0.85, "severity": severity, "key_findings": key, "evidence_references": evidence,
            "next_agents": ["cryptography-key-management"] if (counts["critical"] or counts["high"]) else [], "human_approval_required": False, "timestamp_utc": _now(),
            "assets": assets, "mitre_ttps": [], "affected_assets": [str(x["name"]) for x in assets if x.get("name")], "_exit": exit_code}


def main() -> int:
    ap = argparse.ArgumentParser(description="USAP quantum-security-readiness")
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
    print(json.dumps(p, indent=2) if args.output == "json" else f"quantum-security-readiness: severity={p['severity']}")
    return code


if __name__ == "__main__":
    raise SystemExit(main())
