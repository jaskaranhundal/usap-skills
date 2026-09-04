#!/usr/bin/env python3
"""Regression tests for the evidence gate's local:// containment.

local:// sources must resolve inside the repository (Codex review on PR #147,
comment 3936200739). In-repo sources pass; traversal and outside symlinks fail
with a distinct reason; missing in-repo paths still report not found.

    python3 tools/output_contract_test.py
"""
from __future__ import annotations

import os
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "tools"))
from output_contract import validate_evidence_resolvable  # noqa: E402


def payload(source: str) -> dict:
    return {"evidence_references": [{"source": source, "ref": "t"}]}


class LocalContainment(unittest.TestCase):
    def test_in_repo_path_passes(self):
        self.assertEqual(validate_evidence_resolvable(payload("local://standards/output-contract.md")), [])

    def test_traversal_rejected_even_when_target_exists(self):
        target = "/etc/hosts" if os.path.exists("/etc/hosts") else "/etc/passwd"
        depth = len(REPO.resolve().parts)  # enough ".." to reach the filesystem root
        src = "local://" + "../" * depth + target.lstrip("/")
        v = validate_evidence_resolvable(payload(src))
        self.assertTrue(v, "traversal source was accepted")
        self.assertIn("escapes the repository root", v[0])

    def test_missing_in_repo_path_reports_not_found(self):
        v = validate_evidence_resolvable(payload("local://standards/does-not-exist.md"))
        self.assertTrue(v)
        self.assertIn("not found", v[0])

    def test_symlink_outside_repo_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            outside = Path(tmp) / "secret.txt"
            outside.write_text("x")
            link = REPO / ".oc_test_link"
            try:
                link.symlink_to(outside)
                v = validate_evidence_resolvable(payload("local://.oc_test_link"))
                self.assertTrue(v)
                self.assertIn("escapes the repository root", v[0])
            finally:
                if link.is_symlink():
                    link.unlink()


if __name__ == "__main__":
    unittest.main(verbosity=1)
