#!/usr/bin/env python3
"""Shared scaffolding for USAP specialist-MCP adapters.

Every adapter is a small MCP server that the USAP master MCP launches as a
subprocess when a capability needs to be invoked. The adapter:

  1. Reads JSON-RPC frames from stdin.
  2. Handles `initialize`, `tools/list`, and `tools/call`.
  3. Writes responses to stdout.
  4. Exits cleanly when stdin closes.

Mode is controlled by USAP_ADAPTER_MODE:
  - "fixture" (default) — return canned data. Safe for CI + first-time users.
  - "live"              — make real API calls. Requires the adapter's
                          documented credentials (e.g. SLACK_BOT_TOKEN).

Adapters call ``run_adapter(name, version, capabilities, fixtures, live_fn)``
with their declared capabilities and a callable for live mode (or None if
the adapter has not implemented live mode yet — Phase 3 ships fixture mode
for all three reference adapters; live wiring is a single-line swap per
capability).
"""
from __future__ import annotations

import json
import os
import sys
import traceback
from typing import Callable, Optional


PROTOCOL_VERSION = "2025-06-18"


def _send(obj: dict) -> None:
    sys.stdout.write(json.dumps(obj) + "\n")
    sys.stdout.flush()


def _err(msg_id, code: int, message: str) -> dict:
    return {
        "jsonrpc": "2.0",
        "id": msg_id,
        "error": {"code": code, "message": message},
    }


def _result(msg_id, result: dict) -> dict:
    return {"jsonrpc": "2.0", "id": msg_id, "result": result}


def run_adapter(
    name: str,
    version: str,
    capabilities: list[dict],
    fixtures: dict[str, dict],
    live_fn: Optional[Callable[[str, dict], dict]] = None,
) -> int:
    """Run a USAP specialist-MCP adapter.

    Args:
        name:           Adapter name (e.g. "slack").
        version:        Adapter version (semver string).
        capabilities:   List of MCP tool definitions advertised to the router.
                        Each entry follows MCP's tools/list schema.
        fixtures:       Map of capability id -> canned response dict, used when
                        USAP_ADAPTER_MODE != "live" (the default).
        live_fn:        Optional callable (capability_id, arguments) -> result
                        dict, invoked when USAP_ADAPTER_MODE == "live". Adapter
                        implementations supply this for real API integration.

    Returns:
        Exit code (0 normal).
    """
    mode = os.environ.get("USAP_ADAPTER_MODE", "fixture")

    for raw in sys.stdin:
        line = raw.strip()
        if not line:
            continue
        try:
            msg = json.loads(line)
        except json.JSONDecodeError as exc:
            sys.stderr.write(f"adapter:{name}: invalid JSON: {exc}\n")
            continue

        method = msg.get("method")
        msg_id = msg.get("id")
        params = msg.get("params") or {}

        if msg_id is None:
            # Notification — no response expected
            continue

        if method == "initialize":
            _send(_result(msg_id, {
                "protocolVersion": PROTOCOL_VERSION,
                "capabilities": {"tools": {}},
                "serverInfo": {
                    "name": f"usap-adapter-{name}",
                    "version": version,
                },
                "instructions": (
                    f"USAP specialist-MCP adapter for {name}. "
                    f"Mode: {mode}. Capabilities: "
                    f"{[c['name'] for c in capabilities]}"
                ),
            }))
            continue

        if method == "tools/list":
            _send(_result(msg_id, {"tools": capabilities}))
            continue

        if method == "tools/call":
            tool_name = params.get("name")
            args = params.get("arguments", {}) or {}
            try:
                if mode == "live" and live_fn is not None:
                    result = live_fn(tool_name, args)
                else:
                    if tool_name not in fixtures:
                        _send(_err(msg_id, -32602,
                                   f"Unknown capability: {tool_name}"))
                        continue
                    # Fixture mode — augment the canned response with the
                    # args so the test client can verify the dispatch shape.
                    fixture = dict(fixtures[tool_name])
                    fixture["_mode"] = "fixture"
                    fixture["_adapter"] = name
                    fixture["_capability"] = tool_name
                    fixture["_received_args"] = args
                    result = fixture
                _send(_result(msg_id, {
                    "content": [
                        {"type": "text", "text": json.dumps(result, indent=2)}
                    ],
                }))
            except Exception as exc:
                _send(_err(msg_id, -32000, f"{type(exc).__name__}: {exc}"))
            continue

        _send(_err(msg_id, -32601, f"Method not found: {method}"))

    return 0
