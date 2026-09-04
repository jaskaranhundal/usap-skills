#!/usr/bin/env python3
"""Pipeline Security Scan CLI helper for USAP skill package."""

import argparse
import json
import sys
from datetime import datetime, timezone


SCAN_CATEGORIES = [
    "secrets-in-env-vars",
    "missing-sast-stage",
    "missing-sca-stage",
    "missing-secrets-scan-stage",
    "artifact-signing-gap",
    "sbom-generation-gap",
    "unpinned-actions",
    "overly-permissive-pipeline-tokens",
]


def main() -> int:
    parser = argparse.ArgumentParser(description="Pipeline Security Scan helper")
    parser.add_argument("--input", type=str, help="Path to pipeline YAML file or JSON input")
    parser.add_argument("--output", choices=["text", "json"], default="text")
    args = parser.parse_args()

    payload = {
        "agent_slug": "pipeline-security-scan",
        "agent_name": "Pipeline Security Scan",
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
        "scan_categories": SCAN_CATEGORIES,
        "supported_pipelines": [
            "github-actions",
            "gitlab-ci",
            "jenkins",
            "circleci",
            "bitbucket-pipelines"
        ]
    }

    if args.output == "json":
        print(json.dumps(payload, indent=2))
    else:
        print(f"Pipeline Security Scan tool executed: {payload['status']}")
        print(f"Scan categories: {len(SCAN_CATEGORIES)}")
    print(
        "WARNING: this tool is a stub - it did not read the supplied input and "
        "performed no analysis. Exit code 2 means NOT IMPLEMENTED, not a clean result.",
        file=sys.stderr,
    )
    return 3


if __name__ == "__main__":
    raise SystemExit(main())
