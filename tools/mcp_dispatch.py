#!/usr/bin/env python3
"""USAP MCP dispatch — Phase 3.

Given a registry MCP entry and a capability id, launch the adapter as a
subprocess, complete the JSON-RPC handshake, invoke the capability, capture
the response, and terminate cleanly.

The dispatcher is the wire between USAP's routing decision (Phase 2) and the
specialist MCP adapter (Phase 3 onward). It is intentionally minimal — one
adapter call per dispatch invocation, no connection pooling, no streaming.
A future Phase will add pooling and richer transport options.

Stdlib only.
"""
from __future__ import annotations

import json
import os
import selectors
import subprocess
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

# Maximum seconds we will wait for an adapter response. Keeps SEV-1 latency
# bounded; configurable per dispatch via dispatch(timeout=...).
DEFAULT_TIMEOUT = 20.0
PROTOCOL_VERSION = "2025-06-18"


class DispatchError(RuntimeError):
    """Raised when an adapter fails to dispatch within the timeout or returns
    an error response."""


def _resolve_command(mcp: dict) -> tuple[str, list[str]]:
    """Resolve the adapter's launch command, treating relative paths in
    `args` as repo-root-relative so the registry stays portable."""
    command = mcp.get("command", "python3")
    raw_args = mcp.get("args", [])
    args: list[str] = []
    for a in raw_args:
        if a.startswith("./") or a.startswith("../"):
            args.append(str((REPO_ROOT / a.lstrip("./")).resolve()))
        else:
            args.append(a)
    return command, args


def _send(proc: subprocess.Popen, msg: dict) -> None:
    proc.stdin.write(json.dumps(msg) + "\n")
    proc.stdin.flush()


def _recv(proc: subprocess.Popen, timeout: float) -> dict:
    """Read one JSON-RPC line from the adapter within ``timeout`` seconds.

    Reads the pipe descriptor non-blockingly and re-checks the deadline between
    reads, so an adapter that stays alive without ever emitting a newline cannot
    block past the deadline (Codex review on PR #147, comment 3936200734).
    Bytes read past the first newline are kept on the process object for the
    next call.
    """
    deadline = time.monotonic() + timeout
    buf: bytes = getattr(proc, "_usap_buf", b"")
    fd = proc.stdout.fileno()
    sel = selectors.DefaultSelector()
    sel.register(fd, selectors.EVENT_READ)
    try:
        while True:
            nl = buf.find(b"\n")
            if nl != -1:
                line, buf = buf[:nl], buf[nl + 1:]
                proc._usap_buf = buf  # type: ignore[attr-defined]
                if line.strip():
                    return json.loads(line.decode("utf-8", "replace"))
                continue
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                proc._usap_buf = buf  # type: ignore[attr-defined]
                raise DispatchError(f"Adapter did not respond within {timeout}s")
            if not sel.select(timeout=min(remaining, 0.25)):
                if proc.poll() is not None:
                    raise DispatchError(_premature(proc))
                continue
            chunk = os.read(fd, 65536)
            if not chunk:
                raise DispatchError(_premature(proc))
            buf += chunk
    finally:
        sel.close()


def _premature(proc: subprocess.Popen) -> str:
    code = proc.poll()
    err = ""
    if code is not None and proc.stderr is not None:
        try:
            err = proc.stderr.read()
        except Exception:
            err = "(unreadable)"
    return f"Adapter exited prematurely (code={code}). stderr: {err or '(adapter closed stdout)'}"


def dispatch(
    mcp: dict,
    capability_id: str,
    arguments: dict | None = None,
    timeout: float = DEFAULT_TIMEOUT,
) -> dict:
    """Invoke one capability on a specialist adapter and return the result.

    Args:
        mcp: One entry from the registry — must contain `command`, `args`, `id`.
        capability_id: The capability to invoke (e.g. "post_message").
        arguments: Arguments passed to the capability.
        timeout: Seconds before we declare the adapter unresponsive.

    Returns:
        A dict with:
            ok (bool)         — True if the capability returned without error.
            adapter (str)     — The adapter id that handled the call.
            capability (str)  — The capability id invoked.
            response (dict|str) — The adapter's response content.
            error (str|None)  — Error message if ok is False.

    Raises:
        DispatchError on adapter launch failure or protocol violation.
    """
    arguments = arguments or {}
    command, args = _resolve_command(mcp)

    proc = subprocess.Popen(
        [command, *args],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        cwd=str(REPO_ROOT),
    )

    try:
        # 1. Initialize
        _send(proc, {
            "jsonrpc": "2.0", "id": 1, "method": "initialize",
            "params": {"protocolVersion": PROTOCOL_VERSION, "capabilities": {}},
        })
        init_resp = _recv(proc, timeout)
        if "error" in init_resp:
            raise DispatchError(f"initialize failed: {init_resp['error']}")

        # 2. tools/call <capability>
        _send(proc, {
            "jsonrpc": "2.0", "id": 2, "method": "tools/call",
            "params": {"name": capability_id, "arguments": arguments},
        })
        call_resp = _recv(proc, timeout)

        if "error" in call_resp:
            return {
                "ok": False,
                "adapter": mcp.get("id"),
                "capability": capability_id,
                "response": None,
                "error": call_resp["error"].get("message", "unknown adapter error"),
            }

        content = call_resp.get("result", {}).get("content", [])
        text = content[0].get("text", "") if content else ""
        # The adapter returns JSON-stringified content; parse for the caller.
        try:
            parsed = json.loads(text)
        except json.JSONDecodeError:
            parsed = text

        return {
            "ok": True,
            "adapter": mcp.get("id"),
            "capability": capability_id,
            "response": parsed,
            "error": None,
        }

    finally:
        try:
            proc.stdin.close()
        except Exception:
            pass
        try:
            proc.terminate()
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()


def main() -> int:
    """CLI for ad-hoc dispatch: ``python3 tools/mcp_dispatch.py <mcp-id> <capability>``."""
    import argparse
    sys.path.insert(0, str(REPO_ROOT / "tools"))
    from mcp_registry import load_registry  # noqa: E402

    ap = argparse.ArgumentParser()
    ap.add_argument("mcp_id")
    ap.add_argument("capability")
    ap.add_argument("--args", default="{}",
                    help="JSON-encoded arguments object")
    ap.add_argument("--timeout", type=float, default=DEFAULT_TIMEOUT)
    args = ap.parse_args()

    reg = load_registry()
    mcp = next((m for m in reg["mcps"] if m["id"] == args.mcp_id), None)
    if mcp is None:
        print(f"Unknown MCP: {args.mcp_id}", file=sys.stderr)
        return 1

    payload_args = json.loads(args.args)
    result = dispatch(mcp, args.capability, payload_args, timeout=args.timeout)
    print(json.dumps(result, indent=2))
    return 0 if result["ok"] else 2


if __name__ == "__main__":
    sys.exit(main())
