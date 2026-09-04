#!/usr/bin/env python3
"""Regression tests for tools/mcp_dispatch.py's response deadline.

A fake adapter that answers initialize and then stalls after a partial line
must make dispatch(timeout=1.0) raise DispatchError within a few seconds
(Codex review on PR #147, comment 3936200734). A healthy adapter still works;
an adapter that exits immediately reports the premature exit.

    python3 tools/mcp_dispatch_test.py
"""
from __future__ import annotations

import sys
import tempfile
import textwrap
import time
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "tools"))
from mcp_dispatch import DispatchError, dispatch  # noqa: E402

STALL = textwrap.dedent('''
    import json, sys, time
    for raw in sys.stdin:
        msg = json.loads(raw)
        if msg["method"] == "initialize":
            sys.stdout.write(json.dumps({"jsonrpc": "2.0", "id": msg["id"], "result": {"protocolVersion": "2025-06-18", "capabilities": {"tools": {}}, "serverInfo": {"name": "stall", "version": "0"}}}) + "\\n"); sys.stdout.flush()
        else:
            sys.stdout.write("{"); sys.stdout.flush()   # partial line, never a newline
            time.sleep(30)
''')
HEALTHY = textwrap.dedent('''
    import json, sys
    for raw in sys.stdin:
        msg = json.loads(raw)
        if msg["method"] == "initialize":
            res = {"protocolVersion": "2025-06-18", "capabilities": {"tools": {}}, "serverInfo": {"name": "ok", "version": "0"}}
        else:
            res = {"content": [{"type": "text", "text": json.dumps({"echo": msg["params"]["arguments"]})}]}
        sys.stdout.write(json.dumps({"jsonrpc": "2.0", "id": msg["id"], "result": res}) + "\\n"); sys.stdout.flush()
''')
EXIT = "import sys; sys.exit(7)\n"


def fake(tmp: Path, name: str, body: str) -> dict:
    f = tmp / f"{name}.py"
    f.write_text(body)
    return {"id": name, "command": sys.executable, "args": [str(f)]}


class Deadline(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def test_stalled_adapter_is_bounded(self):
        t0 = time.monotonic()
        with self.assertRaises(DispatchError) as ctx:
            dispatch(fake(self.dir, "stall", STALL), "post_message", {"x": 1}, timeout=1.0)
        self.assertLess(time.monotonic() - t0, 4.0)
        self.assertIn("did not respond within", str(ctx.exception))

    def test_healthy_adapter(self):
        r = dispatch(fake(self.dir, "ok", HEALTHY), "search", {"q": "a"}, timeout=5.0)
        self.assertTrue(r["ok"], r)
        self.assertEqual(r["response"], {"echo": {"q": "a"}})

    def test_premature_exit(self):
        with self.assertRaises(DispatchError) as ctx:
            dispatch(fake(self.dir, "exit", EXIT), "search", {}, timeout=5.0)
        self.assertIn("prematurely", str(ctx.exception))


if __name__ == "__main__":
    unittest.main(verbosity=1)
