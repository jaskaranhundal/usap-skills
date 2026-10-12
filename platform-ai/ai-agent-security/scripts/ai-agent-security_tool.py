#!/usr/bin/env python3
"""ai-agent-security_tool.py

Detects prompt injection and misuse against agentic workflows and maps the
recommended response to the SKILL.md action table (read-only detections vs.
mutating remediations that require approval). Emits the USAP 11-field payload.

  python3 ai-agent-security_tool.py --input session.json --output json
  python3 ai-agent-security_tool.py --output json    # no input: informational, exit 0

Input (see tests/fixtures/ai-agent-security-input.json):
{agent, indicators[] (prompt_injection|tool_misuse|data_exfil_prompt|
jailbreak|hallucination|unauthorized_provider)}.

Exit codes: 0 clean; 1 high; 2 critical. Stdlib only.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

SLUG = "ai-agent-security"
HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parents[2]
# indicator -> (severity, recommended remediation, mutating?)
INDICATOR = {
    "prompt_injection": ("critical", "Block the agent session", True),
    "jailbreak": ("critical", "Block the agent session", True),
    "data_exfil_prompt": ("critical", "Quarantine the retrieved document source", True),
    "tool_misuse": ("high", "Revoke agent tool permissions", True),
    "unauthorized_provider": ("high", "Suspend the model endpoint", True),
    "hallucination": ("medium", "Flag the session for human review", False),
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
    raw = t.get("indicators") or []
    if not t or not raw:
        return {"agent_slug": SLUG, "intent_type": "detect", "action": "Supply agent indicators; nothing was provided.",
                "rationale": "No indicators supplied.", "confidence": 0.30, "severity": "informational", "key_findings": ["No indicators supplied"],
                "evidence_references": [{"source": "local://platform-ai/ai-agent-security/SKILL.md", "ref": "action table (not applied)"}],
                "next_agents": [], "human_approval_required": False, "timestamp_utc": _now(), "findings": [], "_exit": 0}
    findings: List[dict] = []
    for i in [str(x).lower() for x in raw]:
        sev, rem, mut = INDICATOR.get(i, ("medium", "Flag for human review", False))
        findings.append({"indicator": i, "severity": sev, "remediation": rem, "mutating": mut})
    findings.sort(key=lambda x: -SEV_RANK[x["severity"]])
    counts = {k: sum(1 for x in findings if x["severity"] == k) for k in SEV_RANK}
    mutating = [x for x in findings if x["mutating"]]
    severity = findings[0]["severity"] if findings else "informational"
    exit_code = 2 if counts["critical"] else 1 if counts["high"] else 0
    agent = t.get("agent", "the agent")
    action = (f"{counts['critical']} critical misuse indicator(s) on {agent}; recommend: " + "; ".join(sorted({x['remediation'] for x in findings if x['severity']=='critical'}))[:150] + " (mutating — requires approval)." if counts["critical"] else
              f"{counts['high']} high misuse indicator(s) on {agent}; recommend mutating remediation with approval." if counts["high"] else
              f"No high misuse indicator on {agent}.")
    key = [f"{agent}: {len(findings)} indicator(s) ({counts['critical']} critical, {counts['high']} high); {len(mutating)} mutating remediation(s) recommended"]
    key += [f"{x['severity']} {x['indicator']} -> {x['remediation']}" + (" [approval]" if x['mutating'] else "") for x in findings[:6]]
    evidence = [{"source": f"local://{rel}" if rel else "local://platform-ai/ai-agent-security/SKILL.md", "ref": "agent session indicators"},
                {"source": "local://platform-ai/ai-agent-security/SKILL.md", "ref": "action classification table"}]
    return {"agent_slug": SLUG, "intent_type": "respond" if mutating else "detect", "action": action,
            "rationale": ("Detection of injection, misuse and hallucination is read-only; the recommended remediation is mapped to the SKILL.md action table — blocking a session, revoking "
                          "tool permissions, quarantining a source or suspending an endpoint are all mutating actions that require human approval before execution."),
            "confidence": 0.85, "severity": severity, "key_findings": key, "evidence_references": evidence,
            "next_agents": ["agent-integrity-monitor", "guardrail"] if mutating else [], "human_approval_required": bool(mutating), "timestamp_utc": _now(),
            "findings": findings, "mitre_ttps": [], "affected_assets": [str(agent)], "_exit": exit_code}


def main() -> int:
    ap = argparse.ArgumentParser(description="USAP ai-agent-security")
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
    print(json.dumps(p, indent=2) if args.output == "json" else f"ai-agent-security: severity={p['severity']}")
    return code


if __name__ == "__main__":
    raise SystemExit(main())
