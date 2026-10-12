#!/usr/bin/env python3
"""knowledge-management_tool.py

Answers "have we seen this before, what did we decide, why" per the SKILL.md
precedent-search and consistency-enforcement logic: matches a query against a
supplied knowledge base of prior decisions, risk acceptances and runbooks, and
flags conflicts (a new remediation against an in-effect risk acceptance, a
known false-positive pattern). Read-only. Emits the USAP 11-field payload.

  python3 knowledge-management_tool.py --input query.json --output json
  python3 knowledge-management_tool.py --output json    # no input: informational, exit 0

Input (see tests/fixtures/knowledge-management-input.json): query{event_type,
severity, affected_resource, proposed_action}, knowledge_base[]: {id, kind
(decision|risk_acceptance|false_positive|runbook|lesson), event_type,
affected_resource, decision, status (active|expired), expiry_utc, rationale}.

Exit codes: 0 no conflict; 1 a precedent conflict needs review. Stdlib only.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

SLUG = "knowledge-management"
HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parents[2]


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _parse(ts: Optional[str]) -> Optional[datetime]:
    try:
        return datetime.fromisoformat(str(ts).replace("Z", "+00:00")).astimezone(timezone.utc)
    except (ValueError, TypeError):
        return None


def _relevance(q: dict, k: dict) -> int:
    score = 0
    if q.get("event_type") and str(k.get("event_type", "")).lower() == str(q["event_type"]).lower():
        score += 2
    if q.get("affected_resource") and str(k.get("affected_resource", "")).lower() == str(q["affected_resource"]).lower():
        score += 2
    return score


def analyse(t: dict, input_path: Optional[str] = None) -> Dict[str, Any]:
    rel = None
    if input_path:
        try:
            rel = Path(input_path).resolve().relative_to(REPO_ROOT).as_posix()
        except ValueError:
            rel = None
    q = t.get("query") or {}
    kb = [k for k in (t.get("knowledge_base") or []) if isinstance(k, dict)]
    if not t or not q:
        return {"agent_slug": SLUG, "intent_type": "report", "action": "Supply a query and knowledge base; nothing was provided.",
                "rationale": "No query supplied; no precedent search.", "confidence": 0.30, "severity": "informational",
                "key_findings": ["No query supplied"], "evidence_references": [{"source": "local://governance/knowledge-management/SKILL.md", "ref": "precedent search (not applied)"}],
                "next_agents": [], "human_approval_required": False, "timestamp_utc": _now(), "precedents": [], "_exit": 0}
    now = datetime.now(timezone.utc)
    matches = sorted([(k, _relevance(q, k)) for k in kb], key=lambda x: -x[1])
    relevant = [k for k, s in matches if s >= 2]
    conflicts: List[str] = []
    for k in relevant:
        kind = str(k.get("kind", "")).lower()
        active = str(k.get("status", "active")).lower() == "active" and (not _parse(k.get("expiry_utc")) or _parse(k.get("expiry_utc")) > now)
        pa = str(q.get("proposed_action", "")).lower()
        if kind == "risk_acceptance" and active and "remediat" in pa:
            conflicts.append(f"{k.get('id')}: an active risk acceptance covers this ({k.get('rationale', '')[:80]}); a new remediation conflicts — confirm before proceeding")
        if kind == "false_positive" and active and pa and "verify" not in pa:
            conflicts.append(f"{k.get('id')}: this matches a known false-positive pattern; re-investigation may be wasted effort")
    runbooks = [k for k in relevant if str(k.get("kind", "")).lower() == "runbook"]
    severity = "medium" if conflicts else "informational"
    exit_code = 1 if conflicts else 0
    action = ("Precedent conflict: " + "; ".join(conflicts[:2]) + ".") if conflicts else \
             (f"{len(relevant)} relevant precedent(s) found; " + (f"apply runbook {runbooks[0].get('id')}." if runbooks else "no conflict with the proposed action.")) if relevant else \
             "No precedent found; this appears to be a new situation — record the decision for future reuse."
    key = [f"Query {q.get('event_type', '?')} on {q.get('affected_resource', '?')}: {len(relevant)} relevant precedent(s), {len(conflicts)} conflict(s)"]
    key += [f"{k.get('kind')} {k.get('id')}: {str(k.get('decision', k.get('rationale', '')))[:100]} (status {k.get('status', 'active')})" for k in relevant[:5]]
    key += [f"CONFLICT {c}" for c in conflicts]
    if not relevant:
        key.append("No prior decision on this event type and resource — capture this one as a decision record")
    evidence = [{"source": f"local://{rel}" if rel else "local://governance/knowledge-management/SKILL.md", "ref": "query and knowledge base"},
                {"source": "local://governance/knowledge-management/SKILL.md", "ref": "precedent search and consistency enforcement logic"}]
    return {"agent_slug": SLUG, "intent_type": "report", "action": action,
            "rationale": ("Precedents matched on event type and affected resource; a precedent is in effect only if active and unexpired. A new remediation against an active risk "
                          "acceptance, or a query matching a known false-positive pattern, is flagged as a conflict for human confirmation. Read-only."),
            "confidence": 0.8 if relevant else 0.5, "severity": severity, "key_findings": key, "evidence_references": evidence,
            "next_agents": ["findings-tracker"] if conflicts else [], "human_approval_required": False, "timestamp_utc": _now(),
            "precedents": [{"id": k.get("id"), "kind": k.get("kind"), "status": k.get("status", "active")} for k in relevant], "conflicts": conflicts,
            "mitre_ttps": [], "affected_assets": [q.get("affected_resource")] if q.get("affected_resource") else [], "_exit": exit_code}


def main() -> int:
    ap = argparse.ArgumentParser(description="USAP knowledge-management")
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
    print(json.dumps(p, indent=2) if args.output == "json" else f"knowledge-management: severity={p['severity']}")
    return code


if __name__ == "__main__":
    raise SystemExit(main())
