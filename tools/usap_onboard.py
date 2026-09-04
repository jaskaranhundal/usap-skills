#!/usr/bin/env python3
"""USAP first-time operator onboarding.

Idempotent — running twice is safe and does not clobber an existing audit
key. Stdlib only. Never network.

Defaults:
  * Create ~/.usap/ and ~/.usap/audit/ if missing.
  * Generate ~/.usap/.audit_key (64 hex chars from secrets.token_hex(32))
    if missing, chmod 600. NEVER overwrites an existing key.
  * Print the export line the operator must add to their shell init.

Flags:
  --enable JOB_ID   Flip the named runner.yaml job's `enabled:` to true
                    (preserving the rest of the file verbatim).
  --quiet           Skip interactive prompts; print only essentials.
"""

from __future__ import annotations

import argparse
import re
import secrets
import stat
import sys
from pathlib import Path
from typing import Iterable


REPO_ROOT = Path(__file__).resolve().parent.parent
USAP_DIR = Path.home() / ".usap"
AUDIT_DIR = USAP_DIR / "audit"
AUDIT_KEY_FILE = USAP_DIR / ".audit_key"
RUNNER_CONFIG = REPO_ROOT / "runner" / "runner.yaml"


def ensure_dirs(quiet: bool) -> bool:
    created = False
    if not USAP_DIR.is_dir():
        USAP_DIR.mkdir(parents=True, exist_ok=True)
        created = True
        if not quiet:
            print(f"[created] {USAP_DIR}")
    if not AUDIT_DIR.is_dir():
        AUDIT_DIR.mkdir(parents=True, exist_ok=True)
        created = True
        if not quiet:
            print(f"[created] {AUDIT_DIR}")
    return created


def ensure_audit_key(quiet: bool) -> bool:
    """Generate the key if missing. Never overwrite. Always tighten perms."""
    if AUDIT_KEY_FILE.is_file():
        mode = stat.S_IMODE(AUDIT_KEY_FILE.stat().st_mode)
        if mode != 0o600:
            AUDIT_KEY_FILE.chmod(0o600)
            if not quiet:
                print(f"[chmod 600] {AUDIT_KEY_FILE} (was {oct(mode)})")
        elif not quiet:
            print(f"[ok] {AUDIT_KEY_FILE} already present")
        return False
    AUDIT_KEY_FILE.write_text(secrets.token_hex(32))
    AUDIT_KEY_FILE.chmod(0o600)
    if not quiet:
        print(f"[created] {AUDIT_KEY_FILE} (0600, 64 hex chars)")
    return True


def print_shell_hint(quiet: bool) -> None:
    if quiet:
        print(f"export USAP_AUDIT_KEY={AUDIT_KEY_FILE}")
        return
    print()
    print("Add this line to your shell init (~/.zshrc, ~/.bashrc) so the runner")
    print("and audit verifier can sign and check log entries:")
    print()
    print(f"    export USAP_AUDIT_KEY={AUDIT_KEY_FILE}")
    print()


_JOB_HEADER_RE = re.compile(r"^(\s*-\s*id:\s*)(\S+)\s*$")
_ENABLED_RE = re.compile(r"^(\s*enabled:\s*)(true|false)(.*)$")


def enable_job(job_id: str, quiet: bool) -> int:
    if not RUNNER_CONFIG.is_file():
        print(f"error: {RUNNER_CONFIG} not found", file=sys.stderr)
        return 1
    lines = RUNNER_CONFIG.read_text().splitlines()
    in_job = False
    job_start: int | None = None
    found = False
    for i, line in enumerate(lines):
        m = _JOB_HEADER_RE.match(line)
        if m:
            in_job = m.group(2) == job_id
            if in_job:
                job_start = i
                found = True
            continue
        if in_job:
            em = _ENABLED_RE.match(line)
            if em:
                if em.group(2) == "true":
                    if not quiet:
                        print(f"[ok] job {job_id!r} already enabled")
                    return 0
                lines[i] = f"{em.group(1)}true{em.group(3)}"
                RUNNER_CONFIG.write_text("\n".join(lines) + "\n")
                if not quiet:
                    print(f"[enabled] job {job_id!r} (line {i + 1})")
                return 0
    if not found:
        print(f"error: job id {job_id!r} not found in {RUNNER_CONFIG}", file=sys.stderr)
        return 1
    print(
        f"error: job {job_id!r} has no `enabled:` line; refusing to invent one",
        file=sys.stderr,
    )
    return 1


def main(argv: Iterable[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="USAP first-time operator onboarding.")
    ap.add_argument(
        "--enable",
        metavar="JOB_ID",
        help="Flip the named runner.yaml job to enabled: true.",
    )
    ap.add_argument(
        "--quiet", action="store_true", help="Skip prompts; print only essentials."
    )
    args = ap.parse_args(list(argv) if argv is not None else None)

    if args.enable:
        return enable_job(args.enable, args.quiet)

    ensure_dirs(args.quiet)
    ensure_audit_key(args.quiet)
    print_shell_hint(args.quiet)
    return 0


if __name__ == "__main__":
    sys.exit(main())
