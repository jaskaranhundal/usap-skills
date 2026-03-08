#!/usr/bin/env python3
"""
bb_scope_enforcer.py — Bug Bounty Scope Enforcement Utility

Called FIRST by every bb-* pre_analysis.py before any tool execution.
Reads a scope YAML (or JSON) file, validates the target against in_scope /
out_of_scope rules, checks CIDR ranges, wildcard domains, and returns a
ScopeResult indicating whether passive and/or active tools are authorized.

Usage (from other pre_analysis scripts):
    from bb_scope_enforcer import enforce_scope, can_run_active_tools, ScopeViolation

    scope = enforce_scope(fact)          # raises ScopeViolation or exits on out_of_scope
    if not can_run_active_tools(scope):
        # print passive-only result and exit
        sys.exit(0)

stdin:  (optional) SecurityFact JSON — only used when run standalone for testing
stdout: (standalone only) JSON ScopeResult
exit:   0 = in scope, 1 = out of scope (standalone test)
"""

from __future__ import annotations

import ipaddress
import json
import os
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional


# ── ScopeResult dataclass ─────────────────────────────────────────────────────

@dataclass
class ScopeResult:
    in_scope: bool
    target: str
    program: str
    platform: str                         # hackerone | bugcrowd | intigriti | private
    tool_authorization_tier: str          # passive | active | exploit
    matched_rule: Optional[str]           # which in_scope rule matched
    violations: List[str] = field(default_factory=list)
    restrictions: List[str] = field(default_factory=list)
    safe_harbor: bool = True
    vdp_only: bool = False


class ScopeViolation(Exception):
    """Raised when target explicitly matches an out_of_scope rule."""
    def __init__(self, target: str, rule: str):
        self.target = target
        self.rule = rule
        super().__init__(f"Target '{target}' is explicitly out of scope: '{rule}'")


# ── Scope file loading ────────────────────────────────────────────────────────

def _load_scope_file(scope_file: str) -> Dict[str, Any]:
    """
    Load a scope YAML or JSON file.
    Gracefully falls back to JSON if pyyaml is not installed.
    """
    path = Path(scope_file)

    # Try relative to cwd (repo root) if not absolute
    if not path.is_absolute():
        cwd_path = Path.cwd() / path
        if cwd_path.exists():
            path = cwd_path

    if not path.exists():
        # Return permissive defaults so tools can still run without a scope file
        return {
            "program": "unknown",
            "platform": "private",
            "safe_harbor": False,
            "vdp_only": False,
            "in_scope": [],
            "out_of_scope": [],
            "restrictions": [],
            "tool_tiers": {},
        }

    content = path.read_text(encoding="utf-8")

    # Try YAML first, fall back to JSON
    try:
        import yaml  # type: ignore
        return yaml.safe_load(content) or {}
    except ImportError:
        pass

    try:
        return json.loads(content)
    except json.JSONDecodeError:
        return {}


# ── Matching helpers ──────────────────────────────────────────────────────────

def _normalize(value: str) -> str:
    """Strip scheme, trailing slashes, lowercase."""
    v = value.strip().lower()
    v = re.sub(r"^https?://", "", v)
    v = v.rstrip("/")
    return v


def _wildcard_match(pattern: str, target: str) -> bool:
    """
    Match wildcard domain patterns (e.g. *.example.com).
    Does NOT support glob patterns beyond leading asterisk.
    """
    pattern = _normalize(pattern)
    target = _normalize(target)

    if pattern == target:
        return True

    if pattern.startswith("*."):
        suffix = pattern[2:]  # e.g. "example.com"
        # target must end with .suffix — the bare suffix itself is NOT a match
        if target == suffix:
            return False
        if target.endswith("." + suffix):
            return True
        return False

    return False


def _cidr_match(cidr_str: str, target: str) -> bool:
    """Return True if target is an IP address inside cidr_str."""
    try:
        network = ipaddress.ip_network(cidr_str, strict=False)
        addr = ipaddress.ip_address(_normalize(target))
        return addr in network
    except ValueError:
        return False


def _matches_any(rules: List[str], target: str) -> Optional[str]:
    """
    Return the first rule that matches target (wildcard or CIDR or exact).
    Returns None if no match.
    """
    target_n = _normalize(target)
    for rule in rules:
        rule_n = _normalize(rule)
        # CIDR check (only if rule looks like an IP network)
        if "/" in rule_n and re.match(r"^\d{1,3}\.\d{1,3}", rule_n):
            if _cidr_match(rule_n, target_n):
                return rule
        # Wildcard / exact match
        if _wildcard_match(rule_n, target_n):
            return rule
    return None


# ── Tier comparison ───────────────────────────────────────────────────────────

_TIER_ORDER = {"passive": 0, "active": 1, "exploit": 2}


def _tier_gte(requested: str, minimum: str) -> bool:
    """Return True if requested tier is >= minimum tier."""
    return _TIER_ORDER.get(requested.lower(), 0) >= _TIER_ORDER.get(minimum.lower(), 0)


# ── Public API ────────────────────────────────────────────────────────────────

