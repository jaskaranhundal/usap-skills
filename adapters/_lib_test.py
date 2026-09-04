#!/usr/bin/env python3
"""Regression tests for adapters/_lib.py mode selection.

Live mode with no live handler must return an error and never a fixture
(Codex review on PR #147, comment 3936200728). Fixture mode is unchanged.

    python3 adapters/_lib_test.py
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SLACK = REPO / "adapters" / "slack" / "server.py"

INIT = {"jsonrpc": "2.0", "id": 1, "method": "initialize",
        "params": {"protocolVersion": "2025-06-18", "capabilities": {}}}
CALL = {"jsonrpc": "2.0", "id": 2, "method": "tools/call",
        "params": {"name": "post_message", "arguments": {"channel": "#sec", "text": "hi"}}}


def run_adapter(mode: str):
    env = dict(os.environ, USAP_ADAPTER_MODE=mode)
    p = subprocess.run([sys.executable, str(SLACK)], input=json.dumps(INIT) + "\n" + json.dumps(CALL) + "\n",
                       capture_output=True, text=True, env=env, timeout=30, cwd=str(REPO))
    lines = [json.loads(l) for l in p.stdout.splitlines() if l.strip()]
    return p, lines


class LiveModeGuard(unittest.TestCase):
    def test_live_without_handler_errors_and_makes_no_call(self):
        p, lines = run_adapter("live")
        self.assertEqual(len(lines), 2, p.stdout)
        call = lines[1]
        self.assertIn("error", call, call)
        self.assertEqual(call["error"]["code"], -32001)
        self.assertIn("no call was made", call["error"]["message"])
        self.assertNotIn('"_mode": "fixture"', p.stdout)
        self.assertIn("no live handler", p.stderr)

    def test_fixture_mode_unchanged(self):
        p, lines = run_adapter("fixture")
        self.assertEqual(len(lines), 2, p.stdout)
        text = lines[1]["result"]["content"][0]["text"]
        payload = json.loads(text)
        self.assertEqual(payload["_mode"], "fixture")
        self.assertEqual(payload["_capability"], "post_message")


if __name__ == "__main__":
    unittest.main(verbosity=1)
