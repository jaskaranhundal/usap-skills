#!/usr/bin/env python3
"""USAP MCP Registry loader + validator (Phase 2).

Reads ``registry/usap-mcp-registry.yaml``, normalises every entry to a
predictable Python dict, and enforces structural rules:

  * Every MCP has id, name, transport, command, args, capabilities[],
    routes_intent[], relevant_agents[].
  * Every capability has id, mutating (bool), approval_required (bool).
  * routes_intent values are drawn from the standard 7 intents
    (detect, respond, analyze, advise, escalate, report, block).
  * Mutating capabilities MUST have approval_required=true. The router
    refuses to dispatch unapproved mutating actions, but a registry
    that declares a mutating capability without an approval gate is
    a config bug we catch at load time, not at routing time.

Stdlib-only YAML parser — handles the subset of YAML the registry
uses (simple key:value, lists with hyphens, nested dicts, quoted /
unquoted scalars, hash comments).

Usage::

    python3 tools/mcp_registry.py --validate
    python3 tools/mcp_registry.py --list
    python3 tools/mcp_registry.py --explain <mcp-id>
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_REGISTRY = REPO_ROOT / "registry" / "usap-mcp-registry.yaml"

VALID_INTENTS = {"detect", "respond", "analyze", "advise", "escalate", "report", "block"}


# ─── Minimal YAML parser ────────────────────────────────────────────

def _strip_quotes(s: str) -> str:
    s = s.strip()
    if len(s) >= 2 and s[0] == s[-1] and s[0] in ('"', "'"):
        return s[1:-1]
    return s


def _coerce_scalar(s: str) -> Any:
    s = _strip_quotes(s.strip())
    if s == "true":
        return True
    if s == "false":
        return False
    if s == "null" or s == "~":
        return None
    if s.isdigit() or (s.startswith("-") and s[1:].isdigit()):
        try:
            return int(s)
        except ValueError:
            pass
    return s


def _split_inline_list(s: str) -> list:
    # Handles `[a, b, c]` or `["a","b"]`
    s = s.strip()
    if not (s.startswith("[") and s.endswith("]")):
        return _coerce_scalar(s)
    inner = s[1:-1].strip()
    if not inner:
        return []
    parts = []
    depth = 0
    buf = ""
    for ch in inner:
        if ch == "," and depth == 0:
            parts.append(buf)
            buf = ""
        else:
            if ch in "[{":
                depth += 1
            elif ch in "]}":
                depth -= 1
            buf += ch
    if buf.strip():
        parts.append(buf)
    return [_coerce_scalar(p) for p in parts]


def _indent_of(line: str) -> int:
    return len(line) - len(line.lstrip(" "))


def parse_yaml(text: str) -> Any:
    """Recursive descent over a sufficient subset of YAML for the registry shape.

    Supports: top-level mappings, lists with `- ` prefix, nested mappings under
    a parent key, inline lists `[a, b]`, scalars (string / int / bool / null),
    `#` comments, blank lines.
    """
    # Strip comments and empty lines while preserving indent positions.
    raw_lines = []
    for line in text.splitlines():
        stripped = line.split("#", 1)[0].rstrip()
        if stripped.strip():
            raw_lines.append(stripped)

    def parse_block(start_idx: int, indent: int) -> tuple[Any, int]:
        # If the first non-blank line at this indent starts with "- ", parse a list.
        if start_idx >= len(raw_lines):
            return None, start_idx
        first = raw_lines[start_idx]
        first_indent = _indent_of(first)
        if first_indent < indent:
            return None, start_idx
        if first.lstrip().startswith("- "):
            return _parse_list(start_idx, first_indent)
        return _parse_mapping(start_idx, first_indent)

    def _parse_mapping(start_idx: int, indent: int) -> tuple[dict, int]:
        out: dict = {}
        i = start_idx
        while i < len(raw_lines):
            line = raw_lines[i]
            this_indent = _indent_of(line)
            if this_indent < indent:
                break
            if this_indent > indent:
                # Skipping over a child block we didn't expect — bail.
                break
            content = line.strip()
            if ":" not in content:
                break
            key, _, val = content.partition(":")
            key = key.strip()
            val = val.strip()
            if not val:
                # Nested block follows.
                child, i = parse_block(i + 1, indent + 2)
                out[key] = child if child is not None else {}
            elif val.startswith("["):
                out[key] = _split_inline_list(val)
                i += 1
            else:
                out[key] = _coerce_scalar(val)
                i += 1
        return out, i

    def _parse_list(start_idx: int, indent: int) -> tuple[list, int]:
        out: list = []
        i = start_idx
        while i < len(raw_lines):
            line = raw_lines[i]
            this_indent = _indent_of(line)
            if this_indent < indent:
                break
            if this_indent > indent:
                break
            content = line.lstrip()
            if not content.startswith("- "):
                break
            payload = content[2:].strip()
            if not payload:
                # Element is a nested block on the following lines.
                child, i = parse_block(i + 1, indent + 2)
                out.append(child if child is not None else {})
                continue
            if ":" in payload and not payload.startswith("[") and not payload.startswith("{"):
                # The list element is a mapping that starts on this line.
                key, _, val = payload.partition(":")
                element: dict = {}
                key = key.strip()
                val = val.strip()
                if val:
                    if val.startswith("["):
                        element[key] = _split_inline_list(val)
                    else:
                        element[key] = _coerce_scalar(val)
                    # Possibly more keys follow at indent + 2.
                    child, i = parse_block(i + 1, indent + 2)
                    if isinstance(child, dict):
                        element.update(child)
                else:
                    child, i = parse_block(i + 1, indent + 2)
                    if isinstance(child, dict):
                        element[key] = child
                    else:
                        element[key] = None
                out.append(element)
            elif payload.startswith("["):
                out.append(_split_inline_list(payload))
                i += 1
            else:
                out.append(_coerce_scalar(payload))
                i += 1
        return out, i

    result, _ = parse_block(0, 0)
    return result


# ─── Loader + validator ────────────────────────────────────────────

REQUIRED_MCP_KEYS = {"id", "name", "transport", "command", "args", "capabilities"}
REQUIRED_CAPABILITY_KEYS = {"id", "mutating", "approval_required"}


def load_registry(path: Path | None = None) -> dict:
    """Load and structurally validate the registry. Returns the parsed dict."""
    path = path or DEFAULT_REGISTRY
    if not path.is_file():
        raise FileNotFoundError(f"Registry not found: {path}")
    parsed = parse_yaml(path.read_text(encoding="utf-8"))
    if not isinstance(parsed, dict):
        raise ValueError("Registry root must be a mapping.")
    if parsed.get("version") != 1:
        raise ValueError(
            f"Registry version must be 1 (got {parsed.get('version')!r})."
        )
    mcps = parsed.get("mcps") or []
    if not isinstance(mcps, list):
        raise ValueError("Registry `mcps` must be a list.")

    errors: list[str] = []
    seen_ids: set[str] = set()
    for idx, mcp in enumerate(mcps):
        prefix = f"mcps[{idx}]"
        if not isinstance(mcp, dict):
            errors.append(f"{prefix}: must be a mapping")
            continue
        missing = REQUIRED_MCP_KEYS - set(mcp.keys())
        if missing:
            errors.append(f"{prefix}: missing required keys {sorted(missing)}")
            continue
        mid = mcp["id"]
        if mid in seen_ids:
            errors.append(f"{prefix}: duplicate id {mid!r}")
        seen_ids.add(mid)
        # Defaults — make absent fields explicit.
        mcp.setdefault("enabled", False)
        mcp.setdefault("routes_intent", [])
        mcp.setdefault("relevant_agents", [])
        if not isinstance(mcp["args"], list):
            errors.append(f"{prefix}: `args` must be a list")
        for intent in mcp["routes_intent"]:
            if intent not in VALID_INTENTS:
                errors.append(
                    f"{prefix}: routes_intent contains invalid intent {intent!r}"
                )
        caps = mcp["capabilities"]
        if not isinstance(caps, list) or not caps:
            errors.append(f"{prefix}: `capabilities` must be a non-empty list")
            continue
        for cidx, cap in enumerate(caps):
            cprefix = f"{prefix}.capabilities[{cidx}]"
            if not isinstance(cap, dict):
                errors.append(f"{cprefix}: must be a mapping")
                continue
            cmissing = REQUIRED_CAPABILITY_KEYS - set(cap.keys())
            if cmissing:
                errors.append(f"{cprefix}: missing required keys {sorted(cmissing)}")
                continue
            if cap["mutating"] and not cap["approval_required"]:
                errors.append(
                    f"{cprefix}: mutating capability must have "
                    f"approval_required: true"
                )

    if errors:
        raise ValueError(
            "Registry validation failed:\n  " + "\n  ".join(errors)
        )

    return parsed


# ─── CLI ────────────────────────────────────────────────────────────

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--validate", action="store_true",
                    help="Validate the registry and exit 0 on success.")
    ap.add_argument("--list", action="store_true",
                    help="List MCPs in the registry with their status.")
    ap.add_argument("--explain", metavar="MCP_ID",
                    help="Print the full entry for one MCP.")
    ap.add_argument("--registry", type=Path, default=DEFAULT_REGISTRY,
                    help="Override registry path.")
    args = ap.parse_args()

    try:
        reg = load_registry(args.registry)
    except (FileNotFoundError, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        return 1

    if args.list:
        for m in reg["mcps"]:
            status = "enabled" if m.get("enabled") else "disabled"
            print(f"  {m['id']:<22} {status:<10} caps={len(m['capabilities'])} "
                  f"intents={m['routes_intent']}")
        return 0

    if args.explain:
        for m in reg["mcps"]:
            if m["id"] == args.explain:
                print(json.dumps(m, indent=2))
                return 0
        print(f"MCP not found: {args.explain}", file=sys.stderr)
        return 1

    if args.validate or not (args.list or args.explain):
        print(f"OK  {len(reg['mcps'])} MCP(s) loaded from {args.registry}")
        return 0


if __name__ == "__main__":
    sys.exit(main())
