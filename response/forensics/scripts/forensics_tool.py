#!/usr/bin/env python3
"""forensics_tool.py

Orders evidence collection by the SKILL.md Evidence Priority Matrix (volatility),
checks chain-of-custody admissibility (hash at acquisition, documented tool
provenance, write-blocked target), and reconstructs a timeline from supplied
events. Timeline is read-only; a collection step that modifies a system is a
gated remediation_action. Emits the USAP 11-field payload.

  python3 forensics_tool.py --input case.json --output json
  python3 forensics_tool.py --output json     # no input: informational, exit 0

Input (see tests/fixtures/forensics-input.json): case_id, hosts[], available_evidence[]
(ram|network_connections|processes|siem_logs|cloudtrail|disk|browser_history),
timeline[]: {ts, event}, custody{hash_at_acquisition, tool_provenance,
write_blocked}.

Exit codes: 0 timeline only; 1 volatile evidence at risk; 2 chain-of-custody
defect (inadmissible). Stdlib only.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

SLUG = "forensics"
HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parents[2]
PRIORITY = {"ram": ("P0", "seconds"), "network_connections": ("P0", "minutes"), "processes": ("P0", "minutes"),
            "siem_logs": ("P1", "hours"), "cloudtrail": ("P1", "days"), "disk": ("P2", "persistent"),
            "browser_history": ("P2", "persistent")}


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
        return {"agent_slug": SLUG, "intent_type": "analyze", "action": "Supply a forensics case; nothing was provided.",
                "rationale": "No case supplied.", "confidence": 0.30, "severity": "informational", "key_findings": ["No case supplied"],
                "evidence_references": [{"source": "local://response/forensics/SKILL.md", "ref": "evidence priority matrix (not applied)"}],
                "next_agents": [], "human_approval_required": False, "timestamp_utc": _now(), "collection_plan": [], "_exit": 0}
    avail = [str(e).lower() for e in (t.get("available_evidence") or [])]
    custody = t.get("custody") or {}
    timeline = [e for e in (t.get("timeline") or []) if isinstance(e, dict)]
    plan = sorted(
        [{"evidence": e, "priority": PRIORITY.get(e, ("P2", "persistent"))[0], "volatility": PRIORITY.get(e, ("P2", "persistent"))[1]} for e in avail],
        key=lambda x: x["priority"])
    volatile_present = [p for p in plan if p["priority"] == "P0"]
    custody_defects = []
    if not custody.get("hash_at_acquisition"):
        custody_defects.append("no hash recorded at acquisition — evidence inadmissible")
    if not custody.get("tool_provenance"):
        custody_defects.append("acquisition tool provenance not documented")
    if custody.get("write_blocked") is False:
        custody_defects.append("evidence target not write-blocked")
    severity = "critical" if custody_defects else "high" if volatile_present else "medium" if plan else "informational"
    exit_code = 2 if custody_defects else 1 if volatile_present else 0
    tl = sorted(timeline, key=lambda e: str(e.get("ts", "")))
    action = ("Fix chain of custody before analysis: " + "; ".join(custody_defects) + ". Then collect P0 volatile evidence first." if custody_defects else
              ("Collect volatile evidence now (RAM, network, processes) before it is lost, in the P0-P1-P2 order; recommended collection modifies live state and needs approval."
               if volatile_present else "Reconstruct the timeline from the preserved evidence."))
    key = [f"Case {t.get('case_id', 'n/a')}: {len(avail)} evidence source(s), {len(volatile_present)} volatile (P0), {len(custody_defects)} custody defect(s), {len(tl)} timeline event(s)"]
    key += [f"{p['priority']} {p['evidence']} (volatility {p['volatility']})" for p in plan[:6]]
    key += [f"CUSTODY DEFECT: {c}" for c in custody_defects]
    if tl:
        key.append("Timeline: " + " -> ".join(f"{e.get('ts')} {e.get('event','')[:40]}" for e in tl[:3]))
    evidence = [{"source": f"local://{rel}" if rel else "local://response/forensics/SKILL.md", "ref": "case evidence and custody record"},
                {"source": "local://response/forensics/SKILL.md", "ref": "evidence priority matrix and chain-of-custody requirements"}]
    return {"agent_slug": SLUG, "intent_type": "analyze", "action": action,
            "rationale": ("Evidence ordered by the SKILL.md volatility matrix (RAM, network, processes are P0). Chain of custody requires a hash at acquisition, documented tool "
                          "provenance and a write-blocked target; a missing one makes evidence inadmissible (critical). Timeline reconstruction is read-only; a collection step that "
                          "modifies a live system is a gated remediation_action."),
            "confidence": 0.85, "severity": severity, "key_findings": key, "evidence_references": evidence,
            "next_agents": ["incident-commander"] if volatile_present or custody_defects else [], "human_approval_required": bool(volatile_present and not custody_defects),
            "timestamp_utc": _now(), "collection_plan": plan, "custody_defects": custody_defects, "mitre_ttps": [], "affected_assets": [str(h) for h in (t.get("hosts") or [])], "_exit": exit_code}


def main() -> int:
    ap = argparse.ArgumentParser(description="USAP forensics")
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
    print(json.dumps(p, indent=2) if args.output == "json" else f"forensics: severity={p['severity']}")
    return code


if __name__ == "__main__":
    raise SystemExit(main())
