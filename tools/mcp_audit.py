#!/usr/bin/env python3
"""USAP MCP audit log writer (Phase 4).

Every routing decision and scheduled job is appended to a JSONL file under
``~/.usap/audit/YYYY-MM-DD.jsonl``. Phase 4 adds tamper-detection:

  * **Hash chain.** Each line includes ``prev_hash`` = SHA-256 of the previous
    line's full JSON (or "GENESIS" for the first line). A verifier can walk
    the chain forward, recompute every hash, and detect any insertion,
    deletion, or modification anywhere in the log.

  * **HMAC line signatures.** If ``USAP_AUDIT_KEY`` is set in the environment,
    every line also carries an HMAC-SHA256 signature over its content. The
    verifier checks both the chain AND every signature, so an attacker who
    obtained the key still can't insert lines without breaking the chain.

Each line carries:

  timestamp_utc    ISO 8601 UTC
  event            "route" | "dispatch" | "approval_granted" |
                   "approval_denied" | "scheduled_run"
  payload          the 11-field USAP payload that drove the decision
  decision         the router result (status, selected_mcp, ...)
  prev_hash        SHA-256 of the previous line, hex-encoded
  sig              optional HMAC-SHA256(content, USAP_AUDIT_KEY), hex-encoded

Audit dir is overridable via ``USAP_AUDIT_DIR`` — useful in CI / tests.

Stdlib only.
"""
from __future__ import annotations

import hashlib
import hmac
import json
import os
import sys

try:
    import fcntl  # POSIX advisory locks; see write_audit
except ImportError:  # pragma: no cover - Windows is outside the runtime's scope
    fcntl = None
_LOCK_WARNED = False
from datetime import datetime, timezone
from pathlib import Path


GENESIS_HASH = "GENESIS"


def audit_dir() -> Path:
    override = os.environ.get("USAP_AUDIT_DIR")
    if override:
        d = Path(override)
    else:
        d = Path.home() / ".usap" / "audit"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _now_utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")


def _audit_key() -> bytes | None:
    """Return the per-deployment HMAC key, or None if unset.

    USAP_AUDIT_KEY can be:
      * Hex-encoded bytes (length ≥ 32, all hex chars) — decoded as-is.
      * A path to a readable file — bytes read from disk.
      * Any other string — treated as a passphrase, derived via SHA-256.
    """
    raw = os.environ.get("USAP_AUDIT_KEY")
    if not raw:
        return None
    if len(raw) >= 32 and all(c in "0123456789abcdefABCDEF" for c in raw):
        try:
            return bytes.fromhex(raw)
        except ValueError:
            pass
    p = Path(raw)
    if p.is_file():
        return p.read_bytes().strip()
    return hashlib.sha256(raw.encode()).digest()


def _hash_line(line: str) -> str:
    return hashlib.sha256(line.encode()).hexdigest()


def _last_hash(log: Path) -> str:
    """Read the last line's SHA-256, or GENESIS if the log is empty/missing."""
    if not log.is_file() or log.stat().st_size == 0:
        return GENESIS_HASH
    with log.open("rb") as f:
        f.seek(0, 2)
        end = f.tell()
        buf = b""
        while end > 0 and b"\n" not in buf[:-1]:
            read_size = min(4096, end)
            end -= read_size
            f.seek(end)
            buf = f.read(read_size) + buf
        lines = [ln for ln in buf.split(b"\n") if ln.strip()]
    if not lines:
        return GENESIS_HASH
    return _hash_line(lines[-1].decode())


