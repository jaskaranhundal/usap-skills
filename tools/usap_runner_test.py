#!/usr/bin/env python3
"""Regression tests for tools/usap_runner.py.

The runner runs the skill's real tool before dispatch and only dispatches a
contract-conformant, non-stub payload; a stub, a missing tool or a missing
input is recorded and skipped, never dispatched as a clean result
(#139, design docs/design/2026-09-05-runner-real-tools-dr.md). --once exits
non-zero when nothing was dispatched (#148 comment 3936197828).

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
FIXTURE = "tests/fixtures/secrets-exposure-input.json"

CONFIG = f"""version: 1
jobs:
  - id: real-to-disabled
    skill: secrets-exposure
    schedule: "@daily"
    input: {FIXTURE}
    dispatch_to: crowdstrike
    dispatch_args: {{}}
    intent_type: report
    enabled: true
  - id: real-to-fixture-splunk
    skill: secrets-exposure
    schedule: "@daily"
    input: {FIXTURE}
    dispatch_to: splunk
    dispatch_args:
      spl: "index=secrets"
    intent_type: detect
    enabled: true
  - id: stub-skill
    skill: threat-intelligence
    schedule: "@daily"
    input: {FIXTURE}
    dispatch_to: splunk
    dispatch_args: {{}}
    intent_type: detect
    enabled: true
  - id: missing-tool
    skill: not-a-real-skill
    schedule: "@daily"
    input: {FIXTURE}
    dispatch_to: splunk
    dispatch_args: {{}}
    intent_type: detect
    enabled: true
  - id: no-input
    skill: secrets-exposure
    schedule: "@daily"
    dispatch_to: splunk
    dispatch_args: {{}}
    intent_type: detect
    enabled: true
"""


class Runner(unittest.TestCase):
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

    def test_real_tool_dispatches_and_carries_its_severity(self):
        rc, body, err = self._once("real-to-fixture-splunk")
        self.assertEqual(body.get("status"), "dispatched", (body, err))
        self.assertEqual(body.get("skill"), "secrets-exposure")
        self.assertEqual(body.get("skill_severity"), "critical")  # from the real tool, not synthesised
        self.assertEqual(rc, 0, err)

    def test_real_tool_to_disabled_mcp_fails(self):
        rc, body, err = self._once("real-to-disabled")
        self.assertEqual(body.get("status"), "dispatch_failed", (body, err))
        self.assertEqual(rc, 2, err)

    def test_stub_skill_is_skipped_not_dispatched(self):
        rc, body, err = self._once("stub-skill")
        self.assertEqual(body.get("status"), "skipped", (body, err))
        self.assertIn("stub", body.get("reason", "").lower() + body.get("reason", ""))
        self.assertEqual(rc, 2, err)

    def test_missing_tool_is_skipped(self):
        rc, body, err = self._once("missing-tool")
        self.assertEqual(body.get("status"), "skipped", (body, err))
        self.assertIn("no tool script", body.get("reason", ""))
        self.assertEqual(rc, 2, err)

    def test_no_input_job_is_skipped(self):
        rc, body, err = self._once("no-input")
        self.assertEqual(body.get("status"), "skipped", (body, err))
        self.assertIn("no `input`", body.get("reason", ""))
        self.assertEqual(rc, 2, err)


if __name__ == "__main__":
    unittest.main(verbosity=1)
