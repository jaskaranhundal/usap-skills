#!/usr/bin/env python3
"""USAP MCP Router (Phase 2).

Given a USAP 11-field output payload from a skill, looks up the matching
specialist MCP(s) from the registry and returns a routing decision.

Routing logic:

  1. Score every ENABLED MCP against the payload:
     +2 if the payload's intent_type appears in the MCP's routes_intent
     +1 for each cs-* agent in payload.next_agents that the MCP serves
     -inf if the MCP is disabled
     Ties are broken alphabetically by id so the decision is deterministic.

  2. If no candidate scores > 0, return status: "no_match".

  3. If the payload carries human_approval_required: true, return
     status: "approval_required" with an approval prompt the calling
     client can surface to the user. NO dispatch happens at this stage.

  4. If approval is not required, return status: "would_dispatch"
     with the selected MCP and the action the router would invoke.
     Phase 2 does NOT actually call the adapter — Phase 3 wires that.
     This keeps Phase 2 changes additive and safe to merge before any
     real specialist MCP exists.

Every routing decision is written to the audit log via
tools/mcp_audit.write_audit() so the trail is complete from day one.

Stdlib only.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "tools"))

from mcp_registry import load_registry  # noqa: E402
from mcp_audit import write_audit  # noqa: E402
from mcp_audit import audit_dir  # noqa: E402

# ─── Approval tokens ─────────────────────────────────────────────────
# route() issues a server-side, single-use token whenever it returns
# approval_required. dispatch_after_approval() dispatches only with that
# token, bound to the same MCP, capability and arguments, once, within the
# TTL. A free-text token was the gate's bypass (Codex review on PR #149,
# comment 3936208945); design review docs/design/2026-09-04-approval-token-and-audit-lock-dr.md.
import hashlib as _hashlib
import re as _re
import secrets as _secrets
import time as _time

APPROVAL_TTL_SECONDS = 3600
_TOKEN_RE = _re.compile(r"^[A-Za-z0-9_-]{16,64}$")


def _approvals_dir() -> Path:
    d = audit_dir() / "approvals"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _args_sha256(arguments: dict | None) -> str:
    canon = json.dumps(arguments or {}, sort_keys=True, separators=(",", ":"))
    return _hashlib.sha256(canon.encode()).hexdigest()


def _token_sha256(token: str | None) -> str | None:
    return _hashlib.sha256(token.encode()).hexdigest() if token else None


def issue_approval_token(mcp_id: str, capability_id: str | None, arguments: dict | None) -> str:
    token = _secrets.token_urlsafe(24)
    now = _time.time()
    rec = {"mcp": mcp_id, "capability": capability_id, "arguments_sha256": _args_sha256(arguments),
           "issued_epoch": now, "expires_epoch": now + APPROVAL_TTL_SECONDS}
    (_approvals_dir() / f"{token}.json").write_text(json.dumps(rec), encoding="utf-8")
    return token


def consume_approval_token(token: str | None, mcp_id: str, capability_id: str | None,
                           arguments: dict | None) -> tuple[bool, str]:
    """Validate and consume a token. Returns (ok, reason). Single use."""
    if not token or not isinstance(token, str) or not _TOKEN_RE.match(token):
        return False, "approval token missing or malformed"
    path = _approvals_dir() / f"{token}.json"
    if not path.is_file():
        return False, "approval token unknown or already used"
    try:
        rec = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return False, "approval token record unreadable"
    if _time.time() > float(rec.get("expires_epoch", 0)):
        return False, "approval token expired"
    if rec.get("mcp") != mcp_id:
        return False, "approval token was issued for a different MCP"
    if rec.get("capability") != capability_id:
        return False, "approval token was issued for a different capability"
    if rec.get("arguments_sha256") != _args_sha256(arguments):
        return False, "approval token was issued for different arguments"
    try:
        path.rename(path.with_suffix(".used"))  # consumed before dispatch: never twice
    except OSError:
        return False, "approval token unknown or already used"
    return True, ""

# Capability ↔ intent fallback map. If a payload's intent_type doesn't match
# any capability id directly, pick the highest-trust capability for the intent.
INTENT_CAPABILITY_HINTS = {
    "detect":   ["list_detections", "search", "list_findings", "list_events"],
    "respond":  ["isolate_host", "block_ip", "suspend_user", "post_message"],
    "analyze":  ["search", "list_findings", "get_pr_diff", "list_events"],
    "advise":   ["get_pr_diff", "list_repos", "list_policies"],
    "escalate": ["post_message", "open_issue"],
    "report":   ["post_message", "open_issue", "update_finding"],
    "block":    ["block_ip", "isolate_host", "suspend_user"],
}


# ─── Connector-agnostic logical-name resolution ─────────────────────
# cs-* agents declare logical capabilities (mcp:siem:search) instead of
# physical MCP tool names. The resolver maps a logical name to whichever
# physical MCP the operator has actually enabled — so the same agent works
# against Splunk, Elastic, or Sentinel with no edit. If nothing implements
# the logical name, the agent degrades gracefully (resolve returns None).

def _normalize_logical(name: str) -> str:
    """Normalise an agent-declared logical name to the registry key form.

    Accepts ``mcp:siem:search``, ``mcp.siem.search``, or ``siem.search`` —
    all normalise to ``siem.search``. Pass the LOGICAL portion only; strip
    any trailing tool-call-id from an evidence URI before calling.
    """
    n = (name or "").strip()
    for pref in ("mcp:", "mcp."):
        if n.startswith(pref):
            n = n[len(pref):]
            break
    return n.replace(":", ".")


def resolve_logical(name: str, registry: dict | None = None) -> str | None:
    """Resolve a logical capability name to a physical MCP tool name.

    Returns the first ``implementations`` entry (preferred-first) whose
    physical MCP is ``enabled: true`` in the registry AND advertises the
    capability, or ``None`` when the operator has connected no implementing
    MCP. Deterministic: same registry + same name → same result.
    """
    from mcp_registry import logical_names as _logical_names, _parse_physical
    reg = registry if registry is not None else load_registry()
    entry = _logical_names(reg).get(_normalize_logical(name))
    if not isinstance(entry, dict):
        return None
    by_id = {m["id"]: m for m in reg.get("mcps", []) if isinstance(m, dict)}
    for impl in entry.get("implementations") or []:
        if not isinstance(impl, str):
            continue
        server, tool = _parse_physical(impl)
        mcp = by_id.get(server)
        if mcp and mcp.get("enabled") and any(
            c.get("id") == tool for c in (mcp.get("capabilities") or [])
        ):
            return impl
    return None


def resolve_logical_full(name: str, registry: dict | None = None) -> dict | None:
    """Like :func:`resolve_logical` but returns full context.

    Returns ``{logical, physical, mcp_id, capability}`` or ``None``.
    """
    from mcp_registry import _parse_physical
    physical = resolve_logical(name, registry)
    if physical is None:
        return None
    server, tool = _parse_physical(physical)
    return {
        "logical": _normalize_logical(name),
        "physical": physical,
        "mcp_id": server,
        "capability": tool,
    }


def _score_mcp(mcp: dict, payload: dict) -> int:
    if not mcp.get("enabled", False):
        return -1
    score = 0
    intent = payload.get("intent_type")
    if intent and intent in mcp.get("routes_intent", []):
        score += 2
    for agent in payload.get("next_agents", []) or []:
        if agent in mcp.get("relevant_agents", []):
            score += 1
    return score


def _pick_capability(mcp: dict, payload: dict) -> dict | None:
    """Choose which capability of the MCP this payload would invoke."""
    intent = payload.get("intent_type", "")
    hints = INTENT_CAPABILITY_HINTS.get(intent, [])
    by_id = {c["id"]: c for c in mcp["capabilities"]}
    for hint in hints:
        if hint in by_id:
            return by_id[hint]
    # No hint matched — return the first non-mutating capability if any.
    for c in mcp["capabilities"]:
        if not c.get("mutating", False):
            return c
    # Fall back to the first capability.
    return mcp["capabilities"][0] if mcp["capabilities"] else None


def route(payload: dict, registry: dict | None = None) -> dict:
    """Route an 11-field payload to a downstream MCP candidate.

    Returns a dict with one of these `status` values:
      - "no_match"             — no enabled MCP scored > 0 for this payload
      - "approval_required"    — payload requests human approval; surface to user
      - "would_dispatch"       — Phase 2: this is the MCP+capability that
                                  WOULD be invoked. Phase 3 actually invokes.
    Every result is written to the audit log before return.
    """
    reg = registry or load_registry()
    mcps = reg.get("mcps", [])

    scored = sorted(
        ((m, _score_mcp(m, payload)) for m in mcps),
        key=lambda t: (-t[1], t[0].get("id", "")),
    )
    candidates = [(m, s) for m, s in scored if s > 0]

    if not candidates:
        result = {
            "status": "no_match",
            "reason": (
                "No enabled MCP matches this payload's intent_type "
                f"({payload.get('intent_type')!r}) or next_agents "
                f"({payload.get('next_agents')!r})."
            ),
            "considered": [m.get("id") for m in mcps],
        }
        write_audit({"event": "route", "payload": payload, "decision": result})
        return result

    chosen_mcp, _score = candidates[0]
    chosen_cap = _pick_capability(chosen_mcp, payload)

    approval_required = (
        bool(payload.get("human_approval_required", False))
        or (chosen_cap.get("approval_required", False) if chosen_cap else False)
    )

    if approval_required:
        result = {
            "status": "approval_required",
            "selected_mcp": chosen_mcp["id"],
            "selected_mcp_name": chosen_mcp["name"],
            "selected_capability": chosen_cap["id"] if chosen_cap else None,
            "mutating": chosen_cap.get("mutating", False) if chosen_cap else False,
            "approval_prompt": _build_approval_prompt(payload, chosen_mcp, chosen_cap),
            "alternatives": [m["id"] for m, _ in candidates[1:5]],
            "phase": 3,
            "phase_note": (
                "Caller must surface the approval prompt; on consent call "
                "dispatch_after_approval with this approval_token (single use, "
                f"valid {APPROVAL_TTL_SECONDS // 60} min, bound to this MCP, capability and arguments)."
            ),
        }
        token = issue_approval_token(chosen_mcp["id"], result["selected_capability"],
                                     payload.get("dispatch_args") or {})
        result["approval_token"] = token
        audit_decision = {k: v for k, v in result.items() if k != "approval_token"}
        audit_decision["approval_token_sha256"] = _token_sha256(token)
        write_audit({"event": "route", "payload": payload, "decision": audit_decision})
        return result

    # Phase 3: actually dispatch. The router decides → dispatch executes.
    from mcp_dispatch import dispatch, DispatchError  # noqa: E402
    dispatch_args = (payload.get("dispatch_args") or {}) if isinstance(payload, dict) else {}
    try:
        outcome = dispatch(chosen_mcp, chosen_cap["id"], dispatch_args)
    except DispatchError as exc:
        outcome = {
            "ok": False,
            "adapter": chosen_mcp["id"],
            "capability": chosen_cap["id"] if chosen_cap else None,
            "response": None,
            "error": str(exc),
        }

    result = {
        "status": "dispatched" if outcome["ok"] else "dispatch_failed",
        "selected_mcp": chosen_mcp["id"],
        "selected_mcp_name": chosen_mcp["name"],
        "selected_capability": chosen_cap["id"] if chosen_cap else None,
        "alternatives": [m["id"] for m, _ in candidates[1:5]],
        "phase": 3,
        "outcome": outcome,
    }
    write_audit({
        "event": "dispatch",
        "payload": payload,
        "decision": result,
    })
    return result


def dispatch_after_approval(
    mcp_id: str,
    capability_id: str,
    arguments: dict | None = None,
    approval_token: str | None = None,
    registry: dict | None = None,
) -> dict:
    """Dispatch a capability after the calling client has surfaced the
    approval prompt and received user consent.

    Phase 3 trust model: the client is trusted to actually show the prompt
    and capture the user's response. Phase 4 will tighten this with a
    signed approval token that USAP issues on the original route call and
    verifies on this call.

    The audit log records both the approval (event: "approval_granted")
    and the subsequent dispatch (event: "dispatch") so the chain is
    auditable end-to-end.
    """
    reg = registry or load_registry()
    mcp = next((m for m in reg["mcps"] if m["id"] == mcp_id), None)
    if mcp is None:
        result = {
            "status": "dispatch_failed",
            "error": f"Unknown MCP: {mcp_id}",
        }
        write_audit({"event": "approval_granted_dispatch_failed", "decision": result})
        return result
    if not mcp.get("enabled", False):
        result = {
            "status": "dispatch_failed",
            "error": f"MCP {mcp_id} is disabled in the registry.",
        }
        write_audit({"event": "approval_granted_dispatch_failed", "decision": result})
        return result

    ok, why = consume_approval_token(approval_token, mcp_id, capability_id, arguments or {})
    if not ok:
        result = {
            "status": "dispatch_failed",
            "selected_mcp": mcp_id,
            "selected_capability": capability_id,
            "error": f"approval token rejected: {why}",
        }
        write_audit({"event": "approval_rejected", "decision": result})
        return result

    write_audit({
        "event": "approval_granted",
        "decision": {
            "mcp": mcp_id,
            "capability": capability_id,
            "approval_token_sha256": _token_sha256(approval_token),
        },
    })

    from mcp_dispatch import dispatch, DispatchError  # noqa: E402
    try:
        outcome = dispatch(mcp, capability_id, arguments or {})
    except DispatchError as exc:
        outcome = {
            "ok": False,
            "adapter": mcp_id,
            "capability": capability_id,
            "response": None,
            "error": str(exc),
        }

    result = {
        "status": "dispatched" if outcome["ok"] else "dispatch_failed",
        "selected_mcp": mcp_id,
        "selected_mcp_name": mcp.get("name"),
        "selected_capability": capability_id,
        "phase": 3,
        "outcome": outcome,
    }
    write_audit({
        "event": "dispatch",
        "approval_token": approval_token,
        "decision": result,
    })
    return result


def _build_approval_prompt(payload: dict, mcp: dict, capability: dict | None) -> str:
    action = capability["id"] if capability else "(unknown action)"
    sev = payload.get("severity", "informational")
    rationale = payload.get("rationale", "")[:240]
    return (
        f"USAP wants to call {mcp['name']!r} → {action} "
        f"(severity={sev}, mutating={capability.get('mutating', False) if capability else False}).\n"
        f"Rationale: {rationale}\n"
        "Approve? Reject? Or rewrite the action."
    )


def main() -> int:
    """CLI: route a payload, or resolve a logical name."""
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("payload", nargs="?", help="Path to a JSON payload file (or - for stdin)")
    ap.add_argument("--resolve", metavar="LOGICAL",
                    help="Resolve a logical name (e.g. mcp:siem:search) to a "
                         "physical MCP tool against the current registry.")
    args = ap.parse_args()

    if args.resolve:
        full = resolve_logical_full(args.resolve)
        if full is None:
            print(json.dumps({
                "logical": _normalize_logical(args.resolve),
                "resolved": None,
                "note": "no enabled MCP implements this logical name",
            }, indent=2))
            return 0
        print(json.dumps({"resolved": full["physical"], **full}, indent=2))
        return 0

    if args.payload is None or args.payload == "-":
        data = json.loads(sys.stdin.read())
    else:
        data = json.loads(Path(args.payload).read_text())
    decision = route(data)
    print(json.dumps(decision, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())


def dispatch_unattended(
    mcp_id: str,
    capability_id: str,
    arguments: dict | None = None,
    registry: dict | None = None,
) -> dict:
    """Dispatch a capability with no human present.

    Only capabilities that are neither approval_required nor mutating in the
    registry may run this way; everything else is refused with
    dispatch_failed. Used by the scheduled runner instead of a synthetic
    approval token.
    """
    reg = registry or load_registry()
    mcp = next((m for m in reg["mcps"] if m["id"] == mcp_id), None)
    if mcp is None:
        result = {"status": "dispatch_failed", "error": f"Unknown MCP: {mcp_id}"}
        write_audit({"event": "unattended_dispatch_failed", "decision": result})
        return result
    if not mcp.get("enabled", False):
        result = {"status": "dispatch_failed", "error": f"MCP {mcp_id} is disabled in the registry."}
        write_audit({"event": "unattended_dispatch_failed", "decision": result})
        return result
    cap = next((c for c in mcp.get("capabilities", []) if c.get("id") == capability_id), None)
    if cap is None or cap.get("approval_required") or cap.get("mutating"):
        result = {
            "status": "dispatch_failed",
            "selected_mcp": mcp_id,
            "selected_capability": capability_id,
            "error": f"capability {mcp_id}/{capability_id} requires approval; unattended dispatch refused",
        }
        write_audit({"event": "unattended_dispatch_failed", "decision": result})
        return result

    from mcp_dispatch import dispatch, DispatchError  # noqa: E402
    try:
        outcome = dispatch(mcp, capability_id, arguments or {})
    except DispatchError as exc:
        outcome = {"ok": False, "adapter": mcp_id, "capability": capability_id, "response": None, "error": str(exc)}
    result = {
        "status": "dispatched" if outcome["ok"] else "dispatch_failed",
        "selected_mcp": mcp_id,
        "selected_capability": capability_id,
        "phase": 4,
        "outcome": outcome,
    }
    if not outcome["ok"]:
        result["error"] = outcome.get("error") or "adapter error"
    write_audit({"event": "unattended_dispatch", "decision": result})
    return result
