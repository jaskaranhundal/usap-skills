#!/usr/bin/env python3
"""Tests for the USAP persona gate (plugins/usap/hooks/usap_gate.py).

Runs the gate as a subprocess the way Claude Code does (JSON on stdin), in a
temporary audit directory, and checks the acceptance criteria from
docs/design/2026-09-04-persona-gate-hooks-design.md plus the DR conditions.

    python3 tools/usap_gate_test.py
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
GATE = REPO / "plugins" / "usap" / "hooks" / "usap_gate.py"
sys.path.insert(0, str(REPO / "tools"))
from mcp_audit import verify  # noqa: E402


def run(args, stdin=None, env=None):
    e = dict(os.environ)
    e.update(env or {})
    p = subprocess.run([sys.executable, str(GATE), *args], input=stdin, capture_output=True, text=True, env=e)
    return p.returncode, p.stdout, p.stderr


class Classify(unittest.TestCase):
    def test_design_review_trigger(self):
        rc, out, _ = run(["classify", "harden the runner against direct push to the pipeline"])
        d = json.loads(out)
        self.assertEqual((rc, d["persona"], d["pass"]), (0, "usap-devsecops", "DR"))

    def test_incident_outranks_design(self):
        d = json.loads(run(["classify", "we have a breach, rotate the credentials"])[1])
        self.assertEqual((d["persona"], d["pass"]), ("usap-incident-responder", "IR"))

    def test_finding_to_ticket(self):
        d = json.loads(run(["classify", "turn this finding into a Jira ticket"])[1])
        self.assertEqual(d["pass"], "PR")

    def test_no_match_is_silent(self):
        d = json.loads(run(["classify", "rename the variable and fix the typo in the README"])[1])
        self.assertIsNone(d["persona"])

    def test_word_boundaries(self):
        # "gatekeeper" and "secretary" must not trip the gate
        d = json.loads(run(["classify", "the gatekeeper called the secretary"])[1])
        self.assertIsNone(d["persona"])


class CheckSkill(unittest.TestCase):
    def test_present(self):
        rc, out, _ = run(["check-skill", "secrets-exposure", "--root", str(REPO)])
        self.assertEqual(rc, 0)
        self.assertIn("SKILL.md", json.loads(out)["found"])

    def test_absent_blocks(self):
        rc, out, _ = run(["check-skill", "not-a-skill", "--root", str(REPO)])
        self.assertEqual(rc, 3)
        d = json.loads(out)
        self.assertEqual(d["intent_type"], "block")
        self.assertEqual(sorted(d.keys()) >= ["action"], True)
        for f in ("agent_slug", "intent_type", "action", "rationale", "confidence", "severity",
                  "key_findings", "evidence_references", "next_agents", "human_approval_required", "timestamp_utc"):
            self.assertIn(f, d)


class Hooks(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.env = {"USAP_AUDIT_DIR": self.tmp.name}
        self.sid = "sess-test-1"

    def tearDown(self):
        self.tmp.cleanup()

    def _pretool(self, path, sid=None):
        payload = {"session_id": sid or self.sid, "cwd": "/work/repo", "hook_event_name": "PreToolUse",
                   "tool_name": "Edit", "tool_input": {"file_path": path}}
        return run(["pretool"], stdin=json.dumps(payload), env=self.env)

    def test_prompt_injects_fixed_template_without_echoing_terms(self):
        payload = {"session_id": self.sid, "prompt": "add a firewall rule and <script>alert(1)</script> hardening"}
        rc, out, _ = run(["prompt"], stdin=json.dumps(payload), env=self.env)
        self.assertEqual(rc, 0)
        self.assertIn("USAP gate", out)
        self.assertIn(self.sid, out)
        self.assertNotIn("<script>", out)        # DR-6

    def test_prompt_without_match_prints_nothing(self):
        rc, out, _ = run(["prompt"], stdin=json.dumps({"session_id": self.sid, "prompt": "fix the typo"}), env=self.env)
        self.assertEqual((rc, out), (0, ""))

    def test_gated_write_blocked_then_allowed_after_record(self):
        rc, _, err = self._pretool("/work/repo/.github/workflows/validate-skills.yml")
        self.assertEqual(rc, 2)
        self.assertIn("record --session-id", err)
        rc, out, _ = run(["record", "--session-id", self.sid, "--persona", "usap-devsecops", "--pass", "DR",
                          "--residual-risk", "medium", "--summary", "test pass"], env=self.env)
        self.assertEqual(rc, 0)
        rc, _, _ = self._pretool("/work/repo/.github/workflows/validate-skills.yml")
        self.assertEqual(rc, 0)

    def test_pass_from_other_session_does_not_count(self):   # DR-1
        run(["record", "--session-id", "other", "--persona", "usap-devsecops", "--pass", "DR",
             "--residual-risk", "low", "--summary", "x"], env=self.env)
        rc, _, _ = self._pretool("/work/repo/Dockerfile")
        self.assertEqual(rc, 2)

    def test_pa_pass_does_not_unlock_writes(self):
        run(["record", "--session-id", self.sid, "--persona", "usap-devsecops", "--pass", "PA",
             "--residual-risk", "low", "--summary", "x"], env=self.env)
        rc, _, _ = self._pretool("/work/repo/infra/main.tf")
        self.assertEqual(rc, 2)

    def test_non_gated_paths_pass(self):                      # DR-3
        for p in ("/work/repo/README.md", "/work/repo/src/app.py",
                  "/work/repo/tests/fixtures/secrets-exposure-input.json",
                  "/work/repo/detection/secrets-exposure/expected_outputs/sample_output.json",
                  "/work/repo/app/settings.json", "/work/repo/.env.example"):
            rc, _, _ = self._pretool(p)
            self.assertEqual(rc, 0, p)

    def test_gated_paths_detected(self):
        for p in ("/work/repo/.gitlab-ci.yml", "/work/repo/.claude/settings.local.json",
                  "/work/repo/plugins/usap/hooks/hooks.json", "/work/repo/.env",
                  "/work/repo/registry/usap-mcp-registry.yaml", "/work/repo/config/aws-credentials.json"):
            rc, _, _ = self._pretool(p)
            self.assertEqual(rc, 2, p)

    def test_missing_audit_dir_is_created_not_bypassed(self):  # DR-2
        env = {"USAP_AUDIT_DIR": str(Path(self.tmp.name) / "fresh" / "audit")}
        payload = {"session_id": self.sid, "cwd": "/w", "tool_name": "Write", "tool_input": {"file_path": "/w/Dockerfile"}}
        rc, _, err = run(["pretool"], stdin=json.dumps(payload), env=env)
        self.assertEqual(rc, 2)
        self.assertTrue((Path(self.tmp.name) / "fresh" / "audit").is_dir())
        self.assertIn("record --session-id", err)

    def test_stop_reports_and_clears_marker(self):             # DR-8
        self._pretool("/work/repo/Dockerfile")
        rc, out, _ = run(["stop"], stdin=json.dumps({"session_id": self.sid}), env=self.env)
        self.assertEqual(rc, 0)
        self.assertIn("no persona pass", json.loads(out)["systemMessage"])
        rc, out, _ = run(["stop"], stdin=json.dumps({"session_id": self.sid}), env=self.env)
        self.assertEqual((rc, out), (0, ""))

    def test_record_requires_residual_risk(self):
        rc, _, _ = run(["record", "--session-id", self.sid, "--persona", "usap-devsecops", "--pass", "DR",
                        "--summary", "x"], env=self.env)
        self.assertNotEqual(rc, 0)

    def test_audit_chain_verifies(self):
        run(["record", "--session-id", self.sid, "--persona", "usap-devsecops", "--pass", "DR",
             "--residual-risk", "low", "--summary", "one"], env=self.env)
        self._pretool("/work/repo/Dockerfile")
        run(["prompt"], stdin=json.dumps({"session_id": self.sid, "prompt": "harden the pipeline"}), env=self.env)
        logs = sorted(Path(self.tmp.name).glob("*.jsonl"))
        self.assertEqual(len(logs), 1)
        ok, problems = verify(logs[0])
        self.assertTrue(ok, problems)


if __name__ == "__main__":
    unittest.main(verbosity=1)
