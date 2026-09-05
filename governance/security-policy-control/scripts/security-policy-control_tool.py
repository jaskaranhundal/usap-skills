#!/usr/bin/env python3
"""security-policy-control_tool.py

Assesses a policy set and its control tests per the SKILL.md: policy-hierarchy
completeness, per-policy implementability (owner, verification, review currency),
and control-test pass rate mapped to CIS Controls v8. Read-only assessment;
policy deployment would be a gated policy_change. Emits the USAP 11-field payload.

  python3 security-policy-control_tool.py --input policies.json --output json
  python3 security-policy-control_tool.py --output json    # no input: informational, exit 0

Input (see tests/fixtures/security-policy-control-input.json): as_of_utc,
policies[]: {name, tier (1|2|3|4), owner, verification, last_reviewed_utc,
status (active|draft|expired)}, control_tests[]: {control (CIS n), result
(pass|fail), policy}.

Exit codes: 0 healthy; 1 gaps (unowned/unverified/failed control); 2 a Tier 1
policy missing or expired, or a failed CIS control with no compensating note.
Stdlib only.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

SLUG = "security-policy-control"
HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parents[2]
REVIEW_MAX_DAYS = 365


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _parse(ts: Optional[str]) -> Optional[datetime]:
    try:
        return datetime.fromisoformat(str(ts).replace("Z", "+00:00")).astimezone(timezone.utc)
    except (ValueError, TypeError):
        return None


def analyse(t: dict, input_path: Optional[str] = None) -> Dict[str, Any]:
    rel = None
    if input_path:
        try:
            rel = Path(input_path).resolve().relative_to(REPO_ROOT).as_posix()
        except ValueError:
            rel = None
    policies = [p for p in (t.get("policies") or []) if isinstance(p, dict)]
    tests = [c for c in (t.get("control_tests") or []) if isinstance(c, dict)]
    if not t or (not policies and not tests):
        return {"agent_slug": SLUG, "intent_type": "report", "action": "Supply policies and control tests; nothing was provided.",
                "rationale": "No policy set supplied; no assessment.", "confidence": 0.30, "severity": "informational",
                "key_findings": ["No policies or control tests supplied"], "evidence_references": [{"source": "local://governance/security-policy-control/SKILL.md", "ref": "policy hierarchy (not applied)"}],
                "next_agents": [], "human_approval_required": False, "timestamp_utc": _now(), "assessment": {}, "_exit": 0}
    as_of = _parse(t.get("as_of_utc")) or datetime.now(timezone.utc)
    gaps: List[dict] = []
    tier1_problem = False
    for p in policies:
        name = p.get("name", "?"); tier = int(p.get("tier") or 4); status = str(p.get("status", "active")).lower()
        reviewed = _parse(p.get("last_reviewed_utc"))
        stale = reviewed is None or (as_of - reviewed) > timedelta(days=REVIEW_MAX_DAYS)
        issues = []
        if not p.get("owner"):
            issues.append("no operational owner")
        if not p.get("verification"):
            issues.append("no verification mechanism")
        if stale:
            issues.append("review older than 12 months" if reviewed else "never reviewed")
        if status in ("draft", "expired"):
            issues.append(f"status {status}")
        if issues:
            sev = "critical" if tier == 1 and status in ("draft", "expired") else "high" if tier <= 2 else "medium"
            if tier == 1 and status in ("draft", "expired"):
                tier1_problem = True
            gaps.append({"policy": name, "tier": tier, "severity": sev, "issues": issues})
    failed = [c for c in tests if str(c.get("result", "")).lower() == "fail"]
    fail_uncompensated = [c for c in failed if not c.get("compensating_control")]
    passed = [c for c in tests if str(c.get("result", "")).lower() == "pass"]
    coverage = round(len(passed) / len(tests) * 100) if tests else 0
    gaps.sort(key=lambda g: {"critical": 0, "high": 1, "medium": 2}.get(g["severity"], 3))

    severity = "critical" if (tier1_problem or fail_uncompensated) else "high" if (gaps or failed) else "low" if (policies or tests) else "informational"
    exit_code = 2 if (tier1_problem or fail_uncompensated) else 1 if (gaps or failed) else 0
    action = ((f"{len(gaps)} policy gap(s) and {len(failed)} failed control(s); control coverage {coverage}%. "
               + (f"Tier 1 policy problem: {', '.join(g['policy'] for g in gaps if g['tier']==1)}. " if tier1_problem else "")
               + "Assign owners, add verification, and re-test failed controls.") if (gaps or failed) else
              f"Policy set healthy; control coverage {coverage}%.")
    key = [f"{len(policies)} policy(ies), {len(tests)} control test(s): coverage {coverage}%, {len(gaps)} policy gap(s), {len(failed)} failed control(s)"]
    key += [f"{g['severity'].upper()} Tier {g['tier']} {g['policy']}: {', '.join(g['issues'])}" for g in gaps[:5]]
    key += [f"FAILED {c.get('control')} (policy {c.get('policy', 'n/a')})" + ("" if c.get("compensating_control") else " — no compensating control") for c in failed[:4]]

    evidence = [{"source": f"local://{rel}" if rel else "local://governance/security-policy-control/SKILL.md", "ref": "policy set and control tests"},
                {"source": "https://www.cisecurity.org/controls/v8", "ref": "CIS Controls v8 mapping"},
                {"source": "local://governance/security-policy-control/SKILL.md", "ref": "policy hierarchy and control framework mapping"}]
    return {"agent_slug": SLUG, "intent_type": "report", "action": action,
            "rationale": ("Each policy is a gap unless it has an owner, a verification mechanism, a review within 12 months, and active status; a Tier 1 policy in draft or expired "
                          "is critical. Control coverage is the pass rate; a failed control with no compensating note is critical. Assessment is read-only; deploying a policy "
                          "would be a gated policy_change."),
            "confidence": 0.85, "severity": severity, "key_findings": key, "evidence_references": evidence,
            "next_agents": (["findings-tracker"] if gaps or failed else []) + (["compliance-mapping"] if failed else []),
            "human_approval_required": False, "timestamp_utc": _now(),
            "assessment": {"policies": len(policies), "control_coverage_pct": coverage, "policy_gaps": gaps, "failed_controls": [c.get("control") for c in failed]},
            "mitre_ttps": [], "affected_assets": [], "_exit": exit_code}


def main() -> int:
    ap = argparse.ArgumentParser(description="USAP security-policy-control")
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
    print(json.dumps(p, indent=2) if args.output == "json" else f"security-policy-control: severity={p['severity']}")
    return code


if __name__ == "__main__":
    raise SystemExit(main())
