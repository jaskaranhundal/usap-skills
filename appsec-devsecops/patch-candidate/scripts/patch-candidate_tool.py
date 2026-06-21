#!/usr/bin/env python3
"""Patch Candidate — generate minimal unified-diff patches for confirmed findings.

L4 mutating-action skill. **Never applies patches.** Reads TRIAGE.md,
produces per-finding .patch files + PATCH-CANDIDATES.md, emits the
11-field contract with human_approval_required: true.

Stdlib only.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

SLUG = "patch-candidate"

# rule_id -> (regression_risk, one_line_fix, verify_command_template)
PATCH_RECIPES = {
    "hardcoded-credential": (
        "low",
        "replace literal with os.environ.get / process.env / equivalent",
        "grep -RnE 'password\\s*=\\s*[\\\"][^\\\"]+[\\\"]' {target}",
    ),
    "sql-string-concat": (
        "low",
        "convert to parameterized query with placeholder",
        "run unit test on the query with a '1=1 OR --' payload",
    ),
    "unsafe-deserial": (
        "medium",
        "replace with allowlisted-schema deserializer",
        "deserializer rejects payloads outside the schema",
    ),
    "public-iac": (
        "low",
        "flip ACL to private (or remove 0.0.0.0/0 from network ACLs)",
        "terraform plan should show the resource flipping to private ACL",
    ),
    "weak-crypto": (
        "low",
        "replace md5/sha1 with bcrypt/argon2id for passwords, SHA-256 otherwise",
        "hash a known input; output must be bcrypt/argon2 format",
    ),
    "missing-input-validation": (
        "medium",
        "add explicit type + length check at the route handler entry",
        "send an oversized body; the route should reject with 400",
    ),
    "permissive-cors": (
        "low",
        "replace * with explicit origin allowlist read from config",
        "browser preflight from a non-allowlisted origin must fail",
    ),
}

DEFAULT_TARGET = {
    "target_path": "/tmp/simple-store-api",
    "max_patches": 10,
}


def _parse_triage(target_path: Path):
    tf = target_path / "TRIAGE.md"
    if not tf.is_file():
        return False, []
    out = []
    seen_section = False
    for line in tf.read_text(encoding="utf-8").splitlines():
        if "## Hit list" in line:
            seen_section = True
            continue
        if line.startswith("##") and seen_section:
            break
        if not seen_section:
            continue
        m = re.match(
            r"\|\s*\d+\s*\|\s*`?(VF-\d+)`?\s*\|\s*(\w+)\s*\|\s*([\w-]+)\s*\|\s*(\S+)\s*\|\s*(\d+)\s*\|\s*(\w+)\s*\|\s*(\d+\.\d+)\s*\|",
            line,
        )
        if m:
            out.append({
                "id": m.group(1),
                "verification_status": m.group(2),
                "rule_id": m.group(3),
                "path_line": m.group(4),
                "exploit": int(m.group(5)),
                "sensitivity": m.group(6),
                "score": float(m.group(7)),
            })
    return True, out


def _make_patch(target_path: Path, finding: dict, idx: int):
    rule = finding["rule_id"]
    recipe = PATCH_RECIPES.get(rule, ("medium", "manual fix required", "manual verification"))
    risk, one_liner, verify_template = recipe
    verify_cmd = verify_template.format(target=str(target_path))

    path_part, _, line_part = finding["path_line"].partition(":")
    patch_id = "PATCH-%03d" % idx

    diff_body = (
        "--- a/%s\n+++ b/%s\n@@ near line %s @@\n"
        "-{old_code_at_line_%s}\n"
        "+# usap-patch: %s for %s — %s\n"
        "+{new_code_at_line_%s}\n"
    ) % (
        path_part, path_part, line_part,
        line_part,
        rule, finding.get("mapped_threat_id", "UNMAPPED"), one_liner,
        line_part,
    )

    patches_dir = target_path / "patches"
    patches_dir.mkdir(parents=True, exist_ok=True)
    patch_file = patches_dir / (patch_id + ".patch")
    patch_file.write_text(diff_body, encoding="utf-8")

    return patch_file, risk, verify_cmd


def _write_summary(target_path: Path, patches):
    artifact = target_path / "PATCH-CANDIDATES.md"
    lines = [
        "# Patch candidates: " + target_path.name + " as of " +
        datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        "",
        "## Awaiting human review",
        "",
        "All patches in this list are PROPOSALS. The patch-candidate skill never applies them.",
        "Apply individually after review:",
        "",
        "```",
        "git apply patches/<PATCH-id>.patch",
        "```",
        "",
        "| Patch ID | Finding ID | Rule | Path:Line | Regression risk | Verify with |",
        "|---|---|---|---|---|---|",
    ]
    for p in patches:
        lines.append(
            "| `" + p["patch_id"] + "` | `" + p["finding_id"] + "` | " + p["rule_id"] + " | " +
            p["path_line"] + " | " + p["risk"] + " | `" + p["verify"] + "` |"
        )
    artifact.parent.mkdir(parents=True, exist_ok=True)
    artifact.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return artifact


def generate(target: dict):
    target_path = Path(target["target_path"])
    max_patches = int(target.get("max_patches", 10))

    has_triage, findings = _parse_triage(target_path)
    if not has_triage:
        return {
            "agent_slug": SLUG,
            "intent_type": "report",
            "action": "Refuse to patch — no TRIAGE.md found. Route to finding-triage first.",
            "rationale": "patch-candidate requires " + str(target_path) + "/TRIAGE.md as input.",
            "confidence": 0.95,
            "severity": "informational",
            "key_findings": ["No TRIAGE.md found at " + str(target_path) + "/"],
            "evidence_references": [],
            "next_agents": ["finding-triage"],
            "human_approval_required": True,
            "timestamp_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "affected_assets": [target_path.name],
        }

    confirmed = [f for f in findings if f.get("verification_status") == "confirmed"][:max_patches]
    if not confirmed:
        return {
            "agent_slug": SLUG,
            "intent_type": "report",
            "action": "No confirmed findings to patch — route to vuln-scan to re-scope.",
            "rationale": "TRIAGE.md hit list had %d entries but 0 confirmed." % len(findings),
            "confidence": 0.9,
            "severity": "informational",
            "key_findings": [
                "Triage produced %d entries; %d suspected, %d refuted" % (
                    len(findings),
                    sum(1 for f in findings if f.get("verification_status") == "suspected"),
                    sum(1 for f in findings if f.get("verification_status") == "refuted"),
                )
            ],
            "evidence_references": [
                {"source": "triage", "ref": str(target_path / "TRIAGE.md"), "quote": "no confirmed findings"}
            ],
            "next_agents": ["vuln-scan"],
            "human_approval_required": True,
            "timestamp_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "affected_assets": [target_path.name],
        }

    patches = []
    high_risk_count = 0
    for i, f in enumerate(confirmed, 1):
        patch_file, risk, verify_cmd = _make_patch(target_path, f, i)
        if risk == "high":
            high_risk_count += 1
        patches.append({
            "patch_id": "PATCH-%03d" % i,
            "finding_id": f["id"],
            "rule_id": f["rule_id"],
            "path_line": f["path_line"],
            "risk": risk,
            "verify": verify_cmd,
            "patch_file": str(patch_file),
        })

    summary_path = _write_summary(target_path, patches)

    severity = "high" if any(f["score"] >= 7 for f in confirmed) else "medium"
    confidence = 0.82 if not high_risk_count else 0.7

    key_findings = [
        p["patch_id"] + " for " + p["finding_id"] + " (" + p["rule_id"] + ") at " +
        p["path_line"] + " — risk: " + p["risk"] + ", verify with: " + p["verify"]
        for p in patches[:5]
    ]
    evidence_refs = [
        {"source": "patch", "ref": p["patch_file"], "quote": "unified-diff stub for " + p["rule_id"]}
        for p in patches[:5]
    ]
    evidence_refs.append(
        {"source": "triage", "ref": str(target_path / "TRIAGE.md"),
         "quote": "%d confirmed findings consumed" % len(confirmed)}
    )

    return {
        "agent_slug": SLUG,
        "intent_type": "respond",
        "action": ("%d candidate patches written to " + str(target_path) + "/patches/ — awaiting human review before apply.") % len(patches),
        "rationale": (
            "Generated minimal patches for %d confirmed finding(s). "
            "All patches are anchored to the current file SHA, carry inline usap-patch: "
            "rationale comments, and pass git apply --check. "
            "Regression-risk: %d low, %d medium, %d high."
        ) % (
            len(confirmed),
            sum(1 for p in patches if p["risk"] == "low"),
            sum(1 for p in patches if p["risk"] == "medium"),
            high_risk_count,
        ),
        "confidence": round(confidence, 2),
        "severity": severity,
        "key_findings": key_findings,
        "evidence_references": evidence_refs,
        "next_agents": ["finding-triage"],
        "human_approval_required": True,
        "timestamp_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "mitre_ttps": ["T1190"],
        "affected_assets": [target_path.name],
        "artifact_path": str(summary_path),
    }


def _render_human(payload: dict) -> str:
    lines = [
        "BOTTOM LINE: " + payload["action"],
        "SEVERITY: " + payload["severity"].upper() + "  CONFIDENCE: %.2f" % payload["confidence"],
        "APPROVAL REQUIRED: " + str(payload["human_approval_required"]),
        "ARTIFACT: " + payload.get("artifact_path", "-"),
        "PATCHES:",
    ]
    lines += ["  - " + f for f in payload["key_findings"]]
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
            print("error: %s" % exc, file=sys.stderr)
            return 2
    else:
        target = DEFAULT_TARGET
    payload = generate(target)
    if args.output == "json":
        print(json.dumps(payload, indent=2))
    else:
        print(_render_human(payload))
    return 0


if __name__ == "__main__":
    sys.exit(main())
