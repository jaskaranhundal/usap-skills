#!/usr/bin/env python3
"""network-exposure_tool.py

Analyses a normalised network descriptor per the SKILL.md 8-step procedure:
port/service risk, firewall-rule risk, segmentation gaps, unencrypted services,
and egress IoC signals (beaconing, DNS tunnelling, large transfers, C2).
Read-only detection; firewall changes require human authorization. Emits the
USAP 11-field payload.

  python3 network-exposure_tool.py --input net.json --output json
  python3 network-exposure_tool.py --output json     # no input: informational, exit 0

Input (see tests/fixtures/network-exposure-input.json): source, open_ports[]:
{host, port, service, exposure (internet|dmz|internal)}, firewall_rules[]:
{id, source, dest, port, action}, segmentation{db_reachable_from_internet,
admin_without_jump, ot_bridged_to_it, dmz_unrestricted_egress}, egress_iocs[]:
{type (beaconing|dns_tunneling|large_transfer|c2), detail}.

Exit codes: 0 low; 1 high; 2 critical. Stdlib only.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

SLUG = "network-exposure"
HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parents[2]
ADMIN_PORTS = {22: "SSH", 3389: "RDP", 5985: "WinRM"}
DB_PORTS = {5432: "PostgreSQL", 3306: "MySQL", 1433: "MSSQL", 27017: "MongoDB", 6379: "Redis", 9200: "Elasticsearch"}
PLAINTEXT = {21: "FTP", 23: "Telnet", 80: "HTTP", 110: "POP3", 143: "IMAP", 161: "SNMP"}
SEV_RANK = {"critical": 4, "high": 3, "medium": 2, "low": 1, "informational": 0}
IOC_SEV = {"c2": "critical", "beaconing": "high", "dns_tunneling": "high", "large_transfer": "high"}


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def analyse(t: dict, input_path: Optional[str] = None) -> Dict[str, Any]:
    rel = None
    if input_path:
        try:
            rel = Path(input_path).resolve().relative_to(REPO_ROOT).as_posix()
        except ValueError:
            rel = None
    ports = [p for p in (t.get("open_ports") or []) if isinstance(p, dict)]
    rules = [r for r in (t.get("firewall_rules") or []) if isinstance(r, dict)]
    seg = t.get("segmentation") or {}
    iocs = [i for i in (t.get("egress_iocs") or []) if isinstance(i, dict)]
    if not t or not (ports or rules or seg or iocs):
        return {"agent_slug": SLUG, "intent_type": "detect", "action": "Supply a network descriptor; nothing was provided.",
                "rationale": "No network data supplied; no exposure analysis.", "confidence": 0.30, "severity": "informational",
                "key_findings": ["No network data supplied"], "evidence_references": [{"source": "local://detection/network-exposure/SKILL.md", "ref": "classification tables (not applied)"}],
                "next_agents": [], "human_approval_required": False, "timestamp_utc": _now(), "findings": [], "_exit": 0}
    findings: List[dict] = []
    for p in ports:
        port = int(p.get("port") or 0); exp = str(p.get("exposure", "internal")).lower(); host = p.get("host", "?")
        internet = exp in ("internet", "dmz")
        if port in ADMIN_PORTS and internet:
            findings.append({"type": "port_exposure", "severity": "critical", "detail": f"{ADMIN_PORTS[port]} ({port}) exposed on {host} ({exp})", "remediation": "Restrict to VPN/bastion or use SSM"})
        elif port in DB_PORTS and internet:
            findings.append({"type": "port_exposure", "severity": "critical", "detail": f"{DB_PORTS[port]} ({port}) exposed on {host} ({exp})", "remediation": "Move the database off any internet-reachable path"})
        elif port in PLAINTEXT and internet:
            findings.append({"type": "unencrypted_service", "severity": "high", "detail": f"plaintext {PLAINTEXT[port]} ({port}) on {host} ({exp})", "remediation": "Enforce TLS / disable the plaintext service"})
    for r in rules:
        if str(r.get("action", "")).lower() == "allow" and str(r.get("source", "")) in ("0.0.0.0/0", "any", "*") and str(r.get("dest", "")).lower() in ("internal", "any", "*"):
            findings.append({"type": "firewall_rule", "severity": "high", "detail": f"rule {r.get('id')} allows any -> {r.get('dest')} on {r.get('port')}", "remediation": "Scope the source CIDR and destination"})
    seg_map = {"db_reachable_from_internet": ("critical", "database tier reachable from the internet/DMZ without the app tier"),
               "admin_without_jump": ("high", "admin network reachable from workstations without a jump server"),
               "ot_bridged_to_it": ("critical", "OT/IoT network bridged to corporate IT"),
               "dmz_unrestricted_egress": ("high", "DMZ has unrestricted egress to internal subnets")}
    for k, (sev, desc) in seg_map.items():
        if seg.get(k):
            findings.append({"type": "segmentation_gap", "severity": sev, "detail": desc, "remediation": "Introduce the missing segmentation boundary"})
    for i in iocs:
        kind = str(i.get("type", "")).lower()
        findings.append({"type": "egress_ioc", "severity": IOC_SEV.get(kind, "medium"), "detail": f"{kind}: {i.get('detail', '')}", "remediation": "Block the destination and hunt the source host"})
    findings.sort(key=lambda f: -SEV_RANK[f["severity"]])
    counts = {k: sum(1 for f in findings if f["severity"] == k) for k in SEV_RANK}
    severity = findings[0]["severity"] if findings else "informational"
    exit_code = 2 if severity == "critical" else 1 if severity in ("high", "medium") else 0
    action = (f"{counts['critical']} critical and {counts['high']} high network finding(s); "
              + (findings[0]["remediation"] + " first." if findings else "")) if findings else "No network exposure against the classification tables."
    key = [f"{t.get('source', 'network')}: {len(ports)} port(s), {len(rules)} rule(s), {len(iocs)} egress IoC(s); {len(findings)} finding(s) ({counts['critical']} critical, {counts['high']} high)"]
    key += [f"{f['severity']} [{f['type']}] {f['detail']} -> {f['remediation']}" for f in findings[:7]]
    evidence = [{"source": f"local://{rel}" if rel else "local://detection/network-exposure/SKILL.md", "ref": "network descriptor"},
                {"source": "local://detection/network-exposure/references/classification-tables.md", "ref": "port/service, firewall, segmentation tables"}]
    return {"agent_slug": SLUG, "intent_type": "detect", "action": action,
            "rationale": ("Each open port classified against admin/database/plaintext tables with exposure context, firewall rules against the any->internal pattern, segmentation "
                          "against the four boundary questions, and egress against the beaconing/DNS-tunnelling/large-transfer/C2 signals. Read-only; firewall changes need authorization."),
            "confidence": 0.85, "severity": severity, "key_findings": key, "evidence_references": evidence,
            "next_agents": (["vulnerability-management"] if any(f["type"] == "port_exposure" for f in findings) else []) + (["threat-hunting"] if any(f["type"] == "egress_ioc" for f in findings) else []),
            "human_approval_required": False, "timestamp_utc": _now(),
            "findings": findings, "mitre_ttps": sorted({"T1046" for f in findings if f["type"] == "port_exposure"} | {"T1071.004" for f in findings if "dns_tunneling" in f["detail"]} | {"T1048" for f in findings if "large_transfer" in f["detail"]} | {"T1571" for f in findings if "beaconing" in f["detail"] or f["detail"].startswith("c2")}),
            "affected_assets": sorted({str(p.get("host")) for p in ports if p.get("host")}), "_exit": exit_code}


def main() -> int:
    ap = argparse.ArgumentParser(description="USAP network-exposure")
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
    print(json.dumps(p, indent=2) if args.output == "json" else f"network-exposure: severity={p['severity']}")
    return code


if __name__ == "__main__":
    raise SystemExit(main())
