#!/usr/bin/env python3
"""SRE Runbook Advisor CLI helper for USAP skill package."""

import argparse
import json


BURN_RATE_THRESHOLDS = [
    (14.4, "critical", "Page on-call immediately"),
    (6.0, "high", "Ticket + Slack alert"),
    (1.0, "medium", "Warning — monitor closely"),
    (0.0, "low", "Within error budget"),
]


def calculate_burn_rate(error_rate: float, slo_target: float) -> float:
    error_budget = 1.0 - slo_target
    if error_budget <= 0:
        return 0.0
    return round(error_rate / error_budget, 2)


def burn_rate_to_tier(burn_rate: float) -> dict:
    for threshold, severity, action in BURN_RATE_THRESHOLDS:
        if burn_rate >= threshold:
            return {"severity": severity, "action": action}
    return {"severity": "low", "action": "Within error budget"}


def main() -> int:
    parser = argparse.ArgumentParser(description="SRE Runbook Advisor helper")
    parser.add_argument("--error-rate", type=float, default=0.01, help="Current error rate (0.0-1.0)")
    parser.add_argument("--slo-target", type=float, default=0.999, help="SLO target (e.g. 0.999)")
    parser.add_argument("--output", choices=["text", "json"], default="text")
    args = parser.parse_args()

    burn_rate = calculate_burn_rate(args.error_rate, args.slo_target)
    tier = burn_rate_to_tier(burn_rate)

    payload = {
        "agent_slug": "sre-runbook-advisor",
        "agent_name": "SRE Runbook Advisor",
        "status": "ok",
        "phase": "phase2",
        "plane": "work",
        "level": "L3",
        "slo_analysis": {
            "slo_target": args.slo_target,
            "error_rate": args.error_rate,
            "burn_rate": burn_rate,
            "severity": tier["severity"],
            "recommended_action": tier["action"]
        }
    }

    if args.output == "json":
        print(json.dumps(payload, indent=2))
    else:
        print(f"SRE Runbook Advisor — Burn Rate: {burn_rate}x ({tier['severity']})")
        print(f"Action: {tier['action']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
