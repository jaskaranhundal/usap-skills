#!/usr/bin/env python3
"""internal-audit-assurance_tool.py

Tests USAP control operating effectiveness against the SKILL.md audit dimensions
(evidence completeness, approval integrity, hash-chain integrity, approver-role
compliance, TTL compliance, no unauthorized execution) and maps failures to ISO
27001 / SOC 2 / PCI-DSS / GDPR controls. Read-only. Emits the USAP 11-field
payload.

  python3 internal-audit-assurance_tool.py --input audit.json --output json
  python3 internal-audit-assurance_tool.py --output json    # no input: informational, exit 0

Input (see tests/fixtures/internal-audit-assurance-input.json):
{scope, dimensions{evidence_completeness (0-1 or bool), approval_integrity,
hash_chain_integrity, approver_role_compliance, ttl_compliance,
no_unauthorized_execution} }.

Exit codes: 0 clean; 1 findings; 2 a critical finding (unauthorized execution,
broken hash chain, or missing approval). Stdlib only.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

SLUG = "internal-audit-assurance"
HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parents[2]
# dimension -> (severity if failing, ISO, SOC2, PCI, GDPR, description)
DIMENSION = {
    "no_unauthorized_execution": ("critical", "A.9.4.2", "CC6.6", "Req 7.1", "Art 25", "execution record without a prior signed approval"),
    "hash_chain_integrity": ("critical", "A.12.4.2", "CC7.2", "Req 10.5", "Art 32", "evidence-chain hash links broken or unverifiable"),
    "approval_integrity": ("high", "A.6.1.2", "CC6.1", "Req 7", "Art 5(1)(f)", "mutating intent without a signed approval before execution"),
    "approver_role_compliance": ("high", "A.6.1.2", "CC6.1", "Req 7", "Art 5(1)(f)", "approver role does not match the required approver role"),
    "evidence_completeness": ("high", "A.12.4.1", "CC7.2", "Req 10.2", "Art 30", "recommendation without a corresponding evidence record"),
    "ttl_compliance": ("medium", "A.12.1.1", "CC7.1", "Req 10.6", "Art 32", "agent ran beyond its defined TTL"),
}
SEV_RANK = {"critical": 4, "high": 3, "medium": 2, "low": 1, "informational": 0}


def _passing(v: Any) -> bool:
    if isinstance(v, bool):
        return v
    try:
        return float(v) >= 1.0
    except (TypeError, ValueError):
        return False


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def analyse(t: dict, input_path: Optional[str] = None) -> Dict[str, Any]:
    rel = None
    if input_path:
        try:
            rel = Path(input_path).resolve().relative_to(REPO_ROOT).as_posix()
        except ValueError:
            rel = None
    dims = t.get("dimensions")
    if not t or dims is None:
        return {"agent_slug": SLUG, "intent_type": "report", "action": "Supply audit dimensions; nothing was provided.",
                "rationale": "No audit supplied.", "confidence": 0.30, "severity": "informational", "key_findings": ["No audit supplied"],
                "evidence_references": [{"source": "local://risk-compliance/internal-audit-assurance/SKILL.md", "ref": "audit dimensions (not applied)"}],
                "next_agents": [], "human_approval_required": False, "timestamp_utc": _now(), "findings": [], "_exit": 0}
    dims = dims or {}
    findings: List[dict] = []
    for dim, (sev, iso, soc2, pci, gdpr, desc) in DIMENSION.items():
        if dim in dims and not _passing(dims[dim]):
            findings.append({"dimension": dim, "severity": sev, "description": desc,
                             "mappings": {"iso27001": iso, "soc2": soc2, "pci_dss": pci, "gdpr": gdpr}})
    findings.sort(key=lambda x: -SEV_RANK[x["severity"]])
    counts = {k: sum(1 for x in findings if x["severity"] == k) for k in SEV_RANK}
    tested = len([d for d in DIMENSION if d in dims])
    severity = findings[0]["severity"] if findings else "informational"
    exit_code = 2 if counts["critical"] else 1 if findings else 0
    scope = t.get("scope", "the control set")
    action = (f"{counts['critical']} critical audit finding(s) in {scope}: " + "; ".join(f["description"] for f in findings if f["severity"]=="critical")[:180] + ". Escalate with management response." if counts["critical"] else
              f"{counts['high']} audit finding(s) in {scope} requiring a management response." if findings else
              f"{scope}: all {tested} tested control dimension(s) passed.")
    key = [f"{scope}: {tested} dimension(s) tested, {len(findings)} finding(s) ({counts['critical']} critical, {counts['high']} high)"]
    key += [f"{f['severity']} {f['dimension']}: {f['description']} [ISO {f['mappings']['iso27001']} / SOC2 {f['mappings']['soc2']}]" for f in findings[:6]]
    evidence = [{"source": f"local://{rel}" if rel else "local://risk-compliance/internal-audit-assurance/SKILL.md", "ref": "control test results"},
                {"source": "local://risk-compliance/internal-audit-assurance/SKILL.md", "ref": "audit dimension and framework-mapping tables"}]
    return {"agent_slug": SLUG, "intent_type": "report", "action": action,
            "rationale": ("Each dimension is tested against its pass criterion; a failing 'no unauthorized execution' or a broken hash chain is critical because it breaks the integrity of the "
                          "control plane's audit trail, and each finding is mapped to the ISO 27001, SOC 2, PCI-DSS and GDPR control it violates. Read-only assurance."),
            "confidence": 0.88, "severity": severity, "key_findings": key, "evidence_references": evidence,
            "next_agents": ["ciso-brief-generator"] if counts["critical"] else [], "human_approval_required": False, "timestamp_utc": _now(),
            "findings": findings, "mitre_ttps": [], "affected_assets": [str(scope)], "_exit": exit_code}


def main() -> int:
    ap = argparse.ArgumentParser(description="USAP internal-audit-assurance")
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
    print(json.dumps(p, indent=2) if args.output == "json" else f"internal-audit-assurance: severity={p['severity']}")
    return code


if __name__ == "__main__":
    raise SystemExit(main())
