#!/usr/bin/env python3
"""build-integrity_tool.py

Verifies build provenance against the SKILL.md SLSA levels and classifies build
pipeline anomalies against the anomaly table (severity + action). Read-only
verification; blocking a compromised artifact is a mutating action requiring
approval. Emits the USAP 11-field payload.

  python3 build-integrity_tool.py --input build.json --output json
  python3 build-integrity_tool.py --output json    # no input: informational, exit 0

Input (see tests/fixtures/build-integrity-input.json):
{artifact, slsa_level (1-4), target_slsa, anomalies[] (keys from the table)}.

Exit codes: 0 clean; 1 high; 2 critical (a block-worthy anomaly). Stdlib only.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

SLUG = "build-integrity"
HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parents[2]
# anomaly -> (severity, action, blocks)
ANOMALY = {
    "unexpected_binary": ("critical", "Block and investigate", True),
    "build_outside_window": ("high", "Verify authorization", False),
    "signing_key_off_host": ("critical", "Revoke key and open incident", True),
    "build_env_modified": ("high", "Investigate and rebuild", False),
    "dependency_hash_mismatch": ("critical", "Block and investigate", True),
    "provenance_missing": ("high", "Block until resolved", True),
    "signature_verification_failed": ("critical", "Block and open incident", True),
    "artifact_size_changed": ("medium", "Review and verify", False),
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
    if not t or (not t.get("anomalies") and t.get("slsa_level") is None):
        return {"agent_slug": SLUG, "intent_type": "detect", "action": "Supply a build descriptor; nothing was provided.",
                "rationale": "No build supplied.", "confidence": 0.30, "severity": "informational", "key_findings": ["No build supplied"],
                "evidence_references": [{"source": "local://appsec-devsecops/build-integrity/SKILL.md", "ref": "anomaly table (not applied)"}],
                "next_agents": [], "human_approval_required": False, "timestamp_utc": _now(), "findings": [], "_exit": 0}
    findings: List[dict] = []
    for a in [str(x).lower() for x in (t.get("anomalies") or [])]:
        sev, action, blocks = ANOMALY.get(a, ("medium", "Review", False))
        findings.append({"anomaly": a, "severity": sev, "action": action, "blocks": blocks})
    # SLSA gap
    slsa = t.get("slsa_level")
    target = t.get("target_slsa")
    slsa_gap = None
    try:
        if slsa is not None and target is not None and int(slsa) < int(target):
            slsa_gap = f"SLSA {slsa} below target SLSA {target}"
            findings.append({"anomaly": "slsa_below_target", "severity": "high", "action": f"Raise build to SLSA {target}", "blocks": False})
    except (TypeError, ValueError):
        pass
    findings.sort(key=lambda x: -SEV_RANK[x["severity"]])
    counts = {k: sum(1 for x in findings if x["severity"] == k) for k in SEV_RANK}
    blocking = [x for x in findings if x.get("blocks")]
    severity = findings[0]["severity"] if findings else "informational"
    exit_code = 2 if counts["critical"] else 1 if counts["high"] else 0
    artifact = t.get("artifact", "the artifact")
    action = (f"Block {artifact}: {len(blocking)} block-worthy anomaly(ies) — " + "; ".join(f"{x['anomaly']} -> {x['action']}" for x in blocking[:3])[:180] + ". Blocking requires approval." if blocking else
              f"{counts['high']} high build-integrity anomaly(ies) to verify on {artifact}." if counts["high"] else
              f"Build integrity intact for {artifact}." + (f" ({slsa_gap})" if slsa_gap else ""))
    key = [f"{artifact}: SLSA {slsa if slsa is not None else 'n/a'}; {len(findings)} anomaly(ies) ({counts['critical']} critical, {counts['high']} high); {len(blocking)} block-worthy"]
    key += [f"{x['severity']} {x['anomaly']} -> {x['action']}" for x in findings[:6]]
    evidence = [{"source": f"local://{rel}" if rel else "local://appsec-devsecops/build-integrity/SKILL.md", "ref": "build provenance and anomalies"},
                {"source": "https://slsa.dev/spec/v1.0/levels", "ref": "SLSA levels"},
                {"source": "local://appsec-devsecops/build-integrity/SKILL.md", "ref": "build anomaly table"}]
    return {"agent_slug": SLUG, "intent_type": "respond" if blocking else "detect", "action": action,
            "rationale": ("Each anomaly is scored against the SKILL.md build-anomaly table: an unexpected binary, a signing key used off its authorized host, a dependency-hash mismatch or "
                          "a failed signature verification is critical and blocks the artifact. Blocking a compromised artifact is a mutating action requiring human approval."),
            "confidence": 0.85, "severity": severity, "key_findings": key, "evidence_references": evidence,
            "next_agents": ["incident-commander"] if any(x["anomaly"] in ("signing_key_off_host", "signature_verification_failed") for x in blocking) else (["findings-tracker"] if findings else []),
            "human_approval_required": bool(blocking), "timestamp_utc": _now(),
            "findings": findings, "mitre_ttps": ["T1195.001"] if blocking else [], "affected_assets": [artifact] if t.get("artifact") else [], "_exit": exit_code}


def main() -> int:
    ap = argparse.ArgumentParser(description="USAP build-integrity")
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
    print(json.dumps(p, indent=2) if args.output == "json" else f"build-integrity: severity={p['severity']}")
    return code


if __name__ == "__main__":
    raise SystemExit(main())
