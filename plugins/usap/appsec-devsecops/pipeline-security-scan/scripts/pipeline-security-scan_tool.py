#!/usr/bin/env python3
"""pipeline-security-scan_tool.py

Scans a parsed CI/CD pipeline configuration for the SKILL.md scan categories
(secrets in the pipeline, SAST/SCA integration gaps, artifact integrity gaps,
pipeline permissions, third-party action pinning) and emits the USAP
11-field payload.

  python3 pipeline-security-scan_tool.py --input pipeline.json --output json
  cat pipeline.json | python3 pipeline-security-scan_tool.py --output json
  python3 pipeline-security-scan_tool.py --output json     # no input: informational, exit 0

Input (see tests/fixtures/pipeline-security-scan-input.json):
  platform: github_actions|gitlab_ci|other, repo, workflow, permissions,
  triggers[], env{}, jobs[]: {name, permissions, env{}, steps[]: {name, uses, run, with{}, env{}}},
  security_stages{sast,sca,secrets_scan,artifact_signing,sbom,provenance}: {present, on[]}

Exit codes: 0 nothing above medium; 1 high findings; 2 critical (secret in the
pipeline). Secret values are never printed; only a redacted prefix. Stdlib only.
"""
from __future__ import annotations

import argparse
import json
import math
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

SLUG = "pipeline-security-scan"
HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parents[2]

