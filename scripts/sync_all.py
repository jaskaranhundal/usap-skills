#!/usr/bin/env python3
"""Run every polyglot sync script in one pass.

Forwards ``--clean`` and ``--check`` to each of:

  * scripts/sync_codex_skills.py
  * scripts/sync_gemini_skills.py
  * scripts/sync_cursor_skills.py
  * scripts/sync_windsurf_skills.py
  * scripts/sync_aider_skills.py

Stdlib only.  Exits non-zero in ``--check`` mode if any sync would change
anything, so CI can gate on a single command.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _sync_lib import sync_target  # noqa: E402

TARGETS = (".codex", ".gemini", ".cursor", ".windsurf", ".aider")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--clean", action="store_true", help="wipe and rewrite every symlink tree")
    parser.add_argument("--check", action="store_true", help="exit non-zero if any regen would change anything")
    args = parser.parse_args()

    any_changed = False
    for target in TARGETS:
        changed, messages = sync_target(target, clean=args.clean, check=args.check)
        for line in messages:
            print(line)
        any_changed = any_changed or changed

    if args.check and any_changed:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
