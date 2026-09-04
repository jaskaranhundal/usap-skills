#!/usr/bin/env python3
"""Regression test for tools/mcp_audit.py: concurrent appends keep the chain intact.

Eight processes append 25 entries each to the same daily log. Without the
per-log exclusive lock two writers could read the same predecessor hash and
verify() would report a broken chain during ordinary parallel operation
(Codex review on PR #148, comment 3936197783).

    python3 tools/mcp_audit_test.py
"""
from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "tools"))
from mcp_audit import verify  # noqa: E402

WRITER = (
    "import sys; sys.path.insert(0, %r)\n"
    "from mcp_audit import write_audit\n"
    "for i in range(25): write_audit({'event': 'route', 'decision': {'w': sys.argv[1], 'i': i}})\n"
) % str(REPO / "tools")


class ConcurrentAppends(unittest.TestCase):
    def test_chain_survives_parallel_writers(self):
        with tempfile.TemporaryDirectory() as tmp:
            env = dict(os.environ, USAP_AUDIT_DIR=tmp)
            env.pop("USAP_AUDIT_KEY", None)
            procs = [subprocess.Popen([sys.executable, "-c", WRITER, str(w)], env=env) for w in range(8)]
            for p in procs:
                self.assertEqual(p.wait(timeout=120), 0)
            logs = sorted(Path(tmp).glob("*.jsonl"))
            self.assertEqual(len(logs), 1, logs)
            lines = [l for l in logs[0].read_text().splitlines() if l.strip()]
            self.assertEqual(len(lines), 200)
            ok, errors = verify(logs[0])
            self.assertTrue(ok, errors[:5])
            self.assertTrue((Path(tmp) / (logs[0].stem + ".lock")).exists())


if __name__ == "__main__":
    unittest.main(verbosity=1)
