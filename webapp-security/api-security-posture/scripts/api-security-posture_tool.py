#!/usr/bin/env python3
"""API Security Posture scorer.

Scores an API descriptor against five dimensions of OWASP API Top 10 and
emits a USAP 11-field contract payload. Stdlib only.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

SLUG = "api-security-posture"

DIMENSIONS = ("bola", "auth", "rate", "mass_assignment", "audit")

ROUTING = {
    "bola": ["secure-sdlc", "identity-access-risk"],
    "auth": ["identity-access-risk"],
    "rate": ["secure-sdlc"],
    "mass_assignment": ["security-requirements-review"],
    "audit": ["telemetry-signal-quality"],
}

DEFAULT_API = {
    "name": "SimpleStoreAPI",
    "endpoints": [
        {
            "path": "/api/v1/orders/{id}",
            "methods": ["GET", "PATCH"],
            "auth_required": True,
            "accepts_object_id": True,
            "object_authz_check": "owner-only",
        },
        {
            "path": "/api/v1/users/{id}",
            "methods": ["GET"],
            "auth_required": True,
            "accepts_object_id": True,
            "object_authz_check": "owner-only",
        },
    ],
    "auth_scheme": "oauth2",
    "rate_limit_policy": {
        "per_user": "no",
        "per_ip": "no",
        "per_route": "yes",
    },
    "mass_assignment_guard": "none",
    "audit_logging": {
        "structured": "yes",
        "correlated": "no",
        "retention_days": 30,
    },
}


def _score_bola(endpoints: list[dict]) -> tuple[int, str, str]:
    targets = [e for e in endpoints if e.get("accepts_object_id")]
    if not targets:
        return 20, "no id-accepting endpoints — BOLA not applicable", "ok"
    per_ep = 20 / len(targets)
    score = 0.0
    for ep in targets:
        check = ep.get("object_authz_check", "unknown")
        if check in ("owner-only", "rbac"):
            score += per_ep
        elif check == "unknown":
            score += per_ep * 0.25
    score = min(20, int(round(score)))
    if score == 20:
        return score, "owner-only or rbac checks confirmed on every id-accepting endpoint", "strong"
    if score == 0:
        return 0, "no authorization check on id-accepting endpoints", "critical"
    return score, "partial authorization coverage on id-accepting endpoints", "gap"


def _score_auth(api: dict) -> tuple[int, str, str]:
    scheme = api.get("auth_scheme", "unknown")
    scores = {"oauth2": 20, "oidc": 20, "api-key": 12, "basic": 5, "none": 0, "unknown": 0}
    score = scores.get(scheme, 0)
    needs_auth = [e for e in api.get("endpoints", []) if e.get("auth_required")]
    if needs_auth and scheme in ("none", "unknown"):
        score = max(0, score - 5)
    text = {
        "oauth2": "oauth2 scheme covers all auth-required endpoints",
        "oidc": "oidc scheme covers all auth-required endpoints",
        "api-key": "api-key scheme — adequate but not best-practice",
        "basic": "basic auth in use — weak for production APIs",
        "none": "no auth scheme declared",
        "unknown": "auth scheme not declared (unknown)",
    }.get(scheme, "auth scheme not declared")
    tag = "strong" if score >= 18 else ("gap" if score >= 5 else "critical")
    return score, text, tag


def _score_rate(api: dict) -> tuple[int, str, str]:
    p = api.get("rate_limit_policy", {})
    pts = 0
    if p.get("per_user") == "yes":
        pts += 7
    if p.get("per_ip") == "yes":
        pts += 7
    if p.get("per_route") == "yes":
        pts += 6
    pts = min(20, pts)
    missing = [k for k in ("per_user", "per_ip", "per_route") if p.get(k) != "yes"]
    text = (
        "rate-limit policy covers per_user, per_ip, and per_route"
        if not missing
        else f"missing: {', '.join(missing)}"
    )
    tag = "strong" if pts >= 18 else ("gap" if pts > 0 else "critical")
    return pts, text, tag


def _score_mass_assignment(api: dict) -> tuple[int, str, str]:
    guard = api.get("mass_assignment_guard", "unknown")
    scores = {"allowlist": 20, "denylist": 10, "none": 0, "unknown": 0}
    pts = scores.get(guard, 0)
    text = {
        "allowlist": "explicit allowlist guard documented",
        "denylist": "denylist guard documented — weaker than allowlist",
        "none": "no mass-assignment guard documented",
        "unknown": "mass-assignment guard not declared (unknown)",
    }.get(guard, "mass-assignment guard not declared")
    tag = "strong" if pts >= 18 else ("critical" if pts == 0 else "gap")
    return pts, text, tag


def _score_audit(api: dict) -> tuple[int, str, str]:
    log = api.get("audit_logging", {})
    pts = 0
    if log.get("structured") == "yes":
        pts += 7
    if log.get("correlated") == "yes":
        pts += 7
    retention = int(log.get("retention_days") or 0)
    if retention >= 90:
        pts += 6
    pts = min(20, pts)
    if pts == 0:
        text = "no audit logging declared"
        tag = "critical"
    elif pts >= 18:
        text = "structured + correlated + 90-day retention all confirmed"
        tag = "strong"
    else:
        text = f"partial — retention {retention}d, structured={log.get('structured','no')}, correlated={log.get('correlated','no')}"
        tag = "gap"
    return pts, text, tag


def score_api(api: dict) -> dict:
    endpoints = api.get("endpoints") or []
    s_bola, t_bola, tag_bola = _score_bola(endpoints)
    s_auth, t_auth, tag_auth = _score_auth(api)
    s_rate, t_rate, tag_rate = _score_rate(api)
    s_mass, t_mass, tag_mass = _score_mass_assignment(api)
    s_audit, t_audit, tag_audit = _score_audit(api)

    total = s_bola + s_auth + s_rate + s_mass + s_audit

    # Confidence — drops as unknown count rises.
    unknown = sum(1 for tag in (tag_bola, tag_auth, tag_rate, tag_mass, tag_audit) if tag == "critical" and "(unknown)" in (t_bola + t_auth + t_rate + t_mass + t_audit))
    confidence = max(0.5, 0.8 - 0.05 * unknown)

    if total <= 40:
        severity = "critical"
        intent = "escalate"
    elif total <= 60:
        severity = "high"
        intent = "analyze"
    elif total <= 80:
        severity = "medium"
        intent = "analyze"
    else:
        severity = "low"
        intent = "analyze"

    # Find worst dimension by absolute score.
    dim_scores = {
        "bola": s_bola,
        "auth": s_auth,
        "rate": s_rate,
        "mass_assignment": s_mass,
        "audit": s_audit,
    }
    worst = min(dim_scores, key=lambda k: dim_scores[k])
    next_agents = ROUTING[worst]

    key_findings = [
        f"BOLA visibility: {s_bola}/20 — {t_bola}",
        f"Authentication: {s_auth}/20 — {t_auth}",
        f"Rate limiting: {s_rate}/20 — {t_rate}",
        f"Mass-assignment guard: {s_mass}/20 — {t_mass}",
        f"Audit logging: {s_audit}/20 — {t_audit}",
    ]

    name = api.get("name", "<unnamed API>")
    evidence_refs = [
        {
            "source": "descriptor",
            "ref": name,
            "quote": (
                f"{worst} = {dim_scores[worst]}/20 (worst single dimension)"
            ),
        }
    ]

    payload = {
        "agent_slug": SLUG,
        "intent_type": intent,
        "action": (
            f"Route to {next_agents[0]} — {worst} is the largest single posture "
            f"drag on the {name} surface."
        ),
        "rationale": (
            f"Posture score {total}/100. Worst dim: {worst} ({dim_scores[worst]}/20). "
            "See key_findings for the per-dimension breakdown."
        ),
        "confidence": round(confidence, 2),
        "severity": severity,
        "key_findings": key_findings,
        "evidence_references": evidence_refs,
        "next_agents": next_agents,
        "human_approval_required": False,
        "timestamp_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
    if total < 61:
        payload["mitre_ttps"] = ["T1078", "T1190"]
    return payload


def _render_human(payload: dict) -> str:
    lines = [
        "BOTTOM LINE: " + payload["action"],
        f"SEVERITY: {payload['severity'].upper()}  CONFIDENCE: {payload['confidence']:.2f}",
        "SCORECARD:",
    ]
    lines += [f"  - {f}" for f in payload["key_findings"]]
    lines.append("NEXT: " + " -> ".join(payload["next_agents"]))
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--input",
        help="JSON file with an API descriptor. If omitted, the bundled sample is used.",
    )
    parser.add_argument("--output", choices=("json", "human"), default="json")
    args = parser.parse_args()

    if args.input:
        try:
            api = json.loads(Path(args.input).read_text(encoding="utf-8"))
        except (FileNotFoundError, json.JSONDecodeError) as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 2
    else:
        api = DEFAULT_API

    payload = score_api(api)
    if args.output == "json":
        print(json.dumps(payload, indent=2))
    else:
        print(_render_human(payload))
    return 0


if __name__ == "__main__":
    sys.exit(main())
