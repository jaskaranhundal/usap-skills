"""Shared helpers for the polyglot sync scripts.

Each `scripts/sync_<target>.py` invokes :func:`sync_target` with a target
directory name (``.codex``, ``.gemini``, ``.cursor``, ``.windsurf``,
``.aider``). The library mirrors every canonical ``<domain>/<slug>/SKILL.md``
into ``<target>/skills/<slug>.md`` as a relative symlink and writes a
``<target>/skills-index.json`` describing the set.

Stdlib only. Re-uses ``tools/validate_skill.parse_frontmatter`` so YAML
parsing stays in one place.
"""
from __future__ import annotations

import json
import os
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple

REPO_ROOT = Path(__file__).resolve().parent.parent
TOOLS_DIR = REPO_ROOT / "tools"

# Reuse the validator's frontmatter parser to keep YAML rules in one place.
sys.path.insert(0, str(TOOLS_DIR))
from validate_skill import ACTIVE_DOMAINS, parse_frontmatter  # noqa: E402

INDEX_VERSION = "1.0"


@dataclass(frozen=True)
class SkillEntry:
    slug: str
    domain: str
    name: str
    description: str
    skill_md: Path  # absolute path to canonical SKILL.md

    def to_index(self, target_dir: str) -> Dict[str, str]:
        # Path of the symlink we will create, relative to repo root.
        link_path = f"{target_dir}/skills/{self.slug}.md"
        # Canonical SKILL.md path, relative to repo root.
        canonical = f"{self.domain}/{self.slug}/SKILL.md"
        return {
            "slug": self.slug,
            "domain": self.domain,
            "name": self.name,
            "description": self.description,
            "path": link_path,
            "target_path": canonical,
        }


def walk_skills() -> List[SkillEntry]:
    """Return one entry per canonical ``<domain>/<slug>/SKILL.md``.

    Only the 12 ACTIVE_DOMAINS are scanned; legacy / scratch directories
    are ignored.  Sorted by (domain, slug) for stable output.
    """
    entries: List[SkillEntry] = []
    for domain in ACTIVE_DOMAINS:
        domain_dir = REPO_ROOT / domain
        if not domain_dir.is_dir():
            continue
        for skill_dir in sorted(domain_dir.iterdir()):
            if not skill_dir.is_dir():
                continue
            skill_md = skill_dir / "SKILL.md"
            if not skill_md.is_file():
                continue
            fm = parse_frontmatter(skill_md.read_text(encoding="utf-8")) or {}
            name = str(fm.get("name") or skill_dir.name)
            description = str(fm.get("description") or "").strip()
            entries.append(
                SkillEntry(
                    slug=skill_dir.name,
                    domain=domain,
                    name=name,
                    description=description,
                    skill_md=skill_md,
                )
            )
    entries.sort(key=lambda e: (e.domain, e.slug))
    return entries


def _expected_link_target(entry: SkillEntry, target_dir: str) -> str:
    """Symlink target string (relative path from the symlink location)."""
    # Symlink lives at <repo>/<target_dir>/skills/<slug>.md
    # Canonical SKILL.md at <repo>/<domain>/<slug>/SKILL.md
    # Relative path is two levels up, then domain/slug/SKILL.md
    return f"../../{entry.domain}/{entry.slug}/SKILL.md"


def _link_ok(link_path: Path, expected_target: str) -> bool:
    if not link_path.is_symlink():
        return False
    try:
        return os.readlink(link_path) == expected_target
    except OSError:
        return False


def _serialize_index(entries: List[SkillEntry], target_dir: str, generated_at: str) -> str:
    payload = {
        "version": INDEX_VERSION,
        "generated_at_utc": generated_at,
        "target": target_dir,
        "skills": [e.to_index(target_dir) for e in entries],
    }
    return json.dumps(payload, indent=2, sort_keys=False) + "\n"


