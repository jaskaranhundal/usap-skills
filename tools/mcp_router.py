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
            "phase": 2,
            "phase_note": (
                "Phase 2 returns the approval prompt only. Phase 3 will "
                "dispatch once the user approves."
            ),
        }
        write_audit({"event": "route", "payload": payload, "decision": result})
        return result

    result = {
        "status": "would_dispatch",
        "selected_mcp": chosen_mcp["id"],
        "selected_mcp_name": chosen_mcp["name"],
        "selected_capability": chosen_cap["id"] if chosen_cap else None,
        "alternatives": [m["id"] for m, _ in candidates[1:5]],
        "phase": 2,
        "phase_note": (
            "Phase 2 does not dispatch. Phase 3 will launch the adapter "
            f"({chosen_mcp.get('command')} {' '.join(chosen_mcp.get('args', []))}) "
            "and invoke the capability."
        ),
    }
    write_audit({"event": "route", "payload": payload, "decision": result})
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
    """CLI: route a payload from a file or stdin."""
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("payload", nargs="?", help="Path to a JSON payload file (or - for stdin)")
    args = ap.parse_args()
    if args.payload is None or args.payload == "-":
        data = json.loads(sys.stdin.read())
    else:
        data = json.loads(Path(args.payload).read_text())
    decision = route(data)
    print(json.dumps(decision, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
