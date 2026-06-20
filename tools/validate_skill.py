#!/usr/bin/env python3
"""Validate SKILL.md frontmatter for USAP skills.

Enforces USAP's canonical 5+5 schema (see ``standards/frontmatter-spec.md``):

  Top-level required:  name, description, license
  metadata required:   version, author, category, updated, agent_slug

Checks:
  - ``name`` is kebab-case, max 64 chars, matches directory slug
  - ``description`` is a string of >= 50 chars
  - ``license`` is one of MIT, Apache-2.0, GPL-3.0
  - ``metadata.version`` is valid semver (X.Y.Z)
  - ``metadata.category`` is one of the 8 USAP enum tokens
  - ``metadata.updated`` is ISO YYYY-MM-DD
  - ``metadata.agent_slug`` equals ``name``
  - no ``*.ps1`` files anywhere under ``<skill>/scripts/`` (USAP keeps tool
    scripts cross-platform stdlib-only Python)

Emits non-blocking WARNs (does not fail the run) for:
  - legacy extended-frontmatter keys still present at the YAML top level
    (agent_id, level, plane, phase, ttl, mutating_intents, can_execute,
    providers, required_invoke_role, required_approver_role, input_schema,
    output_schema, runtime_contract, approval_required) — see Phase 4 of the
    roadmap for migration

Usage::

    python3 tools/validate_skill.py <skill-dir>
    python3 tools/validate_skill.py --all
    python3 tools/validate_skill.py --all --summary

``--summary`` appends a per-domain skill-count table to ``$GITHUB_STEP_SUMMARY``
(or stdout if the env var is not set), so future doc-vs-disk count drift fails
the build.

Exit codes:
  0 = clean
  1 = one or more skills have errors
"""
from __future__ import annotations

import argparse
import os
import re
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

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

REQUIRED_TOP = ("name", "description", "license")
REQUIRED_METADATA = ("version", "author", "category", "updated", "agent_slug")

ALLOWED_LICENSES = {"MIT", "Apache-2.0", "GPL-3.0"}
ALLOWED_CATEGORIES = {
    # Kept in sync with standards/frontmatter-spec.md (Category section).
    # Extended 2026-06-20 from the original 8 to the 18 tokens actually used
    # across the 11 active domains. Add new tokens to both this set and the
    # spec; the CI workflow refuses values outside the set.
    "usap-adversary",
    "usap-appsec-devsecops",
    "usap-control-plane",
    "usap-detection",
    "usap-devsecops",
    "usap-engineering",
    "usap-executive",
    "usap-governance",
    "usap-identity-access",
    "usap-infrastructure",
    "usap-operations",
    "usap-pentest",
    "usap-platform-ai",
    "usap-red-team",
    "usap-response",
    "usap-risk-compliance",
    "usap-safety",
    "usap-system-security",
    "usap-webapp",
}

FRAMEWORK_CAP = 8
FRAMEWORK_PATTERNS = {
    # See standards/frontmatter-spec.md "Framework Mappings".
    "mitre_attack": re.compile(r"^T\d{4}(\.\d{3})?$"),
    "nist_csf": re.compile(r"^[A-Z]{2}\.[A-Z]{2}-\d{2}$"),
    "mitre_atlas": re.compile(r"^AML\.T\d{4}(\.\d{3})?$"),
    "owasp_top10": re.compile(r"^A\d{2}$"),
    "nist_ai_rmf": re.compile(r"^[A-Z]{2,7}-\d+(\.\d+)*$"),
    # d3fend: free-text technique labels; cap-only, no pattern check.
    "d3fend": None,
}

LEGACY_KEYS = {
    "agent_id",
    "level",
    "plane",
    "phase",
    "ttl",
    "approval_required",
    "mutating_intents",
    "can_execute",
    "providers",
    "required_invoke_role",
    "required_approver_role",
    "input_schema",
    "output_schema",
    "runtime_contract",
}

KEBAB_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
SEMVER_RE = re.compile(r"^\d+\.\d+\.\d+$")
ISO_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
MAX_NAME_LEN = 64
MIN_DESC_LEN = 50

