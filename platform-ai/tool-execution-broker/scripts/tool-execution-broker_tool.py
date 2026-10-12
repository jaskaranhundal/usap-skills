#!/usr/bin/env python3
"""tool-execution-broker_tool.py

Validates a mutating tool call against the SKILL.md pre-execution checklist
(approval signature, TTL, approver role, scope, production restriction, duplicate
execution, guardrail cleared, connector availability). Returns authorize or the
first blocking reason. Validation is read-only — this tool never executes the
action. Emits the USAP 11-field payload.

  python3 tool-execution-broker_tool.py --input request.json --output json
  python3 tool-execution-broker_tool.py --output json    # no input: informational, exit 0

Input (see tests/fixtures/tool-execution-broker-input.json):
{recommendation_id, checks{approval_signature_present, approval_not_expired,
approver_role_authorized, action_within_scope, target_not_production_restricted,
no_duplicate_execution, guardrail_cleared, connector_available}} (booleans).

Exit codes: 0 authorized; 2 blocked. Stdlib only.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

SLUG = "tool-execution-broker"
HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parents[2]
# ordered checks -> blocked reason on failure
CHECKS = [
    ("approval_signature_present", "blocked: missing_approval"),
    ("approval_not_expired", "blocked: approval_expired"),
    ("approver_role_authorized", "blocked: unauthorized_approver"),
    ("action_within_scope", "blocked: out_of_scope"),
    ("target_not_production_restricted", "blocked: production_restriction"),
    ("no_duplicate_execution", "blocked: duplicate_execution"),
    ("guardrail_cleared", "blocked: guardrail_not_cleared"),
    ("connector_available", "blocked: connector_unavailable"),
]


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def analyse(t: dict, input_path: Optional[str] = None) -> Dict[str, Any]:
    rel = None
    if input_path:
        try:
            rel = Path(input_path).resolve().relative_to(REPO_ROOT).as_posix()
        except ValueError:
            rel = None
    if not t or not t.get("recommendation_id"):
        return {"agent_slug": SLUG, "intent_type": "report", "action": "Supply a tool-call request; nothing was provided.",
                "rationale": "No request supplied.", "confidence": 0.30, "severity": "informational", "key_findings": ["No request supplied"],
                "evidence_references": [{"source": "local://platform-ai/tool-execution-broker/SKILL.md", "ref": "pre-execution checklist (not applied)"}],
                "next_agents": [], "human_approval_required": False, "timestamp_utc": _now(), "broker_result": None, "_exit": 0}
    checks = t.get("checks") or {}
    rid = t.get("recommendation_id")
    blocked_reason = None
    failed = []
    for name, reason in CHECKS:
        if not checks.get(name):
            failed.append(name)
            if blocked_reason is None:
                blocked_reason = reason
    authorized = blocked_reason is None
    result = "authorized" if authorized else blocked_reason
    severity = "informational" if authorized else "high"
    exit_code = 0 if authorized else 2
    action = (f"AUTHORIZE {rid}: all pre-execution checks passed; the connector may execute the approved action." if authorized else
              f"REJECT {rid}: {result} (failed checks: {', '.join(failed)}). Execution is not permitted.")
    key = [f"recommendation {rid}: broker_result={result}",
           f"{len(CHECKS)-len(failed)}/{len(CHECKS)} checks passed"]
    if failed:
        key.append("failed: " + ", ".join(failed))
    evidence = [{"source": f"local://{rel}" if rel else "local://platform-ai/tool-execution-broker/SKILL.md", "ref": "tool-call request and checks"},
                {"source": "local://platform-ai/tool-execution-broker/SKILL.md", "ref": "pre-execution authorization checklist"}]
    return {"agent_slug": SLUG, "intent_type": "block" if not authorized else "report", "action": action,
            "rationale": ("The request is validated against the SKILL.md checklist in order — a present and unexpired signed approval, an authorized approver, action in scope, no production "
                          "restriction, no duplicate execution, a cleared guardrail, and a reachable connector. The first failing check rejects the call. Validation is read-only; this tool "
                          "never executes the action itself."),
            "confidence": 0.95, "severity": severity, "key_findings": key, "evidence_references": evidence,
            "next_agents": [], "human_approval_required": False, "timestamp_utc": _now(),
            "broker_result": result, "mitre_ttps": [], "affected_assets": [str(rid)], "_exit": exit_code}


def main() -> int:
    ap = argparse.ArgumentParser(description="USAP tool-execution-broker")
    ap.add_argument("--input"); ap.add_argument("--output", choices=["json", "text"], default="text")
    args = ap.parse_args()
    if args.input:
        try:
            t = json.loads(Path(args.input).read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            print(f"error: {exc}", file=sys.stderr); return 2
    else:
        raw = "" if sys.stdin.isatty() else sys.stdin.read()
        t = json.loads(raw) if raw.strip() else {}
    p = analyse(t, args.input); code = p.pop("_exit", 0)
    print(json.dumps(p, indent=2) if args.output == "json" else f"tool-execution-broker: {p.get('broker_result')}")
    return code


if __name__ == "__main__":
    raise SystemExit(main())
