#!/usr/bin/env python3
"""OWASP Top 10 2025 classifier.

Ranks a webapp finding into OWASP Top 10 categories with confidence,
emits a USAP 11-field contract payload. Stdlib only.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

SLUG = "owasp-top10-classifier"

# (code, label, keywords, cwe_anchors)
CATEGORIES = [
    ("A01", "Broken access control",
     ("access-control", "idor", "path traversal", "bola", "directory traversal", "csrf"),
     ("CWE-22", "CWE-285", "CWE-639")),
    ("A02", "Cryptographic failures",
     ("crypto", "tls", "mac", "weak hash", "md5", "plaintext password"),
     ("CWE-327", "CWE-330")),
    ("A03", "Injection",
     ("sql", "nosql", "cmd-inject", "command injection", "xxe", "xss", "dom",
      "template-inject", "ldap-inject"),
     ("CWE-79", "CWE-89", "CWE-77", "CWE-91")),
    ("A04", "Insecure design",
     ("design flaw", "business logic", "race condition", "missing rate limit"),
     ("CWE-840",)),
    ("A05", "Security misconfiguration",
     ("default password", "header missing", "cors *", "s3 public", "debug enabled",
      "misconfig"),
     ("CWE-16", "CWE-732")),
    ("A06", "Vulnerable and outdated components",
     ("cve-", "library out of date", "dependency vuln"),
     ("CWE-1104",)),
    ("A07", "Identification and authentication failures",
     ("auth bypass", "weak session", "mfa missing", "password policy"),
     ("CWE-287", "CWE-384")),
    ("A08", "Software and data integrity failures",
     ("serial", "deserialization", "unsafe-load", "supply chain"),
     ("CWE-502", "CWE-829")),
    ("A09", "Security logging and monitoring failures",
     ("no logs", "audit missing", "siem gap"),
     ("CWE-778",)),
    ("A10", "Server-side request forgery",
     ("ssrf", "internal callback", "metadata endpoint"),
     ("CWE-918",)),
]

DEFAULT_FINDING = {
    "description": (
        "Endpoint /api/v1/profile accepts PUT from unauthenticated origin "
        "(CSRF token absent); allows path traversal via the 'next' query parameter."
    ),
    "cwe_id": "CWE-639",
    "cvss_score": 6.2,
    "source": "scanner",
    "evidence": [
        {
            "source": "scanner",
            "ref": "owasp-zap://alert/12871",
            "quote": "Endpoint /api/v1/profile accepts PUT from unauthenticated origin "
                     "(CSRF token absent)",
        }
    ],
}


def _classify(finding: dict) -> list[tuple[str, str, float, list[str]]]:
    desc = (finding.get("description") or "").lower()
    cwe = (finding.get("cwe_id") or "").upper()
    cvss = float(finding.get("cvss_score") or 0)

    results = []
    for code, label, kws, cwes in CATEGORIES:
        score = 0.0
        hits = []
        for kw in kws:
            if kw in desc:
                score = min(0.7, score + 0.5)
                hits.append(kw)
        if cwe in cwes:
            score = min(1.0, score + 0.5)
            hits.append(cwe)
        results.append((code, label, score, hits))

    if cvss >= 7.0 and any(r[2] > 0.3 for r in results):
        bumped = []
        for code, label, score, hits in results:
            if score > 0.3:
                score = min(1.0, score + 0.1)
                hits = hits + [f"cvss:{cvss}"]
            bumped.append((code, label, score, hits))
        results = bumped

    return sorted(results, key=lambda r: -r[2])


def _severity(top_score: float, cvss: float) -> str:
    if top_score >= 0.85 and cvss >= 9.0:
        return "critical"
    if top_score >= 0.85 and cvss >= 7.0:
        return "high"
    if top_score >= 0.7:
        return "high"
    if top_score >= 0.5:
        return "medium"
    return "informational"


def classify(finding: dict) -> dict:
    ranked = _classify(finding)
    top = ranked[0]
    cvss = float(finding.get("cvss_score") or 0)
    severity = _severity(top[2], cvss)

    next_agents = ["webapp-risk-triage"]
    if len(ranked) > 1 and (top[2] - ranked[1][2]) < 0.1 and ranked[1][2] >= 0.5:
        next_agents.append("sast-dast-coordinator")
    intent = "detect" if top[2] >= 0.5 else "report"

    key_findings = []
    for code, label, score, hits in ranked[:3]:
        if score == 0:
            continue
        hit_text = ", ".join(hits) if hits else "no specific hit"
        key_findings.append(f"{code} ({label}): score {score:.2f} (hits: {hit_text})")
    if not key_findings:
        key_findings.append(
            "No OWASP category scored above the noise floor — emit as informational"
        )

    evidence_refs = []
    for ev in finding.get("evidence", []):
        if isinstance(ev, dict):
            entry = {k: ev.get(k, "") for k in ("source", "ref", "quote") if ev.get(k)}
            if entry:
                evidence_refs.append(entry)

    return {
        "agent_slug": SLUG,
        "intent_type": intent,
        "action": f"Hand off {top[0]} ranking to {next_agents[0]} for re-routing.",
        "rationale": (
            f"Top match {top[0]} ({top[1]}) scored {top[2]:.2f} on keyword + CWE signals. "
            f"CVSS={cvss}. Severity derived from rubric in workflow.md."
        ),
        "confidence": round(top[2], 2),
        "severity": severity,
        "key_findings": key_findings,
        "evidence_references": evidence_refs,
        "next_agents": next_agents,
        "human_approval_required": False,
        "timestamp_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }


def _render_human(payload: dict) -> str:
    lines = [
        "BOTTOM LINE: " + payload["action"],
        f"TOP MATCH SEVERITY: {payload['severity'].upper()}  CONFIDENCE: {payload['confidence']:.2f}",
        "WHAT:",
    ]
    lines += [f"  - {f}" for f in payload["key_findings"]]
    lines.append("NEXT: " + " -> ".join(payload["next_agents"]))
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--input",
        help="JSON file with a finding payload. If omitted, the bundled sample is used.",
    )
    parser.add_argument("--output", choices=("json", "human"), default="json")
    args = parser.parse_args()

    if args.input:
        try:
            finding = json.loads(Path(args.input).read_text(encoding="utf-8"))
        except (FileNotFoundError, json.JSONDecodeError) as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 2
    else:
        finding = DEFAULT_FINDING

    payload = classify(finding)
    if args.output == "json":
        print(json.dumps(payload, indent=2))
    else:
        print(_render_human(payload))
    return 0


if __name__ == "__main__":
    sys.exit(main())
