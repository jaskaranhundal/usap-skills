#!/usr/bin/env python3
"""supply-chain-risk_tool.py

Scores a software bill of materials against the SKILL.md risk model and emits
the USAP 11-field payload. Implements the Dependency Risk Scoring table, the
Supply Chain Attack Taxonomy (dependency confusion, typosquatting, maintainer
takeover, build pipeline compromise), the License Risk table and the SLSA
Build Pipeline Security Checklist.

  python3 supply-chain-risk_tool.py --input sbom.json --output json
  cat sbom.json | python3 supply-chain-risk_tool.py --output json
  python3 supply-chain-risk_tool.py --output json      # no input: informational, exit 0

Input (see tests/fixtures/supply-chain-risk-input.json):
  project, ecosystem, sbom_format, internal_package_names[],
  components[]: name, version, direct, license, registry (public|private),
      cves[]: {id, cvss, fixed_version, kev}, last_release_days, maintainers,
      new_maintainer_days, binary_added, obfuscated_code, typosquat_of,
  build: slsa_level, artifacts_signed, provenance_attestation, lockfile_committed,
      versions_pinned, private_registry, mfa_enforced, immutable_logs, hermetic

Exit codes: 0 nothing above medium; 1 high findings; 2 critical findings or a
block recommendation. Never touches a registry or a system. Stdlib only.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

SLUG = "supply-chain-risk"
HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parents[2]

# SKILL.md "Dependency Risk Scoring" weights (percent points).
W_CVE, W_KEV, W_ABANDONED, W_SINGLE_MAINTAINER, W_NEW_MAINTAINER = 40, 60, 20, 15, 25
ABANDONED_DAYS, NEW_MAINTAINER_DAYS = 730, 180

# SKILL.md "License Risk": anything not in the safe set needs review; copyleft is a violation for commercial use.
SAFE_LICENSES = {"MIT", "BSD-2-CLAUSE", "BSD-3-CLAUSE", "APACHE-2.0", "ISC", "0BSD", "UNLICENSE", "CC0-1.0"}
COPYLEFT = {"GPL-2.0", "GPL-3.0", "AGPL-3.0", "SSPL-1.0", "GPL-2.0-ONLY", "GPL-3.0-ONLY", "AGPL-3.0-ONLY"}
CONDITIONAL = {"LGPL-2.1", "LGPL-3.0", "MPL-2.0", "EPL-2.0"}

# SKILL.md "Build Pipeline Security Checklist" (8 items) -> build_integrity_score.
CHECKLIST = [
    ("mfa_enforced", "MFA required for all pipeline access"),
    ("artifacts_signed", "Build artifacts cryptographically signed (Sigstore/cosign)"),
    ("provenance_attestation", "Provenance attestation (SLSA 2+)"),
    ("immutable_logs", "Build logs immutable and auditable"),
    ("versions_pinned", "Dependency pinning (exact versions, not ranges)"),
    ("lockfile_committed", "Lock files committed to source control"),
    ("private_registry", "Private registry with allowlist"),
    ("hermetic", "No direct internet access from build environment"),
]

SEV_RANK = {"critical": 4, "high": 3, "medium": 2, "low": 1, "informational": 0}
NVD = "https://nvd.nist.gov/vuln/detail/"
KEV_URL = "https://www.cisa.gov/known-exploited-vulnerabilities-catalog"
SLSA_URL = "https://slsa.dev/spec/v1.0/levels"


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _norm_license(lic: Optional[str]) -> str:
    return (lic or "").strip().upper()


def _bare_name(name: str) -> str:
    """'@acme/auth-core' -> 'auth-core'; 'acme-auth-core' unchanged."""
    return name.split("/", 1)[1] if name.startswith("@") and "/" in name else name


def score_component(c: dict, internal_names: set) -> dict:
    """Apply the risk table to one component. Returns a high_risk_packages entry or None-like dict."""
    name, version = str(c.get("name", "?")), str(c.get("version", "?"))
    factors: List[str] = []
    score = 0
    critical_flags: List[str] = []
    cves = [x for x in (c.get("cves") or []) if isinstance(x, dict) and x.get("id")]
    kev = [x for x in cves if x.get("kev")]

    if cves:
        score += W_CVE; factors.append(f"known CVE (+{W_CVE})")
    if kev:
        score += W_KEV; factors.append(f"CISA KEV (+{W_KEV})")
    if int(c.get("last_release_days") or 0) > ABANDONED_DAYS:
        score += W_ABANDONED; factors.append(f"abandoned >{ABANDONED_DAYS // 365}y (+{W_ABANDONED})")
    if int(c.get("maintainers") or 0) == 1:
        score += W_SINGLE_MAINTAINER; factors.append(f"single maintainer (+{W_SINGLE_MAINTAINER})")
    nmd = c.get("new_maintainer_days")
    if nmd is not None and int(nmd) < NEW_MAINTAINER_DAYS:
        score += W_NEW_MAINTAINER; factors.append(f"new maintainer <{NEW_MAINTAINER_DAYS}d (+{W_NEW_MAINTAINER})")
    if c.get("binary_added"):
        critical_flags.append("unexplained binary added in release")
    if c.get("obfuscated_code"):
        critical_flags.append("obfuscated code added in new version")
    if c.get("typosquat_of"):
        critical_flags.append(f"typosquat of {c['typosquat_of']}")
    # Dependency confusion: a public-registry package carrying an internal package's bare name.
    if str(c.get("registry", "public")).lower() == "public" and _bare_name(name) in internal_names:
        critical_flags.append("dependency confusion: public package shadows an internal package name")

    lic = _norm_license(c.get("license"))
    license_issue = None
    if lic in COPYLEFT:
        license_issue = f"{lic}: copyleft, commercial-use violation"
    elif lic in CONDITIONAL:
        license_issue = f"{lic}: conditional, legal review"
    elif lic and lic not in SAFE_LICENSES:
        license_issue = f"{lic}: custom or unrecognised licence, legal review"

    score = min(100, score)
    if critical_flags or kev:
        severity = "critical"
    elif score >= 60:
        severity = "high"
    elif score >= 30 or license_issue:
        severity = "medium"
    elif score > 0:
        severity = "low"
    else:
        severity = "informational"

    if critical_flags:
        risk_type, action = ("typosquatting" if any("typosquat" in f for f in critical_flags) else "takeover"), "block"
        if any("dependency confusion" in f for f in critical_flags):
            risk_type = "dependency_confusion"
    elif kev:
        risk_type, action = "cve", "block"
    elif cves:
        risk_type = "cve"
        action = "update" if any(x.get("fixed_version") for x in cves) else "replace"
    elif int(c.get("last_release_days") or 0) > ABANDONED_DAYS:
        risk_type, action = "abandoned", "replace"
    elif license_issue and lic in COPYLEFT:
        risk_type, action = "license", "review"
    elif score > 0 or license_issue:
        risk_type, action = ("license" if license_issue and score == 0 else "maintainer"), "review"
    else:
        risk_type, action = "none", "none"

    return {
        "package": name, "version": version, "direct": bool(c.get("direct", False)),
        "risk_type": risk_type, "severity": severity, "risk_score": score,
        "cve_id": kev[0]["id"] if kev else (cves[0]["id"] if cves else None),
        "cve_ids": [x["id"] for x in cves], "kev": bool(kev),
        "factors": factors + critical_flags, "license_issue": license_issue, "action": action,
    }


def analyse(target: dict, input_path: Optional[str] = None) -> Dict[str, Any]:
    components = [c for c in (target.get("components") or []) if isinstance(c, dict)]
    internal = {_bare_name(n) for n in (target.get("internal_package_names") or [])}
    build = target.get("build") or {}
    project = target.get("project", "unknown-project")

    scored = [score_component(c, internal) for c in components]
    risky = sorted([s for s in scored if s["severity"] != "informational"],
                   key=lambda s: (-SEV_RANK[s["severity"]], -s["risk_score"], s["package"]))
    direct = sum(1 for c in components if c.get("direct"))
    with_cve = sum(1 for s in scored if s["cve_ids"])
    kev_count = sum(1 for s in scored if s["kev"])
    abandoned = sum(1 for c in components if int(c.get("last_release_days") or 0) > ABANDONED_DAYS)
    license_violations = [f"{s['package']}@{s['version']}: {s['license_issue']}" for s in scored if s["license_issue"]]

    passed = [label for key, label in CHECKLIST if build.get(key)]
    failed = [label for key, label in CHECKLIST if not build.get(key)]
    build_score = round(len(passed) / len(CHECKLIST) * 100)
    slsa = int(build.get("slsa_level") or 0)

    blocking = [s for s in risky if s["action"] == "block"]
    top = risky[0]["severity"] if risky else "informational"
    if slsa < 2 and SEV_RANK[top] < SEV_RANK["high"] and components:
        top = "high"  # SKILL.md: SLSA below 2 leaves signed artifacts unverifiable
    severity = top

    if blocking:
        intent, approval = "block", True
        action = (f"Block {len(blocking)} package(s) in registry policy before the next build: "
                  + ", ".join(f"{b['package']}@{b['version']} ({b['risk_type']})" for b in blocking[:4])
                  + ". Policy change; requires security_director approval.")
    elif risky:
        intent, approval = "analyze", False
        action = ("Update or replace the flagged dependencies in severity order; "
                  f"top item {risky[0]['package']}@{risky[0]['version']} ({risky[0]['action']}).")
    else:
        intent, approval = "analyze", False
        action = "No dependency risk above informational; keep the SBOM current and re-run on the next lock-file change."
    if failed:
        action += f" Close the build-integrity gaps: {'; '.join(failed[:3])}" + ("." if len(failed) <= 3 else f" and {len(failed) - 3} more.")

    findings = [
        f"{len(components)} component(s): {direct} direct, {len(components) - direct} transitive; "
        f"{with_cve} with a known CVE, {kev_count} in CISA KEV, {abandoned} abandoned",
    ]
    for s in risky[:5]:
        findings.append(f"{s['package']}@{s['version']} {s['severity']} ({s['risk_type']}, score {s['risk_score']}): "
                        + "; ".join(s["factors"] or [s["license_issue"] or "policy"]) + f" -> {s['action']}")
    findings.append(f"Build integrity {build_score}/100 ({len(passed)}/{len(CHECKLIST)} checklist items), SLSA level {slsa}"
                    + ("; below SLSA 2, artifact provenance cannot be verified" if slsa < 2 else ""))
    if license_violations:
        findings.append(f"{len(license_violations)} licence issue(s): " + "; ".join(license_violations[:3]))

    # Evidence: every CVE to NVD, KEV to the CISA catalogue, SLSA to the spec, the SBOM itself when in-repo.
    evidence: List[dict] = []
    for s in risky:
        for cid in s["cve_ids"][:2]:
            evidence.append({"source": f"{NVD}{cid}", "ref": f"{s['package']}@{s['version']}", "quote": f"{cid}" + (" (CISA KEV)" if s["kev"] else "")})
    if kev_count:
        evidence.append({"source": KEV_URL, "ref": "CISA Known Exploited Vulnerabilities catalogue", "quote": f"{kev_count} component(s) listed"})
    if components:
        evidence.append({"source": SLSA_URL, "ref": f"SLSA level {slsa} declared for {project}"})
    rel = None
    if input_path:
        try:
            rel = Path(input_path).resolve().relative_to(REPO_ROOT).as_posix()
        except ValueError:
            rel = None
    evidence.append({"source": f"local://{rel}" if rel else "local://appsec-devsecops/supply-chain-risk/SKILL.md",
                     "ref": "SBOM descriptor analysed" if rel else "risk model applied (no in-repo input)"})
    if rel:
        evidence.append({"source": "local://appsec-devsecops/supply-chain-risk/SKILL.md", "ref": "Dependency Risk Scoring, License Risk and SLSA checklist tables"})

    # Confidence: named factors, capped so a long list cannot inflate it.
    conf, conf_factors = 0.55, ["base 0.55 for a declared SBOM"]
    if build.get("lockfile_committed"):
        conf += 0.10; conf_factors.append("lock file committed (+0.10)")
    if with_cve:
        conf += 0.15; conf_factors.append("CVE data supplied per component (+0.15)")
    if any(c.get("last_release_days") is not None for c in components):
        conf += 0.07; conf_factors.append("maintenance metadata supplied (+0.07)")
    if not components:
        conf = 0.30; conf_factors = ["no components supplied (0.30)"]
    conf = round(min(conf, 0.92), 2)

    next_agents = []
    if with_cve:
        next_agents.append("vulnerability-management")
    if slsa < 2 or not build.get("artifacts_signed"):
        next_agents.append("build-integrity")
    if risky:
        next_agents.append("findings-tracker")

    mitre = sorted({"T1195.001" if s["risk_type"] in ("typosquatting", "dependency_confusion") else "T1195.002"
                    for s in risky if s["risk_type"] in ("typosquatting", "dependency_confusion", "takeover")})
    if slsa < 2 and components:
        mitre.append("T1195.002")
    mitre = sorted(set(mitre))

    payload = {
        "agent_slug": SLUG,
        "intent_type": intent,
        "action": action,
        "rationale": (
            f"{project} ({target.get('ecosystem', 'unknown')} {target.get('sbom_format', 'sbom')}): risk scored per component with the "
            f"SKILL.md weights (CVE +{W_CVE}, KEV +{W_KEV}, abandoned +{W_ABANDONED}, single maintainer +{W_SINGLE_MAINTAINER}, "
            f"new maintainer +{W_NEW_MAINTAINER}; binary, obfuscation, typosquat and dependency confusion are immediate blocks). "
            f"{len(blocking)} block recommendation(s), {len(risky)} package(s) above informational. "
            f"Build integrity {build_score}/100 at SLSA {slsa}. Confidence factors: {', '.join(conf_factors)}."
        ),
        "confidence": conf,
        "severity": severity,
        "key_findings": findings,
        "evidence_references": evidence,
        "next_agents": next_agents,
        "human_approval_required": approval,
        "timestamp_utc": _now(),
        "sbom_analysis": {
            "total_components": len(components), "direct_dependencies": direct,
            "transitive_dependencies": len(components) - direct, "components_with_cve": with_cve,
            "cisa_kev_components": kev_count, "abandoned_packages": abandoned,
            "license_violations": license_violations,
        },
        "high_risk_packages": [
            {k: s[k] for k in ("package", "version", "direct", "risk_type", "severity", "risk_score", "cve_id", "action", "factors")}
            for s in risky
        ],
        "build_integrity_score": build_score,
        "build_integrity_gaps": failed,
        "slsa_level": slsa,
        "blocking_required": bool(blocking),
        "requires_approval": approval,
        "approver_roles": ["security_director"] if approval else [],
        "mutating_category": "policy_change" if approval else None,
        "mitre_ttps": mitre,
        "affected_assets": [project],
    }
    return payload


def _exit_code(payload: dict) -> int:
    if payload["blocking_required"] or payload["severity"] == "critical":
        return 2
    if payload["severity"] == "high":
        return 1
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="USAP supply-chain-risk: score an SBOM descriptor")
    ap.add_argument("--input", help="SBOM descriptor JSON (see module docstring)")
    ap.add_argument("--output", choices=["json", "text"], default="text")
    args = ap.parse_args()

    if args.input:
        try:
            target = json.loads(Path(args.input).read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            print(f"error: cannot read --input: {exc}", file=sys.stderr)
            return 2
    else:
        raw = "" if sys.stdin.isatty() else sys.stdin.read()
        try:
            target = json.loads(raw) if raw.strip() else {}
        except json.JSONDecodeError:
            target = {}

    payload = analyse(target, args.input)
    if args.output == "json":
        print(json.dumps(payload, indent=2))
    else:
        print(f"supply-chain-risk: severity={payload['severity']} intent={payload['intent_type']} blocking={payload['blocking_required']}")
        for f in payload["key_findings"]:
            print(f"  - {f}")
        print(f"  action: {payload['action']}")
    return _exit_code(payload)


if __name__ == "__main__":
    raise SystemExit(main())