# ANSI colours only when stdout is a TTY (avoid escape-code noise in CI logs).
_TTY = sys.stdout.isatty()
RED = "\033[91m" if _TTY else ""
GREEN = "\033[92m" if _TTY else ""
YELLOW = "\033[93m" if _TTY else ""
RESET = "\033[0m" if _TTY else ""


def _strip_quotes(value: str) -> str:
    value = value.strip()
    if (value.startswith('"') and value.endswith('"')) or (
        value.startswith("'") and value.endswith("'")
    ):
        return value[1:-1]
    return value


def parse_frontmatter(text: str) -> Optional[Dict[str, object]]:
    """Parse the leading ``---`` frontmatter as a nested dict, stdlib-only.

    Supports the patterns USAP actually uses, at arbitrary nesting depth
    expressed by 2-space indent steps:

      - ``key: scalar`` (any indent level)
      - ``key: [a, b, c]`` (inline list at any indent level)
      - ``key:`` followed by indented child lines — children may be either
        ``- item`` block-list entries or nested ``key: value`` pairs
      - Comment lines starting with ``#`` are ignored

    Returns ``None`` if no frontmatter block is found. Anchors, tags, and
    multi-line folded scalars are not supported; USAP's spec does not use
    them. Recursive descent on indent depth makes ``metadata.frameworks.*``
    parse correctly without special-casing.
    """
    if not text.startswith("---"):
        return None
    end = text.find("\n---", 3)
    if end == -1:
        return None
    block = text[3:end]

    # Pre-strip empty and comment lines; preserve original indent on what remains.
    lines: List[str] = []
    for raw in block.split("\n"):
        line = raw.rstrip()
        if not line.strip() or line.strip().startswith("#"):
            continue
        lines.append(line)

    # Recursive descent uses a single-element mutable cursor so the helper can
    # advance it across sibling calls. Closure over ``cursor`` keeps the public
    # signature clean while letting nested calls move the parse forward.
    cursor = [0]

    def _parse_at(min_indent: int):
        result: Dict[str, object] = {}
        block_list: List[str] = []
        is_list = False

        while cursor[0] < len(lines):
            line = lines[cursor[0]]
            indent = len(line) - len(line.lstrip(" "))

            if indent < min_indent:
                break

            if indent > min_indent:
                # Stray deeper indent without a parent context — skip safely.
                cursor[0] += 1
                continue

            stripped = line.strip()

            # Block-list item.
            if stripped.startswith("- "):
                is_list = True
                block_list.append(_strip_quotes(stripped[2:]))
                cursor[0] += 1
                continue

            # Inline list at this level.
            m = re.match(r"^([a-zA-Z_][\w-]*):\s*\[(.*)\]\s*$", stripped)
            if m:
                items = [
                    _strip_quotes(i)
                    for i in m.group(2).split(",")
                    if i.strip()
                ]
                result[m.group(1)] = items
                cursor[0] += 1
                continue

            # key: value (value may be empty — nested block follows).
            m = re.match(r"^([a-zA-Z_][\w-]*):\s*(.*)$", stripped)
            if m:
                key = m.group(1)
                val = m.group(2).strip()
                cursor[0] += 1
                if val:
                    result[key] = _strip_quotes(val)
                else:
                    # Look ahead: is the next non-trivial line more indented?
                    if cursor[0] < len(lines):
                        nxt = lines[cursor[0]]
                        nxt_indent = len(nxt) - len(nxt.lstrip(" "))
                        if nxt_indent > min_indent:
                            result[key] = _parse_at(nxt_indent)
                            continue
                    # No nested body — record as empty string.
                    result[key] = ""
                continue

            # Unrecognized construct — advance to avoid infinite loop.
            cursor[0] += 1

        return block_list if is_list else result

    parsed = _parse_at(0)
    return parsed if isinstance(parsed, dict) else {}


