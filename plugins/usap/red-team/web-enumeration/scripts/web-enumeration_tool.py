#!/usr/bin/env python3
"""web-enumeration_tool.py

Ranks active web content-discovery results (ffuf, gobuster) into the highest-
value probe targets per the SKILL.md Path Priority and Status Code tables,
filters static noise, flags 403s as high value, correlates with the tech
stack, and refuses out-of-scope or unauthorized input. Emits the USAP
11-field payload.

  python3 web-enumeration_tool.py --input enum.json --output json
  python3 web-enumeration_tool.py --output json     # no input: informational, exit 0

Input (see tests/fixtures/web-enumeration-input.json): target, authorized,
scope{in_scope[]}, tech_stack[], paths[]: {path, status, length, method}.

Exit codes: 0 ranked (or nothing of value); 1 P1 targets present; 2 refused
out of scope or unauthorized. Read-only analysis. Stdlib only.
"""
from __future__ import annotations

import argparse
import fnmatch
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

SLUG = "web-enumeration"
HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parents[2]

# SKILL.md Path Priority Classification: (regex, priority, why)
PRIORITY_RULES: List[Tuple[re.Pattern, str, str]] = [
    (re.compile(r"/(admin|administrator|wp-admin)(/|$)", re.I), "P1", "direct admin access"),
    (re.compile(r"\.(bak|old|zip|tar|gz|sql)$|/backup(/|$)", re.I), "P1", "backup or source exposure"),
    (re.compile(r"/(api|v[12]|graphql)(/|$)", re.I), "P1", "API surface, possible unauthenticated data"),
    (re.compile(r"/(setup|install|config)(/|$)", re.I), "P1", "setup page left enabled"),
    (re.compile(r"/(\.git|\.env|web\.config|\.svn|\.htpasswd)(/|$)?", re.I), "P1", "credential or source leakage"),
    (re.compile(r"/(login|signin|auth)(/|$)", re.I), "P2", "auth endpoint, credential testing"),
    (re.compile(r"/(upload|file|import)(/|$)", re.I), "P2", "file upload, webshell vector"),
    (re.compile(r"/(user|account|profile)(/|$)", re.I), "P2", "IDOR surface"),
    (re.compile(r"/(phpmyadmin|adminer)(/|$)", re.I), "P2", "database admin exposure"),
    (re.compile(r"/(xmlrpc\.php|wp-json)(/|$)?", re.I), "P2", "WordPress attack surface"),
]
STATIC = re.compile(r"\.(js|css|png|jpg|jpeg|gif|svg|ico|woff2?|ttf|eot|map|webp)$", re.I)
PRIO_RANK = {"P1": 3, "P2": 2, "P3": 1, "P4": 0}


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _in_scope(target: str, rules: List[str]) -> bool:
    if not rules:
        return False
    t = str(target).strip().lower().replace("https://", "").replace("http://", "").split("/")[0]
    for r in rules:
        r = str(r).strip().lower()
        if r == t or fnmatch.fnmatch(t, r) or t.endswith(r.lstrip("*.")):
            return True
    return False


def _classify(path: str) -> Tuple[str, str]:
    for rx, prio, why in PRIORITY_RULES:
        if rx.search(path):
            return prio, why
    if STATIC.search(path):
        return "P4", "static asset, rarely exploitable"
    return "P3", "unclassified path"


def _status_note(code: int) -> Tuple[str, int]:
    if code == 403:
        return "exists but forbidden: auth-bypass candidate, high value", 2   # bump
    if code == 401:
        return "auth required: credential-testing candidate", 1
    if code in (301, 302):
        return "redirect: may bypass a WAF or reveal an internal path", 0
    if code == 500:
        return "server error: possible injection or misconfiguration", 1
    if code == 200:
        return "accessible", 0
    return f"status {code}", 0


