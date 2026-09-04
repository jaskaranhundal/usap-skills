#!/usr/bin/env python3
"""secrets-exposure_tool.py

Analyses one SecurityFact describing a detected secret and emits the USAP
11-field payload. Implements the SKILL.md Reasoning Procedure (steps 1 to 9)
on top of the deterministic detectors in pre_analysis.py, which lives next to
this file and is imported, not duplicated.

  python3 secrets-exposure_tool.py --input fact.json --output json
  cat fact.json | python3 secrets-exposure_tool.py --output json
  python3 secrets-exposure_tool.py --output json          # no input: informational, exit 0

Input: a SecurityFact (see tests/fixtures/secrets-exposure-input.json):
  event_id, source, source_credibility, finding, raw_payload{secret_type,
  matched_value_redacted, file_path, git_branch, repository, environment,
  exposure_window_hours, entropy, line_number, raw_line, attached_policies,
  cloudtrail_anomaly ...}, structured_fact{...}, context{...}

Exit codes (match pre_analysis.py and tests/run_all.sh):
  0  read-only verdict (verify / monitor / false positive) or no input
  1  mutating verdict, service_scoped blast radius
  2  mutating verdict, full_account blast radius

Never prints a raw secret value. Never touches any system. Stdlib only.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

SLUG = "secrets-exposure"
HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parents[2]

# Load the sibling detector module by path so the tool works from any cwd.
_spec = importlib.util.spec_from_file_location("secrets_pre_analysis", HERE / "pre_analysis.py")
_pre = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_pre)  # type: ignore[union-attr]

MITRE_BY_TYPE = {
    "aws_access_key": "T1552.005", "aws_secret_key": "T1552.005",
    "private_key_pem": "T1552.004", "ssh_private_key": "T1552.004",
}
DEFAULT_MITRE = "T1552.001"

# SKILL.md "Attacker Timeline": (minutes, description, technique)
TIMELINES = {
    "aws_access_key": [
        (2, "key validated (sts:GetCallerIdentity)", "T1552.005"),
        (5, "accessible services mapped", "T1619"),
        (10, "backdoor IAM user and access key created", "T1098.001"),
        (15, "S3 and Secrets Manager exfiltration started", "T1530"),
        (25, "CloudTrail logging disabled", "T1562.008"),
        (45, "bulk data export complete", "T1530"),
    ],
    "github_pat": [
        (1, "token validated", "T1552.001"),
        (5, "all accessible private repositories cloned", "T1213.003"),
        (15, "deploy key or webhook persistence", "T1098"),
        (20, "malicious commit pushed if write scope", "T1195.001"),
    ],
    "stripe_live_key": [
        (2, "test charge confirms live key", "T1552.001"),
        (10, "customer and payment data harvested", "T1213"),
        (20, "refund or transfer fraud", "T1657"),
    ],
    "database_url": [
        (5, "connection established and schema enumerated", "T1552.001"),
        (15, "full database exported", "T1530"),
    ],
}
REVOKE_BY_MIN = {"aws_access_key": 5, "github_pat": 5, "stripe_live_key": 5, "database_url": 5, "jwt_secret": 0}

FP_PATH_MARKERS = ("__tests__", "/spec/", ".test.", "/mock", "/mocks/", "fixture", ".example", "/test/", "/tests/")
COMMENT_PREFIXES = ("#", "//", "/*", "--")
PLACEHOLDER_VALUE_RE = _pre.re.compile(
    r"^(?:example.*|placeholder.*|your[_-]?(?:key|secret|token).*|replace[_-]?me|changeme|todo|dummy|fake|x{4,}|<[a-z_]+>|\$\{[a-z_]+\})$",
    _pre.re.IGNORECASE)


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _rel_or_none(path: Optional[str]) -> Optional[str]:
    """Repo-relative path for local:// evidence, or None when outside the repo."""
    if not path:
        return None
    try:
        return Path(path).resolve().relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return None


