#!/usr/bin/env python3
"""attack-surface-management_tool.py

Classifies a discovery snapshot of external assets against the SKILL.md
Reasoning Procedure: exposure scoring, certificate expiry thresholds,
subdomain-takeover indicators, admin-interface risk, shadow IT, trend versus
the previous snapshot, and SLA assignment. Emits the USAP 11-field payload.

  python3 attack-surface-management_tool.py --input snapshot.json --output json
  python3 attack-surface-management_tool.py --output json     # no input: informational, exit 0

Input (see tests/fixtures/attack-surface-management-input.json):
  organization, scan_utc, seed_scope{domains, asns, cloud_accounts},
  approved_inventory[], previous_snapshot{internet_facing_count, asset_ids[]},
  assets[]: id, type (domain|ip|cloud_resource|service|api|admin_interface),
    name, exposure (internet_facing|cloud_perimeter|partner|internal|isolated|unknown),
    verified_by (tcp_connect|http_get|none), ports[], service, auth_required,
    tls{expires_in_days, wildcard}, cname_target, cname_status
    (ok|nxdomain|404|available|dangling), in_inventory, discovery_source, first_seen_utc

Exit codes: 0 nothing above medium; 1 high findings; 2 critical findings.
Discovery only: never modifies, decommissions or probes anything. Stdlib only.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

SLUG = "attack-surface-management"
HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parents[2]

# references/classification-tables.md: Exposure Scoring Matrix
EXPOSURE_MULTIPLIER = {"internet_facing": 3.0, "cloud_perimeter": 2.0, "partner": 1.5, "internal": 0.8, "isolated": 0.2, "unknown": 1.0}
# Admin Interface Risk Classification
ADMIN_RISK = {"jenkins": "critical", "gitlab": "critical", "kubernetes_dashboard": "critical", "aws_console": "critical",
              "elasticsearch": "critical", "redis": "critical", "mongodb": "critical", "jupyter": "critical", "grafana": "high"}
TAKEOVER_STATUS = {"nxdomain": "critical", "404": "critical", "available": "critical", "dangling": "high"}
SEV_RANK = {"critical": 4, "high": 3, "medium": 2, "low": 1, "informational": 0}
BASE_SCORE = {"critical": 30, "high": 20, "medium": 10, "low": 5}
SLA_HOURS = {"critical": 24, "high": 24 * 7, "medium": 24 * 30, "low": 24 * 30}
MITRE = {"admin_interface": "T1133", "takeover": "T1584.001", "certificate": "T1608.003", "shadow_it": "T1133", "exposure": "T1595"}


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _parse(ts: Optional[str]) -> datetime:
    if ts:
        try:
            return datetime.fromisoformat(ts.replace("Z", "+00:00")).astimezone(timezone.utc)
        except ValueError:
            pass
    return datetime.now(timezone.utc)


def _finding(asset: dict, kind: str, sev: str, title: str, action: str, scan: datetime, cascade: List[str]) -> dict:
    exposure = asset.get("exposure", "unknown")
    return {
        "asset_id": asset.get("id"), "asset": asset.get("name"), "asset_type": asset.get("type"), "kind": kind,
        "severity": sev, "exposure_class": exposure, "verified_by": asset.get("verified_by", "none"),
        "risk_score": round(BASE_SCORE.get(sev, 0) * EXPOSURE_MULTIPLIER.get(exposure, 1.0), 1),
        "title": title, "recommended_action": action,
        "sla_deadline_utc": (scan + timedelta(hours=SLA_HOURS[sev])).strftime("%Y-%m-%dT%H:%M:%SZ") if sev in SLA_HOURS else None,
        "discovery_source": asset.get("discovery_source"), "first_seen_utc": asset.get("first_seen_utc"),
        "cascade_to": cascade, "mitre_technique": MITRE.get(kind),
    }


def analyse(target: dict, input_path: Optional[str] = None) -> Dict[str, Any]:
    org = target.get("organization", "unknown-org")
    scan = _parse(target.get("scan_utc"))
    assets = [a for a in (target.get("assets") or []) if isinstance(a, dict)]
    inventory = set(target.get("approved_inventory") or [])
    prev = target.get("previous_snapshot") or {}
    findings: List[dict] = []
    unverified: List[str] = []

    for a in assets:
        name = a.get("name", a.get("id", "?"))
        exposure = str(a.get("exposure", "unknown"))
        verified = str(a.get("verified_by", "none")) != "none"
        if exposure == "internet_facing" and not verified:
            # MUST NOT infer exposure from the name; downgrade to unknown until probed.
            a = {**a, "exposure": "unknown"}
            unverified.append(name)
        internet = a.get("exposure") == "internet_facing"
        in_inv = bool(a.get("in_inventory", name in inventory or a.get("id") in inventory))

        svc = str(a.get("service") or "").lower().replace(" ", "_").replace("-", "_")
        if a.get("type") == "admin_interface" or svc in ADMIN_RISK:
            base = ADMIN_RISK.get(svc, "high")
            if internet and not a.get("auth_required", True):
                findings.append(_finding(a, "admin_interface", "critical", f"{svc or 'admin interface'} on {name} reachable from the internet without authentication",
                                         "Remove from the internet or put behind SSO within 24 hours; then rotate any credential it exposes.", scan, ["vulnerability-management"]))
            elif internet:
                findings.append(_finding(a, "admin_interface", base if base != "critical" else "high", f"{svc or 'admin interface'} on {name} exposed to the internet (authenticated)",
                                         "Restrict to VPN or IP allow-list; authentication alone is not a boundary.", scan, ["vulnerability-management"]))

        status = str(a.get("cname_status") or "ok").lower()
        if a.get("cname_target") and status in TAKEOVER_STATUS:
            findings.append(_finding(a, "takeover", TAKEOVER_STATUS[status], f"{name} CNAME to {a['cname_target']} is {status}: subdomain takeover candidate",
                                     "Remove the DNS record or reclaim the target within 24 hours.", scan, []))

        tls = a.get("tls") or {}
        if isinstance(tls, dict) and tls.get("expires_in_days") is not None:
            d = int(tls["expires_in_days"])
            if d <= 0:
                findings.append(_finding(a, "certificate", "critical", f"certificate on {name} expired {abs(d)} day(s) ago", "Renew immediately; expired certificate on a live endpoint.", scan, []))
            elif d <= 7:
                findings.append(_finding(a, "certificate", "critical", f"certificate on {name} expires in {d} day(s)", "Renew within 24 hours; page the certificate owner.", scan, []))
            elif d <= 14:
                findings.append(_finding(a, "certificate", "high", f"certificate on {name} expires in {d} day(s)", "Escalate to the infrastructure team; renew this week.", scan, []))
            elif d <= 30:
                findings.append(_finding(a, "certificate", "low", f"certificate on {name} expires in {d} day(s)", "Notify the certificate owner.", scan, []))
            if tls.get("wildcard") and internet:
                findings.append(_finding(a, "certificate", "medium", f"wildcard certificate in use on internet-facing {name}", "Review whether a wildcard is needed on a high-risk host.", scan, []))

        if not in_inv:
            sev = "high" if internet else "medium"
            cascade = ["cloud-security-posture"] if a.get("type") == "cloud_resource" else []
            if a.get("type") == "cloud_resource" and a.get("iac_managed") is False:
                cascade.append("iac-security")
            findings.append(_finding(a, "shadow_it", sev, f"{name} is not in the approved inventory" + (" and is internet-facing" if internet else ""),
                                     "Register the asset with an owner or decommission it; shadow IT cannot be risk-accepted.", scan, cascade))
        elif internet and a.get("id") not in set(prev.get("asset_ids") or []) and a.get("id"):
            findings.append(_finding(a, "exposure", "high", f"new internet-facing asset {name} since the previous snapshot",
                                     "Scan for vulnerabilities and confirm the business owner within 7 days.", scan, ["vulnerability-management"] + (["network-exposure"] if a.get("ports") else [])))

    findings.sort(key=lambda f: (-SEV_RANK[f["severity"]], -f["risk_score"], f["asset"] or ""))
    internet_now = sum(1 for a in assets if a.get("exposure") == "internet_facing" and str(a.get("verified_by", "none")) != "none")
    prev_count = prev.get("internet_facing_count")
    if prev_count is None:
        trend = "no previous snapshot"
    else:
        trend = "expanding" if internet_now > int(prev_count) else "contracting" if internet_now < int(prev_count) else "stable"
    counts = {k: sum(1 for f in findings if f["severity"] == k) for k in SEV_RANK}
    severity = findings[0]["severity"] if findings else "informational"

    if counts["critical"]:
        action = f"{counts['critical']} critical exposure(s) with a 24-hour SLA: " + "; ".join(f["recommended_action"] for f in findings[:2])
    elif counts["high"]:
        action = f"{counts['high']} high exposure(s) with a 7-day SLA; start with {findings[0]['asset']}."
    elif findings:
        action = "Register or decommission the medium and low items within their 30-day SLA."
    else:
        action = "No new exposure; keep the 24-hour discovery cycle running."

    key_findings = [f"{org}: {len(assets)} asset(s) in snapshot, {internet_now} verified internet-facing "
                    f"(previous {prev_count if prev_count is not None else 'n/a'}): surface {trend}; "
                    f"{len(findings)} finding(s): {counts['critical']} critical, {counts['high']} high, {counts['medium']} medium, {counts['low']} low"]
    key_findings += [f"{f['severity']} [{f['kind']}] {f['title']} -> SLA {f['sla_deadline_utc']}" for f in findings[:6]]
    if unverified:
        key_findings.append(f"{len(unverified)} asset(s) claimed internet-facing without active probing, classified unknown until verified: {', '.join(unverified[:3])}")

    rel = None
    if input_path:
        try:
            rel = Path(input_path).resolve().relative_to(REPO_ROOT).as_posix()
        except ValueError:
            rel = None
    src = f"local://{rel}" if rel else "local://detection/attack-surface-management/SKILL.md"
    evidence = [{"source": src, "ref": f"{f['asset']} ({f['discovery_source'] or 'snapshot'}, first seen {f['first_seen_utc'] or 'n/a'})", "quote": f["title"]} for f in findings[:6]]
    evidence.append({"source": "local://detection/attack-surface-management/references/classification-tables.md", "ref": "exposure matrix, certificate thresholds, takeover indicators, admin interface risk"})
    if any(f["kind"] == "takeover" for f in findings):
        evidence.append({"source": "https://attack.mitre.org/techniques/T1584/001/", "ref": "Compromise Infrastructure: Domains (subdomain takeover)"})

    conf, factors = 0.55, ["base 0.55 for a discovery snapshot"]
    if assets and all(str(a.get("verified_by", "none")) != "none" for a in assets if a.get("exposure") == "internet_facing"):
        conf += 0.20; factors.append("every internet-facing claim probed (+0.20)")
    elif assets:
        conf += 0.08; factors.append("some exposure claims unprobed (+0.08)")
    if prev_count is not None:
        conf += 0.10; factors.append("previous snapshot available for trend (+0.10)")
    if inventory:
        conf += 0.05; factors.append("approved inventory supplied (+0.05)")
    if not assets:
        conf, factors = 0.30, ["no assets supplied (0.30)"]
    conf = round(min(conf, 0.92), 2)

    cascade = []
    for f in findings:
        for c in f["cascade_to"]:
            if c not in cascade:
                cascade.append(c)
    return {
        "agent_slug": SLUG, "intent_type": "detect", "action": action,
        "rationale": (f"Snapshot classified per the SKILL.md procedure: exposure verified by probing (unprobed claims downgraded to unknown), "
                      f"admin interfaces against the risk table, CNAME status against the takeover indicators, certificate expiry against the thresholds, "
                      f"inventory membership for shadow IT, trend against the previous snapshot, SLA per severity. Confidence factors: {', '.join(factors)}."),
        "confidence": conf, "severity": severity, "key_findings": key_findings, "evidence_references": evidence,
        "next_agents": cascade, "human_approval_required": False, "timestamp_utc": _now(),
        "surface": {"assets_total": len(assets), "internet_facing_verified": internet_now, "previous_internet_facing": prev_count,
                    "trend": trend, "unverified_exposure_claims": unverified, "counts": counts},
        "findings": findings, "mitre_ttps": sorted({f["mitre_technique"] for f in findings if f.get("mitre_technique")}),
        "affected_assets": [f["asset"] for f in findings[:10]],
    }


def _exit(p: dict) -> int:
    return {"critical": 2, "high": 1}.get(p["severity"], 0)


def main() -> int:
    ap = argparse.ArgumentParser(description="USAP attack-surface-management: classify a discovery snapshot")
    ap.add_argument("--input"); ap.add_argument("--output", choices=["json", "text"], default="text")
    args = ap.parse_args()
    if args.input:
        try:
            target = json.loads(Path(args.input).read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            print(f"error: cannot read --input: {exc}", file=sys.stderr); return 2
    else:
        raw = "" if sys.stdin.isatty() else sys.stdin.read()
        try:
            target = json.loads(raw) if raw.strip() else {}
        except json.JSONDecodeError:
            target = {}
    p = analyse(target, args.input)
    if args.output == "json":
        print(json.dumps(p, indent=2))
    else:
        print(f"attack-surface-management: severity={p['severity']} trend={p['surface']['trend']}")
        for f in p["key_findings"]:
            print(f"  - {f}")
    return _exit(p)


if __name__ == "__main__":
    raise SystemExit(main())