def enforce_scope(fact: Dict[str, Any]) -> ScopeResult:
    """
    Primary entry point.  Call at the top of every bb-* pre_analysis.py.

    Reads fact.raw_payload for:
        target                  — hostname, IP, or URL to test
        scope_file              — path to scope YAML/JSON
        tool_authorization_tier — passive | active | exploit (default: passive)
        program                 — program name (optional)
        platform                — hackerone | bugcrowd | intigriti | private

    Raises:
        ScopeViolation — if target explicitly matches out_of_scope list.
                         Caller should print an error JSON and sys.exit(0).

    Returns:
        ScopeResult — caller checks .in_scope and can_run_active_tools()
    """
    payload = fact.get("raw_payload", {}) if isinstance(fact, dict) else {}
    if not isinstance(payload, dict):
        payload = {}

    target = str(payload.get("target", ""))
    scope_file = str(payload.get("scope_file", ""))
    tier = str(payload.get("tool_authorization_tier", "passive")).lower()
    program = str(payload.get("program", "unknown"))
    platform = str(payload.get("platform", "private"))

    scope_data = _load_scope_file(scope_file) if scope_file else {}

    in_scope_rules: List[str] = scope_data.get("in_scope", [])
    out_of_scope_rules: List[str] = scope_data.get("out_of_scope", [])
    restrictions: List[str] = scope_data.get("restrictions", [])
    safe_harbor: bool = bool(scope_data.get("safe_harbor", True))
    vdp_only: bool = bool(scope_data.get("vdp_only", False))

    # 1. Check explicit out_of_scope first (hard block)
    oos_match = _matches_any(out_of_scope_rules, target)
    if oos_match:
        raise ScopeViolation(target, oos_match)

    # 2. Check in_scope (soft miss if no rules defined → allow)
    if in_scope_rules:
        matched_rule = _matches_any(in_scope_rules, target)
    else:
        matched_rule = "(no scope rules — open scope)"

    return ScopeResult(
        in_scope=matched_rule is not None,
        target=target,
        program=scope_data.get("program", program),
        platform=scope_data.get("platform", platform),
        tool_authorization_tier=tier,
        matched_rule=matched_rule,
        violations=[],
        restrictions=restrictions,
        safe_harbor=safe_harbor,
        vdp_only=vdp_only,
    )


def can_run_active_tools(scope_result: ScopeResult) -> bool:
    """Return True if the authorization tier permits active tool execution."""
    return _tier_gte(scope_result.tool_authorization_tier, "active")


def can_run_exploit_tools(scope_result: ScopeResult) -> bool:
    """Return True if the authorization tier permits exploit-class tools."""
    return _tier_gte(scope_result.tool_authorization_tier, "exploit")


def out_of_scope_result(target: str, rule: str, agent: str) -> Dict[str, Any]:
    """Return a standard out-of-scope JSON result dict."""
    return {
        "scope_status": "out_of_scope",
        "target": target,
        "blocked_by_rule": rule,
        "agent": agent,
        "findings": [],
        "message": f"Target '{target}' is explicitly excluded from scope. No tools executed.",
    }


def not_in_scope_result(target: str, agent: str) -> Dict[str, Any]:
    """Return a standard not-in-scope (soft miss) JSON result dict."""
    return {
        "scope_status": "not_in_scope",
        "target": target,
        "agent": agent,
        "findings": [],
        "message": (
            f"Target '{target}' is not listed in the in_scope rules. "
            "Add it to the program scope file to enable testing."
        ),
    }


def passive_only_result(target: str, agent: str, passive_findings: Any = None) -> Dict[str, Any]:
    """Return a standard passive-only result (active tools not authorized)."""
    return {
        "scope_status": "in_scope_passive_only",
        "target": target,
        "agent": agent,
        "tool_authorization_tier": "passive",
        "findings": passive_findings or [],
        "message": (
            f"Target '{target}' is in scope but tool_authorization_tier is 'passive'. "
            "Active tools (nuclei, nmap, ffuf, dalfox) were NOT executed. "
            "Set tool_authorization_tier: active in the SecurityFact to enable them."
        ),
    }


# ── Standalone test entry point ───────────────────────────────────────────────

def main() -> int:
    try:
        raw = sys.stdin.read()
        fact: Dict[str, Any] = json.loads(raw) if raw.strip() else {}
    except json.JSONDecodeError:
        fact = {}

    try:
        scope = enforce_scope(fact)
    except ScopeViolation as e:
        result = out_of_scope_result(e.target, e.rule, "bb_scope_enforcer")
        print(json.dumps(result, indent=2))
        return 1

    if not scope.in_scope:
        result = not_in_scope_result(scope.target, "bb_scope_enforcer")
        print(json.dumps(result, indent=2))
        return 1

    result = {
        "scope_status": "in_scope",
        "target": scope.target,
        "program": scope.program,
        "platform": scope.platform,
        "tool_authorization_tier": scope.tool_authorization_tier,
        "matched_rule": scope.matched_rule,
        "can_run_active_tools": can_run_active_tools(scope),
        "can_run_exploit_tools": can_run_exploit_tools(scope),
        "safe_harbor": scope.safe_harbor,
        "vdp_only": scope.vdp_only,
        "restrictions": scope.restrictions,
    }
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