# --------------------------------------------------------------------------- steps
def step1_type(fact: dict, pre: dict) -> Tuple[str, str]:
    t = pre.get("detected_secret_type") or "generic_api_secret"
    if t.startswith("github_"):
        t = "github_pat" if "pat" in t or "classic" in t else t
    return t, MITRE_BY_TYPE.get(t, DEFAULT_MITRE)


def step2_false_positive(fact: dict, pre: dict) -> List[str]:
    rp = fact.get("raw_payload") or {}
    signals: List[str] = []
    path = str(rp.get("file_path") or "").lower()
    if any(m in f"/{path}" for m in FP_PATH_MARKERS):
        signals.append(f"file path '{rp.get('file_path')}' is a test, mock or fixture location")
    raw_line = str(rp.get("raw_line") or "").strip()
    if raw_line.startswith(COMMENT_PREFIXES):
        signals.append("matched line is a comment")
    val = str(rp.get("matched_value_redacted") or "")
    rhs = raw_line.split("=", 1)[-1].strip().strip("'\"") if "=" in raw_line else ""
    # Redacted value: substring check. Raw line value: only when the whole value
    # is a placeholder token; a real key that happens to contain "EXAMPLE" is not one.
    if _pre.FP_VALUE_PATTERN.search(val) or PLACEHOLDER_VALUE_RE.match(rhs):
        signals.append("value carries a placeholder marker (EXAMPLE, PLACEHOLDER, YOUR_KEY, xxxx, changeme)")
    signals.extend(s for s in pre.get("false_positive_signals", []) if s not in signals and "regex" in s)
    return signals


def step3_confidence(fact: dict, pre: dict, secret_type: str, fp: List[str]) -> Tuple[float, List[str]]:
    rp = fact.get("raw_payload") or {}
    factors: List[str] = []
    if fp:
        conf = 0.15 if len(fp) > 1 else 0.30
        factors.append("false-positive indicators cap confidence at 0.30 (0.15 with two or more)")
        if str(rp.get("raw_line") or "").strip().startswith(COMMENT_PREFIXES):
            conf = max(0.10, conf - 0.20); factors.append("comment line: -0.20")
        return round(conf, 2), factors
    conf = float(pre.get("confidence") or 0.0)
    factors.append(f"detector base {conf:.2f} (pattern for {secret_type}, source credibility {fact.get('source_credibility', 'n/a')})")
    entropy = rp.get("entropy")
    try:
        entropy = float(entropy) if entropy is not None else None
    except (TypeError, ValueError):
        entropy = None
    named = bool(_pre.re.search(r"(secret|key|token|password)", str(rp.get("raw_line") or "").split("=")[0], _pre.re.I))
    if entropy is not None and entropy > 4.5 and named:
        conf = max(conf, 0.92); factors.append(f"entropy {entropy} > 4.5 and variable named SECRET/KEY/TOKEN: floor 0.92")
    elif entropy is not None and entropy > 4.0:
        conf = max(conf, 0.82); factors.append(f"entropy {entropy} > 4.0: floor 0.82")
    elif entropy is not None:
        conf = min(conf, 0.65); factors.append(f"entropy {entropy} <= 4.0: cap 0.65")
    path = str(rp.get("file_path") or "").lower()
    if path.endswith(".env") or "/.env" in path or path.startswith(".env"):
        conf += 0.05; factors.append(".env file (not .env.example): +0.05")
    if str(rp.get("environment") or "").lower() == "production" or str(rp.get("git_branch") or "") in ("main", "master", "production"):
        conf += 0.05; factors.append("production branch or environment: +0.05")
    if entropy is None and not rp.get("secret_type"):
        conf = min(conf, 0.70); factors.append("pattern match only, no supporting context: cap 0.70")
    return round(min(conf, 0.97), 2), factors


