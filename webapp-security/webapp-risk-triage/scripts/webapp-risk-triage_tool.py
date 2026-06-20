#!/usr/bin/env python3
"""Webapp Risk Triage — first-pass triage of a webapp security finding.

Reads a finding JSON, applies the severity matrix and routing rules from
``references/workflow.md``, and emits a USAP 11-field contract payload.

Usage::

    python3 webapp-risk-triage_tool.py                     # bundled sample
    python3 webapp-risk-triage_tool.py --input finding.json
    python3 webapp-risk-triage_tool.py --output human

Stdlib only. Exits 0 on success, 2 on bad input.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

SLUG = "webapp-risk-triage"

# Severity matrix from references/workflow.md.
# Tier order: 0=informational, 1=low, 2=medium, 3=high, 4=critical.
SEVERITY_TIERS = ("informational", "low", "medium", "high", "critical")
SEVERITY_MATRIX = {
    "anonymous":     {"public": 0, "internal": 1, "confidential": 2, "regulated": 3},
    "authenticated": {"public": 1, "internal": 2, "confidential": 3, "regulated": 4},
    "admin":         {"public": 2, "internal": 3, "confidential": 4, "regulated": 4},
}

EXPLOIT_BUMP = {"theoretical": 0, "poc": 0, "public-exploit": 1, "active-in-the-wild": 1}

OWASP_HEURISTICS = (
    (("sql", "nosql", "cmd-inject", "xxe", "xss", "dom", "template-inject"), "A03"),
    (("auth", "session", "mfa", "password", "weak_auth"), "A07"),
    (("redirect", "cors", "csrf-token-missing", "broken_access"), "A01"),
    (("public", "default password", "header missing", "misconfig"), "A05"),
    (("serial", "deserialization"), "A08"),
)

DEFAULT_FINDING = {
    "finding_type": "sql_injection",
    "target_url": "https://example.com/api/v1/orders/<id>",
    "auth_state": "authenticated",
    "data_sensitivity": "confidential",
    "exploit_availability": "public-exploit",
    "evidence": [
        {
            "source": "scanner",
            "ref": "burp-pro://scan/2891/issue/sqli-1",
            "quote": "Parameter order_id reflected in error message with PostgreSQL stack trace",
        },
        {
            "source": "siem",
            "ref": "splunk://search/abc123",
            "quote": "10x increase in 500-status responses from /api/v1/orders in the 6-hour window",
        },
    ],
    "environment": "production",
}


def _classify_owasp(finding: dict) -> list[str]:
    haystack = " ".join([
        str(finding.get("finding_type", "")),
        " ".join(e.get("quote", "") for e in finding.get("evidence", []) if isinstance(e, dict)),
    ]).lower()
    matches = []
    for keywords, code in OWASP_HEURISTICS:
        if any(kw in haystack for kw in keywords):
            matches.append(code)
    # Deduplicate while preserving order.
    seen = set()
    return [c for c in matches if not (c in seen or seen.add(c))]


def _score_severity(finding: dict) -> str:
    auth = finding.get("auth_state", "authenticated")
    data = finding.get("data_sensitivity", "internal")
    tier = SEVERITY_MATRIX.get(auth, SEVERITY_MATRIX["authenticated"]).get(data, 2)
    tier = min(4, tier + EXPLOIT_BUMP.get(finding.get("exploit_availability", "theoretical"), 0))
    return SEVERITY_TIERS[tier]


def _confidence(finding: dict) -> float:
    score = 0.92
    evidence = finding.get("evidence") or []
    if len(evidence) < 2:
        score = min(score, 0.7)
    if not finding.get("environment"):
        score = min(score, 0.6)
    if finding.get("exploit_availability") == "theoretical":
        score = min(score, 0.6)
    return max(0.4, score)


def _route(finding: dict, severity: str) -> tuple[list[str], str]:
    """Return (next_agents, intent_type)."""
    env = finding.get("environment")
    exploit = finding.get("exploit_availability")
    ftype = finding.get("finding_type", "")
    auth = finding.get("auth_state")

    if env == "production" and exploit == "active-in-the-wild":
        return ["incident-classification", "compliance-mapping"], "escalate"
    if severity == "critical":
        if auth == "anonymous":
            return ["incident-classification"], "escalate"
        return ["incident-classification", "compliance-mapping"], "escalate"
    if ftype == "weak_auth":
        return ["identity-access-risk"], "advise"
    if finding.get("data_sensitivity") == "regulated":
        return ["owasp-top10-classifier", "compliance-mapping"], "analyze"
    return ["owasp-top10-classifier"], "analyze"


def triage(finding: dict) -> dict:
    """Build the 11-field contract payload from a finding."""
    severity = _score_severity(finding)
    next_agents, intent_type = _route(finding, severity)
    confidence = _confidence(finding)
    owasp = _classify_owasp(finding)

    key_findings = [
        f"Finding type: {finding.get('finding_type', 'unknown')} on {finding.get('target_url', '<no url>')}",
        f"Auth state: {finding.get('auth_state', 'unknown')}; data sensitivity: {finding.get('data_sensitivity', 'unknown')}",
        f"Exploit availability: {finding.get('exploit_availability', 'unknown')}; environment: {finding.get('environment', 'unknown')}",
    ]
    if owasp:
        key_findings.append(
            "Likely OWASP category: " + ", ".join(owasp)
        )

    evidence_refs = []
    for ev in finding.get("evidence", []):
        if isinstance(ev, dict):
            entry = {k: ev.get(k, "") for k in ("source", "ref", "quote") if ev.get(k)}
            if entry:
                evidence_refs.append(entry)

    rationale_parts = [
        f"Severity {severity} derived from auth_state '{finding.get('auth_state')}' x data_sensitivity "
        f"'{finding.get('data_sensitivity')}' with exploit-availability adjustment "
        f"'{finding.get('exploit_availability')}'.",
        f"Routed to {', '.join(next_agents)} per workflow.md routing table.",
    ]
    if owasp:
        rationale_parts.append("OWASP heuristics matched: " + ", ".join(owasp) + ".")

    payload = {
        "agent_slug": SLUG,
        "intent_type": intent_type,
        "action": f"Hand off to {next_agents[0]} for {intent_type}; include the full finding payload as context.",
        "rationale": " ".join(rationale_parts),
        "confidence": round(confidence, 2),
        "severity": severity,
        "key_findings": key_findings,
        "evidence_references": evidence_refs,
        "next_agents": next_agents,
        "human_approval_required": False,
        "timestamp_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
    if "T1190" not in payload.get("mitre_ttps", []):
        payload["mitre_ttps"] = ["T1190"]
    if finding.get("target_url"):
        payload["affected_assets"] = [finding["target_url"]]
    if finding.get("data_sensitivity") == "regulated":
        payload["regulatory_flags"] = ["PCI-DSS 6.5.1", "GDPR Art. 32"]
    return payload


def _render_human(payload: dict) -> str:
    lines = [
        "BOTTOM LINE: " + payload["action"],
        f"SEVERITY: {payload['severity'].upper()}  CONFIDENCE: {payload['confidence']:.2f}",
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
    parser.add_argument(
        "--output",
        choices=("json", "human"),
        default="json",
    )
    args = parser.parse_args()

    if args.input:
        try:
            finding = json.loads(Path(args.input).read_text(encoding="utf-8"))
        except (FileNotFoundError, json.JSONDecodeError) as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 2
    else:
        finding = DEFAULT_FINDING

    payload = triage(finding)
    if args.output == "json":
        print(json.dumps(payload, indent=2))
    else:
        print(_render_human(payload))
    return 0


if __name__ == "__main__":
    sys.exit(main())
