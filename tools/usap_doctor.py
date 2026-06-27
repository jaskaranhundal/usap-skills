#!/usr/bin/env python3
"""USAP operator-side defects scanner.

Diagnoses common breakages in an operator's local USAP install: missing
directories, missing or mis-permissioned audit key, dead PID files, audit-
chain breaks, mixed signed/unsigned audit lines (the docs/mcp-scheduled.md
§7 gotcha), and invalid runner / registry configs.

Modes:
  --check         Read-only diagnostic (default).
  --fix           Apply safe remediations (create dirs, regen missing key,
                  remove dead PID files).
  --report yaml   Emit a machine-readable summary instead of human prose.

Stdlib only. Never network, never mutates outside ~/.usap/ unless --fix.
"""

from __future__ import annotations

import argparse
import json
import os
import secrets
import stat
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable


REPO_ROOT = Path(__file__).resolve().parent.parent
USAP_DIR = Path.home() / ".usap"
AUDIT_DIR = USAP_DIR / "audit"
AUDIT_KEY_FILE = USAP_DIR / ".audit_key"
RUNNER_PID = USAP_DIR / "runner.pid"
RUNNER_CONFIG = REPO_ROOT / "runner" / "runner.yaml"
REGISTRY_FILE = REPO_ROOT / "registry" / "usap-mcp-registry.yaml"


@dataclass
class Finding:
    check: str
    status: str  # "ok" | "warn" | "fail"
    detail: str
    fixed: bool = False
    fix_hint: str = ""


@dataclass
class Report:
    findings: list[Finding] = field(default_factory=list)
    fix_mode: bool = False

    def add(self, f: Finding) -> None:
        self.findings.append(f)

    @property
    def worst(self) -> str:
        order = {"ok": 0, "warn": 1, "fail": 2}
        return max((f.status for f in self.findings), key=lambda s: order[s], default="ok")


def _today_files() -> list[Path]:
    if not AUDIT_DIR.is_dir():
        return []
    return sorted(p for p in AUDIT_DIR.glob("*.jsonl") if p.is_file())


def _pid_alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
    except (ProcessLookupError, PermissionError):
        return pid > 0 and os.path.exists(f"/proc/{pid}") if sys.platform == "linux" else False
    except OSError:
        return False
    return True


def check_usap_dir(report: Report) -> None:
    if USAP_DIR.is_dir():
        report.add(Finding("usap-dir", "ok", f"{USAP_DIR} exists"))
        return
    if report.fix_mode:
        USAP_DIR.mkdir(parents=True, exist_ok=True)
        AUDIT_DIR.mkdir(parents=True, exist_ok=True)
        report.add(Finding("usap-dir", "ok", f"created {USAP_DIR}", fixed=True))
    else:
        report.add(
            Finding(
                "usap-dir",
                "fail",
                f"{USAP_DIR} missing",
                fix_hint="run with --fix to create",
            )
        )


def check_audit_key(report: Report) -> None:
    if not AUDIT_KEY_FILE.is_file():
        if report.fix_mode and USAP_DIR.is_dir():
            AUDIT_KEY_FILE.write_text(secrets.token_hex(32))
            AUDIT_KEY_FILE.chmod(0o600)
            report.add(
                Finding(
                    "audit-key",
                    "ok",
                    f"generated {AUDIT_KEY_FILE} (0600)",
                    fixed=True,
                )
            )
        else:
            report.add(
                Finding(
                    "audit-key",
                    "warn",
                    f"{AUDIT_KEY_FILE} missing (unsigned audit mode)",
                    fix_hint="run with --fix to generate, or run usap_onboard.py",
                )
            )
        return

    mode = stat.S_IMODE(AUDIT_KEY_FILE.stat().st_mode)
    if mode != 0o600:
        if report.fix_mode:
            AUDIT_KEY_FILE.chmod(0o600)
            report.add(
                Finding(
                    "audit-key",
                    "ok",
                    f"tightened {AUDIT_KEY_FILE} to 0600 (was {oct(mode)})",
                    fixed=True,
                )
            )
        else:
            report.add(
                Finding(
                    "audit-key",
                    "fail",
                    f"{AUDIT_KEY_FILE} has perms {oct(mode)}; expected 0600",
                    fix_hint="run with --fix to chmod 600",
                )
            )
        return
    report.add(Finding("audit-key", "ok", f"{AUDIT_KEY_FILE} present (0600)"))


def check_runner_pid(report: Report) -> None:
    if not RUNNER_PID.is_file():
        report.add(Finding("runner-pid", "ok", "no PID file (runner not started)"))
        return
    raw = RUNNER_PID.read_text().strip()
    try:
        pid = int(raw)
    except ValueError:
        if report.fix_mode:
            RUNNER_PID.unlink()
            report.add(
                Finding("runner-pid", "ok", f"removed garbled PID file ({raw!r})", fixed=True)
            )
        else:
            report.add(
                Finding(
                    "runner-pid",
                    "fail",
                    f"PID file contents not an integer: {raw!r}",
                    fix_hint="run with --fix to remove",
                )
            )
        return
    if _pid_alive(pid):
        report.add(Finding("runner-pid", "ok", f"runner alive (pid {pid})"))
        return
    if report.fix_mode:
        RUNNER_PID.unlink()
        report.add(
            Finding("runner-pid", "ok", f"removed dead PID file (pid {pid})", fixed=True)
        )
    else:
        report.add(
            Finding(
                "runner-pid",
                "warn",
                f"PID {pid} not alive but runner.pid present",
                fix_hint="run with --fix to remove stale PID file",
            )
        )


