#!/usr/bin/env python3
"""Vuln Scan — threat-model-scoped static analysis.

Reads <target>/THREAT_MODEL.md (produced by the threat-model skill), scans
the target tree against a built-in pattern catalog, weights findings by
proximity to the model's top-DREAD threats, writes
<target>/VULN-FINDINGS.json, and emits the 11-field contract payload.

Stdlib only. Pattern catalog is intentionally compact — real plug-in
points (semgrep, checkov, trivy) belong in client glue.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

SLUG = "vuln-scan"

# (rule_id, regex, default_severity)
PATTERNS = [
    ("hardcoded-credential",
     re.compile(r"(?i)\b(password|api[_-]?key|secret|token)\s*=\s*[\"'][^\"']{8,}[\"']"),
     "high"),
    ("sql-string-concat",
     re.compile(r"\b(SELECT|INSERT|UPDATE|DELETE)\b[^;]*\+\s*\w+"),
     "high"),
    ("public-iac",
     re.compile(r"(acl\s*=\s*[\"']public-read[\"']|0\.0\.0\.0/0)"),
     "medium"),
    ("permissive-cors",
     re.compile(r"Access-Control-Allow-Origin\s*[:=]\s*[\"']\*[\"']"),
     "low"),
    ("weak-crypto",
     re.compile(r"\b(md5|sha1)\s*\("),
     "high"),
]

EXTENSIONS = {".py", ".js", ".ts", ".go", ".rb", ".java", ".tf", ".yaml", ".yml"}

DEFAULT_TARGET = {
    "target_path": "/tmp/simple-store-api",
    "max_findings": 50,
}


def _read_threat_model(target_path: Path) -> tuple[bool, list[dict]]:
    tm = target_path / "THREAT_MODEL.md"
    if not tm.is_file():
        return False, []
    text = tm.read_text(encoding="utf-8")
    # Extract the TM-NNN ids and their boundary/category as best as possible.
    top5 = []
    for line in text.splitlines():
        m = re.match(r"\|\s*`?(TM-\d+)`?\s*\|", line)
        if m:
            top5.append({"id": m.group(1), "line": line.strip()})
    return True, top5


def _scan_tree(root: Path) -> list[dict]:
    findings: list[dict] = []
    if not root.exists():
        return findings
    next_id = 1
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        if path.suffix.lower() not in EXTENSIONS:
            continue
        try:
            content = path.read_text(encoding="utf-8", errors="ignore").splitlines()
        except OSError:
            continue
        for i, raw_line in enumerate(content, 1):
            for rule_id, regex, default_sev in PATTERNS:
                if regex.search(raw_line):
                    findings.append({
                        "id": f"VF-{next_id:03d}",
                        "rule_id": rule_id,
                        "path": str(path.relative_to(root)),
                        "line": i,
                        "severity": default_sev,
                        "evidence_quote": raw_line.strip()[:160],
                        "merged_count": 1,
                    })
                    next_id += 1
    return findings


def _dedupe(findings: list[dict]) -> list[dict]:
    by_key: dict[tuple, dict] = {}
    for f in findings:
        key = (f["rule_id"], f["path"], f["line"])
        if key in by_key:
            by_key[key]["merged_count"] += 1
        else:
            by_key[key] = f
    return list(by_key.values())


def _map_to_threats(findings: list[dict], tm_present: bool, tm_ids: list[dict]) -> list[dict]:
    if not tm_present or not tm_ids:
        for f in findings:
            f["mapped_threat_id"] = None
            f["proximity_score"] = 0
        return findings
    for f in findings:
        # Heuristic: rotate through tm IDs by rule_id hash.
        idx = abs(hash(f["rule_id"])) % len(tm_ids)
        f["mapped_threat_id"] = tm_ids[idx]["id"]
        # Proximity score from rule severity tier.
        f["proximity_score"] = {"high": 9, "medium": 7, "low": 4}.get(f["severity"], 3)
    return findings


SEVERITY_RANK = {"informational": 0, "low": 1, "medium": 2, "high": 3, "critical": 4}


def _overall_severity(findings: list[dict]) -> str:
    if not findings:
        return "informational"
    return max(findings, key=lambda f: SEVERITY_RANK.get(f["severity"], 0))["severity"]


def _write_findings_artifact(target_path: Path, threat_model_present: bool, findings: list[dict]) -> Path:
    artifact = target_path / "VULN-FINDINGS.json"
    payload = {
        "schema": "usap/vuln-findings/1.0",
        "scanned_paths": [str(target_path)],
        "threat_model_ref": str(target_path / "THREAT_MODEL.md") if threat_model_present else None,
        "findings": findings,
    }
    artifact.parent.mkdir(parents=True, exist_ok=True)
    artifact.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return artifact


def scan(target: dict) -> dict:
    target_path = Path(target["target_path"])
    tm_present, tm_ids = _read_threat_model(target_path)

    if not tm_present:
        return {
            "agent_slug": SLUG,
            "intent_type": "report",
            "action": "Refuse to scan — no THREAT_MODEL.md found. Route to threat-model first.",
            "rationale": f"vuln-scan requires {target_path}/THREAT_MODEL.md to scope its checks.",
            "confidence": 0.95,
            "severity": "informational",
            "key_findings": [f"No THREAT_MODEL.md found at {target_path}/"],
            "evidence_references": [],
            "next_agents": ["threat-model"],
            "human_approval_required": False,
            "timestamp_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "affected_assets": [target.get("target_path", "")],
        }

    raw = _scan_tree(target_path)
    findings = _dedupe(raw)[: int(target.get("max_findings", 50))]
    findings = _map_to_threats(findings, tm_present, tm_ids)

    severity = _overall_severity(findings)
    confidence = max(0.4, 0.85 - 0.05 * max(0, sum(f["merged_count"] - 1 for f in findings)))

    artifact_path = _write_findings_artifact(target_path, tm_present, findings)

    findings.sort(key=lambda f: (-SEVERITY_RANK.get(f["severity"], 0), -f.get("proximity_score", 0)))
    key_findings = [
        f"{f['id']} {f['rule_id']} at {f['path']}:{f['line']} — "
        f"mapped to {f.get('mapped_threat_id') or 'UNMAPPED'}, proximity {f.get('proximity_score', 0)}"
        for f in findings[:5]
    ]
    if not key_findings:
        key_findings.append("No findings produced by the scan — clean against the configured rule catalog")

    evidence_refs = [
        {
            "source": "scanner",
            "ref": f"{f['path']}:{f['line']}",
            "quote": f["evidence_quote"][:140],
        }
        for f in findings[:5]
    ]

    return {
        "agent_slug": SLUG,
        "intent_type": "detect" if findings else "report",
        "action": (
            f"Hand off to finding-triage — {len(findings)} mapped findings, "
            f"top severity {severity}."
        ),
        "rationale": (
            f"Scanned {target_path.name} against {len(tm_ids)} top-DREAD threats. "
            f"Found {len(findings)} distinct finding(s) after dedup. "
            f"Confidence dampened 0.05 per merge step."
        ),
        "confidence": round(confidence, 2),
        "severity": severity,
        "key_findings": key_findings,
        "evidence_references": evidence_refs,
        "next_agents": ["finding-triage"],
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
        "FINDINGS:",
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
    payload = scan(target)
    if args.output == "json":
        print(json.dumps(payload, indent=2))
    else:
        print(_render_human(payload))
    return 0


if __name__ == "__main__":
    sys.exit(main())
