#!/usr/bin/env python3
"""endpoint-os-security_tool.py

Assesses endpoint posture per the SKILL.md: EDR coverage gaps and the MITRE
ATT&CK endpoint-indicator table (process injection, credential dumping, registry
and scheduled-task persistence, LOLBins, DLL hijack). Read-only detection.
Emits the USAP 11-field payload.

  python3 endpoint-os-security_tool.py --input endpoints.json --output json
  python3 endpoint-os-security_tool.py --output json    # no input: informational, exit 0

Input (see tests/fixtures/endpoint-os-security-input.json): endpoints[]:
{host, os, edr_installed, indicators[] (process_injection|credential_dumping|
registry_persistence|scheduled_task_abuse|lolbin_execution|dll_hijack)}.

Exit codes: 0 low; 1 high; 2 critical (credential dumping / injection). Stdlib only.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

SLUG = "endpoint-os-security"
HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parents[2]
INDICATOR = {"credential_dumping": ("critical", "T1003"), "process_injection": ("critical", "T1055"),
             "dll_hijack": ("high", "T1574.001"), "scheduled_task_abuse": ("high", "T1053.005"),
             "registry_persistence": ("high", "T1547.001"), "lolbin_execution": ("medium", "T1218")}
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
    eps = [e for e in (t.get("endpoints") or []) if isinstance(e, dict)]
    if not t or not eps:
        return {"agent_slug": SLUG, "intent_type": "detect", "action": "Supply endpoints; nothing was provided.",
                "rationale": "No endpoints supplied.", "confidence": 0.30, "severity": "informational", "key_findings": ["No endpoints supplied"],
                "evidence_references": [{"source": "local://cloud-infra/endpoint-os-security/SKILL.md", "ref": "endpoint indicators (not applied)"}],
                "next_agents": [], "human_approval_required": False, "timestamp_utc": _now(), "findings": [], "_exit": 0}
    findings: List[dict] = []
    no_edr: List[str] = []
    for e in eps:
        if not e.get("edr_installed"):
            no_edr.append(str(e.get("host")))
        for ind in [str(i).lower() for i in (e.get("indicators") or [])]:
            sev, mitre = INDICATOR.get(ind, ("medium", "T1059"))
            findings.append({"host": e.get("host"), "os": e.get("os"), "indicator": ind, "severity": sev, "mitre": mitre})
    findings.sort(key=lambda f: -SEV_RANK[f["severity"]])
    counts = {k: sum(1 for f in findings if f["severity"] == k) for k in SEV_RANK}
    severity = findings[0]["severity"] if findings else ("high" if no_edr else "informational")
    exit_code = 2 if counts["critical"] else 1 if (counts["high"] or no_edr) else 0
    action = (f"{counts['critical']} critical endpoint indicator(s) (credential dumping / injection); isolate and collect memory from "
              + ", ".join(sorted({f['host'] for f in findings if f['severity']=='critical'}))[:120] + "." if counts["critical"] else
              f"{counts['high']} high endpoint indicator(s) to triage." if counts["high"] else
              (f"{len(no_edr)} endpoint(s) with no EDR — blind spot." if no_edr else "No endpoint indicators; EDR coverage complete."))
    key = [f"{len(eps)} endpoint(s): {len(findings)} indicator(s) ({counts['critical']} critical, {counts['high']} high); {len(no_edr)} without EDR"]
    key += [f"{f['severity']} {f['host']} ({f['os']}): {f['indicator']} [{f['mitre']}]" for f in findings[:6]]
    if no_edr:
        key.append("No EDR on: " + ", ".join(no_edr[:5]))
    evidence = [{"source": f"local://{rel}" if rel else "local://cloud-infra/endpoint-os-security/SKILL.md", "ref": "endpoint telemetry"},
                {"source": "local://cloud-infra/endpoint-os-security/SKILL.md", "ref": "MITRE ATT&CK endpoint indicator table and EDR coverage"}]
    return {"agent_slug": SLUG, "intent_type": "detect", "action": action,
            "rationale": ("Each indicator is scored against the SKILL.md endpoint ATT&CK table: credential dumping and process injection are critical; persistence and DLL hijack are "
                          "high; LOLBins are medium. Endpoints without EDR are a blind spot. Read-only; host isolation is a downstream gated action."),
            "confidence": 0.85, "severity": severity, "key_findings": key, "evidence_references": evidence,
            "next_agents": (["incident-commander", "forensics"] if counts["critical"] else ["threat-hunting"] if findings else []),
            "human_approval_required": False, "timestamp_utc": _now(),
            "findings": findings, "mitre_ttps": sorted({f["mitre"] for f in findings}), "affected_assets": sorted({str(f["host"]) for f in findings}), "_exit": exit_code}


def main() -> int:
    ap = argparse.ArgumentParser(description="USAP endpoint-os-security")
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
    print(json.dumps(p, indent=2) if args.output == "json" else f"endpoint-os-security: severity={p['severity']}")
    return code


if __name__ == "__main__":
    raise SystemExit(main())
