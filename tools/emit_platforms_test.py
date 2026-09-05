#!/usr/bin/env python3
"""Regression test for tools/emit_platforms.py.

The agentskills.io tree under .agents/skills/<slug>/SKILL.md must contain one
directory per canonical skill, each a symlink resolving to that skill's
SKILL.md, and --check must be clean after an emit (issue #146).

    python3 tools/emit_platforms_test.py
"""
from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "tools"))
sys.path.insert(0, str(REPO / "scripts"))
import emit_platforms as ep  # noqa: E402
from _sync_lib import walk_skills  # noqa: E402


class Emit(unittest.TestCase):
    def test_check_is_clean_and_complete(self):
        changed, _ = ep.emit(".agents", check=True)
        self.assertFalse(changed, "emit --check reports drift; run `python3 tools/emit_platforms.py --target agents` and commit")
        skills = walk_skills()
        base = REPO / ".agents" / "skills"
        for e in skills:
            link = base / e.slug / "SKILL.md"
            self.assertTrue(link.is_symlink(), f"missing symlink for {e.slug}")
            resolved = (link.parent / os.readlink(link)).resolve()
            self.assertEqual(resolved, (REPO / e.domain / e.slug / "SKILL.md").resolve(), e.slug)
        # no extra skill directories
        present = {c.name for c in base.iterdir() if c.is_dir()}
        self.assertEqual(present, {e.slug for e in skills})


if __name__ == "__main__":
    unittest.main(verbosity=1)
