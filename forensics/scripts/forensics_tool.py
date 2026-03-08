#!/usr/bin/env python3
"""Forensics CLI helper for USAP skill package."""

import argparse
import json


def main() -> int:
    parser = argparse.ArgumentParser(description="Forensics helper")
    parser.add_argument("--input", type=str, help="Path to JSON input")
    parser.add_argument("--output", choices=["text", "json"], default="text")
    args = parser.parse_args()

    payload = {
        "agent_slug": "forensics",
        "agent_name": "Forensics",
        "status": "ok",
        "phase": "phase2",
        "plane": "work",
        "level": "L3"
    }

    if args.output == "json":
        print(json.dumps(payload, indent=2))
    else:
        print(f"Forensics tool executed: {payload['status']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
