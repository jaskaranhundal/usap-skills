#!/usr/bin/env python3
"""Validate that every USAP skill directory has the required files on disk.

Per ``standards/SKILL-AUTHORING-STANDARD.md`` (section 7), the canonical
package layout for a skill is::

    <domain>/<slug>/
      SKILL.md
      references/workflow.md
      expected_outputs/sample_output.json
      scripts/<slug>_tool.py

This script checks each of those paths exists for every skill under the 11
active domains. It does NOT parse frontmatter or YAML — that is
``tools/validate_skill.py``'s job. It does NOT check description content —
that is ``tools/validate_description.py``'s job. Single responsibility.

Usage::

    python3 tools/validate_structure.py <skill-dir>
    python3 tools/validate_structure.py --all

Exit codes:
  0 = clean (or any failures are non-blocking — see ``--strict``)
  1 = one or more skills have errors AND ``--strict`` was passed
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import List

REPO_ROOT = Path(__file__).resolve().parent.parent

ACTIVE_DOMAINS = [
    "appsec-devsecops",
    "cloud-infra",
    "detection",
    "governance",
    "identity-access",
    "pentest",
    "platform-ai",
    "red-team",
    "response",
    "risk-compliance",
    "system-security",
    "webapp-security",
]

_TTY = sys.stdout.isatty()
RED = "\033[91m" if _TTY else ""
GREEN = "\033[92m" if _TTY else ""
YELLOW = "\033[93m" if _TTY else ""
RESET = "\033[0m" if _TTY else ""


def required_paths(skill_dir: Path) -> List[Path]:
    slug = skill_dir.name
    return [
        skill_dir / "SKILL.md",
        skill_dir / "references" / "workflow.md",
        skill_dir / "expected_outputs" / "sample_output.json",
        skill_dir / "scripts" / f"{slug}_tool.py",
    ]


def validate_structure(skill_dir: Path) -> List[str]:
    errors: List[str] = []
    for path in required_paths(skill_dir):
        if not path.is_file():
            rel = (
                path.relative_to(skill_dir)
                if path.is_relative_to(skill_dir)
                else path
            )
            errors.append(f"missing required file: {rel}")
    return errors


def list_active_skills(repo_root: Path) -> List[Path]:
    out: List[Path] = []
    for domain in ACTIVE_DOMAINS:
        domain_root = repo_root / domain
        if not domain_root.is_dir():
            continue
        for skill_dir in sorted(domain_root.iterdir()):
            # Include any directory under a domain. Even a half-built skill
            # without SKILL.md should be reported, so we don't gate on
            # SKILL.md's presence here.
            if skill_dir.is_dir() and not skill_dir.name.startswith("."):
                out.append(skill_dir)
    return out


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate USAP skill package directory structure."
    )
    parser.add_argument(
        "target",
        nargs="?",
        help="Path to a single skill directory (omit with --all).",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Validate every skill under the 11 active domains.",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit non-zero on any failing skill (default: report only).",
    )
    args = parser.parse_args()

    if not args.all and not args.target:
        parser.error("provide a skill directory or use --all")

    if args.all:
        targets: List[Path] = list_active_skills(REPO_ROOT)
    else:
        targets = [Path(args.target).resolve()]
        if not targets[0].is_dir():
            print(
                f"{RED}error{RESET}: not a directory: {targets[0]}",
                file=sys.stderr,
            )
            return 1

    passed = failed = 0
    for skill_dir in targets:
        errs = validate_structure(skill_dir)
        rel = (
            skill_dir.relative_to(REPO_ROOT)
            if skill_dir.is_relative_to(REPO_ROOT)
            else skill_dir
        )
        if errs:
            failed += 1
            print(f"{RED}FAIL{RESET} {rel}")
            for err in errs:
                print(f"      {RED}x{RESET} {err}")
        else:
            passed += 1
            print(f"{GREEN}PASS{RESET} {rel}")

    print()
    print("=" * 60)
    print(
        f"Total: {len(targets)}  "
        f"{GREEN}Passed: {passed}{RESET}  "
        f"{RED}Failed: {failed}{RESET}"
    )
    if failed and not args.strict:
        print(
            f"{YELLOW}note{RESET}: report-only mode; pass --strict to fail "
            "the run when files are missing."
        )

    if args.strict and failed:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
