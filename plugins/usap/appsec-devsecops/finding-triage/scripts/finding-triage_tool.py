#!/usr/bin/env python3
"""Finding Triage — verify, dedupe, rank.

Reads VULN-FINDINGS.json + (optional) prior TRIAGE.md, scores findings,
writes <target>/TRIAGE.md, emits the 11-field contract payload.

Stdlib only.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

SLUG = "finding-triage"

# rule_id -> default exploitability score (1..10)
EXPLOITABILITY = {
    "hardcoded-credential": 9,
    "sql-string-concat": 8,
    "unsafe-deserial": 9,
    "public-iac": 7,
    "weak-crypto": 8,
    "missing-input-validation": 6,
    "permissive-cors": 4,
}

IMPACT_MULTIPLIER = {
    "public": 0.4,
    "internal": 0.7,
    "confidential": 1.0,
    "regulated": 1.3,
}

DEFAULT_TARGET = {
    "target_path": "/tmp/simple-store-api",
    "top_n": 10,
    "data_sensitivity": "confidential",
}


def _load_findings(target_path: Path) -> tuple[bool, list[dict]]:
    vf = target_path / "VULN-FINDINGS.json"
    if not vf.is_file():
        return False, []
    try:
        payload = json.loads(vf.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return False, []
    return True, payload.get("findings", []) or []


def _load_prior_triage(target_path: Path) -> dict[tuple, str]:
    tf = target_path / "TRIAGE.md"
    if not tf.is_file():
        return {}
    out: dict[tuple, str] = {}
    for line in tf.read_text(encoding="utf-8").splitlines():
        m = re.match(
            r"\|\s*\d+\s*\|\s*`?(VF-\d+)`?\s*\|\s*(\w+)\s*\|\s*(\S+)\s*\|\s*(\S+)\s*\|",
            line,
        )
        if m:
            vid, status, rule_id, path_line = m.group(1), m.group(2), m.group(3), m.group(4)
            out[(rule_id, path_line)] = status
    return out


def _verify(f: dict, target_path: Path) -> str:
    """Return verification_status."""
    file_path = target_path / f.get("path", "")
    if not file_path.exists():
        return "needs-evidence"
    try:
        content = file_path.read_text(encoding="utf-8", errors="ignore").splitlines()
    except OSError:
        return "needs-evidence"
    line_no = int(f.get("line", 0))
    if 1 <= line_no <= len(content):
        # Re-check evidence_quote against the same line.
        if f.get("evidence_quote", "").strip() and \
           any(part in content[line_no - 1] for part in f["evidence_quote"].split() if len(part) > 3):
            return "confirmed"
        return "suspected"
    return "needs-evidence"


def _score(f: dict, sensitivity: str) -> float:
    exp = EXPLOITABILITY.get(f.get("rule_id", ""), 5)
    mult = IMPACT_MULTIPLIER.get(sensitivity, 1.0)
    return round(exp * mult, 1)


def _write_artifact(target_path: Path, ranked: list[dict], refuted: list[dict], carried: list[dict]) -> Path:
    artifact = target_path / "TRIAGE.md"
    lines = [
        f"# Triage: {target_path.name} as of "
        f"{datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}",
        "",
        "## Hit list (ranked)",
        "",
        "| # | Finding ID | Verification | Rule | Path:Line | Exploit | Impact tier | Score | Next |",
        "|---|---|---|---|---|---|---|---|---|",
    ]
    for i, f in enumerate(ranked, 1):
        lines.append(
            f"| {i} | `{f['id']}` | {f['verification_status']} | "
            f"{f['rule_id']} | {f['path']}:{f['line']} | "
            f"{EXPLOITABILITY.get(f['rule_id'], 5)} | "
            f"{f.get('sensitivity', 'internal')} | {f['score']:.1f} | "
            f"`patch-candidate` |"
        )
    if refuted:
        lines += ["", "## Refuted (false positives)", "", "| Finding ID | Reason |", "|---|---|"]
        for f in refuted:
            lines.append(f"| `{f['id']}` | {f.get('refute_reason','unspecified')} |")
    if carried:
        lines += [
            "", "## Carried over from prior triage", "",
            "| Finding ID | Prior status | Current status |",
            "|---|---|---|",
        ]
        for f in carried:
            lines.append(
                f"| `{f['id']}` | {f.get('prior_status','-')} | {f.get('verification_status','-')} |"
            )
    artifact.parent.mkdir(parents=True, exist_ok=True)
    artifact.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return artifact


def triage(target: dict) -> dict:
    target_path = Path(target["target_path"])
    sensitivity = target.get("data_sensitivity", "internal")
    top_n = int(target.get("top_n", 10))

    has_findings, raw = _load_findings(target_path)
    if not has_findings:
        return {
            "agent_slug": SLUG,
            "intent_type": "report",
            "action": "Refuse to triage — no VULN-FINDINGS.json found. Route to vuln-scan first.",
            "rationale": f"finding-triage requires {target_path}/VULN-FINDINGS.json as input.",
            "confidence": 0.95,
            "severity": "informational",
            "key_findings": [f"No VULN-FINDINGS.json found at {target_path}/"],
            "evidence_references": [],
            "next_agents": ["vuln-scan"],
            "human_approval_required": False,
            "timestamp_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "affected_assets": [target_path.name],
        }

    prior = _load_prior_triage(target_path)
    ranked, refuted, carried = [], [], []
    for f in raw:
        verification = _verify(f, target_path)
        # Carry prior status forward when present.
        key = (f.get("rule_id", ""), f"{f.get('path','')}:{f.get('line','')}")
        if key in prior:
            prior_status = prior[key]
            if prior_status == "refuted":
                verification = "refuted"
            carried.append({**f, "prior_status": prior_status, "verification_status": verification})
        f["verification_status"] = verification
        f["sensitivity"] = sensitivity
        f["score"] = _score(f, sensitivity)
        if verification == "refuted":
            refuted.append(f)
        else:
            ranked.append(f)
    ranked.sort(key=lambda f: -f["score"])
    ranked = ranked[:top_n]

    artifact_path = _write_artifact(target_path, ranked, refuted, carried)

    confirmed = [f for f in ranked if f["verification_status"] == "confirmed"]
    next_agents = ["patch-candidate"] if confirmed else ["vuln-scan"]
    severity = (
        "critical" if any(f["score"] >= 11 for f in ranked)
        else "high" if any(f["score"] >= 7 for f in ranked)
        else "medium" if ranked
        else "informational"
    )
    key_findings = [
        f"rank #{i+1}: {f['id']} {f['rule_id']} at {f['path']}:{f['line']} — "
        f"{f['verification_status'].upper()}, score {f['score']:.1f}"
        for i, f in enumerate(ranked[:5])
    ]
    for f in refuted[:2]:
        key_findings.append(
            f"{f['id']} refuted: {f.get('refute_reason','marked false positive')}"
        )
    if not key_findings:
        # Empty triage — still must satisfy the contract's min-1 key_findings rule.
        key_findings.append(
            f"No findings in VULN-FINDINGS.json — clean triage against the current rule catalog"
        )

    evidence_refs = [
        {
            "source": "scanner",
            "ref": f"{f.get('path','')}:{f.get('line','')}",
            "quote": (f.get("evidence_quote", "") or "")[:140],
        }
        for f in ranked[:5]
    ]

    return {
        "agent_slug": SLUG,
        "intent_type": "analyze" if ranked else "report",
        "action": (
            f"Hand off {len(confirmed)} confirmed finding(s) to patch-candidate; "
            f"{len(refuted)} refuted carried in TRIAGE.md."
            if confirmed
            else "No confirmed findings — re-scope via vuln-scan."
        ),
        "rationale": (
            f"Read {len(raw)} finding(s) from VULN-FINDINGS.json. "
            f"Confirmed: {sum(1 for f in ranked if f['verification_status']=='confirmed')}. "
            f"Suspected: {sum(1 for f in ranked if f['verification_status']=='suspected')}. "
            f"Refuted: {len(refuted)}. "
            f"Scoring against {sensitivity}-tier impact (×{IMPACT_MULTIPLIER.get(sensitivity, 1.0)})."
        ),
        "confidence": 0.85,
        "severity": severity,
        "key_findings": key_findings,
        "evidence_references": evidence_refs,
        "next_agents": next_agents,
        "human_approval_required": False,
        "timestamp_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "mitre_ttps": ["T1552.001", "T1190"],
        "affected_assets": [target_path.name],
        "artifact_path": str(artifact_path),
    }


def _render_human(payload: dict) -> str:
    lines = [
        "BOTTOM LINE: " + payload["action"],
        f"SEVERITY: {payload['severity'].upper()}  CONFIDENCE: {payload['confidence']:.2f}",
        f"ARTIFACT: {payload.get('artifact_path','-')}",
        "HIT LIST:",
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
    payload = triage(target)
    if args.output == "json":
        print(json.dumps(payload, indent=2))
    else:
        print(_render_human(payload))
    return 0


if __name__ == "__main__":
    sys.exit(main())
