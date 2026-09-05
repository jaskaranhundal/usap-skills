#!/usr/bin/env python3
"""appsec-code-review_tool.py

Classifies code-review findings against the SKILL.md OWASP Top 10 review table
(severity + CWE + review approach). Read-only analysis. Emits the USAP 11-field
payload.

  python3 appsec-code-review_tool.py --input findings.json --output json
  python3 appsec-code-review_tool.py --output json    # no input: informational, exit 0

Input (see tests/fixtures/appsec-code-review-input.json):
{repo, findings[] {owasp (A01..A10), name, cwe, file, line}}.

Exit codes: 0 no finding above medium; 1 high; 2 critical. Stdlib only.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

SLUG = "appsec-code-review"
HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parents[2]
# OWASP -> (severity, default CWE, review approach)
OWASP = {
    "a01": ("critical", "CWE-284", "Check authorization on every endpoint; review IDOR patterns"),
    "a02": ("high", "CWE-327", "Verify TLS versions, key sizes, hashing algorithms"),
    "a03": ("critical", "CWE-89", "Parameterized queries, input sanitization, template injection"),
    "a04": ("high", "CWE-657", "Logic-flaw review, threat-model alignment"),
    "a05": ("high", "CWE-16", "Default credentials, debug flags, exposed admin endpoints"),
    "a06": ("high", "CWE-1035", "Dependency version check against known CVE databases"),
    "a07": ("critical", "CWE-287", "Session management, JWT validation, password storage"),
    "a08": ("high", "CWE-502", "Deserialization, SBOM validation, CI/CD integrity"),
    "a09": ("medium", "CWE-778", "Sensitive data in logs, missing security-event logging"),
    "a10": ("high", "CWE-918", "URL validation, request-forwarding controls"),
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
    raw = t.get("findings") or []
    if not t or not raw:
        return {"agent_slug": SLUG, "intent_type": "analyze", "action": "Supply code-review findings; nothing was provided.",
                "rationale": "No findings supplied.", "confidence": 0.30, "severity": "informational", "key_findings": ["No findings supplied"],
                "evidence_references": [{"source": "local://appsec-devsecops/appsec-code-review/SKILL.md", "ref": "OWASP review table (not applied)"}],
                "next_agents": [], "human_approval_required": False, "timestamp_utc": _now(), "findings": [], "_exit": 0}
    findings: List[dict] = []
    for f in raw:
        if not isinstance(f, dict):
            continue
        cat = str(f.get("owasp", "")).lower().replace(" ", "")[:3]
        sev, cwe, approach = OWASP.get(cat, ("medium", f.get("cwe", "CWE-noinfo"), "Manual review"))
        findings.append({"owasp": cat.upper() or "?", "name": f.get("name", approach), "cwe": f.get("cwe") or cwe,
                         "file": f.get("file"), "line": f.get("line"), "severity": sev, "approach": approach})
    findings.sort(key=lambda x: -SEV_RANK[x["severity"]])
    counts = {k: sum(1 for x in findings if x["severity"] == k) for k in SEV_RANK}
    severity = findings[0]["severity"] if findings else "informational"
    exit_code = 2 if counts["critical"] else 1 if counts["high"] else 0
    repo = t.get("repo", "the code")
    action = (f"{counts['critical']} critical code finding(s) in {repo}; require fix before merge: "
              + "; ".join(f"{x['name']} ({x['file']})" for x in findings if x["severity"] == "critical")[:160] + "." if counts["critical"] else
              f"{counts['high']} high code finding(s) to remediate this sprint." if counts["high"] else
              "No code finding above medium against the OWASP review table.")
    key = [f"{repo}: {len(findings)} finding(s) ({counts['critical']} critical, {counts['high']} high, {counts['medium']} medium)"]
    key += [f"{x['severity']} {x['owasp']} {x['name']} [{x['cwe']}] @ {x['file']}:{x['line']}" for x in findings[:6]]
    evidence = [{"source": f"local://{rel}" if rel else "local://appsec-devsecops/appsec-code-review/SKILL.md", "ref": "code-review findings"},
                {"source": "https://owasp.org/Top10/", "ref": "OWASP Top 10:2021"},
                {"source": "local://appsec-devsecops/appsec-code-review/SKILL.md", "ref": "OWASP review approach table"}]
    return {"agent_slug": SLUG, "intent_type": "analyze", "action": action,
            "rationale": ("Each finding is mapped to the SKILL.md OWASP Top 10 review table for severity, CWE and review approach; broken access control, injection and authentication "
                          "failures are critical. Read-only review — remediation and merge gating are downstream actions."),
            "confidence": 0.85, "severity": severity, "key_findings": key, "evidence_references": evidence,
            "next_agents": ["sast-dast-coordinator"] if findings else [], "human_approval_required": False, "timestamp_utc": _now(),
            "findings": findings, "mitre_ttps": [], "affected_assets": sorted({str(x["file"]) for x in findings if x.get("file")}), "_exit": exit_code}


def main() -> int:
    ap = argparse.ArgumentParser(description="USAP appsec-code-review")
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
    print(json.dumps(p, indent=2) if args.output == "json" else f"appsec-code-review: severity={p['severity']}")
    return code


if __name__ == "__main__":
    raise SystemExit(main())
