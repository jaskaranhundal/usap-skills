#!/usr/bin/env python3
"""ot-iot-device-security_tool.py

Assesses OT/ICS/IoT devices per the SKILL.md against IEC 62443 segmentation and
the OT paradox (availability and safety first; patching only in planned windows).
Every mutating OT action requires safety review plus CISO and operations-director
approval. Read-only assessment. Emits the USAP 11-field payload.

  python3 ot-iot-device-security_tool.py --input ot.json --output json
  python3 ot-iot-device-security_tool.py --output json    # no input: informational, exit 0

Input (see tests/fixtures/ot-iot-device-security-input.json): devices[]:
{name, purdue_level (0-5), protocol (modbus|dnp3|s7|ethernet_ip|bacnet|other),
safety_critical, findings[] (it_ot_bridge|internet_exposed|default_credentials|
flat_network|unpatchable_legacy|plaintext_protocol|no_network_monitoring)}.

Exit codes: 0 low; 1 high; 2 critical (IT/OT bridge, internet-exposed OT, or a
safety-critical device with default credentials). Stdlib only.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

SLUG = "ot-iot-device-security"
HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parents[2]
FINDING = {
    "it_ot_bridge": ("critical", "IT/OT network bridge — removes the primary OT containment boundary", "Introduce a segmentation boundary (firewall/data diode) in the next window"),
    "internet_exposed": ("critical", "OT device reachable from the internet", "Remove internet reachability immediately via network path, not device change"),
    "default_credentials": ("high", "default credentials on an OT device", "Change credentials in a planned window; compensate with access control now"),
    "flat_network": ("high", "flat OT network with no zone segmentation", "Segment per the Purdue model / IEC 62443 zones"),
    "unpatchable_legacy": ("high", "unpatchable legacy device", "Wrap in compensating controls (segmentation, monitoring); do not force-patch"),
    "plaintext_protocol": ("medium", "plaintext OT protocol", "Add network monitoring; encrypt where the device supports it"),
    "no_network_monitoring": ("medium", "no passive OT network monitoring", "Deploy passive OT IDS (no active scanning of OT)"),
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
    devices = [d for d in (t.get("devices") or []) if isinstance(d, dict)]
    if not t or not devices:
        return {"agent_slug": SLUG, "intent_type": "detect", "action": "Supply OT/IoT devices; nothing was provided.",
                "rationale": "No devices supplied.", "confidence": 0.30, "severity": "informational", "key_findings": ["No devices supplied"],
                "evidence_references": [{"source": "local://cloud-infra/ot-iot-device-security/SKILL.md", "ref": "OT assessment (not applied)"}],
                "next_agents": [], "human_approval_required": False, "timestamp_utc": _now(), "findings": [], "_exit": 0}
    findings: List[dict] = []
    for d in devices:
        safety = bool(d.get("safety_critical"))
        for f in [str(x).lower() for x in (d.get("findings") or [])]:
            sev, desc, rem = FINDING.get(f, ("medium", f, "Assess against IEC 62443"))
            if f == "default_credentials" and safety:
                sev = "critical"
            findings.append({"device": d.get("name"), "purdue_level": d.get("purdue_level"), "protocol": d.get("protocol"),
                             "safety_critical": safety, "finding": f, "severity": sev, "description": desc, "remediation": rem})
    findings.sort(key=lambda f: -SEV_RANK[f["severity"]])
    counts = {k: sum(1 for f in findings if f["severity"] == k) for k in SEV_RANK}
    severity = findings[0]["severity"] if findings else "informational"
    exit_code = 2 if counts["critical"] else 1 if counts["high"] else 0
    action = (f"{counts['critical']} critical OT exposure(s); remediate via the network path, not a device change: "
              + "; ".join(f["remediation"] for f in findings if f["severity"] == "critical")[:160]
              + ". All OT changes require safety review plus CISO and operations-director approval." if counts["critical"] else
              f"{counts['high']} high OT finding(s); plan remediation for a maintenance window." if counts["high"] else
              "No OT finding above medium; sustain passive monitoring.")
    key = [f"{len(devices)} device(s): {len(findings)} finding(s) ({counts['critical']} critical, {counts['high']} high); OT paradox — availability and safety before patching"]
    key += [f"{f['severity']} {f['device']} (Purdue {f['purdue_level']}, {f['protocol']}{', safety-critical' if f['safety_critical'] else ''}): {f['description']} -> {f['remediation']}" for f in findings[:6]]
    evidence = [{"source": f"local://{rel}" if rel else "local://cloud-infra/ot-iot-device-security/SKILL.md", "ref": "OT/IoT device inventory"},
                {"source": "https://www.isa.org/standards-and-publications/isa-standards/isa-iec-62443-series-of-standards", "ref": "IEC 62443 zones and conduits"},
                {"source": "local://cloud-infra/ot-iot-device-security/SKILL.md", "ref": "OT assessment model and approval gate"}]
    return {"agent_slug": SLUG, "intent_type": "detect", "action": action,
            "rationale": ("Each finding is scored for OT: an IT/OT bridge or an internet-exposed device removes the containment boundary and is critical, as are default credentials on "
                          "a safety-critical device. Remediation favours network-path changes over device changes because OT prioritises availability and safety; every mutating OT "
                          "action requires safety review plus CISO and operations-director approval. Read-only assessment."),
            "confidence": 0.85, "severity": severity, "key_findings": key, "evidence_references": evidence,
            "next_agents": (["network-exposure"] if any(f["finding"] in ("it_ot_bridge", "internet_exposed", "flat_network") for f in findings) else []) + (["findings-tracker"] if findings else []),
            "human_approval_required": bool(counts["critical"]), "timestamp_utc": _now(),
            "approver_roles": ["safety_review", "ciso", "operations_director"] if counts["critical"] else [],
            "findings": findings, "mitre_ttps": ["T0812", "T0886"] if counts["critical"] else [], "affected_assets": sorted({str(f["device"]) for f in findings}), "_exit": exit_code}


def main() -> int:
    ap = argparse.ArgumentParser(description="USAP ot-iot-device-security")
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
    print(json.dumps(p, indent=2) if args.output == "json" else f"ot-iot-device-security: severity={p['severity']}")
    return code


if __name__ == "__main__":
    raise SystemExit(main())
