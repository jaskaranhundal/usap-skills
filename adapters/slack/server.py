#!/usr/bin/env python3
"""USAP specialist-MCP adapter: Slack (Phase 3 fixture mode).

Capabilities (matching registry/usap-mcp-registry.yaml):

  - read_channel    Read the last N messages from a Slack channel.
                    Read-only. Auto-routed by USAP master MCP.
  - post_message    Post a message to a Slack channel.
                    Mutating. Gated behind human_approval_required.

Modes:
  USAP_ADAPTER_MODE=fixture (default)  Returns canned data shaped like a
                                       real Slack API response. Safe for CI
                                       and first-time users.
  USAP_ADAPTER_MODE=live                Calls the Slack Web API using
                                       SLACK_BOT_TOKEN. Not implemented in
                                       Phase 3 — left as a single-line
                                       integration point for a follow-up PR.

Stdlib only.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from _lib import run_adapter  # noqa: E402


CAPABILITIES = [
    {
        "name": "read_channel",
        "description": "Read the last N messages from a Slack channel.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "channel": {"type": "string", "description": "Channel ID or name"},
                "limit": {"type": "integer", "default": 50},
            },
            "required": ["channel"],
        },
    },
    {
        "name": "post_message",
        "description": "Post a message to a Slack channel. Mutating.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "channel": {"type": "string"},
                "text": {"type": "string"},
            },
            "required": ["channel", "text"],
        },
    },
]


FIXTURES = {
    "read_channel": {
        "ok": True,
        "messages": [
            {"user": "U001", "ts": "1719415200.000100",
             "text": "Heads up — saw an unusual surge of failed Okta logins from 198.51.100.42 last hour."},
            {"user": "U002", "ts": "1719415300.000200",
             "text": "Already on it. SIEM rule fired at 14:35 UTC."},
        ],
    },
    "post_message": {
        "ok": True,
        "channel": "<channel>",
        "ts": "1719420000.000100",
        "message": {"text": "<text>"},
    },
}


def main() -> int:
    return run_adapter(
        name="slack",
        version="1.6.0",
        capabilities=CAPABILITIES,
        fixtures=FIXTURES,
    )


if __name__ == "__main__":
    sys.exit(main())