def step4_blast_radius(fact: dict, pre: dict, secret_type: str) -> Tuple[str, str]:
    rp = fact.get("raw_payload") or {}
    br = pre.get("blast_radius") or "service_scoped"
    why = f"classification table for {secret_type}"
    policies = [str(p) for p in (rp.get("attached_policies") or [])]
    if secret_type in ("aws_access_key", "aws_secret_key"):
        if policies and all(("ReadOnly" in p or "Deny" in p) for p in policies):
            br, why = "service_scoped", "IAM policies attached are read-only, visible in the fact"
        else:
            br, why = "full_account", ("attached policies include " + ", ".join(policies[:3])) if policies else "AWS key with no restrictive IAM policy visible"
    sf = fact.get("structured_fact") or {}
    if sf.get("blast_radius") in ("full_account", "service_scoped", "minimal") and sf.get("blast_radius") != br:
        # Never downgrade without explicit evidence; upgrades from the fact are accepted.
        order = {"minimal": 0, "service_scoped": 1, "full_account": 2}
        if order[sf["blast_radius"]] > order[br]:
            br, why = sf["blast_radius"], "structured_fact declares a wider blast radius"
    return br, why


def step5_timeline(fact: dict, secret_type: str) -> Tuple[List[str], List[str], Optional[int]]:
    rp = fact.get("raw_payload") or {}
    hours = rp.get("exposure_window_hours")
    try:
        minutes = int(float(hours) * 60) if hours is not None else None
    except (TypeError, ValueError):
        minutes = None
    plausible: List[str] = []
    ttps: List[str] = []
    for t_min, desc, tech in TIMELINES.get(secret_type, []):
        if minutes is None or minutes >= t_min:
            plausible.append(f"T+{t_min}m {desc} ({tech})")
            if tech not in ttps:
                ttps.append(tech)
    return plausible, ttps, minutes


def step6_intent(conf: float, br: str) -> Tuple[str, Optional[str], bool]:
    if conf >= 0.70 and br in ("full_account", "service_scoped"):
        return "mutating", "credential_operation", True
    return "read_only", None, False


def step7_recommendation(conf: float, br: str, fp: List[str]) -> str:
    if fp and conf < 0.30:
        return "verify_false_positive"
    if conf >= 0.85 and br == "full_account":
        return "rotate_and_revoke_immediately"
    if conf >= 0.70 and br == "service_scoped":
        return "rotate_and_revoke"
    if conf >= 0.70:
        return "revoke_only"
    if br == "minimal":
        return "monitor_only"
    return "verify_scope"


