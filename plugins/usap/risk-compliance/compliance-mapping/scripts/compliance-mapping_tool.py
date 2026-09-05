#!/usr/bin/env python3
"""compliance-mapping_tool.py

Maps one incident to the regulatory frameworks it triggers per the SKILL.md
trigger matrix, computes notification deadlines from the awareness timestamp,
maps technical indicators to failed controls, and assesses materiality.
Read-only: it never files anything. Emits the USAP 11-field payload.

  python3 compliance-mapping_tool.py --input incident.json --output json
  python3 compliance-mapping_tool.py --output json      # no input: informational, exit 0

Input (see tests/fixtures/compliance-mapping-input.json): incident_id,
incident_type, awareness_timestamp_utc, confirmed_breach, records_affected,
data_types[] (pii|phi|cardholder|credentials|none), data_subjects[] (eu|california|us|other),
entity_scope[] (nis2_essential|nis2_important|pci_merchant|hipaa_covered|soc2_service_org|iso27001_certified),
indicators[] (secret_in_source|mfa_not_enforced|overprivileged_identity|data_exfiltrated|no_ir_plan_executed|evidence_chain_incomplete)

Exit codes: 0 no notification clock; 1 a 72-hour or longer clock is running;
2 a 24-hour or immediate clock is running. Stdlib only.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

SLUG = "compliance-mapping"
HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parents[2]

# SKILL.md Incident-to-Framework Trigger Matrix (data-type conditions applied in code)
TRIGGERS = {
    "credential_compromise": ["GDPR", "CCPA", "HIPAA", "PCI-DSS"],
    "data_exfiltration": ["GDPR", "CCPA", "HIPAA", "PCI-DSS", "NIS2"],
    "unauthorized_access": ["GDPR", "CCPA"],
    "ransomware": ["GDPR", "NIS2", "PCI-DSS", "HIPAA"],
    "privilege_escalation": ["SOC 2", "ISO 27001"],
    "supply_chain_attack": ["NIS2", "ISO 27001"],
    "insider_threat": ["GDPR", "SOC 2", "ISO 27001"],
    "misconfiguration": ["GDPR", "CCPA"],
}
# Notification Deadline Calculator: framework -> [(label, hours or None, recipient)]
DEADLINES = {
    "GDPR": [("GDPR Art 33", 72, "Supervisory authority"), ("GDPR Art 34", None, "Affected individuals, without undue delay, if high risk")],
    "NIS2": [("NIS2 early warning", 24, "National CSIRT or competent authority"), ("NIS2 full notification", 72, "National CSIRT or competent authority"), ("NIS2 interim report", 24 * 30, "National CSIRT or competent authority")],
    "PCI-DSS": [("PCI-DSS", 0, "Acquiring bank and card brands")],
    "HIPAA": [("HIPAA Breach Notification Rule", 24 * 60, "HHS and affected individuals")],
    "CCPA": [("CCPA", 24 * 45, "Affected California residents")],
    "SOC 2": [], "ISO 27001": [],
}
CONTROL_FAILURES = {
    "secret_in_source": ("Secrets management control", ["ISO 27001 A.10.1", "PCI-DSS Req 8"]),
    "mfa_not_enforced": ("Authentication control", ["SOC 2 CC6.1", "ISO 27001 A.9.4", "PCI-DSS Req 8.3"]),
    "overprivileged_identity": ("Access control", ["ISO 27001 A.9.2", "SOC 2 CC6.3", "PCI-DSS Req 7"]),
    "data_exfiltrated": ("Data loss prevention", ["GDPR Art 32", "ISO 27001 A.13"]),
    "no_ir_plan_executed": ("Incident management", ["ISO 27001 A.16.1", "SOC 2 CC7"]),
    "evidence_chain_incomplete": ("Audit logging", ["PCI-DSS Req 10", "ISO 27001 A.12.4"]),
}
SOURCES = {"GDPR": "https://eur-lex.europa.eu/eli/reg/2016/679/oj", "NIS2": "https://eur-lex.europa.eu/eli/dir/2022/2555/oj",
           "PCI-DSS": "https://www.pcisecuritystandards.org/", "HIPAA": "https://www.hhs.gov/hipaa/for-professionals/breach-notification/index.html",
           "CCPA": "https://oag.ca.gov/privacy/ccpa", "SOC 2": "https://www.aicpa-cima.com/topic/audit-assurance/audit-and-assurance-greater-than-soc-2",
           "ISO 27001": "https://www.iso.org/standard/27001"}


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _parse(ts: Optional[str]) -> datetime:
    try:
        return datetime.fromisoformat(str(ts).replace("Z", "+00:00")).astimezone(timezone.utc)
    except (ValueError, TypeError):
        return datetime.now(timezone.utc)


def analyse(inc: dict, input_path: Optional[str] = None) -> Dict[str, Any]:
    if not inc:
        return {"agent_slug": SLUG, "intent_type": "report", "action": "Supply an incident descriptor; nothing was provided.",
                "rationale": "No incident supplied; no framework mapped. Absence of input, never a clean result.", "confidence": 0.30,
                "severity": "informational", "key_findings": ["No incident supplied"],
                "evidence_references": [{"source": "local://risk-compliance/compliance-mapping/SKILL.md", "ref": "trigger matrix (not applied: no input)"}],
                "next_agents": [], "human_approval_required": False, "timestamp_utc": _now(), "compliance_summary": {}}
    itype = str(inc.get("incident_type", "")).lower()
    aware = _parse(inc.get("awareness_timestamp_utc"))
    data = {str(d).lower() for d in (inc.get("data_types") or [])}
    subjects = {str(s).lower() for s in (inc.get("data_subjects") or [])}
    scope = {str(s).lower() for s in (inc.get("entity_scope") or [])}
    indicators = [str(i).lower() for i in (inc.get("indicators") or [])]
    regulated = bool(data & {"pii", "phi", "cardholder"})

    candidates = list(TRIGGERS.get(itype, []))
    if itype in ("credential_compromise", "unauthorized_access", "misconfiguration") and not regulated and "credentials" not in data:
        candidates = [c for c in candidates if c in ("SOC 2", "ISO 27001")] or ["ISO 27001"]
    triggered: List[str] = []
    reasons: Dict[str, str] = {}
    for fw in candidates:
        if fw == "GDPR" and ("eu" in subjects or "pii" in data):
            triggered.append(fw); reasons[fw] = "personal data of EU residents involved or possible"
        elif fw == "CCPA" and "california" in subjects:
            triggered.append(fw); reasons[fw] = "California residents' personal information"
        elif fw == "HIPAA" and ("phi" in data or "hipaa_covered" in scope):
            triggered.append(fw); reasons[fw] = "protected health information or covered entity"
        elif fw == "PCI-DSS" and ("cardholder" in data or "pci_merchant" in scope):
            triggered.append(fw); reasons[fw] = "cardholder data environment"
        elif fw == "NIS2" and (scope & {"nis2_essential", "nis2_important"}):
            triggered.append(fw); reasons[fw] = "NIS2 essential or important entity"
        elif fw == "SOC 2" and "soc2_service_org" in scope:
            triggered.append(fw); reasons[fw] = "control failure at a service organisation"
        elif fw == "ISO 27001" and ("iso27001_certified" in scope or not scope):
            triggered.append(fw); reasons[fw] = "ISMS incident management obligation"
    if itype and not triggered:
        triggered, reasons = ["ISO 27001"], {"ISO 27001": "conservative default: systematic response and post-incident review"}

    deadlines: List[dict] = []
    for fw in triggered:
        for label, hours, who in DEADLINES.get(fw, []):
            deadlines.append({"framework": fw, "obligation": label, "hours": hours,
                              "deadline_utc": (aware + timedelta(hours=hours)).strftime("%Y-%m-%dT%H:%M:%SZ") if hours is not None else "without undue delay",
                              "recipient": who})
    failures = [{"indicator": i, "failed_control": CONTROL_FAILURES[i][0], "references": CONTROL_FAILURES[i][1]} for i in indicators if i in CONTROL_FAILURES]

    confirmed = bool(inc.get("confirmed_breach"))
    records = int(inc.get("records_affected") or 0)
    if confirmed and (regulated or records > 0):
        materiality = "material: confirmed breach involving regulated data; notification obligations apply"
    elif confirmed:
        materiality = "confirmed incident without regulated data: document; external notification only where NIS2 or PCI applies"
    elif regulated:
        materiality = "not yet confirmed but regulated data possibly involved: treat clocks as running from awareness (conservative)"
    else:
        materiality = "assess: no confirmed breach and no regulated data indicated"

    shortest = min((d["hours"] for d in deadlines if d["hours"] is not None), default=None)
    severity = "critical" if shortest is not None and shortest <= 24 and (confirmed or regulated) else "high" if shortest is not None and shortest <= 72 and (confirmed or regulated) else "medium" if triggered and (deadlines or failures) else "low" if triggered else "informational"
    urgent = [d for d in sorted(deadlines, key=lambda d: (d["hours"] if d["hours"] is not None else 10**6)) if d["hours"] is not None][:3]
    action = ("Prepare notifications for human filing: " + "; ".join(f"{d['obligation']} to {d['recipient']} by {d['deadline_utc']}" for d in urgent) + ". "
              if urgent else "No external notification clock identified; ") + f"Materiality: {materiality}."

    key = [f"{inc.get('incident_id', 'incident')}: {itype or 'unknown type'} at {aware.strftime('%Y-%m-%dT%H:%M:%SZ')} triggers {', '.join(triggered) or 'no framework'}; data {', '.join(sorted(data)) or 'none stated'}; {records} record(s)"]
    key += [f"{fw}: {reasons[fw]}" for fw in triggered]
    key += [f"Deadline {d['obligation']}: {d['deadline_utc']} ({d['recipient']})" for d in deadlines[:6]]
    key += [f"Control failure: {f['failed_control']} ({', '.join(f['references'])})" for f in failures]
    key.append(f"Materiality: {materiality}")

    rel = None
    if input_path:
        try:
            rel = Path(input_path).resolve().relative_to(REPO_ROOT).as_posix()
        except ValueError:
            rel = None
    evidence = [{"source": f"local://{rel}" if rel else "local://risk-compliance/compliance-mapping/SKILL.md", "ref": str(inc.get("incident_id", "incident")), "quote": f"{itype}; data types {', '.join(sorted(data)) or 'none'}"}]
    evidence += [{"source": SOURCES[fw], "ref": fw, "quote": reasons[fw]} for fw in triggered if fw in SOURCES]
    evidence.append({"source": "local://risk-compliance/compliance-mapping/SKILL.md", "ref": "trigger matrix, deadline calculator, control failure classification"})

    conf, factors = 0.60, ["base 0.60"]
    if data:
        conf += 0.15; factors.append("data types stated (+0.15)")
    if scope:
        conf += 0.10; factors.append("entity scope stated (+0.10)")
    if inc.get("awareness_timestamp_utc"):
        conf += 0.05; factors.append("awareness timestamp supplied (+0.05)")
    conf = round(min(conf, 0.92), 2)

    return {
        "agent_slug": SLUG, "intent_type": "report", "action": action,
        "rationale": (f"Frameworks from the SKILL.md trigger matrix filtered by the data types and entity scope stated in the incident (never assumed); deadlines from the "
                      f"awareness timestamp; control failures from the indicator table; materiality from confirmation status and regulated-data involvement. "
                      f"Read-only: notifications are drafted for a human to file. Confidence factors: {', '.join(factors)}."),
        "confidence": conf, "severity": severity, "key_findings": key, "evidence_references": evidence,
        "next_agents": (["ciso-brief-generator"] if severity in ("critical", "high") else []) + (["findings-tracker"] if failures else []),
        "human_approval_required": False, "timestamp_utc": _now(),
        "compliance_summary": {"incident_type": itype, "frameworks_triggered": triggered, "trigger_reasons": reasons, "notification_deadlines": deadlines,
                               "control_failures": failures, "materiality": materiality, "shortest_clock_hours": shortest},
        "mitre_ttps": [], "affected_assets": [inc.get("system")] if inc.get("system") else [],
    }


def _exit(p: dict) -> int:
    return {"critical": 2, "high": 1}.get(p["severity"], 0)


def main() -> int:
    ap = argparse.ArgumentParser(description="USAP compliance-mapping: regulatory triggers and deadlines for one incident")
    ap.add_argument("--input"); ap.add_argument("--output", choices=["json", "text"], default="text")
    args = ap.parse_args()
    if args.input:
        try:
            inc = json.loads(Path(args.input).read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            print(f"error: cannot read --input: {exc}", file=sys.stderr); return 2
    else:
        raw = "" if sys.stdin.isatty() else sys.stdin.read()
        try:
            inc = json.loads(raw) if raw.strip() else {}
        except json.JSONDecodeError:
            inc = {}
    p = analyse(inc, args.input)
    if args.output == "json":
        print(json.dumps(p, indent=2))
    else:
        print(f"compliance-mapping: severity={p['severity']} frameworks={p['compliance_summary'].get('frameworks_triggered')}")
        for f in p["key_findings"]:
            print(f"  - {f}")
    return _exit(p)


if __name__ == "__main__":
    raise SystemExit(main())
