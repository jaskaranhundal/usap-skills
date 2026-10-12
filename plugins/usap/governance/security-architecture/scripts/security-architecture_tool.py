#!/usr/bin/env python3
"""security-architecture_tool.py

Reviews an architecture change against the SKILL.md Security Architecture
Review criteria (eight SAR questions) and the CISA Zero Trust maturity pillars,
producing an architecture gap register. Read-only advisory. Emits the USAP
11-field payload.

  python3 security-architecture_tool.py --input sar.json --output json
  python3 security-architecture_tool.py --output json    # no input: informational, exit 0

Input (see tests/fixtures/security-architecture-input.json): system, trigger,
sar{authentication, authorization, network, data, audit, secrets_management,
third_party, recovery} each {status (pass|gap|fail), note}, zero_trust{identity,
device, network, application, data} each (traditional|advanced|optimal).

Exit codes: 0 no fail; 1 gaps only; 2 a failed SAR criterion. Stdlib only.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

SLUG = "security-architecture"
HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parents[2]
SAR = {
    "authentication": ("critical", "How are users, services and devices authenticated?"),
    "authorization": ("critical", "Is least privilege enforced for every identity?"),
    "network": ("high", "Is segmentation appropriate and traffic encrypted?"),
    "data": ("critical", "Is data encrypted at rest and in transit?"),
    "audit": ("high", "Are security events logged to tamper-proof storage?"),
    "secrets_management": ("critical", "Are keys and credentials in a vault, not env vars?"),
    "third_party": ("high", "What is the blast radius of a third-party compromise?"),
    "recovery": ("medium", "Can the system recover from a security incident?"),
}
ZT_LEVEL = {"traditional": 0, "advanced": 1, "optimal": 2}
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
    sar = t.get("sar") or {}
    if not t or not sar:
        return {"agent_slug": SLUG, "intent_type": "advise", "action": "Supply a SAR descriptor; nothing was provided.",
                "rationale": "No architecture descriptor supplied; no review.", "confidence": 0.30, "severity": "informational",
                "key_findings": ["No SAR descriptor supplied"], "evidence_references": [{"source": "local://governance/security-architecture/SKILL.md", "ref": "SAR criteria (not applied)"}],
                "next_agents": [], "human_approval_required": False, "timestamp_utc": _now(), "gap_register": [], "_exit": 0}
    register: List[dict] = []
    for crit, (base_sev, question) in SAR.items():
        entry = sar.get(crit) or {}
        status = str(entry.get("status", "gap")).lower()
        if status == "pass":
            continue
        sev = base_sev if status == "fail" else ("high" if base_sev == "critical" else "medium")
        register.append({"criterion": crit, "status": status, "severity": sev, "question": question, "note": entry.get("note", "")})
    zt = t.get("zero_trust") or {}
    zt_gaps = [f"{p}: {lvl}" for p, lvl in zt.items() if ZT_LEVEL.get(str(lvl).lower(), 0) == 0]
    register.sort(key=lambda r: -SEV_RANK[r["severity"]])
    fails = [r for r in register if r["status"] == "fail"]
    severity = "critical" if fails else "high" if register else "low" if zt_gaps else "informational"
    exit_code = 2 if fails else 1 if register else 0

    action = (f"{len(fails)} SAR criterion(criteria) failed on {t.get('system', 'the system')} — do not deploy until fixed: " +
              "; ".join(f"{r['criterion']} ({r['note'] or SAR[r['criterion']][1]})" for r in fails[:3]) + ".") if fails else \
             (f"{len(register)} architecture gap(s) to close before or shortly after deployment of {t.get('system', 'the system')}." if register else
              "Architecture meets the SAR criteria; note Zero Trust pillars still at traditional maturity.")
    key = [f"SAR of {t.get('system', 'n/a')} (trigger: {t.get('trigger', 'n/a')}): {len(register)} open criterion(criteria), {len(fails)} failed; {len(zt_gaps)} ZT pillar(s) at traditional"]
    key += [f"{r['severity'].upper()} {r['criterion']} [{r['status']}]: {r['note'] or r['question']}" for r in register[:6]]
    if zt_gaps:
        key.append("Zero Trust at traditional maturity: " + ", ".join(zt_gaps))

    evidence = [{"source": f"local://{rel}" if rel else "local://governance/security-architecture/SKILL.md", "ref": "SAR descriptor"},
                {"source": "https://csrc.nist.gov/pubs/sp/800/207/final", "ref": "NIST SP 800-207 Zero Trust Architecture"},
                {"source": "local://governance/security-architecture/SKILL.md", "ref": "SAR evaluation criteria and ZT maturity model"}]
    return {"agent_slug": SLUG, "intent_type": "advise", "action": action,
            "rationale": ("Each of the eight SAR criteria is a gap unless marked pass; a fail on a critical criterion (auth, authz, data, secrets) blocks deployment. Zero Trust "
                          "pillars still at traditional maturity are noted against the CISA model. Every control traces to a SAR question. Read-only advisory."),
            "confidence": 0.85, "severity": severity, "key_findings": key, "evidence_references": evidence,
            "next_agents": ["risk-threat-modeling"] if fails else [], "human_approval_required": False, "timestamp_utc": _now(),
            "gap_register": register, "zero_trust_gaps": zt_gaps, "mitre_ttps": [], "affected_assets": [t.get("system")] if t.get("system") else [], "_exit": exit_code}


def main() -> int:
    ap = argparse.ArgumentParser(description="USAP security-architecture")
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
    print(json.dumps(p, indent=2) if args.output == "json" else f"security-architecture: severity={p['severity']}")
    return code


if __name__ == "__main__":
    raise SystemExit(main())
