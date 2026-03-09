#!/usr/bin/env python3
"""Code Reviewer CLI helper for USAP skill package."""

import argparse
import json


REVIEW_DIMENSIONS = ["architecture", "performance", "security", "testing", "quality"]
REVIEW_DECISIONS = ["approve", "approve_with_comments", "request_changes"]


def main() -> int:
    parser = argparse.ArgumentParser(description="Code Reviewer helper")
    parser.add_argument("--input", type=str, help="Path to JSON input with PR diff context")
    parser.add_argument("--output", choices=["text", "json"], default="text")
    args = parser.parse_args()

    payload = {
        "agent_slug": "code-reviewer",
        "agent_name": "Code Reviewer",
        "status": "ok",
        "phase": "phase1",
        "plane": "work",
        "level": "L4",
        "review_dimensions": REVIEW_DIMENSIONS,
        "possible_decisions": REVIEW_DECISIONS
    }

    if args.output == "json":
        print(json.dumps(payload, indent=2))
    else:
        print(f"Code Reviewer tool executed: {payload['status']}")
        print(f"Review dimensions: {', '.join(REVIEW_DIMENSIONS)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
