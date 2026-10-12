#!/usr/bin/env python3
"""Threat Model builder — STRIDE + DREAD from a target descriptor.

Reads a target spec (path or description), enumerates STRIDE threats per
trust boundary, scores each on DREAD, picks the top 5, writes the canonical
THREAT_MODEL.md artifact, and emits the 11-field contract payload.

Stdlib only. Heuristic threat enumeration is intentional: real spec parsing
belongs in client glue. This tool gives the chain a deterministic skeleton.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

SLUG = "threat-model"

STRIDE_ORDER = ("S", "T", "R", "I", "D", "E")
STRIDE_NAMES = {
    "S": "Spoofing",
    "T": "Tampering",
    "R": "Repudiation",
    "I": "Information disclosure",
    "D": "Denial of service",
    "E": "Elevation of privilege",
}

DEFAULT_TARGET = {
    "target_name": "SimpleStoreAPI",
    "target_path": "/tmp/simple-store-api",
    "target_description": None,
    "architecture_diagram_path": None,
    "prd_path": None,
    "tenancy": "single-tenant",
    "data_sensitivity": "confidential",
    "auth_scheme": "none",
    "rate_limit_policy": "missing",
    "transport": "https-unspecified",
    "audit_logging_days": 30,
}


def _enumerate_threats(target: dict) -> list[dict]:
    """Heuristically enumerate STRIDE threats from the descriptor."""
    out = []
    auth = target.get("auth_scheme", "unknown")
    sens = target.get("data_sensitivity", "internal")
    rate = target.get("rate_limit_policy", "unknown")
    audit_days = int(target.get("audit_logging_days") or 0)

    if auth in ("none", "basic", "api-key", "unknown"):
        out.append({
            "id": "TM-001",
            "stride": "S",
            "boundary": "client-server",
            "threat": f"Unauthenticated or weak-auth identity at the client-server boundary (auth_scheme={auth})",
            "dread": {"D": 9, "R": 9, "E": 9, "A": 6, "Disc": 5},
        })
    if sens in ("confidential", "regulated"):
        out.append({
            "id": "TM-002",
            "stride": "I",
            "boundary": "server-db",
            "threat": f"{sens.title()}-tier data exposed without documented row-level or tenant-level authorization",
            "dread": {"D": 8, "R": 7, "E": 7, "A": 7, "Disc": 5},
        })
    if target.get("transport", "").startswith("https-unspecified"):
        out.append({
            "id": "TM-003",
            "stride": "T",
            "boundary": "client-server",
            "threat": "Session credentials traverse the client-server boundary without documented integrity protection",
            "dread": {"D": 6, "R": 6, "E": 5, "A": 5, "Disc": 5},
        })
    if target.get("tenancy") == "multi-tenant":
        out.append({
            "id": "TM-004",
            "stride": "E",
            "boundary": "tenant-isolation",
            "threat": "Privileged and tenant routes share controllers without explicit tenant scoping",
            "dread": {"D": 8, "R": 6, "E": 5, "A": 4, "Disc": 4},
        })
    else:
        out.append({
            "id": "TM-004",
            "stride": "E",
            "boundary": "controller",
            "threat": "Admin and customer routes share controller code paths — privilege boundary depends on prefix matching",
            "dread": {"D": 7, "R": 5, "E": 5, "A": 4, "Disc": 4},
        })
    if rate in ("missing", "unknown"):
        out.append({
            "id": "TM-005",
            "stride": "D",
            "boundary": "client-server",
            "threat": "Endpoints accept unbounded input without documented per-user or per-route rate limit",
            "dread": {"D": 5, "R": 8, "E": 6, "A": 6, "Disc": 6},
        })
    if audit_days < 90:
        out.append({
            "id": "TM-006",
            "stride": "R",
            "boundary": "audit",
            "threat": f"Audit logging retention is {audit_days} days, below the 90-day floor — repudiation risk on disputed actions",
            "dread": {"D": 4, "R": 4, "E": 3, "A": 4, "Disc": 3},
        })
    return out


def _dread_sum(t: dict) -> int:
    return sum(int(v) for v in t["dread"].values())


def _assumptions(target: dict) -> list[str]:
    out = []
    if not target.get("architecture_diagram_path"):
        out.append("No architecture diagram supplied — boundary inventory is heuristic.")
    if target.get("auth_scheme") == "unknown":
        out.append("auth_scheme is unknown — confirm whether OAuth2/OIDC is enforced before sign-off.")
    if target.get("rate_limit_policy") in ("unknown", "missing"):
        out.append("Rate-limit posture is unspecified — confirm per-user and per-route limits in production config.")
    if not target.get("prd_path"):
        out.append("No PRD supplied — business-criticality of each asset is inferred from sensitivity tier alone.")
    if not out:
        out.append("No unverified assumptions surfaced from this descriptor.")
    return out


def _write_artifact(target: dict, threats: list[dict], top5: list[dict], assumptions: list[str]) -> Path:
    target_path = Path(target.get("target_path") or f"/tmp/{target['target_name']}")
    artifact = target_path / "THREAT_MODEL.md"
    lines = [
        f"# Threat Model: {target['target_name']}",
        "",
        f"Generated by USAP `threat-model` skill on "
        f"{datetime.now(timezone.utc).strftime('%Y-%m-%d')}.",
        "",
        "## Assets",
        "",
        "| Asset | Path / location | Sensitivity |",
        "|---|---|---|",
        f"| Target | `{target_path}` | {target.get('data_sensitivity','internal')} |",
        "",
        "## Trust boundaries",
        "",
        "| Boundary | Inside | Outside |",
        "|---|---|---|",
        "| client-server | server processes + db | end-user client |",
        "| server-db | db storage layer | application code |",
        "| audit | audit pipeline | application + ops |",
        "",
        "## STRIDE threat catalog",
        "",
        "| ID | Category | Boundary | Threat |",
        "|---|---|---|---|",
    ]
    for t in threats:
        lines.append(
            f"| `{t['id']}` | {STRIDE_NAMES[t['stride']]} | {t['boundary']} | {t['threat']} |"
        )
    lines += ["", "## Top 5 by DREAD", "", "| ID | D | R | E | A | Disc | Sum | Recommendation |", "|---|---|---|---|---|---|---|---|"]
    for t in top5:
        d = t["dread"]
        lines.append(
            f"| `{t['id']}` | {d['D']} | {d['R']} | {d['E']} | {d['A']} | {d['Disc']} | "
            f"{_dread_sum(t)} | Hand off to `vuln-scan` |"
        )
    lines += ["", "## Assumptions to verify", "", "| # | Assumption |", "|---|---|"]
    for i, a in enumerate(assumptions, 1):
        lines.append(f"| {i} | {a} |")
    lines.append("")
    artifact.parent.mkdir(parents=True, exist_ok=True)
    artifact.write_text("\n".join(lines), encoding="utf-8")
    return artifact


def model(target: dict) -> dict:
    threats = _enumerate_threats(target)
    threats.sort(key=lambda t: -_dread_sum(t))
    top5 = threats[:5]
    assumptions = _assumptions(target)

    artifact_path = _write_artifact(target, threats, top5, assumptions)

    key_findings = [
        f"{t['id']} ({STRIDE_NAMES[t['stride']]}): {t['threat']} — DREAD sum {_dread_sum(t)}"
        for t in top5
    ]
    if assumptions:
        key_findings.append(
            f"{len(assumptions)} unverified assumption(s) logged in {artifact_path.name}"
        )

    top_dread = _dread_sum(top5[0]) if top5 else 0
    if top_dread >= 35:
        severity = "high"
    elif top_dread >= 25:
        severity = "medium"
    else:
        severity = "low"

    confidence = 0.82 if not [a for a in assumptions if a.startswith("No architecture")] else 0.68

    payload = {
        "agent_slug": SLUG,
        "intent_type": "analyze",
        "action": (
            f"Hand off the threat model + DREAD hit list to vuln-scan; scope its checks "
            f"to the top-{min(3, len(top5))} boundaries listed."
        ),
        "rationale": (
            f"{target.get('target_name','target')} produced {len(threats)} STRIDE "
            f"threats across the {len(set(t['boundary'] for t in threats))} boundaries inventoried. "
            f"Top DREAD threat is {top5[0]['id']} at sum {_dread_sum(top5[0])}. "
            f"{len(assumptions)} assumption(s) remain unverified."
        ) if top5 else "No STRIDE threats triggered for this descriptor; model is empty by design.",
        "confidence": round(confidence, 2),
        "severity": severity,
        "key_findings": key_findings,
        "evidence_references": [
            {"source": "spec", "ref": str(target.get("target_path") or target.get("target_description","")), "quote": f"auth_scheme: {target.get('auth_scheme','unknown')}"}
        ],
        "next_agents": ["vuln-scan"],
        "human_approval_required": False,
        "timestamp_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "mitre_ttps": ["T1190", "T1078"],
        "affected_assets": [target.get("target_name", "target")],
        "artifact_path": str(artifact_path),
    }
    return payload


def _render_human(payload: dict) -> str:
    lines = [
        "BOTTOM LINE: " + payload["action"],
        f"SEVERITY: {payload['severity'].upper()}  CONFIDENCE: {payload['confidence']:.2f}",
        f"ARTIFACT: {payload['artifact_path']}",
        "TOP THREATS:",
    ]
    lines += [f"  - {f}" for f in payload["key_findings"]]
    lines.append("NEXT: " + " -> ".join(payload["next_agents"]))
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--input", help="Path to a target descriptor JSON.")
    parser.add_argument("--output", choices=("json", "human"), default="json")
    args = parser.parse_args()
    if args.input:
        try:
            target = json.loads(Path(args.input).read_text(encoding="utf-8"))
        except (FileNotFoundError, json.JSONDecodeError) as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 2
    else:
        target = DEFAULT_TARGET
    payload = model(target)
    if args.output == "json":
        print(json.dumps(payload, indent=2))
    else:
        print(_render_human(payload))
    return 0


if __name__ == "__main__":
    sys.exit(main())
