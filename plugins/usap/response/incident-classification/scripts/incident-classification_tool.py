#!/usr/bin/env python3
"""incident-classification_tool.py

Classifies one SecurityFact into the SKILL.md incident taxonomy (14 types),
scores severity against the matrix, checks the five false-positive indicator
categories, and recommends the escalation route and response category.
Reuses the deterministic NIST-phase classifier in pre_analysis.py next to
this file. Emits the USAP 11-field payload. Classification is read-only and
never recommends containment actions (that is containment-advisor's role).

  python3 incident-classification_tool.py --input fact.json --output json
  python3 incident-classification_tool.py --output json      # no input: informational, exit 0

Input: a SecurityFact (event_id, event_type, severity, source, source_credibility,
finding, raw_payload{...}, structured_fact{whitelisted_ips, whitelisted_identities, tags},
context{environment, ...}). See tests/fixtures/incident-classification-input.json.

Exit codes: 0 low/medium or false positive; 1 high; 2 critical. Stdlib only.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

SLUG = "incident-classification"
HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parents[2]
_spec = importlib.util.spec_from_file_location("ic_pre_analysis", HERE / "pre_analysis.py")
_pre = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_pre)  # type: ignore[union-attr]

# SKILL.md Incident Taxonomy: event_type / keyword -> (incident_type, default severity floor, MITRE)
TAXONOMY: List[Tuple[str, List[str], str, str]] = [
    ("ransomware", ["ransom", "encrypt", "ransomware"], "critical", "T1486"),
    ("data_exfiltration", ["exfil", "data_breach", "bulk s3", "outbound volume", "database dump"], "critical", "T1041"),
    ("privilege_escalation", ["iam_anomaly", "privilege", "assumerole", "sudo", "token manipulation", "escalat"], "critical", "T1068"),
    ("supply_chain_attack", ["supply_chain", "malicious package", "compromised image", "dependency confusion"], "critical", "T1195"),
    ("credential_compromise", ["secret_exposure", "credential", "key leak", "stolen token", "credential stuffing"], "high", "T1078"),
    ("vulnerability_exploited", ["zero_day", "exploit", "exploit kit", "cve"], "high", "T1190"),
    ("malware_execution", ["endpoint_compromise", "malware", "edr alert", "hash match"], "high", "T1204"),
    ("network_intrusion", ["network_intrusion", "port scan", "waf", "ids signature", "intrusion"], "high", "T1190"),
    ("insider_threat", ["insider", "bulk download", "unusual hours"], "high", "T1530"),
    ("unauthorized_access", ["unauthorized", "failed auth", "anomalous ip", "anomalous location", "brute"], "high", "T1110"),
    ("denial_of_service", ["denial", "ddos", "traffic flood", "resource exhaustion"], "medium", "T1498"),
    ("phishing", ["phish", "credential harvest", "malicious attachment", "bec"], "medium", "T1566"),
    ("misconfiguration", ["cloud_misconfiguration", "misconfig", "open s3", "public rds", "permissive"], "medium", "T1530"),
]
SEV_RANK = {"critical": 4, "high": 3, "medium": 2, "low": 1, "informational": 0}
RANK_SEV = {v: k for k, v in SEV_RANK.items()}
TEST_MARKERS = re.compile(r"\b(test|dev|staging|sandbox|qa)\b", re.I)


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _norm_sev(s: Optional[str]) -> str:
    s = str(s or "medium").lower()
    return {"info": "informational", "informational": "informational"}.get(s, s if s in SEV_RANK else "medium")


def classify_type(fact: dict) -> Tuple[str, str, str]:
    text = " ".join([str(fact.get("event_type", "")), str(fact.get("finding", "")), json.dumps(fact.get("raw_payload") or {})]).lower()
    et = str(fact.get("event_type", "")).lower()
    for itype, keys, floor, tech in TAXONOMY:
        if et and any(k == et for k in keys):
            return itype, floor, tech
    for itype, keys, floor, tech in TAXONOMY:
        if any(k in text for k in keys):
            return itype, floor, tech
    return "unknown", "medium", "T1595"


def false_positive_indicators(fact: dict) -> List[str]:
    hits: List[str] = []
    rp = fact.get("raw_payload") or {}
    sf = fact.get("structured_fact") or {}
    ctx = fact.get("context") or {}
    blob = " ".join(str(v) for v in [rp.get("domain"), rp.get("account"), rp.get("account_name"), rp.get("user"), rp.get("hostname"), ctx.get("environment"), " ".join(map(str, sf.get("tags") or []))] if v)
    if TEST_MARKERS.search(blob):
        hits.append("test environment marker (test/dev/staging/sandbox) in domain, account, host or tags")
    src_ip = str(rp.get("source_ip") or rp.get("src_ip") or "")
    ident = str(rp.get("account") or rp.get("account_name") or rp.get("principal") or rp.get("user") or "")
    if src_ip and src_ip in set(map(str, sf.get("whitelisted_ips") or [])):
        hits.append(f"source IP {src_ip} is whitelisted in structured_fact")
    if ident and ident in set(map(str, sf.get("whitelisted_identities") or [])):
        hits.append(f"identity {ident} is whitelisted in structured_fact")
    ua = str(rp.get("user_agent") or "").lower()
    if any(k in ua for k in ("nessus", "qualys", "nuclei", "burp", "zap", "scanner")) or rp.get("known_scanner"):
        hits.append("known security scanner source")
    if rp.get("automation") or "ci" in ident.lower().split("-") or ident.lower().startswith(("svc-ci", "ci-", "github-actions", "gitlab-runner")):
        hits.append("known automation identity (CI/CD agent)")
    if rp.get("expected_schedule") or rp.get("recurring") or ctx.get("expected_batch_job"):
        hits.append("matches an expected batch or scheduled pattern")
    return hits


def analyse(fact: dict, input_path: Optional[str] = None) -> Dict[str, Any]:
    if not fact:
        return {
            "agent_slug": SLUG, "intent_type": "analyze", "action": "Supply a SecurityFact to classify; no event was provided.",
            "rationale": "No event content supplied; nothing classified. Absence of input, never a clean result.", "confidence": 0.30,
            "severity": "informational", "key_findings": ["No SecurityFact supplied"],
            "evidence_references": [{"source": "local://response/incident-classification/SKILL.md", "ref": "taxonomy (not applied: no input)"}],
            "next_agents": [], "human_approval_required": False, "timestamp_utc": _now(),
            "classification": {"incident_type": None, "false_positive_flag": False, "response_category": None},
        }
    pre = _pre.classify_incident(fact)  # NIST phase, category, floor from the sibling detector
    itype, floor, technique = classify_type(fact)
    input_sev = _norm_sev(fact.get("severity"))
    rank = max(SEV_RANK[input_sev], SEV_RANK.get(floor, 0), SEV_RANK.get(_norm_sev(pre.get("inferred_severity")), 0))
    rp = fact.get("raw_payload") or {}
    if rp.get("confirmed_impact") or rp.get("in_progress") or rp.get("spreading"):
        rank = 4
    assessed = RANK_SEV[rank]

    fps = false_positive_indicators(fact)
    cred = float(fact.get("source_credibility") or 0.8)
    conf = min(0.95, cred * (0.92 if itype != "unknown" else 0.65))
    conf = round(max(0.20, conf - 0.20 * len(fps)), 2)
    fp_flag = len(fps) >= 2 or any("whitelisted" in h for h in fps)

    if fp_flag:
        escalation, category = "false_positive_queue", "false_positive_queue"
    elif assessed == "critical":
        escalation, category = "L3 -> L2 -> L1 (immediate cascade)", "immediate_response"
    elif assessed == "high" and itype in ("credential_compromise", "privilege_escalation"):
        escalation, category = "L3 -> L2", "immediate_response"
    elif assessed == "high":
        escalation, category = "L3 (SOC handles)", "analyst_investigation"
    elif assessed == "medium":
        escalation, category = "L3 (analyst queue)", "analyst_investigation"
    else:
        escalation, category = "L4 (automated monitoring)", "automated_monitoring"

    differs = assessed != input_sev
    action = (f"Route to {category.replace('_', ' ')}: {escalation}. Incident type {itype}, severity {assessed}"
              + (f" (input said {input_sev})" if differs else "") + ("; verify the false-positive indicators before any response" if fps else "")
              + ". Containment options belong to containment-advisor.")
    key = [f"{fact.get('event_id', 'event')} from {fact.get('source', 'unknown source')} (credibility {cred}): classified {itype}, severity {assessed}"
           + (f", differs from input {input_sev}" if differs else ", matches input"),
           f"NIST phase {pre.get('nist_ir_phase', 'n/a')}, category {pre.get('incident_category', 'n/a')}; escalation {escalation}; response category {category}",
           f"False-positive indicators: {len(fps)} of 5 categories" + (": " + "; ".join(fps) if fps else " (none)") + f"; false_positive_flag={str(fp_flag).lower()}"]
    if fact.get("finding"):
        key.append(f"Finding: {str(fact['finding'])[:200]}")

    rel = None
    if input_path:
        try:
            rel = Path(input_path).resolve().relative_to(REPO_ROOT).as_posix()
        except ValueError:
            rel = None
    evidence = [{"source": f"local://{rel}" if rel else "local://response/incident-classification/SKILL.md", "ref": str(fact.get("event_id", "fact")), "quote": str(fact.get("finding", ""))[:160]},
                {"source": f"https://attack.mitre.org/techniques/{technique.replace('.', '/')}/", "ref": technique},
                {"source": "local://response/incident-classification/SKILL.md", "ref": "incident taxonomy, severity matrix, false-positive indicators, escalation routing"}]

    next_agents = []
    if not fp_flag and assessed == "critical":
        next_agents += ["incident-commander", "containment-advisor"]
    elif not fp_flag and assessed == "high":
        next_agents += ["incident-commander"]
    if fps:
        next_agents.append("telemetry-signal-quality")
    return {
        "agent_slug": SLUG, "intent_type": "analyze", "action": action,
        "rationale": (f"Type matched on event_type then keywords against the 14-type taxonomy; severity is the highest of the input severity, the type's default floor and the "
                      f"pre-analysis inference, raised to critical on confirmed impact or spread. Confidence = source credibility x match quality, minus 0.20 per false-positive "
                      f"indicator category hit; the flag is set on two or more hits or any whitelist hit. Read-only; no containment recommended."),
        "confidence": conf, "severity": "informational" if fp_flag else assessed, "key_findings": key, "evidence_references": evidence,
        "next_agents": next_agents, "human_approval_required": False, "timestamp_utc": _now(),
        "classification": {"incident_type": itype, "input_severity": input_sev, "severity_assessment": assessed, "severity_differs": differs,
                           "nist_phase": pre.get("nist_ir_phase"), "category": pre.get("incident_category"), "false_positive_flag": fp_flag,
                           "false_positive_indicators": fps, "escalation_recommendation": escalation, "response_category": category},
        "mitre_ttps": [technique], "affected_assets": [a for a in [rp.get("hostname"), rp.get("account") or rp.get("account_name"), rp.get("resource")] if a],
    }


def _exit(p: dict) -> int:
    return {"critical": 2, "high": 1}.get(p["severity"], 0)


def main() -> int:
    ap = argparse.ArgumentParser(description="USAP incident-classification: classify one SecurityFact")
    ap.add_argument("--input"); ap.add_argument("--output", choices=["json", "text"], default="text")
    args = ap.parse_args()
    if args.input:
        try:
            fact = json.loads(Path(args.input).read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            print(f"error: cannot read --input: {exc}", file=sys.stderr); return 2
    else:
        raw = "" if sys.stdin.isatty() else sys.stdin.read()
        try:
            fact = json.loads(raw) if raw.strip() else {}
        except json.JSONDecodeError:
            fact = {}
    p = analyse(fact, args.input)
    if args.output == "json":
        print(json.dumps(p, indent=2))
    else:
        print(f"incident-classification: {p['classification'].get('incident_type')} severity={p['severity']}")
        for f in p["key_findings"]:
            print(f"  - {f}")
    return _exit(p)


if __name__ == "__main__":
    raise SystemExit(main())
