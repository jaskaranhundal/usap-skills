#!/usr/bin/env python3
"""credential-attacks_tool.py

Reasons over a login target and a probe result to choose the safest credential
attack approach per the SKILL.md tables (attack type, lockout risk, wordlist,
thread count) and refuses when the target is out of scope, unauthorized, or the
lockout risk is high. Never runs an attack; it recommends. Emits the USAP
11-field payload.

  python3 credential-attacks_tool.py --input target.json --output json
  python3 credential-attacks_tool.py --output json     # no input: informational, exit 0

Input (see tests/fixtures/credential-attacks-input.json): target, authorized,
scope{in_scope[]}, login{failure_indicator, rate_limit_headers[], lockout_after,
captcha_after, mfa}, probe{known_bad_tested, response_differs}, candidate{
known_software, default_creds_confirmed, username_known}.

Exit codes: 0 recommendation issued or refused safely; 1 manual-only (high
lockout, CAPTCHA or MFA); 2 refused out of scope or unauthorized. Stdlib only.
"""
from __future__ import annotations

import argparse
import fnmatch
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

SLUG = "credential-attacks"
HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parents[2]


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


def _refuse(action: str, rationale: str, target: str, rel: Optional[str], exit_code: int) -> Dict[str, Any]:
    return {"agent_slug": SLUG, "intent_type": "block", "action": action, "rationale": rationale, "confidence": 1.0,
            "severity": "informational", "key_findings": [action, "No attack recommended; authorization and scope are prerequisites."],
            "evidence_references": [{"source": "local://shared/scripts/bb_scope_enforcer.py", "ref": "scope enforcement is mandatory before any active credential test"},
                                    {"source": f"local://{rel}" if rel else "local://red-team/credential-attacks/SKILL.md", "ref": str(target)}],
            "next_agents": [], "human_approval_required": False, "timestamp_utc": _now(),
            "credential_plan": {"decision": "refused", "target": target}, "_exit": exit_code}


