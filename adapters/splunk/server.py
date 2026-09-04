#!/usr/bin/env python3
"""USAP specialist-MCP adapter: Splunk (Phase 3 fixture mode).

Capabilities:
  - search        Run an SPL search. Read-only.
  - list_indexes  List available indexes + EPS health. Read-only.

Live mode would use SPLUNK_HOST + SPLUNK_TOKEN against the Splunk REST API.

Stdlib only.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from _lib import run_adapter  # noqa: E402


CAPABILITIES = [
    {
        "name": "search",
        "description": "Run an SPL search and return the result rows.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "spl": {"type": "string"},
                "earliest": {"type": "string", "default": "-15m"},
                "latest": {"type": "string", "default": "now"},
                "max_count": {"type": "integer", "default": 100},
            },
            "required": ["spl"],
        },
    },
    {
        "name": "list_indexes",
        "description": "List available indexes and their EPS health.",
        "inputSchema": {"type": "object", "properties": {}},
    },
]


FIXTURES = {
    "search": {
        "spl": "<spl>",
        "result_count": 3,
        "results": [
            {"_time": "2026-06-26T14:32:00Z", "src_ip": "198.51.100.42",
             "user": "alice", "action": "failed_login", "count": 12},
            {"_time": "2026-06-26T14:33:00Z", "src_ip": "198.51.100.42",
             "user": "bob", "action": "failed_login", "count": 14},
            {"_time": "2026-06-26T14:34:00Z", "src_ip": "198.51.100.42",
             "user": "carol", "action": "failed_login", "count": 9},
        ],
    },
    "list_indexes": {
        "indexes": [
            {"name": "main", "eps_health": "ok", "events_today": 4_200_000},
            {"name": "security", "eps_health": "ok", "events_today": 18_000_000},
            {"name": "okta_logs", "eps_health": "degraded", "events_today": 230_000},
        ],
    },
}


def main() -> int:
    return run_adapter(
        name="splunk",
        version="1.6.0",
        capabilities=CAPABILITIES,
        fixtures=FIXTURES,
    )


if __name__ == "__main__":
    sys.exit(main())
