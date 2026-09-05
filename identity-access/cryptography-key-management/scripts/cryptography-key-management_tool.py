#!/usr/bin/env python3
"""cryptography-key-management_tool.py

Assesses a cryptographic inventory against the SKILL.md approved/deprecated/
forbidden algorithm and TLS tables and key-lifecycle rules. Read-only. Emits
the USAP 11-field payload.

  python3 cryptography-key-management_tool.py --input crypto.json --output json
  python3 cryptography-key-management_tool.py --output json    # no input: informational, exit 0

Input (see tests/fixtures/cryptography-key-management-input.json): items[]:
{id, kind (symmetric|asymmetric|tls), algorithm, key_size, tls_version, usage,
key_age_days, rotation_period_days}.

Exit codes: 0 all approved; 1 deprecated present; 2 a forbidden algorithm or an
overdue high-sensitivity key. Stdlib only.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

SLUG = "cryptography-key-management"
HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parents[2]
# (algorithm upper, min key size or None, status) — order matters, first match wins
SYMMETRIC = {"AES-GCM": ("approved", 128), "AES-CBC": ("approved", 128), "CHACHA20-POLY1305": ("approved", 256),
             "3DES": ("deprecated", None), "DES": ("forbidden", None), "RC4": ("forbidden", None)}
ASYMMETRIC = {"RSA-OAEP": ("approved", 4096), "RSA-PSS": ("approved", 4096), "ECDSA": ("approved", None),
              "ECDH": ("approved", None), "ED25519": ("approved", None), "RSA": ("deprecated", 4096)}
TLS_STATUS = {"1.3": "approved", "1.2": "approved", "1.1": "forbidden", "1.0": "forbidden", "ssl3": "forbidden", "ssl2": "forbidden"}
SEV = {"forbidden": "critical", "deprecated": "high", "weak_size": "high", "rotation_overdue": "high", "approved": "informational"}


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _assess(item: dict) -> dict:
    kind = str(item.get("kind", "symmetric")).lower()
    alg = str(item.get("algorithm", "")).upper()
    size = item.get("key_size")
    issues: List[str] = []
    status = "approved"
    if kind == "tls":
        v = str(item.get("tls_version", "")).lower().replace("tls", "").strip() or str(item.get("tls_version", "")).lower()
        status = TLS_STATUS.get(v, "deprecated")
        if status != "approved":
            issues.append(f"TLS {item.get('tls_version')} is {status}")
    else:
        table = ASYMMETRIC if kind == "asymmetric" else SYMMETRIC
        st, minsize = table.get(alg, ("deprecated", None))
        status = st
        if st == "forbidden":
            issues.append(f"{alg} is forbidden — remove immediately")
        elif st == "deprecated":
            issues.append(f"{alg} is deprecated — migrate")
        if minsize and size is not None and int(size) < minsize:
            status = "forbidden" if st != "approved" else "weak_size"
            issues.append(f"key size {size} below minimum {minsize} for {alg}")
    # rotation
    age = item.get("key_age_days"); period = item.get("rotation_period_days")
    if age is not None and period is not None and int(age) > int(period):
        issues.append(f"key overdue for rotation ({age}d > {period}d)")
        if status == "approved":
            status = "rotation_overdue"
    sev = SEV.get(status, "medium" if issues else "informational")
    return {"id": item.get("id"), "algorithm": alg or item.get("tls_version"), "kind": kind, "status": status, "severity": sev, "issues": issues, "usage": item.get("usage")}


def analyse(t: dict, input_path: Optional[str] = None) -> Dict[str, Any]:
    rel = None
    if input_path:
        try:
            rel = Path(input_path).resolve().relative_to(REPO_ROOT).as_posix()
        except ValueError:
            rel = None
    items = [i for i in (t.get("items") or []) if isinstance(i, dict)]
    if not t or not items:
        return {"agent_slug": SLUG, "intent_type": "analyze", "action": "Supply a crypto inventory; nothing was provided.",
                "rationale": "No inventory supplied; no assessment.", "confidence": 0.30, "severity": "informational",
                "key_findings": ["No crypto inventory supplied"], "evidence_references": [{"source": "local://identity-access/cryptography-key-management/SKILL.md", "ref": "algorithm tables (not applied)"}],
                "next_agents": [], "human_approval_required": False, "timestamp_utc": _now(), "items": [], "_exit": 0}
    rank = {"critical": 4, "high": 3, "medium": 2, "low": 1, "informational": 0}
    scored = sorted((_assess(i) for i in items), key=lambda r: -rank[r["severity"]])
    forbidden = [r for r in scored if r["status"] == "forbidden"]
    deprecated = [r for r in scored if r["status"] == "deprecated"]
    severity = scored[0]["severity"] if scored else "informational"
    exit_code = 2 if forbidden else 1 if deprecated or any(r["status"] == "rotation_overdue" for r in scored) else 0
    action = (f"Remove {len(forbidden)} forbidden algorithm(s) immediately: {', '.join(r['id'] or r['algorithm'] for r in forbidden[:3])}." if forbidden else
              f"Migrate {len(deprecated)} deprecated item(s)." if deprecated else
              "Cryptographic inventory is within the approved tables.")
    key = [f"{len(items)} crypto item(s): {len(forbidden)} forbidden, {len(deprecated)} deprecated, {sum(1 for r in scored if r['status']=='approved')} approved"]
    key += [f"{r['severity']} {r['id']} ({r['algorithm']}, {r['kind']}): {'; '.join(r['issues']) or 'approved'}" for r in scored[:6]]
    evidence = [{"source": f"local://{rel}" if rel else "local://identity-access/cryptography-key-management/SKILL.md", "ref": "crypto inventory"},
                {"source": "local://identity-access/cryptography-key-management/SKILL.md", "ref": "approved/deprecated/forbidden algorithm and TLS tables"}]
    return {"agent_slug": SLUG, "intent_type": "analyze", "action": action,
            "rationale": ("Each item classified against the SKILL.md symmetric, asymmetric and TLS tables; a forbidden algorithm or a key below the minimum size is critical, "
                          "deprecated algorithms and overdue rotations are high. Read-only."),
            "confidence": 0.9, "severity": severity, "key_findings": key, "evidence_references": evidence,
            "next_agents": ["findings-tracker"] if (forbidden or deprecated) else [], "human_approval_required": False, "timestamp_utc": _now(),
            "items": scored, "mitre_ttps": ["T1552.004"] if forbidden else [], "affected_assets": [str(r["id"]) for r in scored if r["issues"]], "_exit": exit_code}


def main() -> int:
    ap = argparse.ArgumentParser(description="USAP cryptography-key-management")
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
    print(json.dumps(p, indent=2) if args.output == "json" else f"cryptography-key-management: severity={p['severity']}")
    return code


if __name__ == "__main__":
    raise SystemExit(main())