def _scan_audit_file(path: Path) -> tuple[int, int, int, list[str]]:
    """Return (total, with_prev_hash, with_sig, errors)."""
    total = with_prev = with_sig = 0
    errors: list[str] = []
    for lineno, line in enumerate(path.read_text().splitlines(), 1):
        line = line.strip()
        if not line:
            continue
        total += 1
        try:
            entry = json.loads(line)
        except json.JSONDecodeError as exc:
            errors.append(f"{path.name}:{lineno}: not JSON ({exc})")
            continue
        if "prev_hash" in entry:
            with_prev += 1
        else:
            errors.append(f"{path.name}:{lineno}: missing prev_hash")
        if "sig" in entry:
            with_sig += 1
    return total, with_prev, with_sig, errors


def check_audit_logs(report: Report) -> None:
    files = _today_files()
    if not files:
        report.add(Finding("audit-logs", "ok", "no audit logs to scan"))
        return
    key_configured = bool(os.environ.get("USAP_AUDIT_KEY"))
    mixed_files: list[str] = []
    for f in files:
        total, with_prev, with_sig, errors = _scan_audit_file(f)
        if total == 0:
            continue
        for e in errors[:3]:
            report.add(Finding("audit-prev-hash", "fail", e))
        if with_prev < total:
            report.add(
                Finding(
                    "audit-prev-hash",
                    "fail",
                    f"{f.name}: {total - with_prev}/{total} lines missing prev_hash",
                )
            )
        if key_configured and with_sig < total:
            report.add(
                Finding(
                    "audit-signatures",
                    "fail",
                    f"{f.name}: USAP_AUDIT_KEY set but {total - with_sig}/{total} lines unsigned",
                )
            )
        if 0 < with_sig < total:
            mixed_files.append(f"{f.name} (signed={with_sig}/{total})")

    if mixed_files:
        report.add(
            Finding(
                "audit-mixed-mode",
                "warn",
                "mixed signed/unsigned lines in same-day log(s): "
                + "; ".join(mixed_files)
                + " — see docs/mcp-scheduled.md §7 (NOT auto-fixed)",
            )
        )
    else:
        report.add(Finding("audit-mixed-mode", "ok", "no mixed-mode logs detected"))


def _run(cmd: list[str]) -> tuple[int, str]:
    try:
        proc = subprocess.run(
            cmd, capture_output=True, text=True, cwd=str(REPO_ROOT), timeout=30
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return 1, str(exc)
    out = (proc.stdout + proc.stderr).strip().splitlines()
    return proc.returncode, out[-1] if out else ""


def check_runner_config(report: Report) -> None:
    if not RUNNER_CONFIG.is_file():
        report.add(Finding("runner-config", "fail", f"{RUNNER_CONFIG} missing"))
        return
    code, tail = _run([sys.executable, str(REPO_ROOT / "tools" / "usap_runner.py"), "--validate"])
    if code == 0:
        report.add(Finding("runner-config", "ok", "usap_runner.py --validate passed"))
    else:
        report.add(
            Finding(
                "runner-config",
                "fail",
                f"usap_runner.py --validate failed (exit {code}): {tail}",
            )
        )


def check_registry(report: Report) -> None:
    if not REGISTRY_FILE.is_file():
        report.add(Finding("registry", "fail", f"{REGISTRY_FILE} missing"))
        return
    code, tail = _run([sys.executable, str(REPO_ROOT / "tools" / "mcp_registry.py"), "--validate"])
    if code == 0:
        report.add(Finding("registry", "ok", "mcp_registry.py --validate passed"))
    else:
        report.add(
            Finding(
                "registry",
                "fail",
                f"mcp_registry.py --validate failed (exit {code}): {tail}",
            )
        )


def render_prose(report: Report) -> str:
    lines = ["USAP doctor — operator-side checks", "=" * 36]
    for f in report.findings:
        marker = {"ok": "[ok]  ", "warn": "[warn]", "fail": "[fail]"}[f.status]
        suffix = " (fixed)" if f.fixed else ""
        lines.append(f"{marker} {f.check}: {f.detail}{suffix}")
        if f.fix_hint and not f.fixed:
            lines.append(f"        hint: {f.fix_hint}")
    lines.append("")
    lines.append(f"worst: {report.worst}")
    return "\n".join(lines)


def render_yaml(report: Report) -> str:
    out = ["usap_doctor:", f"  worst: {report.worst}", "  findings:"]
    for f in report.findings:
        out.append(f"    - check: {f.check}")
        out.append(f"      status: {f.status}")
        out.append(f"      detail: {json.dumps(f.detail)}")
        out.append(f"      fixed: {'true' if f.fixed else 'false'}")
        if f.fix_hint:
            out.append(f"      fix_hint: {json.dumps(f.fix_hint)}")
    return "\n".join(out)


def main(argv: Iterable[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="USAP operator-side defects scanner.")
    mode = ap.add_mutually_exclusive_group()
    mode.add_argument("--check", action="store_true", help="Read-only diagnostic (default).")
    mode.add_argument("--fix", action="store_true", help="Apply safe remediations.")
    ap.add_argument("--report", choices=["prose", "yaml"], default="prose")
    args = ap.parse_args(list(argv) if argv is not None else None)

    report = Report(fix_mode=bool(args.fix))
    check_usap_dir(report)
    check_audit_key(report)
    check_runner_pid(report)
    check_audit_logs(report)
    check_runner_config(report)
    check_registry(report)

    if args.report == "yaml":
        print(render_yaml(report))
    else:
        print(render_prose(report))

    return 1 if report.worst == "fail" else 0


if __name__ == "__main__":
    sys.exit(main())