def analyse(t: dict, input_path: Optional[str] = None) -> Dict[str, Any]:
    rel = None
    if input_path:
        try:
            rel = Path(input_path).resolve().relative_to(REPO_ROOT).as_posix()
        except ValueError:
            rel = None
    if not t:
        return {"agent_slug": SLUG, "intent_type": "advise", "action": "Supply a target and enumeration results; nothing was provided.",
                "rationale": "No input; nothing ranked. Absence of input, never a clean result.", "confidence": 0.30, "severity": "informational",
                "key_findings": ["No enumeration results supplied"], "evidence_references": [{"source": "local://red-team/web-enumeration/SKILL.md", "ref": "path priority (not applied)"}],
                "next_agents": [], "human_approval_required": False, "timestamp_utc": _now(), "ranked_targets": [], "_exit": 0}

    target = str(t.get("target", "")) or "unspecified"
    scope = (t.get("scope") or {}).get("in_scope") or []
    if not t.get("authorized"):
        return {"agent_slug": SLUG, "intent_type": "block", "action": f"Refuse: no written authorization recorded for {target}.",
                "rationale": "SKILL.md requires explicit authorization and scope validation before ranking enumeration for probing.", "confidence": 1.0, "severity": "informational",
                "key_findings": [f"Refuse: {target} unauthorized"], "evidence_references": [{"source": "local://shared/scripts/bb_scope_enforcer.py", "ref": "authorization prerequisite"}],
                "next_agents": [], "human_approval_required": False, "timestamp_utc": _now(), "ranked_targets": [], "_exit": 2}
    if not _in_scope(target, scope):
        return {"agent_slug": SLUG, "intent_type": "block", "action": f"Refuse: {target} is not in the engagement scope.",
                "rationale": "bb_scope_enforcer rules do not match the target; out-of-scope hosts are never probed.", "confidence": 1.0, "severity": "informational",
                "key_findings": [f"Refuse: {target} out of scope"], "evidence_references": [{"source": "local://shared/scripts/bb_scope_enforcer.py", "ref": f"{target} not in scope"}],
                "next_agents": [], "human_approval_required": False, "timestamp_utc": _now(), "ranked_targets": [], "_exit": 2}

    tech = [str(x).lower() for x in (t.get("tech_stack") or [])]
    paths = [p for p in (t.get("paths") or []) if isinstance(p, dict) and p.get("path")]
    ranked: List[dict] = []
    filtered = 0
    for p in paths:
        path = str(p["path"]); code = int(p.get("status") or 200)
        prio, why = _classify(path)
        if prio == "P4":
            filtered += 1
            continue
        note, bump = _status_note(code)
        rank = PRIO_RANK[prio] + bump
        # Tech-stack correlation: WordPress paths on a non-WP stack are downgraded
        if ("wp-" in path or "xmlrpc" in path) and tech and not any("wordpress" in x or "wp" == x for x in tech):
            rank -= 2; why += "; but tech stack is not WordPress (possible false positive)"
        method = "GET" if code in (200, 301, 302, 403, 401) else "GET+POST"
        if re.search(r"/(login|auth|upload|api|graphql)", path, re.I):
            method = "GET+POST"
        ranked.append({"path": path, "status": code, "priority": prio, "effective_rank": rank, "why": why, "status_note": note, "method": method, "length": p.get("length")})

    ranked.sort(key=lambda r: (-r["effective_rank"], r["priority"], r["path"]))
    top = ranked[:5]
    p1 = [r for r in ranked if r["priority"] == "P1"]
    forbidden = [r for r in ranked if r["status"] == 403]
    severity = "high" if p1 else "medium" if ranked else "informational"

    if top:
        action = "Probe in this order: " + "; ".join(f"{r['path']} ({r['priority']}, {r['method']})" for r in top) + ". Do not probe outside the scope; parameter fuzzing needs researcher approval."
    else:
        action = "No high-value paths after filtering static assets; broaden the wordlist or move to the next host."

    key = [f"{target}: {len(paths)} path(s), {filtered} static filtered, {len(ranked)} ranked; {len(p1)} P1, {len(forbidden)} forbidden (403)"]
    key += [f"{r['priority']} {r['path']} [{r['status']}] {r['method']}: {r['why']} ({r['status_note']})" for r in top]
    if forbidden:
        key.append(f"403s flagged high-value (exist but forbidden, auth-bypass candidates): {', '.join(r['path'] for r in forbidden[:4])}")

    evidence = [{"source": f"local://{rel}" if rel else "local://red-team/web-enumeration/SKILL.md", "ref": f"{target} enumeration results", "quote": f"{len(ranked)} ranked paths"},
                {"source": "local://shared/scripts/bb_scope_enforcer.py", "ref": f"{target} confirmed in scope"},
                {"source": "local://red-team/web-enumeration/SKILL.md", "ref": "path priority and status-code interpretation tables"}]

    return {"agent_slug": SLUG, "intent_type": "advise", "action": action,
            "rationale": ("Authorization and scope are validated first. Static assets are filtered before ranking. Priority comes from the SKILL.md path table; 403 and 500 raise the "
                          "effective rank because a page that exists but is forbidden is more valuable than one openly served; WordPress paths on a non-WordPress stack are downgraded as "
                          "likely false positives. Only the top five are recommended for probing. Read-only; no request is sent."),
            "confidence": 0.82 if ranked else 0.4, "severity": severity, "key_findings": key, "evidence_references": evidence,
            "next_agents": ["web-app-pentest"] if p1 else [], "human_approval_required": False, "timestamp_utc": _now(),
            "ranked_targets": top, "coverage": {"paths_total": len(paths), "static_filtered": filtered, "ranked": len(ranked), "p1_count": len(p1), "forbidden_count": len(forbidden)},
            "mitre_ttps": ["T1595.003"], "affected_assets": [target], "_exit": 1 if p1 else 0}


def main() -> int:
    ap = argparse.ArgumentParser(description="USAP web-enumeration: rank content-discovery results for probing")
    ap.add_argument("--input"); ap.add_argument("--output", choices=["json", "text"], default="text")
    args = ap.parse_args()
    if args.input:
        try:
            t = json.loads(Path(args.input).read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            print(f"error: cannot read --input: {exc}", file=sys.stderr); return 2
    else:
        raw = "" if sys.stdin.isatty() else sys.stdin.read()
        try:
            t = json.loads(raw) if raw.strip() else {}
        except json.JSONDecodeError:
            t = {}
    p = analyse(t, args.input)
    code = p.pop("_exit", 0)
    if args.output == "json":
        print(json.dumps(p, indent=2))
    else:
        print(f"web-enumeration: severity={p['severity']} ranked={len(p.get('ranked_targets', []))}")
        for f in p["key_findings"]:
            print(f"  - {f}")
    return code


if __name__ == "__main__":
    raise SystemExit(main())
