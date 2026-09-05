#!/usr/bin/env python3
"""containment-advisor_tool.py

Turns one confirmed-threat SecurityFact into containment INTENT BLOCKS per the
SKILL.md strategy table: primary and secondary strategy, mutating category,
blast radius, production impact, reversibility, urgency, approver roles, and
attack-path prerequisite validation. Never emits a command; execution is the
tool-execution-broker's job after human approval. Emits the USAP 11-field
payload.

  python3 containment-advisor_tool.py --input fact.json --output json
  python3 containment-advisor_tool.py --output json      # no input: informational, exit 0

Input (see tests/fixtures/containment-advisor-input.json): event_id, event_type
(strategy-table key or alias), severity, finding, raw_payload{affected_hosts[],
affected_accounts[], target_resource, active, spreading, production_service,
service_tier (1|2|3), claimed_attack_paths[]: {target, route_confirmed,
credentials_confirmed}}, context{environment}.

Exit codes: 0 scheduled or read-only; 1 urgent; 2 immediate. Stdlib only.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

SLUG = "containment-advisor"
HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parents[2]

# SKILL.md Containment Strategy Selection: type -> (primary, secondary, category, technique)
STRATEGY = {
    "credential_exposure": ("Revoke and rotate the affected credentials", "Audit access logs for active use of the credential", "credential_operation", "T1078"),
    "iam_anomaly": ("Revoke active sessions for the affected principal", "Apply an IP restriction or MFA requirement to the principal", "credential_operation", "T1078.004"),
    "network_intrusion": ("Block the source IP at the perimeter or WAF", "Isolate the affected host from its network segment", "network_change", "T1190"),
    "malware_detected": ("Isolate the endpoint from the network", "Preserve a disk image for forensics before any cleanup", "network_change", "T1204"),
    "ransomware": ("Isolate every affected system immediately", "Disable network access from the affected segment", "network_change", "T1486"),
    "data_exfiltration": ("Block the exfiltration destination at the firewall", "Revoke the credentials used on the exfiltration path", "network_change", "T1041"),
    "insider_threat": ("Disable the user account and terminate its sessions", "Preserve audit logs under legal hold", "credential_operation", "T1530"),
    "supply_chain": ("Block or quarantine the affected package or image", "Scan every system that uses the package", "remediation_action", "T1195"),
    "secret_in_repo": ("Revoke the exposed credential", "Restrict repository access and remove the secret from history", "credential_operation", "T1552.001"),
    "container_escape": ("Terminate the affected pod or container", "Isolate the node from the cluster network", "remediation_action", "T1611"),
}
ALIASES = {"secret_exposure": "secret_in_repo", "credential_compromise": "credential_exposure", "privilege_escalation": "iam_anomaly",
           "endpoint_compromise": "malware_detected", "malware_execution": "malware_detected", "data_breach": "data_exfiltration",
           "supply_chain_attack": "supply_chain", "supply_chain_event": "supply_chain", "unauthorized_access": "network_intrusion"}
# Reversibility per action class (SKILL.md scope assessment)
REVERSIBILITY = {"credential_operation": "hours", "network_change": "immediate", "remediation_action": "immediate"}
SEV_RANK = {"critical": 4, "high": 3, "medium": 2, "low": 1, "informational": 0}


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _impact(category: str, ttype: str, rp: dict) -> str:
    tier = int(rp.get("service_tier") or 3)
    prod = bool(rp.get("production_service"))
    if not prod:
        return "none"
    if ttype == "ransomware" or (category in ("network_change", "remediation_action") and tier == 1):
        return "outage"
    if category == "credential_operation" and tier <= 2:
        return "degraded"
    return "degraded" if tier == 1 else "none"


def _urgency(sev: str, rp: dict) -> str:
    if rp.get("spreading") or (rp.get("active") and sev == "critical"):
        return "immediate"
    if rp.get("active") or sev in ("critical", "high"):
        return "urgent"
    return "scheduled"


def _block(intent: str, category: str, target: str, blast: str, impact: str, urgency: str) -> dict:
    return {"containment_intent": intent, "intent_type": "mutating", "mutating_category": category, "target_resource": target,
            "blast_radius": blast, "production_impact": impact, "reversibility": REVERSIBILITY[category], "urgency": urgency,
            "requires_approval": True, "approver_roles": ["soc_lead", "ciso"], "executor": "tool-execution-broker"}


def analyse(fact: dict, input_path: Optional[str] = None) -> Dict[str, Any]:
    if not fact:
        return {"agent_slug": SLUG, "intent_type": "advise", "action": "Supply a confirmed-threat SecurityFact; no event was provided.",
                "rationale": "No event content supplied; no containment reasoned. Absence of input, never a clean result.", "confidence": 0.30,
                "severity": "informational", "key_findings": ["No SecurityFact supplied"],
                "evidence_references": [{"source": "local://response/containment-advisor/SKILL.md", "ref": "strategy table (not applied: no input)"}],
                "next_agents": [], "human_approval_required": False, "timestamp_utc": _now(), "containment": {"intents": []}}
    rp = fact.get("raw_payload") or {}
    et = str(fact.get("event_type", "")).lower()
    ttype = et if et in STRATEGY else ALIASES.get(et)
    sev = str(fact.get("severity", "medium")).lower()
    hosts = [str(h) for h in (rp.get("affected_hosts") or [])]
    accounts = [str(a) for a in (rp.get("affected_accounts") or [])]
    target = str(rp.get("target_resource") or (hosts[0] if hosts else accounts[0] if accounts else "unspecified"))
    blast = f"{len(hosts)} host(s), {len(accounts)} account(s)" + (f"; production service {rp.get('production_service')}" if rp.get("production_service") else "")

    if not ttype:
        # Unknown threat type: investigation only, nothing mutating.
        intents: List[dict] = []
        readonly = {"containment_intent": "Investigate and scope before containment: threat type not in the strategy table", "intent_type": "read_only",
                    "mutating_category": None, "target_resource": target, "blast_radius": blast, "production_impact": "none",
                    "reversibility": "immediate", "urgency": _urgency(sev, rp), "requires_approval": False, "approver_roles": []}
        primary, secondary, category, technique = None, None, None, None
    else:
        p, s, category, technique = STRATEGY[ttype]
        urgency = _urgency(sev, rp)
        primary = _block(p, category, target, blast, _impact(category, ttype, rp), urgency)
        sec_cat = "credential_operation" if "credential" in s.lower() or "account" in s.lower() else ("network_change" if "isolat" in s.lower() or "network" in s.lower() else "remediation_action")
        if "audit" in s.lower() or "preserve" in s.lower() or "scan" in s.lower():
            secondary = {"containment_intent": s, "intent_type": "read_only", "mutating_category": None, "target_resource": target, "blast_radius": "none",
                         "production_impact": "none", "reversibility": "immediate", "urgency": urgency, "requires_approval": False, "approver_roles": []}
        else:
            secondary = _block(s, sec_cat, target, blast, _impact(sec_cat, ttype, rp), "urgent" if urgency == "immediate" else urgency)
        intents = [primary, secondary]
        readonly = None

    # Attack path prerequisite validation
    paths: List[dict] = []
    for cp in rp.get("claimed_attack_paths") or []:
        if not isinstance(cp, dict):
            continue
        if cp.get("credentials_confirmed"):
            label = "CONFIRMED"
        elif cp.get("route_confirmed"):
            label = "PLAUSIBLE"
        else:
            label = "PREREQUISITE_UNVERIFIED"
        paths.append({"target": cp.get("target"), "label": label, "prerequisite": cp.get("prerequisite", "credentials or access vector to the target control plane")})

    urgency = (primary or readonly)["urgency"]
    severity = "critical" if urgency == "immediate" else "high" if urgency == "urgent" else "medium"
    if primary:
        action = (f"Request approval (soc_lead, ciso) for: {primary['containment_intent']} on {target} "
                  f"[{primary['mutating_category']}, {urgency}, production impact {primary['production_impact']}, reversibility {primary['reversibility']}]. "
                  f"Then: {secondary['containment_intent']}.")
    else:
        action = readonly["containment_intent"] + f"; event_type '{et}' has no strategy entry."
    key = [f"{fact.get('event_id', 'event')}: threat type {ttype or 'unknown (' + et + ')'}, severity {sev}, urgency {urgency}, blast radius {blast}"]
    for i in intents or [readonly]:
        key.append(f"{i['intent_type']}{' / ' + i['mutating_category'] if i.get('mutating_category') else ''}: {i['containment_intent']} -> impact {i['production_impact']}, reversibility {i['reversibility']}, approval {i['requires_approval']}")
    for pth in paths:
        key.append(f"Attack path to {pth['target']}: {pth['label']} ({pth['prerequisite']})")
    if not paths and rp.get("claimed_attack_paths") is None and ttype in ("network_intrusion", "iam_anomaly"):
        key.append("No secondary attack paths asserted; lateral movement claims require prerequisite validation before being reported")

    rel = None
    if input_path:
        try:
            rel = Path(input_path).resolve().relative_to(REPO_ROOT).as_posix()
        except ValueError:
            rel = None
    evidence = [{"source": f"local://{rel}" if rel else "local://response/containment-advisor/SKILL.md", "ref": str(fact.get("event_id", "fact")), "quote": str(fact.get("finding", ""))[:160]},
                {"source": "local://response/containment-advisor/SKILL.md", "ref": "containment strategy table, scope assessment, prerequisite validation"}]
    if technique:
        evidence.append({"source": f"https://attack.mitre.org/techniques/{technique.replace('.', '/')}/", "ref": technique})

    cred = float(fact.get("source_credibility") or 0.8)
    conf = round(min(0.95, cred * (0.9 if ttype else 0.55) - (0.1 if not hosts and not accounts and not rp.get("target_resource") else 0)), 2)

    return {
        "agent_slug": SLUG, "intent_type": "respond" if primary else "advise", "action": action,
        "rationale": (f"Strategy selected from the SKILL.md table for {ttype or 'an unlisted type'}; urgency from active/spreading flags and severity; production impact from the "
                      f"service tier and action class; reversibility by mutating category. Every state-changing step is an intent block with requires_approval true and "
                      f"approver roles soc_lead and ciso; no command syntax is emitted. Attack paths are labelled CONFIRMED, PLAUSIBLE or PREREQUISITE_UNVERIFIED."),
        "confidence": conf, "severity": severity, "key_findings": key, "evidence_references": evidence,
        "next_agents": (["forensics"] if ttype in ("malware_detected", "ransomware", "insider_threat") else []) + (["compliance-mapping"] if ttype in ("data_exfiltration", "ransomware", "credential_exposure") else []),
        "human_approval_required": bool(primary), "timestamp_utc": _now(),
        "containment": {"threat_type": ttype, "urgency": urgency, "blast_radius": blast, "intents": intents or [readonly], "attack_paths": paths,
                        "approver_roles": ["soc_lead", "ciso"] if primary else []},
        "mutating_category": primary["mutating_category"] if primary else None, "approver_roles": ["soc_lead", "ciso"] if primary else [],
        "mitre_ttps": [technique] if technique else [], "affected_assets": hosts + accounts,
    }


def _exit(p: dict) -> int:
    return {"immediate": 2, "urgent": 1}.get((p.get("containment") or {}).get("urgency"), 0)


def main() -> int:
    ap = argparse.ArgumentParser(description="USAP containment-advisor: containment intent blocks for a confirmed threat")
    ap.add_argument("--input"); ap.add_argument("--output", choices=["json", "text"], default="text")
    args = ap.parse_args()
    if args.input:
        try:
            fact = json.loads(Path(args.input).read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            print(f"error: cannot read --input: {exc}", file=sys.stderr); return 2
    else:
        raw = "" if sys.stdin.isatty() else sys.stdin.read()
        try:
            fact = json.loads(raw) if raw.strip() else {}
        except json.JSONDecodeError:
            fact = {}
    p = analyse(fact, args.input)
    if args.output == "json":
        print(json.dumps(p, indent=2))
    else:
        print(f"containment-advisor: urgency={p['containment']['urgency']} severity={p['severity']}")
        for f in p["key_findings"]:
            print(f"  - {f}")
    return _exit(p)


if __name__ == "__main__":
    raise SystemExit(main())
