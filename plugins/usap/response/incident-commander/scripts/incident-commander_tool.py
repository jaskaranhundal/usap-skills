#!/usr/bin/env python3
"""incident-commander_tool.py

Declares an incident severity per the SKILL.md incident-type severity-floor
table (SEV1-SEV4), assigns the response track and ICS roles, and routes to the
downstream agents. Severity declaration is read-only; every containment action
is a gated mutating intent. Emits the USAP 11-field payload.

  python3 incident-commander_tool.py --input incident.json --output json
  python3 incident-commander_tool.py --output json    # no input: informational, exit 0

Input (see tests/fixtures/incident-commander-input.json): incident_id,
incident_type, confirmed_impact, spreading, affected_hosts[], affected_accounts[].

Exit codes: 0 SEV4; 1 SEV3/SEV2; 2 SEV1. Stdlib only.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

SLUG = "incident-commander"
HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parents[2]
# incident_type -> (sev floor, mutating category, mitre)
FLOORS = {
    "ransomware": ("SEV1", "remediation_action", "T1486"), "destructive_malware": ("SEV1", "remediation_action", "T1485"),
    "data_exfiltration": ("SEV1", "credential_operation", "T1041"), "domain_controller_compromise": ("SEV1", "network_change", "T1003"),
    "ad_compromise": ("SEV1", "network_change", "T1003"), "defense_evasion": ("SEV1", "network_change", "T1562"),
    "credential_compromise_privesc": ("SEV2", "credential_operation", "T1078"), "lateral_movement": ("SEV2", "network_change", "T1021"),
    "single_account_compromise": ("SEV3", "credential_operation", "T1078"), "security_alert": ("SEV4", None, None),
}
SEV_META = {"SEV1": ("critical", "War Room, all-hands", 2), "SEV2": ("high", "24/7 response", 1), "SEV3": ("medium", "business hours", 1), "SEV4": ("low", "tracking", 0)}
ICS = {"incident_commander": "cs-incident-responder", "forensics_lead": "forensics", "containment_lead": "containment-advisor",
       "comms_lead": "ciso-brief-generator", "intel_lead": "threat-intelligence"}


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def analyse(t: dict, input_path: Optional[str] = None) -> Dict[str, Any]:
    rel = None
    if input_path:
        try:
            rel = Path(input_path).resolve().relative_to(REPO_ROOT).as_posix()
        except ValueError:
            rel = None
    if not t or not t.get("incident_type"):
        return {"agent_slug": SLUG, "intent_type": "report", "action": "Supply an incident; nothing was provided.",
                "rationale": "No incident supplied.", "confidence": 0.30, "severity": "informational", "key_findings": ["No incident supplied"],
                "evidence_references": [{"source": "local://response/incident-commander/SKILL.md", "ref": "severity framework (not applied)"}],
                "next_agents": [], "human_approval_required": False, "timestamp_utc": _now(), "command": {}, "_exit": 0}
    it = str(t.get("incident_type", "security_alert")).lower()
    floor, mcat, mitre = FLOORS.get(it, ("SEV3", "remediation_action", "T1078"))
    # confirmed impact or spread cannot lower the floor; raise a SEV3 to SEV2 if spreading
    if t.get("spreading") and floor in ("SEV3", "SEV2"):
        floor = "SEV1" if t.get("confirmed_impact") else "SEV2"
    sev, track, extra_roles = SEV_META[floor]
    exit_code = 2 if floor == "SEV1" else 1 if floor in ("SEV2", "SEV3") else 0
    hosts = [str(h) for h in (t.get("affected_hosts") or [])]
    accts = [str(a) for a in (t.get("affected_accounts") or [])]
    roles = {r: a for r, a in ICS.items()}
    action = (f"Declare {floor} ({sev}) for {t.get('incident_id', 'the incident')}: {track}. Assign IC, forensics, containment and comms. "
              "Containment actions are gated for approval." if floor != "SEV4" else
              f"Track as {floor}: security alert with no confirmed impact; monitor, no war room.")
    key = [f"{t.get('incident_id', 'incident')} type={it}: declared {floor} ({sev}); response track {track}; {len(hosts)} host(s), {len(accts)} account(s)",
           f"ICS roles: " + ", ".join(f"{r}={a}" for r, a in roles.items()),
           f"Containment category if actioned: {mcat or 'none (read-only)'} — gated for approval" if mcat else "No mutating action at SEV4"]
    evidence = [{"source": f"local://{rel}" if rel else "local://response/incident-commander/SKILL.md", "ref": "incident descriptor"},
                {"source": "local://response/incident-commander/SKILL.md", "ref": "incident classification and severity framework (NIST SP 800-61)"}]
    next_agents = []
    if floor in ("SEV1", "SEV2"):
        next_agents = ["containment-advisor", "forensics", "ciso-brief-generator"]
    elif floor == "SEV3":
        next_agents = ["containment-advisor"]
    return {"agent_slug": SLUG, "intent_type": "escalate" if floor in ("SEV1", "SEV2") else "report", "action": action,
            "rationale": ("Severity taken as the incident type's SKILL.md floor, never lowered; spread raises a lower SEV. The commander declares severity (read-only) and assigns "
                          "the ICS roles; each containment action carried out downstream is a gated mutating intent."),
            "confidence": 0.9, "severity": sev, "key_findings": key, "evidence_references": evidence,
            "next_agents": next_agents, "human_approval_required": floor in ("SEV1", "SEV2", "SEV3"), "timestamp_utc": _now(),
            "command": {"incident_id": t.get("incident_id"), "sev": floor, "response_track": track, "ics_roles": roles, "mutating_category": mcat},
            "approver_roles": ["soc_lead", "ciso"] if floor in ("SEV1", "SEV2", "SEV3") else [],
            "mitre_ttps": [mitre] if mitre else [], "affected_assets": hosts + accts, "_exit": exit_code}


def main() -> int:
    ap = argparse.ArgumentParser(description="USAP incident-commander")
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
    print(json.dumps(p, indent=2) if args.output == "json" else f"incident-commander: {p['command'].get('sev')} {p['severity']}")
    return code


if __name__ == "__main__":
    raise SystemExit(main())
