#!/usr/bin/env python3
"""Validate Claude Code invocation-control frontmatter against USAP's L1-L4 invariants.

Reads every active-domain ``SKILL.md`` and checks the optional Claude Code
extension fields (``disable-model-invocation``, ``user-invocable``,
``allowed-tools``, ``disallowed-tools``, ``context``, ``paths``, ``model``,
``effort``) against the level-bound invariants documented in
``standards/level-guide.md``::

    L4 (executive)   -> disable-model-invocation MUST be true; allowed-tools required
    L3 (operational) -> allowed-tools required non-empty
    L2/L1            -> no extra requirements

Level signal precedence:
1. ``metadata.usap_level`` ("L1" .. "L4") in frontmatter — authoritative.
2. Heuristic fallback when ``metadata.usap_level`` is absent:
   - body text mentions "mutating action", "containment", "isolate", or
     ships an ``<slug>_actor.py`` script -> treat as L4 candidate
   - body text mentions "L3 / Operational" header -> treat as L3 candidate
   - otherwise -> level "UNKNOWN" (no enforced invariants)

This validator is WARN-first during the rollout. ``--strict`` flips warnings
into errors so the CI gate can be tightened once backfill is sufficient
(target: 80% of L3 / L4 skills carry ``metadata.usap_level`` + the
invariant fields). Today, the script exits 0 by default even when WARNs
are emitted; use ``--strict`` to test future-CI behaviour locally.

Usage::

    python3 tools/validate_invocation_control.py <skill-dir>
    python3 tools/validate_invocation_control.py --all
    python3 tools/validate_invocation_control.py --all --strict
    python3 tools/validate_invocation_control.py --all --summary

Stdlib only. Shares the YAML parser with ``tools/validate_skill.py``.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# Re-use the validator's parser so YAML rules stay in one place.
sys.path.insert(0, str(Path(__file__).resolve().parent))
from validate_skill import (  # noqa: E402  (import after sys.path tweak)
    ACTIVE_DOMAINS,
    parse_frontmatter,
)

REPO_ROOT = Path(__file__).resolve().parent.parent

LEVEL_L1 = "L1"
LEVEL_L2 = "L2"
LEVEL_L3 = "L3"
LEVEL_L4 = "L4"
LEVEL_UNKNOWN = "UNKNOWN"

# Heuristic markers for level inference when metadata.usap_level is absent.
L4_BODY_MARKERS = re.compile(
    r"\b(mutating\s+action|containment\s+advisor|isolate\s+host|"
    r"revoke\s+(key|credential)|account\s+disablement|human_approval_required\s*:\s*true)\b",
    re.IGNORECASE,
)
L3_BODY_MARKERS = re.compile(r"^\|\s*L3\b|##\s+L3\b", re.IGNORECASE | re.MULTILINE)

CONTEXT_VALUES = {"inherit", "fork"}
EFFORT_VALUES = {"low", "medium", "high", "xhigh", "max"}

_TTY = sys.stdout.isatty()
RED = "\033[91m" if _TTY else ""
GREEN = "\033[92m" if _TTY else ""
YELLOW = "\033[93m" if _TTY else ""
RESET = "\033[0m" if _TTY else ""


def _is_str(v: object) -> bool:
    return isinstance(v, str)


def _coerce_bool(v: object) -> object:
    """Coerce string ``"true"`` / ``"false"`` to Python booleans.

    The shared frontmatter parser in ``tools/validate_skill.py`` is
    stdlib-only and does not infer YAML scalar types beyond strings and
    lists. YAML's ``user-invocable: true`` lands as the literal string
    ``"true"`` here. Coerce so the boolean invariants below check
    against real bools.
    """
    if isinstance(v, bool):
        return v
    if isinstance(v, str):
        lower = v.strip().lower()
        if lower == "true":
            return True
        if lower == "false":
            return False
    return v


def _infer_level(fm: Dict[str, object], body: str, skill_dir: Path) -> str:
    metadata = fm.get("metadata") if isinstance(fm.get("metadata"), dict) else {}
    if isinstance(metadata, dict):
        declared = metadata.get("usap_level")
        if isinstance(declared, str) and declared.upper() in {LEVEL_L1, LEVEL_L2, LEVEL_L3, LEVEL_L4}:
            return declared.upper()
        # Legacy extended-frontmatter sometimes has top-level `level: L3`.
        legacy_level = metadata.get("level")
        if isinstance(legacy_level, str) and legacy_level.upper() in {LEVEL_L1, LEVEL_L2, LEVEL_L3, LEVEL_L4}:
            return legacy_level.upper()
    top_legacy = fm.get("level")
    if isinstance(top_legacy, str) and top_legacy.upper() in {LEVEL_L1, LEVEL_L2, LEVEL_L3, LEVEL_L4}:
        return top_legacy.upper()
    # Heuristic fallback.
    scripts = skill_dir / "scripts"
    has_actor = scripts.is_dir() and any(scripts.glob("*_actor.py"))
    if has_actor or L4_BODY_MARKERS.search(body):
        return LEVEL_L4
    if L3_BODY_MARKERS.search(body):
        return LEVEL_L3
    return LEVEL_UNKNOWN


def _check_skill(skill_dir: Path) -> Tuple[List[str], List[str], str]:
    """Return ``(errors, warnings, level)``."""
    errors: List[str] = []
    warnings: List[str] = []

    skill_md = skill_dir / "SKILL.md"
    if not skill_md.is_file():
        return [f"SKILL.md not found in {skill_dir}"], [], LEVEL_UNKNOWN

    try:
        text = skill_md.read_text(encoding="utf-8")
    except UnicodeDecodeError as exc:
        return [f"not valid UTF-8: {exc}"], [], LEVEL_UNKNOWN

    fm = parse_frontmatter(text)
    if not isinstance(fm, dict):
        return ["no valid YAML frontmatter"], [], LEVEL_UNKNOWN

    body = text.split("---", 2)[-1] if text.startswith("---") else text

    level = _infer_level(fm, body, skill_dir)

    # Validate types of any present invocation-control fields. Coerce
    # string "true"/"false" since the shared parser does not infer YAML
    # booleans.
    dmi = _coerce_bool(fm.get("disable-model-invocation"))
    if "disable-model-invocation" in fm and not isinstance(dmi, bool):
        errors.append("disable-model-invocation must be a boolean")

    ui = _coerce_bool(fm.get("user-invocable"))
    if "user-invocable" in fm and not isinstance(ui, bool):
        errors.append("user-invocable must be a boolean")

    at = fm.get("allowed-tools")
    if "allowed-tools" in fm and not _is_str(at):
        errors.append(
            "allowed-tools must be a space-separated string per spec "
            "(e.g. \"Bash(git:*) Read Write\")"
        )

    dt = fm.get("disallowed-tools")
    if "disallowed-tools" in fm and not _is_str(dt):
        errors.append("disallowed-tools must be a space-separated string per spec")

    ctx = fm.get("context")
    if "context" in fm and ctx not in CONTEXT_VALUES:
        errors.append(f"context must be one of {sorted(CONTEXT_VALUES)}, got {ctx!r}")

    eff = fm.get("effort")
    if "effort" in fm and eff not in EFFORT_VALUES:
        errors.append(f"effort must be one of {sorted(EFFORT_VALUES)}, got {eff!r}")

    paths = fm.get("paths")
    if "paths" in fm and not (
        isinstance(paths, list) and all(isinstance(p, str) for p in paths)
    ):
        errors.append("paths must be an array of glob strings")

    # Level-bound invariants — WARN, not error, during rollout.
    if level == LEVEL_L4:
        if dmi is not True:
            warnings.append(
                "L4 (mutating) skill should set `disable-model-invocation: true` "
                "(see standards/level-guide.md)"
            )
        if not (isinstance(at, str) and at.strip()):
            warnings.append(
                "L4 skill should declare a non-empty `allowed-tools` "
                "(see standards/level-guide.md)"
            )
    elif level == LEVEL_L3:
        if not (isinstance(at, str) and at.strip()):
            warnings.append(
                "L3 skill should declare a non-empty `allowed-tools` "
                "(see standards/level-guide.md)"
            )

    return errors, warnings, level


def _domain_skill_paths() -> List[Tuple[str, Path]]:
    out: List[Tuple[str, Path]] = []
    for domain in ACTIVE_DOMAINS:
        droot = REPO_ROOT / domain
        if not droot.is_dir():
            continue
        for sdir in sorted(droot.iterdir()):
            if sdir.is_dir() and (sdir / "SKILL.md").is_file():
                out.append((domain, sdir))
    return out


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate Claude Code invocation-control frontmatter against L1-L4 invariants."
    )
    parser.add_argument("target", nargs="?", help="Path to one skill dir (or use --all).")
    parser.add_argument("--all", action="store_true", help="Validate every active-domain skill.")
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Treat WARNs as errors (exit 1 on any). Default: WARN-only (exit 0).",
    )
    parser.add_argument(
        "--summary",
        action="store_true",
        help="Emit per-level skill counts (intended for CI step summary).",
    )
    args = parser.parse_args()

    if not args.all and not args.target:
        parser.error("provide a skill dir or use --all")

    if args.all:
        targets = _domain_skill_paths()
    else:
        t = Path(args.target).resolve()
        if not t.is_dir():
            print(f"error: not a dir: {t}", file=sys.stderr)
            return 1
        # Derive the domain from path parents when possible.
        domain = t.parent.name if t.parent.name in ACTIVE_DOMAINS else "(out-of-domain)"
        targets = [(domain, t)]

    level_counts: Dict[str, int] = {LEVEL_L1: 0, LEVEL_L2: 0, LEVEL_L3: 0, LEVEL_L4: 0, LEVEL_UNKNOWN: 0}
    error_count = warn_count = 0

    for domain, sdir in targets:
        errors, warnings, level = _check_skill(sdir)
        level_counts[level] = level_counts.get(level, 0) + 1
        rel = sdir.relative_to(REPO_ROOT) if sdir.is_relative_to(REPO_ROOT) else sdir
        if errors:
            error_count += 1
            print(f"{RED}FAIL{RESET} {rel}  [{level}]")
            for e in errors:
                print(f"      {RED}x{RESET} {e}")
        elif warnings:
            warn_count += 1
            print(f"{YELLOW}WARN{RESET} {rel}  [{level}]")
            for w in warnings:
                print(f"      {YELLOW}!{RESET} {w}")
        else:
            print(f"{GREEN}OK  {RESET} {rel}  [{level}]")

    print()
    print("=" * 60)
    print(
        f"Total: {len(targets)}  "
        f"{GREEN}OK: {len(targets) - error_count - warn_count}{RESET}  "
        f"{YELLOW}WARN: {warn_count}{RESET}  "
        f"{RED}FAIL: {error_count}{RESET}"
    )

    if args.summary:
        print()
        print("Per-level inferred counts:")
        for lvl in (LEVEL_L1, LEVEL_L2, LEVEL_L3, LEVEL_L4, LEVEL_UNKNOWN):
            print(f"  {lvl:8s} {level_counts[lvl]}")

    if error_count:
        return 1
    if args.strict and warn_count:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
