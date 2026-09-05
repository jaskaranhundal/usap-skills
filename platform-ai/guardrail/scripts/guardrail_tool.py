#!/usr/bin/env python3
"""guardrail_tool.py

Enforces the USAP control-plane guardrail per the SKILL.md: approval gates, RBAC
approver authority, intent_type boundaries, separation of duties, and blast-radius
elevation. Returns a `guardrail_result` (cleared or the first blocking reason).
Validation is read-only. Emits the USAP 11-field payload.

  python3 guardrail_tool.py --input recommendation.json --output json
  python3 guardrail_tool.py --output json    # no input: informational, exit 0

Input (see tests/fixtures/guardrail-input.json):
{recommendation_id, mutating (bool), mutating_category, blast_radius
(single_resource|infrastructure|service_scoped|full_account),
approval{present, approver_role, ttl_expired}, invoker, approver}.

Exit codes: 0 cleared (or no-op read-only); 2 blocked. Stdlib only.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

SLUG = "guardrail"
HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parents[2]
# blast radius -> minimally sufficient approver roles (any of)
REQUIRED_APPROVERS = {
    "full_account": {"ciso", "security_director"},
    "service_scoped": {"security_director", "ciso"},
    "infrastructure": {"security_manager", "security_director", "ciso"},
    "single_resource": {"security_analyst", "security_manager", "security_director", "ciso"},
}
BLAST_RANK = {"single_resource": 1, "infrastructure": 2, "service_scoped": 3, "full_account": 4}


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _evaluate(t: dict) -> tuple:
    """Return (guardrail_result, severity, detail)."""
    if not t.get("mutating"):
        return "cleared", "informational", "read-only action; no approval required"
    if not t.get("mutating_category"):
        return "blocked_invalid_schema", "high", "mutating action is missing mutating_category"
    appr = t.get("approval") or {}
    if not appr.get("present"):
        return "blocked_missing_approval", "high", "mutating action has no approval record"
    if appr.get("ttl_expired"):
        return "blocked_approval_expired", "high", "approval TTL has expired"
    blast = str(t.get("blast_radius", "single_resource")).lower()
    role = str(appr.get("approver_role", "")).lower()
    allowed = REQUIRED_APPROVERS.get(blast, REQUIRED_APPROVERS["single_resource"])
    if role not in allowed:
        # distinguish elevation-required from plain unauthorized
        if role in ("security_analyst", "security_manager") and BLAST_RANK.get(blast, 1) >= 3:
            return "blocked_elevation_required", "high", f"blast radius '{blast}' requires elevation above '{role}'"
        return "blocked_unauthorized_approver", "high", f"approver role '{role or 'none'}' insufficient for blast radius '{blast}'"
    invoker = str(t.get("invoker", "")).lower()
    approver = str(t.get("approver", appr.get("approver", ""))).lower()
    if invoker and approver and invoker == approver:
        return "blocked_separation_of_duties", "high", "the same person invoked and approved the action"
    sev = "high" if BLAST_RANK.get(blast, 1) >= 3 else "medium"
    return "cleared", sev, f"all guardrail checks passed for blast radius '{blast}'"


def analyse(t: dict, input_path: Optional[str] = None) -> Dict[str, Any]:
    rel = None
    if input_path:
        try:
            rel = Path(input_path).resolve().relative_to(REPO_ROOT).as_posix()
        except ValueError:
            rel = None
    if not t or not t.get("recommendation_id"):
        return {"agent_slug": SLUG, "intent_type": "report", "action": "Supply a recommendation to evaluate; nothing was provided.",
                "rationale": "No recommendation supplied.", "confidence": 0.30, "severity": "informational", "key_findings": ["No recommendation supplied"],
                "evidence_references": [{"source": "local://platform-ai/guardrail/SKILL.md", "ref": "guardrail checks (not applied)"}],
                "next_agents": [], "human_approval_required": False, "timestamp_utc": _now(), "guardrail_result": None, "_exit": 0}
    result, severity, detail = _evaluate(t)
    blocked = result != "cleared"
    exit_code = 2 if blocked else 0
    rid = t.get("recommendation_id")
    action = (f"BLOCK {rid}: {result} — {detail}." if blocked else f"CLEARED {rid}: {detail}. tool-execution-broker may proceed.")
    key = [f"recommendation {rid}: guardrail_result={result}",
           f"mutating={bool(t.get('mutating'))}, blast_radius={t.get('blast_radius', 'n/a')}, approver={((t.get('approval') or {}).get('approver_role'))}",
           detail]
    evidence = [{"source": f"local://{rel}" if rel else "local://platform-ai/guardrail/SKILL.md", "ref": "recommendation and approval record"},
                {"source": "local://platform-ai/guardrail/SKILL.md", "ref": "blast-radius approval and violation tables"}]
    return {"agent_slug": SLUG, "intent_type": "block" if blocked else "report", "action": action,
            "rationale": ("The recommendation is checked in order against the SKILL.md guardrail rules: a mutating action needs a mutating_category, a present and unexpired approval, an "
                          "approver whose role meets the blast-radius requirement, and a different person as approver than invoker. The first failing check blocks; otherwise the action is "
                          "cleared. Validation is read-only."),
            "confidence": 0.95, "severity": severity, "key_findings": key, "evidence_references": evidence,
            "next_agents": ["tool-execution-broker"] if not blocked and t.get("mutating") else [], "human_approval_required": False, "timestamp_utc": _now(),
            "guardrail_result": result, "mitre_ttps": [], "affected_assets": [str(rid)], "_exit": exit_code}


def main() -> int:
    ap = argparse.ArgumentParser(description="USAP guardrail")
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
    print(json.dumps(p, indent=2) if args.output == "json" else f"guardrail: {p.get('guardrail_result')}")
    return code


if __name__ == "__main__":
    raise SystemExit(main())
