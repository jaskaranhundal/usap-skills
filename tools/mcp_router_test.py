#!/usr/bin/env python3
"""Regression tests for the approval gate in tools/mcp_router.py.

route() issues a server-side, single-use approval token when it returns
approval_required; dispatch_after_approval() dispatches only with that token,
bound to the same MCP, capability and arguments, once, within its TTL
(Codex review on PR #149, comment 3936208945). dispatch_unattended() refuses
capabilities that require approval.

    python3 tools/mcp_router_test.py
"""
from __future__ import annotations

import json
import os
import sys
import tempfile
import time
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "tools"))


class ApprovalTokens(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        os.environ["USAP_AUDIT_DIR"] = self.tmp.name
        os.environ.pop("USAP_AUDIT_KEY", None)
        import importlib
        import mcp_router  # noqa: E402
        self.r = importlib.reload(mcp_router)
        self.args = {"channel": "#ir", "text": "SEV-2 declared"}
        self.payload = {"intent_type": "escalate", "next_agents": ["cs-incident-responder"],
                        "human_approval_required": True, "dispatch_args": self.args}

    def tearDown(self):
        os.environ.pop("USAP_AUDIT_DIR", None)
        self.tmp.cleanup()

    def _route(self):
        d = self.r.route(self.payload)
        self.assertEqual(d["status"], "approval_required", d)
        self.assertTrue(d.get("approval_token"), d)
        return d

    def test_token_issued_and_not_logged_in_clear(self):
        d = self._route()
        logs = sorted(Path(self.tmp.name).glob("*.jsonl"))
        text = logs[0].read_text()
        self.assertNotIn(d["approval_token"], text)
        self.assertIn("approval_token_sha256", text)

    def test_token_dispatches_once(self):
        d = self._route()
        first = self.r.dispatch_after_approval(d["selected_mcp"], d["selected_capability"], self.args, d["approval_token"])
        self.assertIn(first["status"], ("dispatched", "dispatch_failed"), first)
        self.assertNotIn("approval", first.get("error", "") or "")
        second = self.r.dispatch_after_approval(d["selected_mcp"], d["selected_capability"], self.args, d["approval_token"])
        self.assertEqual(second["status"], "dispatch_failed")
        self.assertIn("already used", second["error"])

    def test_missing_or_literal_token_rejected(self):
        d = self._route()
        for tok in (None, "", "approved", "smoke-test-approved"):
            res = self.r.dispatch_after_approval(d["selected_mcp"], d["selected_capability"], self.args, tok)
            self.assertEqual(res["status"], "dispatch_failed", tok)
            self.assertIn("approval token", res["error"])

    def test_binding_to_capability_and_arguments(self):
        d = self._route()
        other_args = self.r.dispatch_after_approval(d["selected_mcp"], d["selected_capability"], {"channel": "#other"}, d["approval_token"])
        self.assertEqual(other_args["status"], "dispatch_failed")
        self.assertIn("arguments", other_args["error"])
        d2 = self._route()
        other_cap = self.r.dispatch_after_approval(d2["selected_mcp"], "not-the-capability", self.args, d2["approval_token"])
        self.assertEqual(other_cap["status"], "dispatch_failed")
        self.assertIn("capability", other_cap["error"])

    def test_expired_token_rejected(self):
        d = self._route()
        rec_path = Path(self.tmp.name) / "approvals" / f"{d['approval_token']}.json"
        rec = json.loads(rec_path.read_text()); rec["expires_epoch"] = time.time() - 1
        rec_path.write_text(json.dumps(rec))
        res = self.r.dispatch_after_approval(d["selected_mcp"], d["selected_capability"], self.args, d["approval_token"])
        self.assertEqual(res["status"], "dispatch_failed")
        self.assertIn("expired", res["error"])

    def test_unattended_refuses_gated_capability(self):
        res = self.r.dispatch_unattended("slack", "post_message", self.args)
        self.assertEqual(res["status"], "dispatch_failed")
        self.assertIn("requires approval", res["error"])
        ok = self.r.dispatch_unattended("splunk", "search", {"spl": "index=x"})
        self.assertIn(ok["status"], ("dispatched", "dispatch_failed"))
        self.assertNotIn("requires approval", ok.get("error", "") or "")


if __name__ == "__main__":
    unittest.main(verbosity=1)
