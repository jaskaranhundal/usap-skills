#!/usr/bin/env python3
"""Incident Commander CLI helper for USAP skill package."""

import argparse
import json


def main() -> int:
    parser = argparse.ArgumentParser(description="Incident Commander helper")
    parser.add_argument("--input", type=str, help="Path to JSON input")
    parser.add_argument("--output", choices=["text", "json"], default="text")
    args = parser.parse_args()

    payload = {
        "agent_slug": "incident-commander",
        "agent_name": "Incident Commander",
        "status": "ok",
        "phase": "phase2",
        "plane": "work",
        "level": "L3"
    }

    if args.output == "json":
        print(json.dumps(payload, indent=2))
    else:
        print(f"Incident Commander tool executed: {payload['status']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
