#!/usr/bin/env python3
"""
sync_plugin.py — mirror the agent definitions and their referenced tool scripts
into plugins/usap/, and verify the mirror has not drifted.

Why this exists
---------------
plugins/usap/ is a distributed copy of content whose source of truth lives at the
repository root. A hand-maintained copy of a security persona drifts silently,
and the drifted copy is the one the installed plugin answers with.

That is not hypothetical. Plugin 1.13.1 shipped five agent definitions copied
from a branch that was 60 commits behind main. Every one of them was missing the
`usap_mcp` capability whitelist and the rule "never invoke a mutating capability
from an autonomous run — both require human_approval_required: true". The plugin
loaded cleanly and answered with a persona whose human-approval gate had been
removed. A loud failure would have been safer than a faithful-looking copy.

Usage
-----
    python3 tools/sync_plugin.py            # write the mirror
    python3 tools/sync_plugin.py --check    # exit 1 if the mirror has drifted

--check is the CI gate. It never writes.
"""

import argparse
import filecmp
import re
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PLUGIN = ROOT / "plugins" / "usap"
PLUGIN_MANIFEST = PLUGIN / ".claude-plugin" / "plugin.json"

# Agents the plugin ships, derived from the skills it declares rather than
# hardcoded — a new plugin skill picks up its agent automatically.
AGENT_REF = re.compile(r"agents/[a-z0-9-]+/cs-[a-z0-9-]+\.md")
# Tool + helper scripts an agent definition invokes, relative to agents/<domain>/.
SCRIPT_REF = re.compile(r"\.\./\.\./((?:[a-z0-9-]+/[a-z0-9-]+/scripts|shared/scripts)/[a-z0-9_-]+\.py)")


def shipped_agents() -> list[str]:
    """Agent paths referenced by the SKILL.md files the plugin ships."""
    found: set[str] = set()
    for skill_md in sorted((PLUGIN / "skills").glob("*/SKILL.md")):
        found.update(AGENT_REF.findall(skill_md.read_text(encoding="utf-8")))
    return sorted(found)


def referenced_scripts(agent_paths: list[str]) -> list[str]:
    """Repo-relative script paths those agents invoke."""
    found: set[str] = set()
    for rel in agent_paths:
        src = ROOT / rel
        if src.is_file():
            found.update(SCRIPT_REF.findall(src.read_text(encoding="utf-8")))
    return sorted(found)


def planned_files() -> list[str]:
    agents = shipped_agents()
    return agents + referenced_scripts(agents)


def sync(check_only: bool) -> int:
    planned = planned_files()
    missing_source = [p for p in planned if not (ROOT / p).is_file()]
    if missing_source:
        for p in missing_source:
            print(f"  MISSING SOURCE {p}", file=sys.stderr)
        print("error: a shipped agent references a path that does not exist", file=sys.stderr)
        return 1

    drifted, copied = [], 0
    for rel in planned:
        src, dst = ROOT / rel, PLUGIN / rel
        if not dst.is_file() or not filecmp.cmp(src, dst, shallow=False):
            drifted.append(rel)
            if not check_only:
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, dst)
                copied += 1

    # Anything mirrored that is no longer referenced is stale and must go, or the
    # plugin keeps shipping an agent the skills no longer point at.
    planned_set = {(PLUGIN / p).resolve() for p in planned}
    orphans = []
    for sub in ("agents",):
        for f in sorted((PLUGIN / sub).rglob("*.md")) if (PLUGIN / sub).is_dir() else []:
            if f.resolve() not in planned_set:
                orphans.append(str(f.relative_to(PLUGIN)))
                if not check_only:
                    f.unlink()

    if check_only:
        if drifted or orphans:
            for p in drifted:
                print(f"  DRIFTED  {p}")
            for p in orphans:
                print(f"  ORPHANED {p}")
            print(
                f"\nerror: plugins/usap/ is out of sync with the source of truth "
                f"({len(drifted)} drifted, {len(orphans)} orphaned).\n"
                f"Run: python3 tools/sync_plugin.py   # then commit the result",
                file=sys.stderr,
            )
            return 1
        print(f"OK  plugins/usap/ mirrors {len(planned)} source file(s); no drift.")
        return 0

    print(f"synced {copied} file(s), removed {len(orphans)} orphan(s) "
          f"({len(planned)} tracked).")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--check", action="store_true", help="report drift and exit 1; never writes")
    return sync(ap.parse_args().check)


if __name__ == "__main__":
    raise SystemExit(main())
