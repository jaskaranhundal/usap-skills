#!/usr/bin/env python3
"""sast-dast-coordinator_tool.py

Correlates SAST, DAST and SCA findings per the SKILL.md: deduplicates across
tools by (owasp, location), and prioritises by exploitability — a finding
confirmed by DAST outranks a SAST-only finding of the same severity. Read-only.
Emits the USAP 11-field payload.

  python3 sast-dast-coordinator_tool.py --input findings.json --output json
  python3 sast-dast-coordinator_tool.py --output json    # no input: informational, exit 0

Input (see tests/fixtures/sast-dast-coordinator-input.json):
{findings[] {tool, kind (sast|dast|sca), owasp, location, severity}}.

Exit codes: 0 no finding above medium; 1 high; 2 critical. Stdlib only.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

SLUG = "sast-dast-coordinator"
HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parents[2]
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
    raw = [f for f in (t.get("findings") or []) if isinstance(f, dict)]
    if not t or not raw:
        return {"agent_slug": SLUG, "intent_type": "analyze", "action": "Supply tool findings; nothing was provided.",
                "rationale": "No findings supplied.", "confidence": 0.30, "severity": "informational", "key_findings": ["No findings supplied"],
                "evidence_references": [{"source": "local://appsec-devsecops/sast-dast-coordinator/SKILL.md", "ref": "correlation model (not applied)"}],
                "next_agents": [], "human_approval_required": False, "timestamp_utc": _now(), "findings": [], "_exit": 0}
    # Deduplicate by (owasp, location); merge tool list; DAST confirmation raises priority.
    merged: Dict[tuple, dict] = {}
    for f in raw:
        owasp = str(f.get("owasp", "?")).upper()
        loc = str(f.get("location", "?"))
        kind = str(f.get("kind", "sast")).lower()
        sev = str(f.get("severity", "medium")).lower()
        if sev not in SEV_RANK:
            sev = "medium"
        k = (owasp, loc)
        e = merged.setdefault(k, {"owasp": owasp, "location": loc, "tools": set(), "kinds": set(), "severity": sev, "dast_confirmed": False})
        e["tools"].add(str(f.get("tool", "?")))
        e["kinds"].add(kind)
        if SEV_RANK[sev] > SEV_RANK[e["severity"]]:
            e["severity"] = sev
        if kind == "dast":
            e["dast_confirmed"] = True
    findings = []
    for e in merged.values():
        findings.append({"owasp": e["owasp"], "location": e["location"], "tools": sorted(e["tools"]),
                         "severity": e["severity"], "dast_confirmed": e["dast_confirmed"],
                         "priority": "exploitable" if e["dast_confirmed"] else "static-only"})
    # Order: DAST-confirmed first within severity, then by severity.
    findings.sort(key=lambda x: (-SEV_RANK[x["severity"]], not x["dast_confirmed"]))
    counts = {k: sum(1 for x in findings if x["severity"] == k) for k in SEV_RANK}
    confirmed = [x for x in findings if x["dast_confirmed"]]
    severity = findings[0]["severity"] if findings else "informational"
    exit_code = 2 if counts["critical"] else 1 if counts["high"] else 0
    action = (f"{len(confirmed)} DAST-confirmed exploitable finding(s) prioritised first; {counts['critical']} critical overall. Fix confirmed criticals before merge: "
              + "; ".join(f"{x['owasp']} @ {x['location']}" for x in confirmed if x["severity"] == "critical")[:150] + "." if counts["critical"] else
              f"{counts['high']} high correlated finding(s) to triage; DAST-confirmed first." if counts["high"] else
              "No correlated finding above medium.")
    key = [f"{len(raw)} raw finding(s) -> {len(findings)} unique after dedupe ({counts['critical']} critical, {counts['high']} high); {len(confirmed)} DAST-confirmed"]
    key += [f"{x['severity']} {x['owasp']} @ {x['location']} [{x['priority']}] via {'+'.join(x['tools'])}" for x in findings[:6]]
    evidence = [{"source": f"local://{rel}" if rel else "local://appsec-devsecops/sast-dast-coordinator/SKILL.md", "ref": "SAST/DAST/SCA findings"},
                {"source": "local://appsec-devsecops/sast-dast-coordinator/SKILL.md", "ref": "tool matrix and correlation model"}]
    return {"agent_slug": SLUG, "intent_type": "analyze", "action": action,
            "rationale": ("Findings are deduplicated across tools by OWASP category and location; the highest reported severity wins, and a DAST confirmation marks the finding exploitable "
                          "and lifts its priority above static-only findings of the same severity. Read-only correlation."),
            "confidence": 0.85, "severity": severity, "key_findings": key, "evidence_references": evidence,
            "next_agents": ["devsecops-pipeline"] if findings else [], "human_approval_required": False, "timestamp_utc": _now(),
            "findings": findings, "mitre_ttps": [], "affected_assets": sorted({x["location"] for x in findings}), "_exit": exit_code}


def main() -> int:
    ap = argparse.ArgumentParser(description="USAP sast-dast-coordinator")
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
    print(json.dumps(p, indent=2) if args.output == "json" else f"sast-dast-coordinator: severity={p['severity']}")
    return code


if __name__ == "__main__":
    raise SystemExit(main())