def validate_skill(skill_dir: Path) -> Tuple[List[str], List[str]]:
    """Return ``(errors, warnings)`` for one skill directory."""
    errors: List[str] = []
    warnings: List[str] = []

    skill_md = skill_dir / "SKILL.md"
    if not skill_md.is_file():
        return [f"SKILL.md not found in {skill_dir}"], []

    try:
        content = skill_md.read_text(encoding="utf-8")
    except UnicodeDecodeError as exc:
        return [f"SKILL.md is not valid UTF-8: {exc}"], []

    fm = parse_frontmatter(content)
    if fm is None:
        return ["No valid YAML frontmatter (must start with ---)"], []

    slug = skill_dir.name

    # Non-blocking warning: legacy extended-frontmatter keys at top level.
    legacy_present = sorted(k for k in LEGACY_KEYS if k in fm)
    if legacy_present:
        warnings.append(
            "legacy extended-frontmatter keys at top level "
            f"({', '.join(legacy_present)}) — see Phase 4 migration"
        )

    # Required top-level fields.
    for field in REQUIRED_TOP:
        if field not in fm:
            errors.append(f"missing required top-level field: {field}")

    # name rules.
    name = fm.get("name", "")
    if isinstance(name, str) and name:
        if not KEBAB_RE.match(name):
            errors.append(f"name '{name}' is not valid kebab-case")
        if len(name) > MAX_NAME_LEN:
            errors.append(
                f"name too long ({len(name)} chars, max {MAX_NAME_LEN})"
            )
        if name != slug:
            errors.append(
                f"name '{name}' must match directory slug '{slug}'"
            )

    # description rules.
    desc = fm.get("description", "")
    if isinstance(desc, list):
        errors.append("description must be a string, not a list")
    elif isinstance(desc, str) and len(desc) < MIN_DESC_LEN:
        errors.append(
            f"description too short ({len(desc)} chars, min {MIN_DESC_LEN})"
        )

    # license enum.
    lic = fm.get("license", "")
    if isinstance(lic, str) and lic and lic not in ALLOWED_LICENSES:
        errors.append(
            f"license '{lic}' not in {sorted(ALLOWED_LICENSES)}"
        )

    # metadata block.
    metadata = fm.get("metadata")
    if metadata is None:
        # Already counted as a missing required field above when applicable;
        # add a specific message so the contributor sees both issues.
        if "metadata" not in fm:
            errors.append("missing required top-level field: metadata")
    elif not isinstance(metadata, dict):
        errors.append("metadata must be an object with required subfields")
    else:
        for sub in REQUIRED_METADATA:
            if sub not in metadata:
                errors.append(f"missing required metadata.{sub}")

        version = metadata.get("version", "")
        if isinstance(version, str) and version and not SEMVER_RE.match(version):
            errors.append(
                f"metadata.version '{version}' is not valid semver (X.Y.Z)"
            )

        category = metadata.get("category", "")
        if (
            isinstance(category, str)
            and category
            and category not in ALLOWED_CATEGORIES
        ):
            errors.append(
                f"metadata.category '{category}' not in "
                f"{sorted(ALLOWED_CATEGORIES)}"
            )

        updated = metadata.get("updated", "")
        if isinstance(updated, str) and updated and not ISO_DATE_RE.match(updated):
            errors.append(
                f"metadata.updated '{updated}' is not ISO YYYY-MM-DD"
            )

        agent_slug = metadata.get("agent_slug", "")
        if (
            isinstance(agent_slug, str)
            and agent_slug
            and isinstance(name, str)
            and name
            and agent_slug != name
        ):
            errors.append(
                f"metadata.agent_slug '{agent_slug}' must equal name '{name}'"
            )

        # Optional metadata.frameworks block.
        frameworks = metadata.get("frameworks")
        if frameworks is not None:
            if not isinstance(frameworks, dict):
                errors.append(
                    "metadata.frameworks must be an object with framework "
                    "names as keys (mitre_attack, nist_csf, ...)"
                )
            else:
                for fname, ids in frameworks.items():
                    if fname not in FRAMEWORK_PATTERNS:
                        errors.append(
                            f"metadata.frameworks.{fname} is not a known "
                            "framework key (see frontmatter-spec.md)"
                        )
                        continue
                    if not isinstance(ids, list) or not all(
                        isinstance(x, str) for x in ids
                    ):
                        errors.append(
                            f"metadata.frameworks.{fname} must be an array of strings"
                        )
                        continue
                    if len(ids) > FRAMEWORK_CAP:
                        errors.append(
                            f"metadata.frameworks.{fname} has {len(ids)} entries "
                            f"(cap {FRAMEWORK_CAP} per framework — split skills "
                            "or trim to highest-signal IDs)"
                        )
                    pattern = FRAMEWORK_PATTERNS[fname]
                    if pattern is not None:
                        for entry in ids:
                            if not pattern.match(entry):
                                errors.append(
                                    f"metadata.frameworks.{fname} '{entry}' does "
                                    f"not match expected pattern {pattern.pattern}"
                                )

    # No PowerShell-only scripts.
    scripts_dir = skill_dir / "scripts"
    if scripts_dir.is_dir():
        ps1_files = sorted(scripts_dir.glob("*.ps1"))
        if ps1_files:
            errors.append(
                ".ps1 files not permitted in scripts/ "
                f"({', '.join(p.name for p in ps1_files)})"
            )

    return errors, warnings