# --------------------------------------------------------------------------- payload
def analyse(fact: dict, input_path: Optional[str]) -> Tuple[dict, int]:
    pre = _pre_analyse(fact)
    secret_type, mitre = step1_type(fact, pre)
    fp = step2_false_positive(fact, pre)
    conf, factors = step3_confidence(fact, pre, secret_type, fp)
    br, br_why = step4_blast_radius(fact, pre, secret_type)
    plausible, ttps, minutes = step5_timeline(fact, secret_type)
    legacy_intent, mut_cat, approval = step6_intent(conf, br)
    rec = step7_recommendation(conf, br, fp)
    approvers = ["soc_lead", "ciso"] if legacy_intent == "mutating" else []
    rp = fact.get("raw_payload") or {}
    ctx = fact.get("context") or {}

    if legacy_intent == "mutating" and br == "full_account":
        severity, exit_code, intent = "critical", 2, "escalate"
    elif legacy_intent == "mutating":
        severity, exit_code, intent = "high", 1, "detect"
    elif fp:
        severity, exit_code, intent = "informational", 0, "report"
    else:
        severity, exit_code, intent = "low", 0, "analyze"

    revoke_by = REVOKE_BY_MIN.get(secret_type)
    window_txt = f"{minutes} minutes" if minutes is not None else "an unknown window"
    findings = [
        f"Secret type {secret_type} ({mitre}); confidence {conf:.2f}: " + "; ".join(factors),
        f"Blast radius {br}: {br_why}",
    ]
    if rp.get("file_path"):
        findings.append(
            f"Location {rp.get('repository') or 'repository'}:{rp.get('file_path')}"
            + (f" line {rp.get('line_number')}" if rp.get("line_number") else "")
            + (f" on branch {rp.get('git_branch')}" if rp.get("git_branch") else "")
            + (f", commit {str(rp.get('git_commit'))[:12]}" if rp.get("git_commit") else ""))
    if fp:
        findings.append("False-positive indicators: " + "; ".join(fp))
    if plausible:
        findings.append(f"Exposure window {window_txt}; attacker steps already plausible: " + "; ".join(plausible[:4]))
    if rp.get("cloudtrail_anomaly") is False:
        findings.append(f"No CloudTrail anomaly as of {rp.get('cloudtrail_last_check_utc', 'last check')}; absence of evidence, not a clean result")
    gaps = [k.replace("_", " ") for k in ("secrets_scanning_enabled", "pre_commit_hooks_present", "mfa_on_committer_account") if ctx.get(k) is False]
    if gaps:
        findings.append("Prevention gaps: " + ", ".join(gaps))

    if rec == "rotate_and_revoke_immediately":
        action = (f"Rotate and revoke the {secret_type} now (target: within {revoke_by} minutes of approval); "
                  f"then audit usage since exposure and purge the value from history. Approval by {', '.join(approvers)} required before any credential operation.")
    elif rec == "rotate_and_revoke":
        action = f"Rotate and revoke the {secret_type} within 30 minutes of approval; audit usage for the exposure window. Approval by {', '.join(approvers)} required."
    elif rec == "revoke_only":
        action = f"Revoke the {secret_type}; rotation scope to be confirmed by the owning team. Approval required."
    elif rec == "verify_false_positive":
        action = "Mark as likely false positive; confirm with the committing developer that the value is a scaffold, then allowlist the pattern."
    elif rec == "monitor_only":
        action = "No credential operation. Monitor for use; re-evaluate if the key is promoted to a live environment."
    else:
        action = "Verify the scope and liveness of the credential before any rotation; confidence is below the mutating threshold."

    rationale = (
        f"{secret_type} detected by {fact.get('source', 'scanner')} (credibility {fact.get('source_credibility', 'n/a')}). "
        f"Confidence {conf:.2f} from: {'; '.join(factors)}. Blast radius {br} ({br_why}). "
        + (f"Exposure window {window_txt}; per the attacker timeline the steps up to T+{plausible and plausible[-1].split(' ')[0][2:] or '0'} are plausible, "
           f"so revocation must be executed within {revoke_by} minutes of approval. " if plausible and revoke_by is not None else "")
        + f"Recommendation {rec}; intent {legacy_intent}"
        + (f", mutating category {mut_cat}, approvers {approvers}." if mut_cat else ".")
    )

    evidence: List[Dict[str, Any]] = []
    rel = _rel_or_none(input_path)
    if rel:
        evidence.append({"source": f"local://{rel}", "ref": f"event {fact.get('event_id', 'n/a')}", "timestamp_utc": fact.get("timestamp_utc")})
    else:
        evidence.append({"source": f"fact:{fact.get('source', 'scanner')}", "ref": f"event {fact.get('event_id', 'n/a')}, input {input_path or 'stdin'}",
                         "timestamp_utc": fact.get("timestamp_utc")})
    evidence.append({"source": "local://detection/secrets-exposure/references/attacker_timeline.md", "ref": f"{secret_type} timeline"})
    if rp.get("git_commit"):
        evidence.append({"source": f"fact:git", "ref": f"{rp.get('repository')}@{str(rp.get('git_commit'))[:12]} {rp.get('file_path')}:{rp.get('line_number')}"})

    next_agents: List[str] = []
    if legacy_intent == "mutating":
        next_agents = ["containment-advisor", "compliance-mapping"]
        if br == "full_account":
            next_agents.insert(0, "incident-classification")

    payload = {
        "agent_slug": SLUG,
        "intent_type": intent,
        "action": action,
        "rationale": rationale,
        "confidence": conf,
        "severity": severity,
        "key_findings": findings,
        "evidence_references": evidence,
        "next_agents": next_agents,
        "human_approval_required": approval,
        "timestamp_utc": _now(),
        "secret_type": secret_type,
        "blast_radius": br,
        "recommendation": rec,
        "mutating_category": mut_cat,
        "requires_approval": approval,
        "approver_roles": approvers,
        "mitre_ttps": [mitre] + [t for t in ttps if t != mitre],
        "affected_assets": [a for a in (
            f"repo:{rp.get('repository')}" if rp.get("repository") else None,
            f"iam:{rp.get('iam_user')}" if rp.get("iam_user") else None,
            f"aws-account:{rp.get('aws_account_id')}" if rp.get("aws_account_id") else None) if a],
        "remediation_steps": _remediation(secret_type, rec, rp),
        "exposure_window_minutes": minutes,
    }
    return payload, exit_code


