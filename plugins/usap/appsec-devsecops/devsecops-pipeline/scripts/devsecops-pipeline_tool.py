#!/usr/bin/env python3
"""devsecops-pipeline_tool.py

Assesses CI/CD security-gate completeness per the SKILL.md finding-severity table
and applies the branch-aware gate matrix (block / warn / pass). Blocking a merge
or deploy is a mutating action requiring approval. Emits the USAP 11-field payload.

  python3 devsecops-pipeline_tool.py --input pipeline.json --output json
  python3 devsecops-pipeline_tool.py --output json    # no input: informational, exit 0

Input (see tests/fixtures/devsecops-pipeline-input.json):
{branch, findings[] (type keys from the table, or {type, cvss})}.

Exit codes: 0 pass; 1 warn; 2 block. Stdlib only.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

SLUG = "devsecops-pipeline"
HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parents[2]
# finding type -> base severity
FINDING = {
    "secret_in_code": "critical",
    "critical_cvss_dependency": "critical",
    "high_cvss_dependency": "high",
    "sast_critical": "critical",
    "sast_high": "high",
    "iac_misconfiguration": "high",
    "container_image_vuln": "high",
    "license_violation": "medium",
    "outdated_base_image": "low",
    "missing_security_controls": "high",
}
SEV_RANK = {"critical": 4, "high": 3, "medium": 2, "low": 1, "informational": 0}


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _protected(branch: str) -> bool:
    b = branch.lower()
    return b in ("main", "master") or b.startswith("release/") or b.startswith("release-")


def _gate(sev: str, protected: bool) -> str:
    # Branch-aware gate matrix from the SKILL.md.
    if protected:
        return "block" if sev in ("critical", "high") else "warn" if sev == "medium" else "pass"
    return "block" if sev == "critical" else "warn" if sev == "high" else "pass"


def analyse(t: dict, input_path: Optional[str] = None) -> Dict[str, Any]:
    rel = None
    if input_path:
        try:
            rel = Path(input_path).resolve().relative_to(REPO_ROOT).as_posix()
        except ValueError:
            rel = None
    raw = t.get("findings") or []
    if not t or not raw:
        return {"agent_slug": SLUG, "intent_type": "advise", "action": "Supply pipeline findings; nothing was provided.",
                "rationale": "No findings supplied.", "confidence": 0.30, "severity": "informational", "key_findings": ["No findings supplied"],
                "evidence_references": [{"source": "local://appsec-devsecops/devsecops-pipeline/SKILL.md", "ref": "gate matrix (not applied)"}],
                "next_agents": [], "human_approval_required": False, "timestamp_utc": _now(), "findings": [], "_exit": 0}
    branch = str(t.get("branch") or "feature/unknown")
    protected = _protected(branch)
    findings: List[dict] = []
    for f in raw:
        ftype = f if isinstance(f, str) else str(f.get("type", ""))
        sev = FINDING.get(ftype, "medium")
        # CVSS refinement for dependency/container findings
        if isinstance(f, dict) and f.get("cvss") is not None and ftype in ("high_cvss_dependency", "container_image_vuln", "critical_cvss_dependency"):
            try:
                sev = "critical" if float(f["cvss"]) >= 9.0 else "high"
            except (TypeError, ValueError):
                pass
        findings.append({"type": ftype, "severity": sev, "gate": _gate(sev, protected)})
    findings.sort(key=lambda x: -SEV_RANK[x["severity"]])
    counts = {k: sum(1 for x in findings if x["severity"] == k) for k in SEV_RANK}
    blocks = [x for x in findings if x["gate"] == "block"]
    warns = [x for x in findings if x["gate"] == "warn"]
    decision = "block" if blocks else "warn" if warns else "pass"
    severity = findings[0]["severity"] if findings else "informational"
    exit_code = 2 if blocks else 1 if warns else 0
    action = (f"BLOCK merge/deploy on {branch}: {len(blocks)} gate-failing finding(s) — " + ", ".join(sorted({x['type'] for x in blocks}))[:150] + ". Blocking requires approval." if blocks else
              f"WARN on {branch}: {len(warns)} finding(s) proceed with annotation." if warns else
              f"PASS on {branch}: no gate-failing findings.")
    key = [f"{branch} ({'protected' if protected else 'feature'}): decision={decision}; {len(findings)} finding(s) ({counts['critical']} critical, {counts['high']} high); {len(blocks)} block, {len(warns)} warn"]
    key += [f"{x['gate'].upper()} {x['type']} ({x['severity']})" for x in findings[:6]]
    evidence = [{"source": f"local://{rel}" if rel else "local://appsec-devsecops/devsecops-pipeline/SKILL.md", "ref": "pipeline findings"},
                {"source": "local://appsec-devsecops/devsecops-pipeline/SKILL.md", "ref": "finding-severity and branch gate matrix"}]
    return {"agent_slug": SLUG, "intent_type": "block" if blocks else "advise", "action": action,
            "rationale": ("Each finding takes its base severity from the SKILL.md finding table (secrets, critical CVSS dependencies and critical SAST always block) and the gate is "
                          "resolved by branch: protected branches block on critical or high, feature branches block only on critical. Blocking a merge or deploy is a mutating action "
                          "requiring human approval."),
            "confidence": 0.88, "severity": severity, "key_findings": key, "evidence_references": evidence,
            "next_agents": ["sast-dast-coordinator"] if findings else [], "human_approval_required": bool(blocks), "timestamp_utc": _now(),
            "gate_decision": decision, "findings": findings, "mitre_ttps": [], "affected_assets": [branch], "_exit": exit_code}


def main() -> int:
    ap = argparse.ArgumentParser(description="USAP devsecops-pipeline")
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
    print(json.dumps(p, indent=2) if args.output == "json" else f"devsecops-pipeline: decision={p.get('gate_decision')}")
    return code


if __name__ == "__main__":
    raise SystemExit(main())
