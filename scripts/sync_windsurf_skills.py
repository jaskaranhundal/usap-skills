#!/usr/bin/env python3
"""Mirror the canonical SKILL.md tree into ``.windsurf/skills/``.

Each ``<domain>/<slug>/SKILL.md`` is exposed as a top-level
``.windsurf/skills/<slug>.md`` relative symlink so Windsurf's Cascade
agent can load USAP skills without copying content.

Stdlib only.  CLI matches the other ``sync_<target>_skills.py`` siblings.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _sync_lib import sync_target  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--clean", action="store_true", help="wipe and rewrite the symlink tree")
    parser.add_argument("--check", action="store_true", help="exit non-zero if a regen would change anything")
    args = parser.parse_args()

    changed, messages = sync_target(".windsurf", clean=args.clean, check=args.check)
    for line in messages:
        print(line)
    if args.check and changed:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
