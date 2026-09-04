#!/usr/bin/env python3
"""iac-security_tool.py

Evaluates a normalised Infrastructure-as-Code descriptor (parsed Terraform,
CloudFormation or Kubernetes resources plus any secrets a scanner found)
against the SKILL.md misconfiguration tables and the CI/CD gate policy, and
emits the USAP 11-field payload.

  python3 iac-security_tool.py --input iac.json --output json
  cat iac.json | python3 iac-security_tool.py --output json
  python3 iac-security_tool.py --output json       # no input: informational, exit 0

Input (see tests/fixtures/iac-security-input.json):
  scan_target: terraform|cloudformation|kubernetes|helm, source, files[]:
    path, resources[]: {type, name, line, attributes{...}}
  secrets_detected[]: {path, line, kind}
  approved_exceptions[]: finding ids that carry a documented exception

Exit codes: 0 pass; 1 warn (high findings, no block); 2 block (critical
finding without an approved exception, or a secret in IaC). Read-only static
analysis; never applies anything. Stdlib only.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

SLUG = "iac-security"
HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parents[2]

# SKILL.md "Compliance Framework Mapping" rows, keyed by control class.
COMPLIANCE = {
    "encryption": {"CIS AWS": "2.1.1", "CIS K8s": "3.1.2", "NIST 800-53": "SC-28", "PCI DSS": "3.4"},
    "least_privilege": {"CIS AWS": "1.1-1.22", "CIS K8s": "5.1.1", "NIST 800-53": "AC-6", "PCI DSS": "7.1"},
    "network": {"CIS AWS": "5.1-5.6", "CIS K8s": "5.2.1", "NIST 800-53": "SC-7", "PCI DSS": "1.1"},
    "logging": {"CIS AWS": "3.1-3.14", "CIS K8s": "3.2.1", "NIST 800-53": "AU-2", "PCI DSS": "10.1"},
    "secrets": {"NIST 800-53": "IA-5", "PCI DSS": "8.2"},
    "resilience": {"NIST 800-53": "CP-9"},
}
NEVER_PUBLIC_PORTS = {22: "SSH", 3389: "RDP", 5432: "PostgreSQL", 3306: "MySQL", 1433: "MSSQL", 27017: "MongoDB"}
SEV_RANK = {"critical": 4, "high": 3, "medium": 2, "low": 1, "informational": 0}
SCORE_WEIGHT = {"critical": 25, "high": 10, "medium": 4, "low": 1, "informational": 0}
CIS_AWS = "https://www.cisecurity.org/benchmark/amazon_web_services"
CIS_K8S = "https://www.cisecurity.org/benchmark/kubernetes"


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _f(fid, title, sev, res, path, mis, rem, cls, block, technique=None) -> dict:
    return {
        "finding_id": fid, "title": title, "severity": sev,
        "resource_type": res.get("type", "?"), "resource_name": res.get("name", "?"),
        "file_path": path, "line_number": int(res.get("line") or 0),
        "misconfiguration": mis, "remediation": rem,
        "compliance_frameworks": [f"{k} {v}" for k, v in COMPLIANCE.get(cls, {}).items()],
        "block_pr": block, "mitre_technique": technique,
    }


def _truthy(v) -> bool:
    return v is True or (isinstance(v, str) and v.strip().lower() in ("true", "yes", "1"))


def _falsy(v) -> bool:
    return v is False or (isinstance(v, str) and v.strip().lower() in ("false", "no", "0"))


def evaluate_resource(path: str, res: dict, seq: List[int]) -> List[dict]:
    """Apply the SKILL.md tables to one resource. Every rule is a table row."""
    out: List[dict] = []
    t = str(res.get("type", "")).lower()
    a = res.get("attributes") or {}
    name = res.get("name", "?")

    def nid() -> str:
        seq[0] += 1
        return f"IAC-{seq[0]:03d}"

    # S3 buckets
    if t.startswith("aws_s3_bucket") or t == "aws::s3::bucket":
        acl = str(a.get("acl", "")).lower()
        if acl in ("public-read", "public-read-write"):
            out.append(_f(nid(), f"S3 bucket {name} has public ACL", "critical", res, path, f'acl = "{acl}"',
                          'Set acl = "private" and enable the public access block on the bucket.', "least_privilege", True, "T1530"))
        if _falsy(a.get("block_public_acls")):
            out.append(_f(nid(), f"S3 bucket {name} allows public ACLs", "critical", res, path, "block_public_acls = false",
                          "Set every aws_s3_bucket_public_access_block flag to true.", "least_privilege", True, "T1530"))
        if _falsy(a.get("server_side_encryption")) or _falsy(a.get("encryption")):
            out.append(_f(nid(), f"S3 bucket {name} is not encrypted at rest", "high", res, path, "server_side_encryption = false",
                          "Add aws_s3_bucket_server_side_encryption_configuration with SSE-KMS.", "encryption", False))
        if _falsy(a.get("versioning")):
            out.append(_f(nid(), f"S3 bucket {name} has versioning disabled", "medium", res, path, "versioning disabled",
                          "Enable versioning; it is the ransomware and accidental-delete recovery path.", "resilience", False))
        if _falsy(a.get("logging")):
            out.append(_f(nid(), f"S3 bucket {name} has access logging disabled", "high", res, path, "logging disabled",
                          "Enable server access logging to a dedicated log bucket.", "logging", False))

    # IAM policies and roles
    if t.startswith("aws_iam") or t.startswith("aws::iam"):
        for st in a.get("statements") or []:
            act, resrc, eff = st.get("Action"), st.get("Resource"), str(st.get("Effect", "Allow"))
            acts = act if isinstance(act, list) else [act]
            ress = resrc if isinstance(resrc, list) else [resrc]
            if eff == "Allow" and "*" in acts and "*" in ress:
                out.append(_f(nid(), f"IAM policy {name} grants Action * on Resource *", "critical", res, path,
                              '"Action": "*" with "Resource": "*"', "Scope actions and resources to the least privilege the workload needs.",
                              "least_privilege", True, "T1078.004"))
        trust = a.get("assume_role_policy") or {}
        for st in trust.get("statements") or []:
            if st.get("Principal") in ("*", {"AWS": "*"}):
                out.append(_f(nid(), f"IAM role {name} trust policy allows any principal", "critical", res, path,
                              '"Principal": "*" in trust policy', "Restrict Principal to the exact account or role ARNs that may assume this role.",
                              "least_privilege", True, "T1078.004"))
            elif not st.get("Condition") or "aws:MultiFactorAuthPresent" not in json.dumps(st.get("Condition")):
                out.append(_f(nid(), f"IAM role {name} can be assumed without MFA", "high", res, path,
                              "No MFA condition on AssumeRole", 'Add Condition {"Bool": {"aws:MultiFactorAuthPresent": "true"}}.',
                              "least_privilege", False))
        if a.get("inline"):
            out.append(_f(nid(), f"IAM inline policy on {name}", "medium", res, path, "inline policy (vs managed)",
                          "Convert to a customer-managed policy so it is versioned and reviewable.", "least_privilege", False))

    # Security groups
    if t in ("aws_security_group_rule", "aws_security_group") or t == "aws::ec2::securitygroup":
        rules = a.get("ingress") if isinstance(a.get("ingress"), list) else [a]
        for r in rules:
            cidrs = r.get("cidr_blocks") or r.get("cidr") or []
            cidrs = cidrs if isinstance(cidrs, list) else [cidrs]
            if not any(c in ("0.0.0.0/0", "::/0") for c in cidrs):
                continue
            lo, hi = int(r.get("from_port") or 0), int(r.get("to_port") or r.get("from_port") or 0)
            hit = [p for p in NEVER_PUBLIC_PORTS if lo <= p <= max(hi, lo)] or ([0] if (lo, hi) == (0, 0) else [])
            if hit:
                label = ", ".join(f"{NEVER_PUBLIC_PORTS.get(p, 'all')} ({p})" for p in hit) if hit != [0] else "all ports"
                out.append(_f(nid(), f"Security group {name} exposes {label} to the internet", "critical", res, path,
                              f"ingress {lo}-{hi} from 0.0.0.0/0", "Restrict the CIDR to the bastion or VPN range, or move to SSM Session Manager.",
                              "network", True, "T1133"))

    # Kubernetes workloads
    if t in ("pod", "deployment", "statefulset", "daemonset", "job", "cronjob"):
        sec = {**(a.get("securityContext") or {}), **a}
        for key, sev, mis, rem, tech in (
            ("privileged", "critical", "privileged: true", "Drop privileged; grant the specific capability instead.", "T1611"),
            ("hostPID", "critical", "hostPID: true", "Remove hostPID; it exposes every process on the node.", "T1611"),
            ("hostNetwork", "critical", "hostNetwork: true", "Remove hostNetwork; use a Service or NetworkPolicy.", "T1611"),
            ("allowPrivilegeEscalation", "high", "allowPrivilegeEscalation: true", "Set allowPrivilegeEscalation: false.", None),
            ("runAsRoot", "high", "runAsRoot: true", "Set runAsNonRoot: true and a fixed runAsUser.", None),
            ("automountServiceAccountToken", "medium", "automountServiceAccountToken: true", "Set automountServiceAccountToken: false unless the pod calls the API.", None),
        ):
            if _truthy(sec.get(key)) or (key == "runAsRoot" and _falsy(sec.get("runAsNonRoot"))):
                out.append(_f(nid(), f"{res.get('type')} {name}: {mis}", sev, res, path, mis, rem, "least_privilege", sev == "critical", tech))

    # RBAC
    if t in ("clusterrolebinding", "rolebinding"):
        role = a.get("roleRef") if isinstance(a.get("roleRef"), str) else (a.get("roleRef") or {}).get("name")
        subs = [s if isinstance(s, str) else f"{s.get('kind')}:{s.get('name')}" for s in (a.get("subjects") or [])]
        if str(role) == "cluster-admin" and any(str(s).lower().startswith("serviceaccount") for s in subs):
            out.append(_f(nid(), f"{res.get('type')} {name} binds a ServiceAccount to cluster-admin", "critical", res, path,
                          "roleRef cluster-admin with ServiceAccount subject", "Bind a namespaced Role with the verbs the workload needs.",
                          "least_privilege", True, "T1078.004"))
    return out


def analyse(target: dict, input_path: Optional[str] = None) -> Dict[str, Any]:
    scan_target = str(target.get("scan_target", "terraform"))
    source = target.get("source", "unknown-source")
    files = [f for f in (target.get("files") or []) if isinstance(f, dict)]
    exceptions = set(target.get("approved_exceptions") or [])
    seq = [0]
    findings: List[dict] = []
    for f in files:
        for res in f.get("resources") or []:
            findings.extend(evaluate_resource(str(f.get("path", "?")), res, seq))
    for s in target.get("secrets_detected") or []:
        seq[0] += 1
        findings.append({
            "finding_id": f"IAC-{seq[0]:03d}", "title": f"Secret in IaC: {s.get('kind', 'credential')}", "severity": "critical",
            "resource_type": "secret", "resource_name": s.get("kind", "credential"), "file_path": s.get("path", "?"),
            "line_number": int(s.get("line") or 0), "misconfiguration": "credential committed in IaC source",
            "remediation": "Move the value to a secrets manager reference and rotate it; the committed value is compromised.",
            "compliance_frameworks": [f"{k} {v}" for k, v in COMPLIANCE["secrets"].items()], "block_pr": True, "mitre_technique": "T1552.001",
        })

    resources = sum(len(f.get("resources") or []) for f in files)
    findings.sort(key=lambda x: (-SEV_RANK[x["severity"]], x["file_path"], x["line_number"]))
    for x in findings:
        x["exception_approved"] = x["finding_id"] in exceptions
    blockers = [x for x in findings if x["block_pr"] and not x["exception_approved"]]
    counts = {k: sum(1 for x in findings if x["severity"] == k) for k in SEV_RANK}
    score = max(0, 100 - sum(SCORE_WEIGHT[x["severity"]] for x in findings if not x["exception_approved"]))
    severity = findings[0]["severity"] if findings else "informational"
    blocked = bool(blockers)
    block_reason = ("; ".join(f"{b['finding_id']} {b['title']}" for b in blockers[:3]) + (f"; +{len(blockers) - 3} more" if len(blockers) > 3 else "")) if blocked else None

    if blocked:
        action = f"Block the PR: {len(blockers)} critical finding(s) without an approved exception. Fix in order: " + "; ".join(f"{b['finding_id']} {b['remediation']}" for b in blockers[:3])
        intent = "block"
    elif counts["high"]:
        action = f"Pass with warning: {counts['high']} high finding(s) need a documented exception or a fix before the next release."
        intent = "analyze"
    elif findings:
        action = "Pass: only medium and low findings; schedule them in the next hardening window."
        intent = "analyze"
    else:
        action = "Pass: no misconfiguration against the SKILL.md tables in the supplied resources."
        intent = "analyze"

    key_findings = [f"{scan_target} scan of {source}: {resources} resource(s) in {len(files)} file(s), "
                    f"{len(findings)} finding(s) ({counts['critical']} critical, {counts['high']} high, {counts['medium']} medium), "
                    f"compliance score {score}/100, PR {'BLOCKED' if blocked else 'not blocked'}"]
    for x in findings[:6]:
        key_findings.append(f"{x['finding_id']} {x['severity']} {x['file_path']}:{x['line_number']} {x['title']}"
                            + (" [exception approved]" if x["exception_approved"] else "") + f" -> {x['remediation']}")

    rel = None
    if input_path:
        try:
            rel = Path(input_path).resolve().relative_to(REPO_ROOT).as_posix()
        except ValueError:
            rel = None
    evidence: List[dict] = []
    for x in findings[:6]:
        evidence.append({"source": f"local://{rel}" if rel else "local://cloud-infra/iac-security/SKILL.md",
                         "ref": f"{x['file_path']}:{x['line_number']} {x['resource_type']}/{x['resource_name']}", "quote": x["misconfiguration"]})
    if any(x["resource_type"].startswith("aws") for x in findings):
        evidence.append({"source": CIS_AWS, "ref": "CIS AWS Foundations Benchmark controls cited per finding"})
    if any(x["resource_type"].lower() in ("pod", "deployment", "statefulset", "daemonset", "clusterrolebinding", "rolebinding") for x in findings):
        evidence.append({"source": CIS_K8S, "ref": "CIS Kubernetes Benchmark controls cited per finding"})
    evidence.append({"source": "local://cloud-infra/iac-security/SKILL.md", "ref": "misconfiguration tables and CI/CD gate policy"})

    conf, factors = 0.60, ["base 0.60 for parsed resources"]
    if resources:
        conf += 0.15; factors.append("resource attributes supplied (+0.15)")
    if target.get("secrets_detected") is not None:
        conf += 0.10; factors.append("secret scan result supplied (+0.10)")
    if not resources and not target.get("secrets_detected"):
        conf, factors = 0.30, ["no resources supplied (0.30)"]
    conf = round(min(conf, 0.93), 2)

    next_agents = []
    if findings:
        next_agents.append("findings-tracker")
    if any(x["compliance_frameworks"] for x in findings):
        next_agents.append("compliance-mapping")
    if any(x["resource_type"] == "secret" for x in findings):
        next_agents.insert(0, "secrets-exposure")

    return {
        "agent_slug": SLUG, "intent_type": intent, "action": action,
        "rationale": (f"Static analysis of {resources} {scan_target} resource(s) against the SKILL.md misconfiguration tables. "
                      f"Block conditions: critical finding without approved exception, secret in IaC, IAM wildcard, public bucket or public admin port. "
                      f"{len(blockers)} blocker(s); compliance score {score}/100 (critical -25, high -10, medium -4, low -1). "
                      f"Confidence factors: {', '.join(factors)}."),
        "confidence": conf, "severity": severity, "key_findings": key_findings, "evidence_references": evidence,
        "next_agents": next_agents, "human_approval_required": False, "timestamp_utc": _now(),
        "scan_target": scan_target, "findings": findings, "critical_count": counts["critical"], "high_count": counts["high"],
        "pr_should_be_blocked": blocked, "block_reason": block_reason, "compliance_score": score,
        "mitre_ttps": sorted({x["mitre_technique"] for x in findings if x.get("mitre_technique")}),
        "affected_assets": [source],
    }


def _exit_code(payload: dict) -> int:
    if payload["pr_should_be_blocked"]:
        return 2
    if payload["high_count"]:
        return 1
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="USAP iac-security: evaluate a normalised IaC descriptor")
    ap.add_argument("--input", help="IaC descriptor JSON (see module docstring)")
    ap.add_argument("--output", choices=["json", "text"], default="text")
    args = ap.parse_args()
    if args.input:
        try:
            target = json.loads(Path(args.input).read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            print(f"error: cannot read --input: {exc}", file=sys.stderr)
            return 2
    else:
        raw = "" if sys.stdin.isatty() else sys.stdin.read()
        try:
            target = json.loads(raw) if raw.strip() else {}
        except json.JSONDecodeError:
            target = {}
    payload = analyse(target, args.input)
    if args.output == "json":
        print(json.dumps(payload, indent=2))
    else:
        print(f"iac-security: severity={payload['severity']} blocked={payload['pr_should_be_blocked']} score={payload['compliance_score']}")
        for f in payload["key_findings"]:
            print(f"  - {f}")
    return _exit_code(payload)


if __name__ == "__main__":
    raise SystemExit(main())
