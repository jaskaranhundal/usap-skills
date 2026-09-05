#!/usr/bin/env python3
"""agent-integrity-monitor_tool.py

Classifies AI-agent integrity violations against the SKILL.md violation table
(prompt injection, execution attempt, approval bypass, evidence tampering, etc.).
ALWAYS read-only — monitoring never mutates. Emits the USAP 11-field payload.

  python3 agent-integrity-monitor_tool.py --input session.json --output json
  python3 agent-integrity-monitor_tool.py --output json    # no input: informational, exit 0

Input (see tests/fixtures/agent-integrity-monitor-input.json):
{agent, session_id, violations[] (keys from the table, or {type, detail})}.

Exit codes: 0 clean; 1 high; 2 critical. Stdlib only.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

SLUG = "agent-integrity-monitor"
HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parents[2]
VIOLATION = {
    "execution_attempt": "critical",
    "approval_bypass": "high",
    "scope_creep": "high",
    "credential_access_attempt": "critical",
    "intent_type_mismatch": "high",
    "ttl_overrun": "medium",
    "schema_violation": "medium",
    "cascading_without_orchestrator": "high",
    "evidence_tampering_attempt": "critical",
    "provider_abuse": "high",
    "prompt_injection_detected": "critical",
}
SEV_RANK = {"critical": 4, "high": 3, "medium": 2, "low": 1, "informational": 0}


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def analyse(t: dict, input_path: Optional[str] = None) -> Dict[str, Any]:
    rel = None
    if input_path:
        try:
            rel = Path(input_path).resolve().relative_to(REPO_ROOT).as_posix()
        except ValueError:
            rel = None
    raw = t.get("violations") or []
    if not t or not raw:
        return {"agent_slug": SLUG, "intent_type": "detect", "action": "Supply a monitored session; nothing was provided.",
                "rationale": "No session supplied.", "confidence": 0.30, "severity": "informational", "key_findings": ["No session supplied"],
                "evidence_references": [{"source": "local://platform-ai/agent-integrity-monitor/SKILL.md", "ref": "violation table (not applied)"}],
                "next_agents": [], "human_approval_required": False, "timestamp_utc": _now(), "violations": [], "_exit": 0}
    violations: List[dict] = []
    for v in raw:
        vt = v if isinstance(v, str) else str(v.get("type", ""))
        detail = "" if isinstance(v, str) else v.get("detail", "")
        sev = VIOLATION.get(vt, "medium")
        violations.append({"type": vt, "severity": sev, "detail": detail})
    violations.sort(key=lambda x: -SEV_RANK[x["severity"]])
    counts = {k: sum(1 for x in violations if x["severity"] == k) for k in SEV_RANK}
    severity = violations[0]["severity"] if violations else "informational"
    exit_code = 2 if counts["critical"] else 1 if counts["high"] else 0
    agent = t.get("agent", "the agent")
    sid = t.get("session_id", "n/a")
    action = (f"Halt and quarantine {agent} session {sid}: {counts['critical']} critical integrity violation(s) — " + ", ".join(sorted({x['type'] for x in violations if x['severity']=='critical'}))[:150] + ". Escalate to the orchestrator." if counts["critical"] else
              f"{counts['high']} high integrity violation(s) on {agent}; raise for review." if counts["high"] else
              f"No high integrity violation on {agent} session {sid}.")
    key = [f"{agent} session {sid}: {len(violations)} violation(s) ({counts['critical']} critical, {counts['high']} high)"]
    key += [f"{x['severity']} {x['type']}" + (f": {x['detail']}" if x['detail'] else "") for x in violations[:6]]
    evidence = [{"source": f"local://{rel}" if rel else "local://platform-ai/agent-integrity-monitor/SKILL.md", "ref": "monitored session"},
                {"source": "local://platform-ai/agent-integrity-monitor/SKILL.md", "ref": "integrity violation table"}]
    return {"agent_slug": SLUG, "intent_type": "detect", "action": action,
            "rationale": ("Each violation is scored against the SKILL.md table: an execution attempt, credential-access attempt, evidence-tampering attempt or detected prompt injection is "
                          "critical because it means the agent has left its read-only, approval-gated envelope. Monitoring is always read-only; halting a session is a downstream gated action."),
            "confidence": 0.88, "severity": severity, "key_findings": key, "evidence_references": evidence,
            "next_agents": ["orchestrator"] if counts["critical"] else (["guardrail"] if violations else []),
            "human_approval_required": False, "timestamp_utc": _now(),
            "violations": violations, "mitre_ttps": [], "affected_assets": [str(agent)], "_exit": exit_code}


def main() -> int:
    ap = argparse.ArgumentParser(description="USAP agent-integrity-monitor")
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
    print(json.dumps(p, indent=2) if args.output == "json" else f"agent-integrity-monitor: severity={p['severity']}")
    return code


if __name__ == "__main__":
    raise SystemExit(main())
