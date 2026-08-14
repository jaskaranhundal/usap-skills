#!/usr/bin/env python3
"""AppSec Code Review CLI helper for USAP skill package."""

import argparse
import json
import sys
from datetime import datetime, timezone


OWASP_CATEGORIES = [
    "A01: Broken Access Control",
    "A02: Cryptographic Failures",
    "A03: Injection",
    "A04: Insecure Design",
    "A05: Security Misconfiguration",
    "A06: Vulnerable and Outdated Components",
    "A07: Identification and Authentication Failures",
    "A08: Software and Data Integrity Failures",
    "A09: Security Logging and Monitoring Failures",
    "A10: Server-Side Request Forgery",
]


def main() -> int:
    parser = argparse.ArgumentParser(description="AppSec Code Review helper")
    parser.add_argument("--input", type=str, help="Path to JSON input with PR diff context")
    parser.add_argument("--output", choices=["text", "json"], default="text")
    args = parser.parse_args()

    payload = {
        "agent_slug": "appsec-code-review",
        "agent_name": "AppSec Code Review",
        "status": "not_implemented",
        "intent_type": "report",
        "action": "No analysis was performed. This tool is a stub: it does not read --input. Run the SKILL.md workflow with an LLM, or supply results from a real scanner.",
        "rationale": "Stub implementation. The tool reports its declared capability surface only and performs no analysis on the supplied input. Treat this as an absence of evidence, never as a clean result.",
        "confidence": 0.0,
        "severity": "informational",
        "key_findings": [
            "Not implemented - no analysis was performed on the supplied input."
        ],
        "evidence_references": [],
        "next_agents": [],
        "human_approval_required": False,
        "timestamp_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "phase": "phase1",
        "plane": "work",
        "level": "L4",
        "owasp_coverage": OWASP_CATEGORIES,
        "gate_decisions": ["block", "warn", "pass"]
    }

    if args.output == "json":
        print(json.dumps(payload, indent=2))
    else:
        print(f"AppSec Code Review tool executed: {payload['status']}")
        print(f"OWASP coverage: {len(OWASP_CATEGORIES)} categories")
    print(
        "WARNING: this tool is a stub - it did not read the supplied input and "
        "performed no analysis. Exit code 2 means NOT IMPLEMENTED, not a clean result.",
        file=sys.stderr,
    )
    return 3


if __name__ == "__main__":
    raise SystemExit(main())
