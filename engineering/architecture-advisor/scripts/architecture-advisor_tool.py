#!/usr/bin/env python3
"""Architecture Advisor CLI helper for USAP skill package."""

import argparse
import json


TRADE_OFF_DIMENSIONS = [
    "performance",
    "scalability",
    "reliability",
    "operability",
    "security",
    "cost",
    "developer_experience",
    "data_consistency",
]


def main() -> int:
    parser = argparse.ArgumentParser(description="Architecture Advisor helper")
    parser.add_argument("--input", type=str, help="Path to JSON input with design context")
    parser.add_argument("--output", choices=["text", "json"], default="text")
    args = parser.parse_args()

    payload = {
        "agent_slug": "architecture-advisor",
        "agent_name": "Architecture Advisor",
        "status": "ok",
        "phase": "phase1",
        "plane": "governance",
        "level": "L3",
        "trade_off_dimensions": TRADE_OFF_DIMENSIONS,
        "adr_format": "MADR"
    }

    if args.output == "json":
        print(json.dumps(payload, indent=2))
    else:
        print(f"Architecture Advisor tool executed: {payload['status']}")
        print(f"Trade-off dimensions: {len(TRADE_OFF_DIMENSIONS)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