def write_audit(entry: dict) -> Path:
    """Append one entry with hash chain (+ optional HMAC) to today's log."""
    entry = dict(entry)
    entry["timestamp_utc"] = entry.get("timestamp_utc") or _now_utc()
    entry.setdefault("event", "route")
    today = entry["timestamp_utc"].split("T")[0]
    log = audit_dir() / f"{today}.jsonl"

    # Hold an exclusive per-log lock across read-predecessor, sign and append.
    # Without it two concurrent writers record the same predecessor and
    # verify() reports a broken chain during ordinary operation (Codex review
    # on PR #148, comment 3936197783).
    global _LOCK_WARNED
    lock_path = log.with_suffix(".lock")
    with lock_path.open("a", encoding="utf-8") as lk:
        if fcntl is not None:
            fcntl.flock(lk.fileno(), fcntl.LOCK_EX)
        elif not _LOCK_WARNED:
            _LOCK_WARNED = True
            sys.stderr.write("mcp_audit: audit_lock_unavailable on this platform; concurrent writers may fork the chain\n")
        try:
            entry["prev_hash"] = _last_hash(log)
            key = _audit_key()
            if key is not None:
                content = json.dumps(entry, separators=(",", ":"), sort_keys=True)
                entry["sig"] = hmac.new(key, content.encode(), hashlib.sha256).hexdigest()
            line = json.dumps(entry, separators=(",", ":"), sort_keys=True)
            with log.open("a", encoding="utf-8") as f:
                f.write(line + "\n")
                f.flush()
        finally:
            if fcntl is not None:
                fcntl.flock(lk.fileno(), fcntl.LOCK_UN)
    return log


def verify(log: Path) -> tuple[bool, list[str]]:
    """Walk the chain forward, recompute every hash, check every signature.

    Returns (ok, errors). ``ok`` is True only if every chain link AND every
    signature checks out.
    """
    if not log.is_file():
        return False, [f"Log not found: {log}"]
    key = _audit_key()
    errors: list[str] = []
    prev_full_hash = GENESIS_HASH
    with log.open("r", encoding="utf-8") as f:
        for lineno, raw in enumerate(f, start=1):
            line = raw.rstrip("\n")
            if not line.strip():
                continue
            try:
                entry = json.loads(line)
            except json.JSONDecodeError as exc:
                errors.append(f"line {lineno}: invalid JSON ({exc})")
                continue
            claimed_prev = entry.get("prev_hash", "(missing)")
            if claimed_prev != prev_full_hash:
                errors.append(
                    f"line {lineno}: prev_hash mismatch "
                    f"(claimed={claimed_prev[:16]}..., expected={prev_full_hash[:16]}...)"
                )
            if key is not None:
                sig = entry.pop("sig", None)
                if sig is None:
                    errors.append(f"line {lineno}: missing sig (key is configured)")
                else:
                    content = json.dumps(entry, separators=(",", ":"), sort_keys=True)
                    expected = hmac.new(key, content.encode(), hashlib.sha256).hexdigest()
                    if not hmac.compare_digest(sig, expected):
                        errors.append(f"line {lineno}: sig mismatch")
                entry["sig"] = sig
            prev_full_hash = _hash_line(line)
    return (not errors), errors


def main() -> int:
    """CLI: tail or verify the most recent audit log."""
    import argparse
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group()
    g.add_argument("--tail", type=int, default=20,
                   help="Number of most recent entries to show.")
    g.add_argument("--verify", action="store_true",
                   help="Walk the chain and report any tampering.")
    args = ap.parse_args()

    d = audit_dir()
    logs = sorted(d.glob("*.jsonl"))
    if not logs:
        print(f"No audit logs in {d}")
        return 0
    latest = logs[-1]

    if args.verify:
        ok, errors = verify(latest)
        print(f"# {latest}")
        if ok:
            print("OK — chain valid, signatures verified (or no key configured).")
            return 0
        print(f"FAIL — {len(errors)} issue(s):")
        for e in errors:
            print(f"  {e}")
        return 1

    lines = latest.read_text().splitlines()[-args.tail:]
    print(f"# {latest}")
    for line in lines:
        try:
            entry = json.loads(line)
            ts = entry.get("timestamp_utc", "?")
            event = entry.get("event", "?")
            status = entry.get("decision", {}).get("status", "?")
            sig_marker = " [signed]" if entry.get("sig") else ""
            print(f"{ts}  {event:<22}  -> {status}{sig_marker}")
        except json.JSONDecodeError:
            print(line)
    return 0


if __name__ == "__main__":
    sys.exit(main())
