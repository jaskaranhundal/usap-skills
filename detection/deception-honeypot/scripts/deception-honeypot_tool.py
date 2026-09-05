#!/usr/bin/env python3
"""deception-honeypot_tool.py

Produces a deception deployment plan per the SKILL.md asset taxonomy: honeypot
types and canary tokens matched to the attacker objectives in scope and the
environment's zones, with alert logic. Advisory; production deployment is
authorization-gated. Emits the USAP 11-field payload.

  python3 deception-honeypot_tool.py --input env.json --output json
  python3 deception-honeypot_tool.py --output json    # no input: informational, exit 0

Input (see tests/fixtures/deception-honeypot-input.json): environment,
objectives[] (lateral_movement|credential_theft|data_exfiltration|
privilege_escalation|scanning), zones[] (domain_controller|jump_box|dmz|
database|admin_subnet|file_share|repositories), existing_deception[].

Exit codes: 0 always (advisory). Stdlib only.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

SLUG = "deception-honeypot"
HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parents[2]
# objective -> recommended assets (type, asset, placement zone hint)
PLAYBOOK = {
    "lateral_movement": [("honeypot", "credential honeypot", "domain_controller/jump_box"), ("trap", "honey credentials + deceptive SMB share", "file_share")],
    "credential_theft": [("canary", "AWS key canary token", "repositories"), ("honeypot", "credential honeypot", "jump_box")],
    "data_exfiltration": [("canary", "DNS canary in documents", "file_share"), ("honeypot", "database honeypot", "database")],
    "privilege_escalation": [("honeypot", "admin honeypot", "admin_subnet"), ("trap", "fake domain admin account with monitoring", "domain_controller")],
    "scanning": [("honeypot", "service honeypot", "dmz")],
}
MITRE = {"lateral_movement": "T1021", "credential_theft": "T1555", "data_exfiltration": "T1041", "privilege_escalation": "T1078", "scanning": "T1046"}


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def analyse(t: dict, input_path: Optional[str] = None) -> Dict[str, Any]:
    rel = None
    if input_path:
        try:
            rel = Path(input_path).resolve().relative_to(REPO_ROOT).as_posix()
        except ValueError:
            rel = None
    objectives = [str(o).lower() for o in (t.get("objectives") or [])]
    zones = [str(z).lower() for z in (t.get("zones") or [])]
    existing = [str(e).lower() for e in (t.get("existing_deception") or [])]
    if not t or not objectives:
        return {"agent_slug": SLUG, "intent_type": "advise", "action": "Supply attacker objectives and zones; nothing was provided.",
                "rationale": "No objectives supplied; no deception plan.", "confidence": 0.30, "severity": "informational",
                "key_findings": ["No objectives supplied"], "evidence_references": [{"source": "local://detection/deception-honeypot/SKILL.md", "ref": "asset taxonomy (not applied)"}],
                "next_agents": [], "human_approval_required": False, "timestamp_utc": _now(), "deployment_plan": [], "_exit": 0}
    plan: List[dict] = []
    for obj in objectives:
        for kind, asset, placement in PLAYBOOK.get(obj, []):
            covered = any(asset.split()[0] in e for e in existing)
            plan.append({"objective": obj, "asset_type": kind, "asset": asset, "placement": placement,
                         "alert_logic": "Any interaction is high-fidelity: real users never touch a decoy. Alert on first read/auth/connect and page the SOC.",
                         "already_deployed": covered})
    new_assets = [p for p in plan if not p["already_deployed"]]
    uncovered_zones = [z for z in zones if not any(z in p["placement"] for p in plan)]
    severity = "medium" if new_assets else "low"
    action = (f"Deploy {len(new_assets)} deception asset(s) for {', '.join(sorted(set(objectives)))}: "
              + "; ".join(f"{p['asset']} near {p['placement']}" for p in new_assets[:4])
              + ". Production deployment requires authorization." if new_assets else "Existing deception already covers the stated objectives.")
    key = [f"{len(objectives)} objective(s), {len(zones)} zone(s): {len(new_assets)} new deception asset(s) recommended, {len(plan)-len(new_assets)} already deployed"]
    key += [f"{p['objective']}: {p['asset_type']} {p['asset']} @ {p['placement']}" + (" [exists]" if p["already_deployed"] else "") for p in plan[:6]]
    if uncovered_zones:
        key.append("Zones with no recommended decoy: " + ", ".join(uncovered_zones))
    evidence = [{"source": f"local://{rel}" if rel else "local://detection/deception-honeypot/SKILL.md", "ref": "environment objectives and zones"},
                {"source": "local://detection/deception-honeypot/SKILL.md", "ref": "deception asset taxonomy and alert logic"}]
    return {"agent_slug": SLUG, "intent_type": "advise", "action": action,
            "rationale": ("Each attacker objective in scope is matched to its SKILL.md deception assets (honeypots, canary tokens, lateral-movement traps) and a placement zone; "
                          "assets already present are noted, not duplicated. Any interaction with a decoy is high-fidelity by design. Advisory; deployment is authorization-gated."),
            "confidence": 0.8, "severity": severity, "key_findings": key, "evidence_references": evidence,
            "next_agents": ["detection-engineering"] if new_assets else [], "human_approval_required": bool(new_assets), "timestamp_utc": _now(),
            "deployment_plan": plan, "mitre_ttps": sorted({MITRE[o] for o in objectives if o in MITRE}), "affected_assets": [], "_exit": 0}


def main() -> int:
    ap = argparse.ArgumentParser(description="USAP deception-honeypot")
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
    print(json.dumps(p, indent=2) if args.output == "json" else f"deception-honeypot: severity={p['severity']}")
    return code


if __name__ == "__main__":
    raise SystemExit(main())
