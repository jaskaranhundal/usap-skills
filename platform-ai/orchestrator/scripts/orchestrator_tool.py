#!/usr/bin/env python3
"""orchestrator_tool.py

Routes a SecurityFact to the deterministic agent sequence defined in the SKILL.md
routing table (primary + secondary agents by event_type and severity). ALWAYS
read-only — the orchestrator coordinates, never executes. Emits the USAP 11-field
payload.

  python3 orchestrator_tool.py --input event.json --output json
  python3 orchestrator_tool.py --output json    # no input: informational, exit 0

Input (see tests/fixtures/orchestrator-input.json):
{event_type, severity}. event_type in: secret_exposure, iam_anomaly,
network_intrusion, vulnerability_scan, malware_detection, data_exfiltration,
compliance_drift, supply_chain.

Exit codes: 0 low/medium; 1 high; 2 critical. Stdlib only.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

SLUG = "orchestrator"
HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parents[2]
SEV_RANK = {"critical": 4, "high": 3, "medium": 2, "low": 1, "informational": 0}


def _route(event: str, sev: str) -> tuple:
    """Return (primary[], secondary[]) per the SKILL.md routing table."""
    high = sev in ("critical", "high")
    table = {
        "secret_exposure": (["secrets-exposure"], ["containment-advisor", "compliance-mapping"]),
        "iam_anomaly": (["identity-access-risk"], ["containment-advisor", "threat-intelligence"] if high else ["findings-tracker"]),
        "network_intrusion": (["threat-intelligence", "incident-classification"], ["incident-commander", "forensics"] if high else ["findings-tracker"]),
        "vulnerability_scan": (["vulnerability-management"], ["containment-advisor"] if sev == "critical" else ["findings-tracker"]),
        "malware_detection": (["incident-classification"], ["threat-intelligence", "forensics"]),
        "data_exfiltration": (["incident-classification"], ["forensics", "compliance-mapping"]),
        "compliance_drift": (["compliance-mapping"], ["findings-tracker"]),
        "supply_chain": (["supply-chain-risk"], ["build-integrity", "threat-intelligence"]),
    }
    return table.get(event, ([], ["findings-tracker"]))


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def analyse(t: dict, input_path: Optional[str] = None) -> Dict[str, Any]:
    rel = None
    if input_path:
        try:
            rel = Path(input_path).resolve().relative_to(REPO_ROOT).as_posix()
        except ValueError:
            rel = None
    event = str(t.get("event_type", "")).lower()
    if not t or not event:
        return {"agent_slug": SLUG, "intent_type": "report", "action": "Supply an event_type to route; nothing was provided.",
                "rationale": "No event supplied.", "confidence": 0.30, "severity": "informational", "key_findings": ["No event supplied"],
                "evidence_references": [{"source": "local://platform-ai/orchestrator/SKILL.md", "ref": "routing table (not applied)"}],
                "next_agents": [], "human_approval_required": False, "timestamp_utc": _now(), "route": [], "_exit": 0}
    sev = str(t.get("severity", "medium")).lower()
    if sev not in SEV_RANK:
        sev = "medium"
    primary, secondary = _route(event, sev)
    route: List[str] = primary + [a for a in secondary if a not in primary]
    exit_code = 2 if sev == "critical" else 1 if sev == "high" else 0
    known = bool(primary)
    action = (f"Route {event} ({sev}) -> primary: {', '.join(primary) or 'none'}; then: {', '.join(secondary) or 'none'}." if known else
              f"No routing rule for event_type '{event}'; send to findings-tracker for triage.")
    key = [f"event={event}, severity={sev}: {len(route)} agent(s) in sequence",
           f"primary: {', '.join(primary) or 'none'}",
           f"secondary: {', '.join(secondary) or 'none'}"]
    evidence = [{"source": f"local://{rel}" if rel else "local://platform-ai/orchestrator/SKILL.md", "ref": "security event"},
                {"source": "local://platform-ai/orchestrator/SKILL.md", "ref": "event routing table"}]
    return {"agent_slug": SLUG, "intent_type": "report", "action": action,
            "rationale": ("The event is routed deterministically by the SKILL.md table: event_type selects the primary agent(s) and severity selects the secondary fan-out — a high or critical "
                          "IAM anomaly, for instance, adds containment and threat-intelligence, while a low one only records a finding. The orchestrator coordinates and never executes."),
            "confidence": 0.9 if known else 0.5, "severity": sev, "key_findings": key, "evidence_references": evidence,
            "next_agents": route, "human_approval_required": False, "timestamp_utc": _now(),
            "route": route, "mitre_ttps": [], "affected_assets": [], "_exit": exit_code}


def main() -> int:
    ap = argparse.ArgumentParser(description="USAP orchestrator")
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
    print(json.dumps(p, indent=2) if args.output == "json" else f"orchestrator: {len(p.get('route', []))} agent(s)")
    return code


if __name__ == "__main__":
    raise SystemExit(main())
