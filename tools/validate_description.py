#!/usr/bin/env python3
"""Validate SKILL.md description fields.

Per ``standards/SKILL-AUTHORING-STANDARD.md``, a skill's ``description``
top-level frontmatter field must:

  - be present and non-empty
  - be <= 200 characters
  - be written in third-person voice (no first-person pronouns)
  - contain a trigger phrase: "Use when", "Use for", or "For "

The script is intentionally separate from ``validate_skill.py`` so that an
in-flight description-rewriting PR can flag issues without failing the main
frontmatter schema check.

Usage::

    python3 tools/validate_description.py <skill-dir>
    python3 tools/validate_description.py --all

Exit codes:
  0 = clean (or any failures are non-blocking — see ``--strict``)
  1 = one or more skills have errors AND ``--strict`` was passed
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import List, Tuple

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

MAX_DESC_LEN = 200

# Word-boundary check for first-person pronouns. Tight regex on word
# boundaries to avoid false positives ("we" in "Wednesday" etc.).
FIRST_PERSON_RE = re.compile(
    r"\b(i|we|us|our|ours|my|mine|me|i'm|i've|we're|we've)\b",
    re.IGNORECASE,
)

TRIGGER_PATTERNS = [
    re.compile(r"\bUse when\b", re.IGNORECASE),
    re.compile(r"\bUse for\b", re.IGNORECASE),
    re.compile(r"\bFor [A-Za-z]", re.IGNORECASE),
]

_TTY = sys.stdout.isatty()
RED = "\033[91m" if _TTY else ""
GREEN = "\033[92m" if _TTY else ""
YELLOW = "\033[93m" if _TTY else ""
RESET = "\033[0m" if _TTY else ""


def extract_description(text: str) -> str:
    """Pull the ``description:`` value from a SKILL.md frontmatter block.

    Returns the empty string when the frontmatter is malformed or the field is
    missing. Multi-line folded scalars are not supported (USAP keeps
    descriptions on a single line).
    """
    if not text.startswith("---"):
        return ""
    end = text.find("\n---", 3)
    if end == -1:
        return ""
    block = text[3:end]
    for line in block.split("\n"):
        m = re.match(r"^description:\s*(.*)$", line)
        if m:
            value = m.group(1).strip()
            # Strip wrapping quotes if any.
            if (value.startswith('"') and value.endswith('"')) or (
                value.startswith("'") and value.endswith("'")
            ):
                value = value[1:-1]
            return value
    return ""


def validate_description(skill_dir: Path) -> List[str]:
    errors: List[str] = []
    skill_md = skill_dir / "SKILL.md"
    if not skill_md.is_file():
        return [f"SKILL.md not found in {skill_dir}"]
    try:
        content = skill_md.read_text(encoding="utf-8")
    except UnicodeDecodeError as exc:
        return [f"SKILL.md is not valid UTF-8: {exc}"]

    desc = extract_description(content)
    if not desc:
        return ["description missing or empty"]

    if len(desc) > MAX_DESC_LEN:
        errors.append(
            f"description is {len(desc)} chars (max {MAX_DESC_LEN})"
        )

    fp = FIRST_PERSON_RE.search(desc)
    if fp:
        errors.append(
            f"description uses first-person pronoun '{fp.group(0)}' — "
            "write in third person"
        )

    if not any(p.search(desc) for p in TRIGGER_PATTERNS):
        errors.append(
            "description lacks a trigger phrase — include 'Use when', "
            "'Use for', or a 'For ...' clause so the runtime can route to it"
        )

    return errors


def list_active_skills(repo_root: Path) -> List[Path]:
    out: List[Path] = []
    for domain in ACTIVE_DOMAINS:
        domain_root = repo_root / domain
        if not domain_root.is_dir():
            continue
        for skill_dir in sorted(domain_root.iterdir()):
            if skill_dir.is_dir() and (skill_dir / "SKILL.md").is_file():
                out.append(skill_dir)
    return out


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate SKILL.md description fields."
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
    failing: List[Tuple[Path, List[str]]] = []

    for skill_dir in targets:
        errs = validate_description(skill_dir)
        rel = (
            skill_dir.relative_to(REPO_ROOT)
            if skill_dir.is_relative_to(REPO_ROOT)
            else skill_dir
        )
        if errs:
            failed += 1
            failing.append((skill_dir, errs))
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
    if failing and not args.strict:
        print(
            f"{YELLOW}note{RESET}: report-only mode; pass --strict to fail "
            "the run when descriptions are off-spec."
        )

    if args.strict and failed:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