def _strip_generated_at(text: str) -> str:
    """Drop the timestamp field for drift comparisons (it always changes)."""
    try:
        payload = json.loads(text)
    except (json.JSONDecodeError, ValueError):
        return text
    payload.pop("generated_at_utc", None)
    return json.dumps(payload, indent=2, sort_keys=False) + "\n"


def sync_target(target_dir: str, *, clean: bool = False, check: bool = False) -> Tuple[bool, List[str]]:
    """Sync one polyglot target.

    Returns ``(changed, messages)``.  In ``check`` mode no writes happen
    and ``changed`` is ``True`` if a regen would alter anything.
    """
    entries = walk_skills()
    skills_dir = REPO_ROOT / target_dir / "skills"
    index_path = REPO_ROOT / target_dir / "skills-index.json"

    messages: List[str] = []
    changed = False
    expected_links = {e.slug: _expected_link_target(e, target_dir) for e in entries}

    # --- detect drift ---
    existing_links: Dict[str, Optional[str]] = {}
    if skills_dir.is_dir():
        for child in skills_dir.iterdir():
            if child.is_symlink() and child.suffix == ".md":
                slug = child.stem
                try:
                    existing_links[slug] = os.readlink(child)
                except OSError:
                    existing_links[slug] = None

    missing = [s for s in expected_links if s not in existing_links]
    wrong = [s for s in expected_links if s in existing_links and existing_links[s] != expected_links[s]]
    extra = [s for s in existing_links if s not in expected_links]

    if missing or wrong or extra:
        changed = True
        if missing:
            messages.append(f"[{target_dir}] {len(missing)} symlink(s) to create")
        if wrong:
            messages.append(f"[{target_dir}] {len(wrong)} symlink(s) point to wrong target")
        if extra:
            messages.append(f"[{target_dir}] {len(extra)} stale symlink(s) to remove")

    # Compare index (ignoring timestamp).
    expected_index_no_ts = _strip_generated_at(
        _serialize_index(entries, target_dir, generated_at="ignored")
    )
    if index_path.is_file():
        actual_no_ts = _strip_generated_at(index_path.read_text(encoding="utf-8"))
        if actual_no_ts != expected_index_no_ts:
            changed = True
            messages.append(f"[{target_dir}] skills-index.json drift")
    else:
        changed = True
        messages.append(f"[{target_dir}] skills-index.json missing")

    if check:
        return changed, messages

    # --- apply changes ---
    skills_dir.mkdir(parents=True, exist_ok=True)

    if clean:
        # Wipe every *.md symlink at the top of skills_dir before recreating.
        for child in list(skills_dir.iterdir()):
            if child.is_symlink() and child.suffix == ".md":
                child.unlink()
        # In clean mode we re-evaluate state.
        existing_links = {}

    # Remove stale symlinks (slugs no longer in the canonical tree).
    for slug in extra:
        stale = skills_dir / f"{slug}.md"
        if stale.is_symlink():
            stale.unlink()

    # Create / fix symlinks.
    for entry in entries:
        link_path = skills_dir / f"{entry.slug}.md"
        target = expected_links[entry.slug]
        if link_path.is_symlink():
            if os.readlink(link_path) == target:
                continue
            link_path.unlink()
        elif link_path.exists():
            # Non-symlink collision — refuse to clobber regular files.
            messages.append(
                f"[{target_dir}] refusing to overwrite non-symlink {link_path}"
            )
            continue
        link_path.symlink_to(target)

    # Write the index only when the stripped (timestamp-less) content drifts —
    # otherwise a no-op rerun would churn the timestamp and pollute git diffs.
    index_path.parent.mkdir(parents=True, exist_ok=True)
    if index_path.is_file():
        actual_no_ts = _strip_generated_at(index_path.read_text(encoding="utf-8"))
    else:
        actual_no_ts = ""
    if actual_no_ts != expected_index_no_ts:
        generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        index_path.write_text(
            _serialize_index(entries, target_dir, generated_at),
            encoding="utf-8",
        )

    if not messages:
        messages.append(f"[{target_dir}] in sync ({len(entries)} skills)")

    return changed, messages
