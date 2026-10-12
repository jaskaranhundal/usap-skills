#!/usr/bin/env python3
"""threat-intelligence_tool.py

Enriches a SecurityFact per the SKILL.md: classifies IOCs by the IOC taxonomy,
maps the event type to MITRE ATT&CK techniques, and assesses threat-actor
likelihood from the indicator signals. Read-only enrichment. Emits the USAP
11-field payload.

  python3 threat-intelligence_tool.py --input fact.json --output json
  python3 threat-intelligence_tool.py --output json     # no input: informational, exit 0

Input (see tests/fixtures/threat-intelligence-input.json): event_type,
severity, iocs[]: {type, value, reputation (malicious|suspicious|clean|unknown),
context}, signals{zero_day, known_apt_infra, low_and_slow, commodity_malware,
mass_scanning}.

Exit codes: 0 clean/unknown only; 1 suspicious indicators; 2 malicious
indicator or nation-state assessment. Stdlib only.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

SLUG = "threat-intelligence"
HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parents[2]
ATTACK_BY_EVENT = {
    "secret_exposure": ["T1552", "T1552.001"], "iam_anomaly": ["T1078", "T1548", "T1550"],
    "network_intrusion": ["T1190", "T1133"], "data_exfiltration": ["T1041", "T1567"],
    "malware_execution": ["T1059", "T1055"], "supply_chain": ["T1195", "T1195.001"],
    "credential_stuffing": ["T1110.004", "T1110"], "privilege_escalation": ["T1548", "T1134"],
    "phishing": ["T1566"], "ransomware": ["T1486", "T1490"],
}
IOC_TYPES = {"ip_address", "domain", "file_hash", "email_address", "url", "user_agent", "aws_account_id", "package_name", "cve_id"}
ATTACK_URL = "https://attack.mitre.org/techniques/"


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def analyse(t: dict, input_path: Optional[str] = None) -> Dict[str, Any]:
    rel = None
    if input_path:
        try:
            rel = Path(input_path).resolve().relative_to(REPO_ROOT).as_posix()
        except ValueError:
            rel = None
    if not t:
        return {"agent_slug": SLUG, "intent_type": "analyze", "action": "Supply a SecurityFact with IOCs; nothing was provided.",
                "rationale": "No fact supplied; no enrichment.", "confidence": 0.30, "severity": "informational",
                "key_findings": ["No fact supplied"], "evidence_references": [{"source": "local://detection/threat-intelligence/SKILL.md", "ref": "IOC taxonomy (not applied)"}],
                "next_agents": [], "human_approval_required": False, "timestamp_utc": _now(), "enrichment": {}, "_exit": 0}
    et = str(t.get("event_type", "unknown")).lower()
    iocs = [i for i in (t.get("iocs") or []) if isinstance(i, dict)]
    sig = t.get("signals") or {}
    mal = [i for i in iocs if str(i.get("reputation", "unknown")).lower() == "malicious"]
    susp = [i for i in iocs if str(i.get("reputation", "unknown")).lower() == "suspicious"]
    techniques = ATTACK_BY_EVENT.get(et, [])

    # Threat actor assessment
    if sig.get("zero_day") or sig.get("known_apt_infra") or sig.get("low_and_slow"):
        actor, actor_conf = "nation_state", 0.7
    elif sig.get("commodity_malware") or (mal and et in ("malware_execution", "ransomware")):
        actor, actor_conf = "cybercrime", 0.65
    elif sig.get("mass_scanning"):
        actor, actor_conf = "opportunistic", 0.6
    elif mal or susp:
        actor, actor_conf = "unattributed_malicious", 0.5
    else:
        actor, actor_conf = "undetermined", 0.4

    severity = "critical" if (mal or actor == "nation_state") else "high" if susp else "low" if iocs else "informational"
    exit_code = 2 if (mal or actor == "nation_state") else 1 if susp else 0
    unknown_types = [i.get("type") for i in iocs if str(i.get("type")) not in IOC_TYPES]
    action = (f"{len(mal)} malicious and {len(susp)} suspicious indicator(s); actor assessment {actor} ({actor_conf:.0%}). "
              + ("Escalate for hunting and containment." if mal or actor == "nation_state" else "Add to the watchlist and re-check reputation.")
              if iocs else "No indicators to enrich.")
    key = [f"Event {et}: {len(iocs)} IOC(s) ({len(mal)} malicious, {len(susp)} suspicious); ATT&CK {', '.join(techniques) or 'n/a'}; actor {actor} ({actor_conf:.0%})"]
    for i in (mal + susp)[:5]:
        key.append(f"{i.get('reputation')} {i.get('type')} {i.get('value')}: {i.get('context', '')[:80]}")
    if unknown_types:
        key.append(f"IOC types outside the taxonomy: {', '.join(str(x) for x in unknown_types)}")

    evidence = [{"source": f"local://{rel}" if rel else "local://detection/threat-intelligence/SKILL.md", "ref": "SecurityFact IOCs", "quote": et}]
    evidence += [{"source": f"{ATTACK_URL}{tech.replace('.', '/')}/", "ref": tech} for tech in techniques[:4]]
    evidence.append({"source": "local://detection/threat-intelligence/SKILL.md", "ref": "IOC taxonomy, ATT&CK mapping, threat-actor assessment"})
    return {"agent_slug": SLUG, "intent_type": "analyze", "action": action,
            "rationale": ("IOCs classified by the SKILL.md taxonomy, the event type mapped to its priority ATT&CK techniques, and the actor category assessed from the indicator "
                          "signals (zero-day / known APT infra / low-and-slow => nation state; commodity malware => cybercrime; mass scanning => opportunistic). Read-only."),
            "confidence": round(actor_conf + (0.1 if mal else 0), 2), "severity": severity, "key_findings": key, "evidence_references": evidence,
            "next_agents": (["threat-hunting", "incident-classification"] if mal else ["threat-hunting"] if susp else []),
            "human_approval_required": False, "timestamp_utc": _now(),
            "enrichment": {"event_type": et, "attack_techniques": techniques, "malicious": len(mal), "suspicious": len(susp),
                           "actor_assessment": actor, "actor_confidence": actor_conf},
            "mitre_ttps": techniques, "affected_assets": [str(i.get("value")) for i in mal], "_exit": exit_code}


def main() -> int:
    ap = argparse.ArgumentParser(description="USAP threat-intelligence")
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
    print(json.dumps(p, indent=2) if args.output == "json" else f"threat-intelligence: severity={p['severity']}")
    return code


if __name__ == "__main__":
    raise SystemExit(main())
