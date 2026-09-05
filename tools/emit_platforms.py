#!/usr/bin/env python3
"""emit_platforms.py — emit the agentskills.io skill layout from the canonical tree.

OpenCode and OpenClaw both discover skills as ``<root>/skills/<name>/SKILL.md``
(a directory per skill), unlike the flat ``.codex/skills/<slug>.md`` mirrors the
``scripts/sync_*`` siblings produce. This tool emits that directory-per-skill
layout under ``.agents/skills/<slug>/SKILL.md`` as relative symlinks back to
each canonical ``<domain>/<slug>/SKILL.md``, plus a ``.agents/skills-index.json``.

  * OpenCode reads ``.agents/skills`` (and ``.claude/skills``) natively.
  * OpenClaw reads ``<workspace>/skills`` and ``~/.agents/skills``; point it at
    this tree or install with ``openclaw skills install git:<repo>@<tag>``.

This is the skill half of the platform emitter (issue #146). The cs-* agent
definitions still need per-platform frontmatter (OpenCode agent mode/permission,
OpenClaw metadata.openclaw gating) — tracked in the follow-up issue.

    python3 tools/emit_platforms.py --target agents          # write the tree
    python3 tools/emit_platforms.py --target agents --check   # exit 1 on drift
    python3 tools/emit_platforms.py --target agents --clean   # wipe and rewrite

Stdlib only. Reuses scripts/_sync_lib.walk_skills so the skill set is defined
in exactly one place.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Tuple

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))
from _sync_lib import walk_skills  # noqa: E402

INDEX_VERSION = "1.0"
TARGETS = {"agents": ".agents"}  # agentskills.io canonical root (OpenCode / OpenClaw)


def _link_target(domain: str, slug: str) -> str:
    # symlink lives at <repo>/<root>/skills/<slug>/SKILL.md -> three levels up, then canonical.
    return f"../../../{domain}/{slug}/SKILL.md"


def _index(entries, root: str, generated_at: str) -> str:
    payload = {
        "version": INDEX_VERSION,
        "generated_at_utc": generated_at,
        "target": root,
        "layout": "agentskills.io directory-per-skill",
        "skills": [
            {"name": e.slug, "domain": e.domain, "description": e.description,
             "path": f"{root}/skills/{e.slug}/SKILL.md", "target_path": f"{e.domain}/{e.slug}/SKILL.md"}
            for e in entries
        ],
    }
    return json.dumps(payload, indent=2) + "\n"


def _strip_ts(text: str) -> str:
    try:
        d = json.loads(text)
    except (json.JSONDecodeError, ValueError):
        return text
    d.pop("generated_at_utc", None)
    return json.dumps(d, indent=2) + "\n"


def emit(root: str, *, check: bool = False, clean: bool = False) -> Tuple[bool, List[str]]:
    entries = walk_skills()
    skills_dir = REPO_ROOT / root / "skills"
    index_path = REPO_ROOT / root / "skills-index.json"
    expected = {e.slug: _link_target(e.domain, e.slug) for e in entries}
    messages: List[str] = []
    changed = False

    existing: Dict[str, str] = {}
    if skills_dir.is_dir():
        for child in skills_dir.iterdir():
            link = child / "SKILL.md"
            if link.is_symlink():
                try:
                    existing[child.name] = os.readlink(link)
                except OSError:
                    existing[child.name] = ""
    missing = [s for s in expected if s not in existing]
    wrong = [s for s in expected if s in existing and existing[s] != expected[s]]
    extra = [s for s in existing if s not in expected]
    if missing or wrong or extra:
        changed = True
        if missing:
            messages.append(f"[{root}] {len(missing)} skill dir(s) to create")
        if wrong:
            messages.append(f"[{root}] {len(wrong)} symlink(s) point to the wrong target")
        if extra:
            messages.append(f"[{root}] {len(extra)} stale skill dir(s) to remove")

    expected_index = _strip_ts(_index(entries, root, "ignored"))
    if index_path.is_file():
        if _strip_ts(index_path.read_text(encoding="utf-8")) != expected_index:
            changed = True
            messages.append(f"[{root}] skills-index.json drift")
    else:
        changed = True
        messages.append(f"[{root}] skills-index.json missing")

    if check:
        return changed, messages or [f"[{root}] in sync ({len(entries)} skills)"]

    skills_dir.mkdir(parents=True, exist_ok=True)
    if clean:
        for child in list(skills_dir.iterdir()):
            link = child / "SKILL.md"
            if link.is_symlink():
                link.unlink()
            if child.is_dir() and not any(child.iterdir()):
                child.rmdir()
        existing = {}
    for slug in extra:
        link = skills_dir / slug / "SKILL.md"
        if link.is_symlink():
            link.unlink()
        d = skills_dir / slug
        if d.is_dir() and not any(d.iterdir()):
            d.rmdir()
    for e in entries:
        d = skills_dir / e.slug
        d.mkdir(parents=True, exist_ok=True)
        link = d / "SKILL.md"
        tgt = expected[e.slug]
        if link.is_symlink():
            if os.readlink(link) == tgt:
                continue
            link.unlink()
        elif link.exists():
            messages.append(f"[{root}] refusing to overwrite non-symlink {link}")
            continue
        link.symlink_to(tgt)
    if not index_path.is_file() or _strip_ts(index_path.read_text(encoding="utf-8")) != expected_index:
        index_path.write_text(_index(entries, root, datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")), encoding="utf-8")
    if not messages:
        messages.append(f"[{root}] in sync ({len(entries)} skills)")
    return changed, messages


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--target", choices=sorted(TARGETS), default="agents")
    ap.add_argument("--check", action="store_true", help="exit non-zero if a regen would change anything")
    ap.add_argument("--clean", action="store_true", help="wipe and rewrite the tree")
    args = ap.parse_args()
    changed, messages = emit(TARGETS[args.target], check=args.check, clean=args.clean)
    for m in messages:
        print(m)
    return 1 if (args.check and changed) else 0


if __name__ == "__main__":
    raise SystemExit(main())
