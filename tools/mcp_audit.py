#!/usr/bin/env python3
"""USAP MCP audit log writer (Phase 2).

Every routing decision is appended to a JSONL file under
``~/.usap/audit/YYYY-MM-DD.jsonl``. Each line is one event with:

  timestamp_utc    ISO 8601 UTC at write time
  event            "route" | "dispatch" | "approval_granted" | "approval_denied"
  payload          the 11-field USAP payload that drove the decision
  decision         the router result (status, selected_mcp, ...)
  meta             optional extra fields (caller id, request id, etc.)

Phase 2 ships only the writer. Phase 3 will add a reader for tail / query.
Phase 4 will add cryptographic signing so the log is unfalsifiable.

The audit dir can be overridden with the ``USAP_AUDIT_DIR`` env var — useful
in CI / tests.

Stdlib only.
"""
from __future__ import annotations

import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path


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


def write_audit(entry: dict) -> Path:
    """Append one entry to today's audit log. Returns the path written."""
    entry = dict(entry)  # don't mutate the caller's dict
    entry["timestamp_utc"] = entry.get("timestamp_utc") or _now_utc()
    entry.setdefault("event", "route")
    today = entry["timestamp_utc"].split("T")[0]
    log = audit_dir() / f"{today}.jsonl"
    with log.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry, separators=(",", ":")) + "\n")
    return log


def main() -> int:
    """CLI: tail the most recent audit log."""
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--tail", type=int, default=20,
                    help="Number of most recent entries to show.")
    args = ap.parse_args()
    d = audit_dir()
    logs = sorted(d.glob("*.jsonl"))
    if not logs:
        print(f"No audit logs in {d}")
        return 0
    latest = logs[-1]
    lines = latest.read_text().splitlines()[-args.tail:]
    print(f"# {latest}")
    for line in lines:
        try:
            entry = json.loads(line)
            print(f"{entry['timestamp_utc']}  {entry.get('event')}  "
                  f"-> {entry.get('decision', {}).get('status', '?')}")
        except json.JSONDecodeError:
            print(line)
    return 0


if __name__ == "__main__":
    sys.exit(main())