def domain_skills(repo_root: Path) -> Dict[str, List[Path]]:
    """Return ``{domain: [skill_dir, ...]}`` for the 11 active domains."""
    out: Dict[str, List[Path]] = {}
    for domain in ACTIVE_DOMAINS:
        domain_root = repo_root / domain
        if not domain_root.is_dir():
            out[domain] = []
            continue
        out[domain] = sorted(
            p
            for p in domain_root.iterdir()
            if p.is_dir() and (p / "SKILL.md").is_file()
        )
    return out


def emit_summary(domain_map: Dict[str, List[Path]], total: int) -> None:
    """Write a per-domain skill-count table to ``GITHUB_STEP_SUMMARY``.

    Falls back to stdout when the env var is not set (useful for local runs).
    """
    lines = [
        "",
        "## USAP skill inventory",
        "",
        "| Domain | Skill count |",
        "|---|---|",
    ]
    for domain, skills in domain_map.items():
        lines.append(f"| `{domain}` | {len(skills)} |")
    lines.append(f"| **Total** | **{total}** |")
    text = "\n".join(lines) + "\n"

    summary_path = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary_path:
        with open(summary_path, "a", encoding="utf-8") as fh:
            fh.write(text)
    else:
        print(text)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate USAP SKILL.md frontmatter."
    )
    parser.add_argument(
        "target",
        nargs="?",
        help="Path to a single skill directory (omit when using --all).",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Validate every skill under the 11 active domains.",
    )
    parser.add_argument(
        "--summary",
        action="store_true",
        help="Emit per-domain skill counts (writes to "
        "GITHUB_STEP_SUMMARY when set, else stdout). Requires --all.",
    )
    args = parser.parse_args()

    if not args.all and not args.target:
        parser.error("provide a skill directory or use --all")

    if args.all:
        domain_map = domain_skills(REPO_ROOT)
        all_dirs = [d for skills in domain_map.values() for d in skills]
    else:
        target = Path(args.target).resolve()
        if not target.is_dir():
            print(f"{RED}error{RESET}: not a directory: {target}", file=sys.stderr)
            return 1
        domain_map = {}
        all_dirs = [target]

    total = len(all_dirs)
    passed = failed = warned = 0

    for skill_dir in all_dirs:
        errors, warnings = validate_skill(skill_dir)
        rel = skill_dir.relative_to(REPO_ROOT) if skill_dir.is_relative_to(REPO_ROOT) else skill_dir

        if errors:
            failed += 1
            print(f"{RED}FAIL{RESET} {rel}")
            for err in errors:
                print(f"      {RED}x{RESET} {err}")
        else:
            passed += 1
            print(f"{GREEN}PASS{RESET} {rel}")

        if warnings:
            warned += 1
            for w in warnings:
                print(f"      {YELLOW}!{RESET} {w}")

    print()
    print("=" * 60)
    print(
        f"Total: {total}  "
        f"{GREEN}Passed: {passed}{RESET}  "
        f"{RED}Failed: {failed}{RESET}  "
        f"{YELLOW}Warned: {warned}{RESET}"
    )

    if args.summary and args.all:
        emit_summary(domain_map, total)

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