def _remediation(secret_type: str, rec: str, rp: dict) -> List[str]:
    if rec in ("verify_false_positive", "monitor_only", "verify_scope"):
        return ["Confirm the value's provenance with the committer.", "Allowlist the pattern or path if it is a scaffold; otherwise re-run with the confirmed context."]
    steps = [f"Revoke the exposed {secret_type} at the provider (after approval).",
             "Issue a replacement credential with least privilege and update consumers.",
             f"Audit provider logs for the exposure window ({rp.get('exposure_window_hours', '?')} h) for use of the credential."]
    if rp.get("git_commit"):
        steps.append(f"Purge the value from git history of {rp.get('repository')} on every branch and force-rotate any secondary secrets in the same file.")
    steps.append("Enable secret scanning and a pre-commit hook on the repository.")
    return steps


def _pre_analyse(fact: dict) -> dict:
    """Run pre_analysis.py's pipeline in-process (its main() reads stdin)."""
    kw_type, kw_blast, kw_conf = _pre.classify_by_keywords(fact)
    all_findings: List[dict] = []
    for field_name, text in _pre.extract_text_fields(fact):
        for f in _pre.scan_text(text):
            f["source_field"] = field_name
            all_findings.append(f)
    best_type, best_blast, best_conf = kw_type, kw_blast, kw_conf
    for f in all_findings:
        if not f["is_false_positive"] and f["confidence"] > best_conf:
            best_type, best_blast, best_conf = f["secret_type"], f["blast_radius"], f["confidence"]
    cred = float(fact.get("source_credibility", 0.80) or 0.80)
    if best_conf == 0.0 and cred > 0:
        best_conf = round(cred * 0.75, 3)
        best_blast = best_blast or "service_scoped"
    fp_signals = ["regex match returned likely false positive value"] if any(f["is_false_positive"] for f in all_findings) else []
    return {"detected_secret_type": best_type, "blast_radius": best_blast, "confidence": best_conf,
            "false_positive_signals": fp_signals, "regex_matches": all_findings[:10]}


def no_input_payload() -> dict:
    return {
        "agent_slug": SLUG, "intent_type": "report",
        "action": "Supply a SecurityFact with --input or on stdin; no analysis was performed.",
        "rationale": "The tool was invoked without a SecurityFact. It analyses one detected-secret event per run and cannot produce a verdict without one.",
        "confidence": 0.0, "severity": "informational",
        "key_findings": ["No input supplied", "No secret analysed", "See tests/fixtures/secrets-exposure-input.json for the expected shape"],
        "evidence_references": [{"source": "local://detection/secrets-exposure/SKILL.md", "ref": "input schema"}],
        "next_agents": [], "human_approval_required": False, "timestamp_utc": _now(),
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="USAP secrets-exposure analyser")
    ap.add_argument("--input", help="SecurityFact JSON file (default: stdin)")
    ap.add_argument("--output", choices=["text", "json"], default="text")
    args = ap.parse_args()

    fact: Optional[dict] = None
    if args.input:
        fact = json.loads(Path(args.input).read_text(encoding="utf-8"))
    elif not sys.stdin.isatty():
        raw = sys.stdin.read()
        fact = json.loads(raw) if raw.strip() else None

    if not fact:
        payload, code = no_input_payload(), 0
    else:
        payload, code = analyse(fact, args.input)

    if args.output == "json":
        print(json.dumps(payload, indent=2))
    else:
        print(f"secrets-exposure: severity={payload['severity']} confidence={payload['confidence']} recommendation={payload.get('recommendation', 'n/a')}")
        for f in payload["key_findings"]:
            print(f"  - {f}")
        print(f"  action: {payload['action']}")
    return code


if __name__ == "__main__":
    raise SystemExit(main())
