#!/usr/bin/env python3
"""Container Image Scan — classifies Trivy/Grype/Snyk findings into the USAP 11-field contract.

Reads a normalized scanner-finding descriptor (a compact JSON shape shared by
Trivy/Grype/Snyk-derived finding lists, or the built-in demo target),
classifies each finding by component type (base-image OS package /
application dependency / unexpected layer), applies the severity-to-action
table and the component-to-remediation table together, and emits the
11-field contract payload.

Stdlib only. Real scanner invocation (the trivy/grype/snyk/syft/docker-scout
binaries) is client glue — this tool consumes their normalized JSON output,
or a compact --input descriptor shaped the same way for demos and CI runs
without a scanner installed.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]

# Reproducible confidence — computed from the evidence via the shared rubric,
# not narrated. See standards/confidence-rubric.md.
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "shared" / "scripts"))
try:
    from confidence_rubric import score_confidence
except Exception:  # repo layout guarantees availability; guard for isolated runs
    def score_confidence(sources):
        return {"confidence": 0.70, "rationale": "confidence_rubric unavailable; default 0.70"}

SLUG = "container-image-scan"

SEVERITY_RANK = {"informational": 0, "low": 1, "medium": 2, "high": 3, "critical": 4}

# Action by CVSS severity (see SKILL.md "Action by CVSS Severity").
ACTION_BY_SEVERITY = {
    "critical": "block-deploy",
    "high": "fix-by-sla-window",
    "medium": "track",
    "low": "accept",
    "informational": "accept",
}

# Component type -> remediation path (see SKILL.md "Component Classification").
REMEDIATION_BY_COMPONENT = {
    "base_image_os_package": "Rebuild FROM a patched base-image tag/digest.",
    "application_dependency": "Bump the dependency to the patched version and rebuild the application layer.",
    "unexpected_layer": "Treat as a possible supply-chain implant (T1525); halt the deploy and escalate.",
}

# Built-in demo target — lets the tool run zero-config (`--output json` with
# no flags) while still exercising all three component-classification paths.
DEFAULT_TARGET = {
    "image": "registry.example.com/acme/payments-api@sha256:8f3e1c2b9a4d5e6f7c8d9e0f1a2b3c4d5e6f7089abcdef0123456789fedcba98",
    "scanner": "trivy",
    "internet_facing": True,
    "findings": [
        {
            "id": "CVE-2024-3094",
            "package": "liblzma5",
            "installed_version": "5.6.0",
            "fixed_version": "5.6.2",
            "component_type": "base_image_os_package",
            "severity": "critical",
        },
        {
            "id": "CVE-2021-44228",
            "package": "log4j-core",
            "installed_version": "2.14.1",
            "fixed_version": "2.17.1",
            "component_type": "application_dependency",
            "severity": "critical",
        },
        {
            "id": None,
            "package": "layer:sha256:9c2a1fe36b4d8095c7e2a9135f0d8b2641a9c3e708b5d2f46a1c9e307d4b8f52",
            "installed_version": None,
            "fixed_version": None,
            "component_type": "unexpected_layer",
            "severity": "critical",
        },
    ],
}


def _overall_severity(findings: list[dict]) -> str:
    if not findings:
        return "informational"
    return max(findings, key=lambda f: SEVERITY_RANK.get(f.get("severity", "informational"), 0))["severity"]


def _classify(findings: list[dict]) -> list[dict]:
    out = []
    for f in findings:
        sev = f.get("severity", "medium")
        component = f.get("component_type", "application_dependency")
        # The component classification and the severity table apply together;
        # an unexpected layer is always block-deploy regardless of severity.
        action = "block-deploy" if component == "unexpected_layer" else ACTION_BY_SEVERITY.get(sev, "track")
        remediation = REMEDIATION_BY_COMPONENT.get(component, REMEDIATION_BY_COMPONENT["application_dependency"])
        out.append({**f, "recommended_action": action, "remediation": remediation})
    return out


def _evidence_source(finding: dict, scanner: str, input_rel: str | None) -> str:
    """Resolvable evidence URI for one finding (the contract rejects bare scanner names)."""
    fid = str(finding.get("id") or "").upper()
    if fid.startswith("CVE-"):
        return f"https://nvd.nist.gov/vuln/detail/{fid}"
    if fid.startswith("GHSA-"):
        return f"https://github.com/advisories/{fid}"
    if input_rel:
        return f"local://{input_rel}"
    return f"scanner:{scanner}"


def _input_rel(input_path: str | None) -> str | None:
    if not input_path:
        return None
    try:
        return Path(input_path).resolve().relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return None


def scan(target: dict, input_path: str | None = None) -> dict:
    image = target.get("image", DEFAULT_TARGET["image"])
    scanner = target.get("scanner", "trivy")
    internet_facing = bool(target.get("internet_facing", False))
    findings = _classify(target.get("findings", []))

    severity = _overall_severity(findings)
    has_implant = any(f["component_type"] == "unexpected_layer" for f in findings)
    block = any(f["recommended_action"] == "block-deploy" for f in findings)

    # Reproducible confidence: each scanner-derived finding is a secondary-tier
    # source; capped at 3 so a long finding list doesn't inflate confidence
    # past what the evidence actually supports.
    conf_sources = [{"tier": "secondary"} for _ in findings][:3] or [{"tier": "secondary"}]
    conf_result = score_confidence(conf_sources)
    confidence = conf_result["confidence"]

    mitre_ttps: list[str] = []
    if has_implant:
        mitre_ttps.append("T1525")
    if internet_facing and any(
        f["component_type"] in ("base_image_os_package", "application_dependency") for f in findings
    ):
        mitre_ttps.append("T1190")

    key_findings = [
        f"{f['id'] or f['package']} ({f['component_type']}) severity={f['severity']} -> {f['recommended_action']}"
        for f in findings[:5]
    ]
    if not key_findings:
        key_findings.append(f"No findings returned by {scanner} for {image} — clean scan.")

    input_rel = _input_rel(input_path)
    evidence_refs = [
        {
            "source": _evidence_source(f, scanner, input_rel),
            "ref": f"{scanner}: {f.get('id') or f['package']}",
            "quote": f"{f['package']} {f.get('installed_version') or ''}".strip(),
        }
        for f in findings[:5]
    ]
    evidence_refs.append({
        "source": "local://cloud-infra/container-image-scan/SKILL.md",
        "ref": "component classification and severity-to-action tables",
    })

    next_agents = []
    if has_implant:
        next_agents.append("incident-commander")
    next_agents.append("cloud-workload-protection")

    action = (
        "Block deploy — one or more findings require remediation before this image ships."
        if block
        else f"Route findings to lifecycle tracking; top severity {severity}."
    )

    return {
        "agent_slug": SLUG,
        "intent_type": "detect",
        "action": action,
        "rationale": (
            f"Scanned {image} with {scanner}. {len(findings)} finding(s) after classification by "
            f"component type (base-image OS package / application dependency / unexpected layer). "
            f"Confidence: {conf_result['rationale']}"
        ),
        "confidence": round(confidence, 2),
        "severity": severity,
        "key_findings": key_findings,
        "evidence_references": evidence_refs,
        "next_agents": next_agents,
        "human_approval_required": False,
        "timestamp_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "mitre_ttps": mitre_ttps,
        "affected_assets": [image],
    }


def _render_table(payload: dict) -> str:
    lines = [
        "BOTTOM LINE: " + payload["action"],
        f"SEVERITY: {payload['severity'].upper()}  CONFIDENCE: {payload['confidence']:.2f}",
        "FINDINGS:",
    ]
    lines += [f"  - {f}" for f in payload["key_findings"]]
    lines.append("NEXT: " + (" -> ".join(payload["next_agents"]) or "(terminal)"))
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Container Image Scan helper")
    parser.add_argument("--input", type=str, help="Path to a JSON target descriptor (image/scanner/findings).")
    parser.add_argument("--image", type=str, help="Image reference to scan (used when --input is omitted).")
    parser.add_argument("--scanner", choices=["trivy", "grype", "snyk"], default="trivy")
    parser.add_argument("--output", choices=["json", "table"], default="json")
    args = parser.parse_args()

    if args.input:
        try:
            target = json.loads(Path(args.input).read_text(encoding="utf-8"))
        except (FileNotFoundError, json.JSONDecodeError) as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 2
    else:
        target = dict(DEFAULT_TARGET)
        if args.image:
            target["image"] = args.image
        target["scanner"] = args.scanner

    payload = scan(target, args.input)

    if args.output == "json":
        print(json.dumps(payload, indent=2))
    else:
        print(_render_table(payload))
    return 0


if __name__ == "__main__":
    sys.exit(main())
