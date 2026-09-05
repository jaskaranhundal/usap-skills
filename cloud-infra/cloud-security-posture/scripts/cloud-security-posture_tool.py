#!/usr/bin/env python3
"""cloud-security-posture_tool.py

Evaluates a collected cloud configuration snapshot against the CSPM check
matrices in references/cspm-check-matrices.md, applies the Misconfiguration
Severity Matrix modifiers, maps every finding to its CIS control, detects
drift against the previous baseline (unauthorised drift is a High finding on
its own), and references the remediation document. Read-only. Emits the USAP
11-field payload.

  python3 cloud-security-posture_tool.py --input snapshot.json --output json
  python3 cloud-security-posture_tool.py --output json     # no input: informational, exit 0

Input (see tests/fixtures/cloud-security-posture-input.json): provider (aws|azure|gcp),
account, scan_utc, collected_utc, change_tickets[], resources[]: {id, type, region,
environment, internet_facing, data_classification, compensating_control_verified,
config{...}, baseline_config{...}, changed_at_utc, change_ticket}

Exit codes: 0 nothing above medium; 1 high; 2 critical. Stdlib only.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

SLUG = "cloud-security-posture"
HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parents[2]
SEV_RANK = {"critical": 4, "high": 3, "medium": 2, "low": 1, "informational": 0}
RANK_SEV = {v: k for k, v in SEV_RANK.items()}
ADMIN_PORTS = {22: "SSH", 3389: "RDP"}
CIS_URL = {"aws": "https://www.cisecurity.org/benchmark/amazon_web_services", "azure": "https://www.cisecurity.org/benchmark/azure", "gcp": "https://www.cisecurity.org/benchmark/google_cloud_computing_platform"}


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _parse(ts: Optional[str]) -> Optional[datetime]:
    if not ts:
        return None
    try:
        return datetime.fromisoformat(str(ts).replace("Z", "+00:00")).astimezone(timezone.utc)
    except ValueError:
        return None


def _open_to_world(rule: dict) -> bool:
    cidrs = rule.get("cidr") or rule.get("cidr_blocks") or rule.get("source") or []
    cidrs = cidrs if isinstance(cidrs, list) else [cidrs]
    return any(str(c) in ("0.0.0.0/0", "::/0", "*", "any", "internet") for c in cidrs)


# Check functions per provider: (check_id, resource types, severity, cis, predicate, finding text, remediation key)
def _aws_checks() -> List[Tuple[str, Tuple[str, ...], str, str, Callable[[dict], bool], str]]:
    return [
        ("AWS-01", ("s3_bucket",), "critical", "CIS AWS 2.1.1", lambda c: c.get("block_public_access") is False, "S3 Block Public Access disabled"),
        ("AWS-02", ("s3_bucket",), "critical", "CIS AWS 2.1.2", lambda c: str(c.get("acl", "")).lower() in ("public-read", "public-read-write"), "S3 bucket ACL grants public read"),
        ("AWS-03", ("rds_instance",), "critical", "CIS AWS 2.3.3", lambda c: c.get("publicly_accessible") is True, "RDS instance publicly accessible"),
        ("AWS-04", ("security_group",), "high", "CIS AWS 5.2", lambda c: any(_open_to_world(r) and int(r.get("from_port", 0)) <= 22 <= int(r.get("to_port", r.get("from_port", 0))) and not (int(r.get("from_port", 0)) == 0 and int(r.get("to_port", 0)) in (0, 65535)) for r in c.get("ingress", [])), "Ingress 0.0.0.0/0 to port 22"),
        ("AWS-05", ("security_group",), "critical", "CIS AWS 5.3", lambda c: any(_open_to_world(r) and int(r.get("from_port", 0)) <= 3389 <= int(r.get("to_port", r.get("from_port", 0))) and not (int(r.get("from_port", 0)) == 0 and int(r.get("to_port", 0)) in (0, 65535)) for r in c.get("ingress", [])), "Ingress 0.0.0.0/0 to port 3389"),
        ("AWS-06", ("security_group",), "critical", "CIS AWS 5.1", lambda c: any(_open_to_world(r) and int(r.get("from_port", 0)) == 0 and int(r.get("to_port", 0)) in (0, 65535) for r in c.get("ingress", [])), "Ingress 0.0.0.0/0 to any port"),
        ("AWS-07", ("cloudtrail", "account"), "critical", "CIS AWS 3.1", lambda c: c.get("cloudtrail_all_regions") is False, "CloudTrail not enabled in all regions"),
        ("AWS-08", ("iam_root", "account"), "critical", "CIS AWS 1.4", lambda c: c.get("root_access_key_active") is True, "Root account has an active access key"),
        ("AWS-09", ("iam_root", "account"), "critical", "CIS AWS 1.5", lambda c: c.get("root_mfa_enabled") is False, "Root account MFA not enabled"),
        ("AWS-12", ("iam_user",), "critical", "CIS AWS 1.10", lambda c: c.get("admin_access") is True and c.get("mfa_enabled") is False, "IAM user with AdministratorAccess and no MFA"),
        ("AWS-13", ("iam_user",), "medium", "CIS AWS 1.14", lambda c: int(c.get("access_key_age_days") or 0) > 90, "Access key not rotated in 90+ days"),
        ("AWS-14", ("kms_key",), "medium", "CIS AWS 3.8", lambda c: c.get("rotation_enabled") is False, "CMK rotation not enabled"),
        ("AWS-15", ("vpc",), "high", "CIS AWS 3.9", lambda c: c.get("flow_logs_enabled") is False, "VPC Flow Logs disabled"),
        ("AWS-16", ("account",), "high", "CIS AWS 3.5", lambda c: c.get("config_enabled") is False, "AWS Config not enabled"),
        ("AWS-19", ("ebs_snapshot",), "critical", "CIS AWS 2.2.1", lambda c: c.get("public") is True, "EBS snapshot is public"),
        ("AWS-20", ("secret",), "high", "Custom", lambda c: int(c.get("age_days") or 0) > 90 and not c.get("rotation_enabled"), "Secret not rotated in 90+ days"),
    ]


def _azure_checks():
    return [
        ("AZ-01", ("storage_account",), "critical", "CIS Azure 3.1", lambda c: c.get("public_blob_access") is True, "Public blob access enabled"),
        ("AZ-02", ("nsg",), "critical", "CIS Azure 6.1", lambda c: any(_open_to_world(r) and 3389 in (r.get("ports") or []) for r in c.get("inbound", [])), "Inbound any source to RDP"),
        ("AZ-03", ("nsg",), "high", "CIS Azure 6.2", lambda c: any(_open_to_world(r) and 22 in (r.get("ports") or []) for r in c.get("inbound", [])), "Inbound any source to SSH"),
        ("AZ-04", ("aad_user",), "critical", "CIS Azure 1.1", lambda c: c.get("global_admin") is True and c.get("mfa_enabled") is False, "Global Admin without MFA"),
        ("AZ-07", ("subscription",), "high", "CIS Azure 2.1", lambda c: c.get("defender_enabled") is False, "Defender for Cloud not enabled"),
        ("AZ-08", ("subscription",), "high", "CIS Azure 5.1", lambda c: c.get("activity_log_export") is False, "No activity log export"),
        ("AZ-10", ("key_vault",), "medium", "CIS Azure 8.4", lambda c: c.get("soft_delete") is False, "Soft delete disabled"),
    ]


def _gcp_checks():
    return [
        ("GCP-01", ("gcs_bucket",), "critical", "CIS GCP 5.1", lambda c: any(m in ("allUsers", "allAuthenticatedUsers") for m in c.get("iam_members", [])), "Bucket IAM grants allUsers or allAuthenticatedUsers"),
        ("GCP-02", ("firewall_rule",), "high", "CIS GCP 3.6", lambda c: _open_to_world(c) and 22 in (c.get("ports") or []), "Firewall 0.0.0.0/0 to port 22"),
        ("GCP-03", ("firewall_rule",), "critical", "CIS GCP 3.7", lambda c: _open_to_world(c) and 3389 in (c.get("ports") or []), "Firewall 0.0.0.0/0 to port 3389"),
        ("GCP-05", ("service_account",), "high", "CIS GCP 1.5", lambda c: any(r in ("roles/editor", "roles/owner") for r in c.get("roles", [])), "Service account has editor or owner"),
        ("GCP-06", ("project",), "critical", "CIS GCP 2.1", lambda c: c.get("admin_activity_logs") is False, "Admin activity audit logs disabled"),
        ("GCP-07", ("cloudsql",), "critical", "CIS GCP 6.2", lambda c: c.get("public_ip") is True, "Cloud SQL publicly accessible"),
    ]


CHECKS = {"aws": _aws_checks, "azure": _azure_checks, "gcp": _gcp_checks}
POSTURE_DOWNGRADE_KEYS = {"block_public_access", "acl", "publicly_accessible", "cloudtrail_all_regions", "root_mfa_enabled", "mfa_enabled", "flow_logs_enabled",
                          "config_enabled", "public", "public_blob_access", "defender_enabled", "admin_activity_logs", "public_ip", "rotation_enabled", "encryption"}


def evaluate(resource: dict, provider: str, scan: datetime, tickets: set) -> Tuple[List[dict], Optional[dict]]:
    cfg = resource.get("config") or {}
    rtype = str(resource.get("type", "")).lower()
    env = str(resource.get("environment", "production")).lower()
    findings: List[dict] = []
    for cid, types, base, cis, pred, text in CHECKS.get(provider, _aws_checks)():
        if rtype not in types:
            continue
        try:
            hit = bool(pred(cfg))
        except (TypeError, ValueError):
            hit = False
        if not hit:
            continue
        rank = SEV_RANK[base]; mods: List[str] = []
        if resource.get("internet_facing"):
            rank += 1; mods.append("internet-facing +1")
        if str(resource.get("data_classification", "")).lower() in ("pii", "pci", "phi"):
            rank += 1; mods.append("regulated data +1")
        if env in ("dev", "development"):
            rank -= 1; mods.append("development -1")
        if resource.get("compensating_control_verified"):
            rank = min(rank - 1, SEV_RANK["medium"]); mods.append("verified compensating control -1 (max medium)")
        if resource.get("active_exploit_known"):
            rank = 4; mods.append("active exploit known -> critical")
        final = RANK_SEV[max(1, min(4, rank))]
        findings.append({"check_id": cid, "resource_id": resource.get("id"), "resource_type": rtype, "provider": provider, "region": resource.get("region"),
                         "environment": env, "finding": text, "base_severity": base, "modifiers": mods, "severity": final,
                         "compliance": [cis, "NIST 800-53 CM-6", "SOC 2 CC6.6"], "remediation_ref": f"local://cloud-infra/cloud-security-posture/references/remediation-commands.md#{cid.lower()}",
                         "drift": False, "scan_utc": scan.strftime("%Y-%m-%dT%H:%M:%SZ")})
    # Drift: posture-relevant keys that changed from the baseline
    base_cfg = resource.get("baseline_config")
    drift = None
    if isinstance(base_cfg, dict):
        changed = {k: (base_cfg.get(k), cfg.get(k)) for k in POSTURE_DOWNGRADE_KEYS if k in base_cfg and base_cfg.get(k) != cfg.get(k)}
        if changed:
            ticket = resource.get("change_ticket")
            authorised = bool(ticket) and (not tickets or ticket in tickets)
            drift = {"resource_id": resource.get("id"), "changes": {k: {"previous": v[0], "current": v[1]} for k, v in changed.items()},
                     "changed_at_utc": resource.get("changed_at_utc"), "change_ticket": ticket, "authorised": authorised}
            for f in findings:
                f["drift"] = True
            if not authorised:
                findings.append({"check_id": "DRIFT", "resource_id": resource.get("id"), "resource_type": rtype, "provider": provider, "region": resource.get("region"),
                                 "environment": env, "finding": f"unauthorised posture drift: {', '.join(changed)} changed with no change ticket", "base_severity": "high", "modifiers": [],
                                 "severity": "high", "compliance": ["ISO 27001 A.8.32", "SOC 2 CC8.1"], "remediation_ref": "local://cloud-infra/cloud-security-posture/references/workflow.md",
                                 "drift": True, "scan_utc": scan.strftime("%Y-%m-%dT%H:%M:%SZ")})
    return findings, drift


def analyse(target: dict, input_path: Optional[str] = None) -> Dict[str, Any]:
    provider = str(target.get("provider", "aws")).lower()
    account = target.get("account", "unknown-account")
    scan = _parse(target.get("scan_utc")) or datetime.now(timezone.utc)
    collected = _parse(target.get("collected_utc")) or scan
    stale = (scan - collected) > timedelta(hours=24)
    resources = [r for r in (target.get("resources") or []) if isinstance(r, dict)]
    tickets = {str(t) for t in (target.get("change_tickets") or [])}
    findings: List[dict] = []; drifts: List[dict] = []
    for r in resources:
        f, d = evaluate(r, provider, scan, tickets)
        findings += f
        if d:
            drifts.append(d)
    findings.sort(key=lambda f: (-SEV_RANK[f["severity"]], f["resource_id"] or ""))
    counts = {k: sum(1 for f in findings if f["severity"] == k) for k in SEV_RANK}
    severity = findings[0]["severity"] if findings else "informational"
    if stale and findings:
        severity = severity  # severity unchanged; staleness lowers confidence and is reported

    if counts["critical"]:
        action = f"{counts['critical']} critical finding(s) in {account}: cascade to the orchestrator now; remediation is human-gated, commands in references/remediation-commands.md. First: {findings[0]['check_id']} on {findings[0]['resource_id']}."
        intent = "escalate"
    elif counts["high"]:
        action = f"{counts['high']} high finding(s): open remediation tickets with the documented commands; verify configuration state after each fix."
        intent = "detect"
    elif findings:
        action = "Medium and low findings only: schedule in the next hardening window."
        intent = "detect"
    else:
        action = "No misconfiguration against the check matrices in the supplied resources; keep the 24-hour scan cadence."
        intent = "detect"
    if stale:
        action += " Configuration data is older than 24 hours; re-collect before acting."

    key = [f"{provider.upper()} {account}: {len(resources)} resource(s), {len(findings)} finding(s) ({counts['critical']} critical, {counts['high']} high, {counts['medium']} medium), "
           f"{len(drifts)} drift event(s) ({sum(1 for d in drifts if not d['authorised'])} unauthorised)" + ("; data STALE >24h" if stale else "")]
    key += [f"{f['severity']} {f['check_id']} {f['resource_type']} {f['resource_id']} ({f['region'] or 'n/a'}, {f['environment']}): {f['finding']}"
            + (f" [{'; '.join(f['modifiers'])}]" if f["modifiers"] else "") + f" -> {f['compliance'][0]}" for f in findings[:7]]
    key += [f"Drift on {d['resource_id']} at {d['changed_at_utc'] or 'n/a'}: " + ", ".join(f"{k} {v['previous']}->{v['current']}" for k, v in d["changes"].items())
            + (f" (ticket {d['change_ticket']})" if d["authorised"] else " (NO change ticket)") for d in drifts[:4]]

    rel = None
    if input_path:
        try:
            rel = Path(input_path).resolve().relative_to(REPO_ROOT).as_posix()
        except ValueError:
            rel = None
    src = f"local://{rel}" if rel else "local://cloud-infra/cloud-security-posture/SKILL.md"
    evidence = [{"source": src, "ref": f"{f['resource_type']} {f['resource_id']}", "quote": f"{f['check_id']} {f['finding']}"} for f in findings[:6]]
    evidence.append({"source": "local://cloud-infra/cloud-security-posture/references/cspm-check-matrices.md", "ref": "check matrix and base severities"})
    evidence.append({"source": CIS_URL.get(provider, CIS_URL["aws"]), "ref": "CIS Benchmark controls cited per finding"})

    conf, factors = 0.60, ["base 0.60"]
    if resources:
        conf += 0.15; factors.append("configuration attributes collected per resource (+0.15)")
    if any("baseline_config" in r for r in resources):
        conf += 0.10; factors.append("baseline available for drift (+0.10)")
    if stale:
        conf -= 0.20; factors.append("data older than 24 h (-0.20)")
    if not resources:
        conf, factors = 0.30, ["no resources supplied (0.30)"]
    conf = round(max(0.2, min(conf, 0.92)), 2)

    next_agents = []
    if any(f["check_id"] in ("AWS-01", "AWS-02", "AZ-01", "GCP-01") for f in findings):
        next_agents.append("attack-surface-management")
    if any(f["check_id"] in ("AWS-04", "AWS-05", "AWS-06", "AZ-02", "AZ-03", "GCP-02", "GCP-03") for f in findings):
        next_agents.append("network-exposure")
    if any(r.get("iac_managed") for r in resources) and drifts:
        next_agents.append("iac-security")
    if any(f["check_id"] in ("AWS-12", "GCP-05", "AZ-04") for f in findings):
        next_agents.append("vulnerability-management")
    if findings:
        next_agents.append("compliance-mapping")

    return {
        "agent_slug": SLUG, "intent_type": intent, "action": action,
        "rationale": (f"Every in-scope resource evaluated against the {provider.upper()} check matrix; base severity from the matrix, then the Misconfiguration Severity Matrix modifiers "
                      f"(internet-facing +1, regulated data +1, development -1, verified compensating control -1 capped at medium, active exploit -> critical). Drift is any change to a "
                      f"posture-relevant key versus the baseline; without a change ticket it is a High finding on its own. Read-only. Confidence factors: {', '.join(factors)}."),
        "confidence": conf, "severity": severity, "key_findings": key, "evidence_references": evidence,
        "next_agents": next_agents, "human_approval_required": False, "timestamp_utc": _now(),
        "posture": {"provider": provider, "account": account, "resources_scanned": len(resources), "counts": counts, "data_stale": stale, "drift_events": drifts},
        "findings": findings, "mitre_ttps": sorted({"T1530" for f in findings if f["check_id"] in ("AWS-01", "AWS-02", "AWS-19", "AZ-01", "GCP-01")} |
                                                   {"T1078.004" for f in findings if f["check_id"] in ("AWS-08", "AWS-09", "AWS-12", "AZ-04", "GCP-05")} |
                                                   {"T1562.008" for f in findings if f["check_id"] in ("AWS-07", "AZ-08", "GCP-06")} |
                                                   {"T1133" for f in findings if f["check_id"] in ("AWS-04", "AWS-05", "AWS-06", "AZ-02", "AZ-03", "GCP-02", "GCP-03")}),
        "affected_assets": sorted({str(f["resource_id"]) for f in findings}),
    }


def _exit(p: dict) -> int:
    return {"critical": 2, "high": 1}.get(p["severity"], 0)


def main() -> int:
    ap = argparse.ArgumentParser(description="USAP cloud-security-posture: evaluate a configuration snapshot")
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
        print(f"cloud-security-posture: severity={p['severity']} findings={len(p['findings'])}")
        for f in p["key_findings"]:
            print(f"  - {f}")
    return _exit(p)


if __name__ == "__main__":
    raise SystemExit(main())