# Deterministic secret detectors (subset of detection/secrets-exposure patterns; kept local so the skill stays self-contained).
SECRET_PATTERNS = [
    ("aws_access_key", re.compile(r"AKIA[0-9A-Z]{16}")),
    ("github_token", re.compile(r"gh[pousr]_[A-Za-z0-9]{36}")),
    ("stripe_live_key", re.compile(r"sk_live_[A-Za-z0-9]{24,}")),
    ("slack_token", re.compile(r"xox[baprs]-[0-9A-Za-z-]{10,}")),
    ("google_api_key", re.compile(r"AIza[0-9A-Za-z\-_]{35}")),
    ("private_key", re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----")),
    ("bearer_token", re.compile(r"(?i)bearer\s+[A-Za-z0-9\-_.=]{20,}")),
]
SECRET_VAR = re.compile(r"(?i)(secret|token|password|passwd|api[_-]?key|private[_-]?key|credential)")
PLACEHOLDER = re.compile(r"(?i)\$\{\{\s*secrets\.|\$[A-Z_]+|\$\{[A-Z_]+\}|example|placeholder|changeme|<[a-z_]+>")
SHA_PIN = re.compile(r"@[0-9a-f]{40}$")
DIGEST = re.compile(r"@sha256:[0-9a-f]{64}")
REQUIRED_STAGES = [("sast", "SAST"), ("sca", "SCA / dependency scanning"), ("secrets_scan", "secrets scanning")]
INTEGRITY_STAGES = [("artifact_signing", "artifact signing (Sigstore/cosign)"), ("sbom", "SBOM generation"), ("provenance", "provenance attestation (SLSA)")]
SEV_RANK = {"critical": 4, "high": 3, "medium": 2, "low": 1, "informational": 0}
GH_HARDENING = "https://docs.github.com/en/actions/security-for-github-actions/security-guides/security-hardening-for-github-actions"
SLSA_URL = "https://slsa.dev/spec/v1.0/requirements"


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _entropy(s: str) -> float:
    if not s:
        return 0.0
    freq: Dict[str, int] = {}
    for ch in s:
        freq[ch] = freq.get(ch, 0) + 1
    n = len(s)
    return -sum(v / n * math.log2(v / n) for v in freq.values())


def _redact(v: str) -> str:
    return v[:6] + "…" + v[-2:] if len(v) > 10 else "****"


def scan_value(where: str, key: Optional[str], value: Any) -> List[dict]:
    """Return secret findings for one string value; a placeholder reference is never a finding."""
    if not isinstance(value, str) or not value.strip():
        return []
    if PLACEHOLDER.search(value):
        return []
    hits: List[dict] = []
    for kind, rx in SECRET_PATTERNS:
        m = rx.search(value)
        if m:
            hits.append({"location": where, "variable": key, "kind": kind, "value_redacted": _redact(m.group(0)), "confidence": 0.95})
            return hits
    if key and SECRET_VAR.search(key) and len(value) >= 16 and _entropy(value) >= 3.8 and " " not in value:
        hits.append({"location": where, "variable": key, "kind": "high_entropy_assignment", "value_redacted": _redact(value), "confidence": 0.75})
    return hits


def analyse(target: dict, input_path: Optional[str] = None) -> Dict[str, Any]:
    platform = str(target.get("platform", "github_actions"))
    repo = target.get("repo", "unknown-repo")
    workflow = target.get("workflow", "pipeline")
    jobs = [j for j in (target.get("jobs") or []) if isinstance(j, dict)]
    stages = target.get("security_stages") or {}
    triggers = [str(t) for t in (target.get("triggers") or [])]
    if not jobs and not stages and not target.get("env"):
        # Nothing to scan is not a finding: report the absence and stop (exit 0).
        return {
            "agent_slug": SLUG, "intent_type": "analyze",
            "action": "Supply a parsed pipeline descriptor (jobs, env, security_stages) to scan; no content was provided.",
            "rationale": "No jobs, environment or security-stage inventory were supplied, so no scan category could be evaluated. "
                         "This is an absence of input, never a clean result.",
            "confidence": 0.30, "severity": "informational",
            "key_findings": ["No pipeline content supplied; nothing scanned"],
            "evidence_references": [{"source": "local://appsec-devsecops/pipeline-security-scan/SKILL.md", "ref": "scan categories (not applied: no input)"}],
            "next_agents": [], "human_approval_required": False, "timestamp_utc": _now(),
            "scan_results": {"secrets_found": 0, "secrets": [], "missing_security_stages": [], "stages_not_on_pull_requests": [],
                             "artifact_integrity_gaps": [], "permission_issues": [], "unpinned_actions": []},
            "mitre_ttps": [], "affected_assets": [f"{repo}:{workflow}"],
        }

    # 1. Secrets in pipeline
    secrets: List[dict] = []
    for k, v in (target.get("env") or {}).items():
        secrets += scan_value(f"{workflow} env", k, v)
    for j in jobs:
        for k, v in (j.get("env") or {}).items():
            secrets += scan_value(f"job {j.get('name')} env", k, v)
        for i, st in enumerate(j.get("steps") or []):
            loc = f"job {j.get('name')} step {i + 1}" + (f" ({st.get('name')})" if st.get("name") else "")
            for k, v in (st.get("env") or {}).items():
                secrets += scan_value(loc + " env", k, v)
            for k, v in (st.get("with") or {}).items():
                secrets += scan_value(loc + " with", k, v)
            secrets += scan_value(loc + " run", None, st.get("run"))

    # 2. SAST/SCA integration gaps
    missing: List[str] = []
    main_only: List[str] = []
    for key, label in REQUIRED_STAGES:
        s = stages.get(key) or {}
        if not s.get("present"):
            missing.append(label)
        elif s.get("on") and not any(x in ("pull_request", "merge_request", "all") for x in s.get("on")):
            main_only.append(f"{label} runs only on {', '.join(s.get('on'))}; must run on every PR")

    # 3. Artifact integrity
    integrity: List[str] = [label + " not configured" for key, label in INTEGRITY_STAGES if not (stages.get(key) or {}).get("present")]
    for j in jobs:
        for st in j.get("steps") or []:
            tags = (st.get("with") or {}).get("tags")
            if (st.get("with") or {}).get("push") and tags and not DIGEST.search(str(tags)):
                integrity.append(f"job {j.get('name')}: image pushed by mutable tag {tags} (pin by digest)")
            for img in re.findall(r"(?:docker\s+(?:pull|run)|image:\s*)([\w./-]+:[\w.-]+)", str(st.get("run") or "")):
                if ":latest" in img:
                    integrity.append(f"job {j.get('name')}: uses mutable image tag {img}")

    # 4. Permissions
    perms: List[str] = []
    top = target.get("permissions")
    if top in ("write-all", "write_all"):
        perms.append("workflow permissions: write-all")
    elif top is None and platform == "github_actions":
        perms.append("workflow permissions not set explicitly (defaults may be write)")
    for j in jobs:
        if j.get("permissions") in ("write-all", "write_all"):
            perms.append(f"job {j.get('name')} permissions: write-all")
    if target.get("token_scope") in ("admin", "repo_admin"):
        perms.append(f"pipeline token scope {target.get('token_scope')}")

    # 5. Third-party actions
    unpinned: List[str] = []
    for j in jobs:
        for st in j.get("steps") or []:
            u = st.get("uses")
            if not isinstance(u, str) or u.startswith("./") or u.startswith("docker://"):
                continue
            if not SHA_PIN.search(u):
                ref = u.split("@", 1)[1] if "@" in u else "(no ref)"
                unpinned.append(f"{u} -> {ref} is mutable; pin to a full commit SHA")

    # Severity
    if secrets:
        severity = "critical"
    elif missing or perms and any("write-all" in p for p in perms) or (unpinned and perms):
        severity = "high"
    elif unpinned or integrity or main_only or perms:
        severity = "medium"
    else:
        severity = "informational"

    actions: List[str] = []
    if secrets:
        actions.append(f"Remove {len(secrets)} hardcoded secret(s) from the pipeline and rotate them (the committed values are compromised)")
    if unpinned:
        actions.append(f"Pin {len(unpinned)} third-party action(s) to full commit SHAs")
    if missing:
        actions.append("Add " + ", ".join(missing) + " stage(s) on every PR")
    if perms:
        actions.append("Set least-privilege permissions (contents: read by default)")
    if integrity:
        actions.append("Add signing, SBOM and provenance steps and pin images by digest")
    action = ("; ".join(actions) + ".") if actions else "No pipeline finding against the SKILL.md scan categories; keep the configuration under review on every change."

    findings = [f"{platform} {workflow} in {repo}: {len(jobs)} job(s), {sum(len(j.get('steps') or []) for j in jobs)} step(s) scanned; "
                f"{len(secrets)} secret(s), {len(missing)} missing security stage(s), {len(integrity)} integrity gap(s), "
                f"{len(perms)} permission issue(s), {len(unpinned)} unpinned action(s)"]
    findings += [f"Secret ({s['kind']}) in {s['location']}" + (f" variable {s['variable']}" if s['variable'] else "") + f": {s['value_redacted']}" for s in secrets[:4]]
    findings += [f"Missing stage: {m}" for m in missing]
    findings += main_only
    findings += [f"Permissions: {p}" for p in perms[:3]]
    findings += [f"Unpinned action: {u}" for u in unpinned[:4]]
    findings += [f"Integrity: {g}" for g in integrity[:4]]

    rel = None
    if input_path:
        try:
            rel = Path(input_path).resolve().relative_to(REPO_ROOT).as_posix()
        except ValueError:
            rel = None
    src = f"local://{rel}" if rel else "local://appsec-devsecops/pipeline-security-scan/SKILL.md"
    evidence: List[dict] = [{"source": src, "ref": s["location"] + (f" ({s['variable']})" if s["variable"] else ""), "quote": f"{s['kind']} {s['value_redacted']}"} for s in secrets[:4]]
    evidence += [{"source": src, "ref": u.split(" -> ")[0], "quote": "mutable action reference"} for u in unpinned[:3]]
    if unpinned or perms:
        evidence.append({"source": GH_HARDENING, "ref": "GitHub Actions security hardening: pin actions to a full-length commit SHA; set minimal permissions"})
    if integrity:
        evidence.append({"source": SLSA_URL, "ref": "SLSA requirements: provenance, signing"})
    evidence.append({"source": "local://appsec-devsecops/pipeline-security-scan/SKILL.md", "ref": "scan categories applied"})

    conf, factors = 0.60, ["base 0.60 for a parsed pipeline"]
    if jobs:
        conf += 0.15; factors.append("job and step definitions supplied (+0.15)")
    if stages:
        conf += 0.12; factors.append("security stage inventory supplied (+0.12)")
    if secrets and all(s["confidence"] >= 0.95 for s in secrets):
        conf += 0.05; factors.append("secret matches are exact-pattern hits (+0.05)")
    if not jobs and not stages:
        conf, factors = 0.30, ["no pipeline content supplied (0.30)"]
    conf = round(min(conf, 0.93), 2)

    next_agents: List[str] = []
    if secrets:
        next_agents.append("secrets-exposure")
    if integrity:
        next_agents.append("build-integrity")
    if unpinned:
        next_agents.append("supply-chain-risk")

    mitre = sorted(set((["T1552.001"] if secrets else []) + (["T1195.002"] if unpinned or integrity else []) + (["T1078.004"] if perms else [])))
    return {
        "agent_slug": SLUG, "intent_type": "analyze", "action": action,
        "rationale": (f"Configuration scan of {workflow} ({platform}) against the SKILL.md categories: secrets in pipeline, SAST/SCA gaps, "
                      f"artifact integrity, permissions, third-party pinning. Secrets are exact-pattern or high-entropy assignments to secret-named "
                      f"variables, placeholders excluded; values are redacted. Triggers: {', '.join(triggers) or 'unknown'}. "
                      f"Confidence factors: {', '.join(factors)}."),
        "confidence": conf, "severity": severity, "key_findings": findings, "evidence_references": evidence,
        "next_agents": next_agents, "human_approval_required": False, "timestamp_utc": _now(),
        "scan_results": {"secrets_found": len(secrets), "secrets": secrets, "missing_security_stages": missing, "stages_not_on_pull_requests": main_only,
                         "artifact_integrity_gaps": integrity, "permission_issues": perms, "unpinned_actions": unpinned},
        "mitre_ttps": mitre, "affected_assets": [f"{repo}:{workflow}"],
    }


def _exit_code(payload: dict) -> int:
    return {"critical": 2, "high": 1}.get(payload["severity"], 0)


def main() -> int:
    ap = argparse.ArgumentParser(description="USAP pipeline-security-scan: scan a parsed pipeline configuration")
    ap.add_argument("--input", help="pipeline descriptor JSON (see module docstring)")
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
        print(f"pipeline-security-scan: severity={payload['severity']}")
        for f in payload["key_findings"]:
            print(f"  - {f}")
        print(f"  action: {payload['action']}")
    return _exit_code(payload)


if __name__ == "__main__":
    raise SystemExit(main())