def analyse(t: dict, input_path: Optional[str] = None) -> Dict[str, Any]:
    rel = None
    if input_path:
        try:
            rel = Path(input_path).resolve().relative_to(REPO_ROOT).as_posix()
        except ValueError:
            rel = None
    if not t:
        return {"agent_slug": SLUG, "intent_type": "advise", "action": "Supply a target and login descriptor; nothing was provided.",
                "rationale": "No input; nothing reasoned. Absence of input, never a clean result.", "confidence": 0.30, "severity": "informational",
                "key_findings": ["No target supplied"], "evidence_references": [{"source": "local://red-team/credential-attacks/SKILL.md", "ref": "attack selection (not applied)"}],
                "next_agents": [], "human_approval_required": False, "timestamp_utc": _now(), "credential_plan": {"decision": "no_input"}, "_exit": 0}

    target = str(t.get("target", "")) or "unspecified"
    scope = (t.get("scope") or {}).get("in_scope") or []
    if not t.get("authorized"):
        return _refuse(f"Refuse: no written authorization recorded for {target}.", "SKILL.md requires explicit written authorization before any credential test.", target, rel, 2)
    if not _in_scope(target, scope):
        return _refuse(f"Refuse: {target} is not in the engagement scope.", "bb_scope_enforcer rules do not match the target; out-of-scope targets are never attacked.", target, rel, 2)

    login = t.get("login") or {}
    probe = t.get("probe") or {}
    cand = t.get("candidate") or {}

    # Lockout risk (SKILL.md table)
    if login.get("mfa"):
        return {**_refuse(f"Manual only: {target} is MFA-protected.", "A credential alone is insufficient against MFA; automation is not appropriate. Flag to the researcher.", target, rel, 1), "severity": "medium"}
    if login.get("captcha_after") is not None:
        return {**_refuse(f"Manual only: {target} shows a CAPTCHA after {login.get('captcha_after')} attempts.", "hydra cannot solve CAPTCHAs; recommend a manual test.", target, rel, 1), "severity": "medium"}
    lock = login.get("lockout_after")
    if lock is not None and int(lock) <= 3:
        return {**_refuse(f"Stop: {target} locks accounts after {lock} attempts.", "Lockout risk is high; an automated attack would cause a denial of service. Flag to the researcher.", target, rel, 1), "severity": "medium"}

    rate = [str(h).lower() for h in (login.get("rate_limit_headers") or [])]
    if lock is not None:
        risk = "high"
    elif any("ratelimit" in h or "retry-after" in h for h in rate):
        risk = "medium"
    elif not probe.get("response_differs", True):
        risk = "unknown"
    else:
        risk = "low"

    # Attack type + wordlist + thread count
    if cand.get("default_creds_confirmed"):
        attack, wordlist, conf = "single-pair test", "default credentials (confirmed)", 0.90
    elif cand.get("known_software"):
        attack, wordlist, conf = "single-pair test", f"default credentials for {cand.get('known_software')}", 0.70
    elif cand.get("username_known"):
        attack, wordlist, conf = "targeted brute-force", "top-100-passwords.txt with the known username", 0.55
    else:
        attack, wordlist, conf = "password spray", "top-10 passwords across enumerated users", 0.45
    threads = 1 if risk in ("medium", "high", "unknown") else 4
    if risk == "medium":
        attack = "slow " + attack + " with delays"

    if not probe.get("known_bad_tested"):
        pre = "Send ONE known-bad credential first to capture the exact failure indicator, then "
        conf = round(conf - 0.10, 2)
    else:
        pre = ""
    failure = login.get("failure_indicator") or "unknown; capture from the known-bad probe"
    action = (f"{pre}run a {attack} against {target} using {wordlist}, {threads} thread(s), matching the failure indicator "
              f"\"{failure}\". Lockout risk {risk}. Verify any hit by replaying the credential manually before reporting it valid.")

    key = [f"Target {target}: authorized and in scope; lockout risk {risk}; attack type {attack}; {threads} thread(s)",
           f"Failure indicator: {failure}",
           f"Wordlist: {wordlist}; confidence {conf}",
           "Verification: replay every hydra hit manually; hydra output alone is not proof of a valid credential"]
    if not probe.get("known_bad_tested"):
        key.append("Prerequisite not yet done: one known-bad credential must be tested first to fix the failure indicator")

    evidence = [{"source": "local://shared/scripts/bb_scope_enforcer.py", "ref": f"{target} confirmed in scope"},
                {"source": f"local://{rel}" if rel else "local://red-team/credential-attacks/SKILL.md", "ref": "login descriptor and probe result"},
                {"source": "local://red-team/credential-attacks/SKILL.md", "ref": "attack type selection, lockout risk, wordlist tables"}]
    return {"agent_slug": SLUG, "intent_type": "advise", "action": action,
            "rationale": ("Authorization and scope are validated first (refuse otherwise). MFA, CAPTCHA or a lockout threshold at or below three attempts forces a manual-only "
                          "recommendation. Otherwise the attack type follows the SKILL.md selection table, the thread count drops to one under any rate limit or lockout signal, "
                          "and confidence follows the documented bands. No attack is executed."),
            "confidence": conf, "severity": "medium" if risk in ("high", "medium") else "low",
            "key_findings": key, "evidence_references": evidence,
            "next_agents": ["safe-exploitation"] if cand.get("default_creds_confirmed") else [], "human_approval_required": False, "timestamp_utc": _now(),
            "credential_plan": {"decision": "recommended", "target": target, "attack_type": attack, "lockout_risk": risk, "threads": threads, "wordlist": wordlist,
                                "failure_indicator": failure, "manual_verification_required": True},
            "mitre_ttps": ["T1110.003" if attack.startswith(("password spray", "slow password spray")) else "T1110.001"], "affected_assets": [target], "_exit": 0}


def main() -> int:
    ap = argparse.ArgumentParser(description="USAP credential-attacks: choose the safest credential-test approach")
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
        print(f"credential-attacks: {p['credential_plan'].get('decision')} severity={p['severity']}")
        for f in p["key_findings"]:
            print(f"  - {f}")
    return code


if __name__ == "__main__":
    raise SystemExit(main())
