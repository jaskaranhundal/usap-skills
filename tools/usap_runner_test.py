#!/usr/bin/env python3
"""Regression tests for tools/usap_runner.py one-shot exit codes.

`--once` must exit non-zero when the dispatch did not happen (disabled MCP)
so automation cannot record success for a failed job (Codex review on PR
#148, comment 3936197828), and must exit 0 when the job dispatched.

    python3 tools/usap_runner_test.py
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
RUNNER = REPO / "tools" / "usap_runner.py"

CONFIG = """version: 1
jobs:
  - id: to-disabled
    skill: secrets-exposure
    schedule: "@daily"
    dispatch_to: crowdstrike
    dispatch_args: {}
    intent_type: report
    enabled: true
  - id: to-fixture-splunk
    skill: secrets-exposure
    schedule: "@daily"
    dispatch_to: splunk
    dispatch_args:
      spl: "index=okta_logs failed_login"
    intent_type: detect
    enabled: true
"""


class OnceExitCodes(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.cfg = Path(self.tmp.name) / "runner.yaml"
        self.cfg.write_text(CONFIG)
        self.env = dict(os.environ, USAP_AUDIT_DIR=self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def _once(self, job):
        p = subprocess.run([sys.executable, str(RUNNER), "--once", job, "--config", str(self.cfg)],
                           capture_output=True, text=True, env=self.env, timeout=120, cwd=str(REPO))
        body = json.loads(p.stdout) if p.stdout.strip().startswith("{") else {}
        return p.returncode, body, p.stderr

    def test_disabled_target_exits_nonzero(self):
        rc, body, err = self._once("to-disabled")
        self.assertEqual(body.get("status"), "dispatch_failed", (body, err))
        self.assertEqual(rc, 2, err)

    def test_fixture_target_exits_zero_when_dispatched(self):
        rc, body, err = self._once("to-fixture-splunk")
        self.assertEqual(body.get("status"), "dispatched", (body, err))
        self.assertEqual(rc, 0, err)


if __name__ == "__main__":
    unittest.main(verbosity=1)
