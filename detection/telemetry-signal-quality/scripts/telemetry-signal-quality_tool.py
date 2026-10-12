#!/usr/bin/env python3
"""telemetry-signal-quality_tool.py

Normalises raw security events into typed, confidence-scored facts per the
SKILL.md controlled vocabulary (event type, severity, confidence by source
credibility) and reports data-source health so a clean hunt verdict is not
trusted over a broken pipeline. Read-only transform. Emits the USAP 11-field
payload.

  python3 telemetry-signal-quality_tool.py --input events.json --output json
  python3 telemetry-signal-quality_tool.py --output json    # no input: informational, exit 0

Input (see tests/fixtures/telemetry-signal-quality-input.json): as_of_utc,
events[]: {raw_type, raw_severity, source, source_credibility, specific_indicator},
sources[]: {name, last_event_utc, expected_within_hours}.

Exit codes: 0 healthy; 1 a data-source gap or low-confidence normalisation;
2 a required source silent (blind spot). Stdlib only.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

SLUG = "telemetry-signal-quality"
HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parents[2]
EVENT_MAP = [
    ("secret_exposure", ("secret", "api key", "credential in", "env file", "key leak")),
    ("iam_anomaly", ("assumerole", "mfa bypass", "root usage", "privilege escal", "unusual api")),
    ("network_intrusion", ("ids", "ips", "port scan", "waf", "lateral movement", "firewall anomaly")),
    ("data_exfiltration", ("exfil", "bulk s3", "outbound transfer")),
    ("malware_execution", ("edr", "hash match", "suspicious process", "malware")),
    ("ransomware", ("ransom", "encryption pattern")),
    ("credential_stuffing", ("auth flood", "failed login", "credential stuffing")),
    ("supply_chain", ("malicious package", "compromised image", "dependency confusion")),
    ("misconfiguration", ("public bucket", "open port", "permissive policy")),
    ("vulnerability_exploited", ("cve", "exploit signature")),
    ("insider_threat", ("bulk download", "off-hours", "credential misuse")),
    ("phishing", ("credential harvest", "malicious attachment", "phish")),
    ("pipeline_security_finding", ("sast", "sca", "secret in ci", "iac misconfig")),
]
SEV_MAP = {"critical": "critical", "p0": "critical", "sev1": "critical", "high": "high", "p1": "high", "sev2": "high",
           "medium": "medium", "moderate": "medium", "p2": "medium", "sev3": "medium", "low": "low", "p3": "low", "sev4": "low",
           "info": "info", "informational": "info", "notice": "info", "p4": "info"}


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _parse(ts: Optional[str]) -> Optional[datetime]:
    try:
        return datetime.fromisoformat(str(ts).replace("Z", "+00:00")).astimezone(timezone.utc)
    except (ValueError, TypeError):
        return None


def _classify(raw_type: str, indicator: str) -> str:
    blob = f"{raw_type} {indicator}".lower()
    for et, keys in EVENT_MAP:
        if any(k in blob for k in keys):
            return et
    return "unknown"


def _confidence(cred: float, specific: bool) -> float:
    if cred >= 0.85:
        return round(0.85 + 0.12 * (1 if specific else 0), 2)
    if cred >= 0.65:
        return round(0.65 + 0.19 * (1 if specific else 0), 2)
    return round(0.40 + 0.24 * (1 if specific else 0), 2)


def analyse(t: dict, input_path: Optional[str] = None) -> Dict[str, Any]:
    rel = None
    if input_path:
        try:
            rel = Path(input_path).resolve().relative_to(REPO_ROOT).as_posix()
        except ValueError:
            rel = None
    events = [e for e in (t.get("events") or []) if isinstance(e, dict)]
    sources = [s for s in (t.get("sources") or []) if isinstance(s, dict)]
    if not t or not (events or sources):
        return {"agent_slug": SLUG, "intent_type": "report", "action": "Supply events and/or sources; nothing was provided.",
                "rationale": "No telemetry supplied; no normalisation.", "confidence": 0.30, "severity": "informational",
                "key_findings": ["No telemetry supplied"], "evidence_references": [{"source": "local://detection/telemetry-signal-quality/SKILL.md", "ref": "vocabulary (not applied)"}],
                "next_agents": [], "human_approval_required": False, "timestamp_utc": _now(), "normalized": [], "_exit": 0}
    as_of = _parse(t.get("as_of_utc")) or datetime.now(timezone.utc)
    normalized: List[dict] = []
    low_conf = 0
    unknown = 0
    for e in events:
        et = _classify(str(e.get("raw_type", "")), str(e.get("specific_indicator", "")))
        sev = SEV_MAP.get(str(e.get("raw_severity", "")).lower(), "medium")
        conf = _confidence(float(e.get("source_credibility") or 0.8), bool(e.get("specific_indicator")))
        if conf < 0.5:
            low_conf += 1
        if et == "unknown":
            unknown += 1
        normalized.append({"event_type": et, "severity": sev, "confidence": conf, "source": e.get("source")})
    gaps: List[str] = []
    for s in sources:
        last = _parse(s.get("last_event_utc"))
        window = float(s.get("expected_within_hours") or 24)
        if last is None or (as_of - last) > timedelta(hours=window):
            gaps.append(f"{s.get('name')} (last event {s.get('last_event_utc') or 'never'}, expected within {window:.0f}h)")
    severity = "critical" if gaps and len(gaps) == len(sources) and sources else "high" if gaps else "medium" if (low_conf or unknown) else "low" if normalized else "informational"
    exit_code = 2 if (gaps and sources and len(gaps) == len(sources)) else 1 if (gaps or low_conf or unknown) else 0
    action = ((f"Data-source gap in {len(gaps)}/{len(sources)} source(s): {', '.join(gaps[:3])}. A clean hunt verdict is not valid for the affected period."
               if gaps else f"{low_conf} low-confidence and {unknown} unclassifiable event(s) — review source quality.") if (gaps or low_conf or unknown) else
              f"{len(normalized)} event(s) normalised; all sources healthy.")
    key = [f"{len(events)} event(s) normalised, {unknown} unknown, {low_conf} low-confidence; {len(gaps)}/{len(sources)} source(s) with a gap"]
    key += [f"gap: {g}" for g in gaps[:4]]
    from collections import Counter
    counts = Counter(n["event_type"] for n in normalized)
    key.append("event types: " + ", ".join(f"{k}={v}" for k, v in counts.most_common(6)) if normalized else "no events")
    evidence = [{"source": f"local://{rel}" if rel else "local://detection/telemetry-signal-quality/SKILL.md", "ref": "raw events and source inventory"},
                {"source": "local://detection/telemetry-signal-quality/SKILL.md", "ref": "event vocabulary, severity and confidence scoring rules"}]
    return {"agent_slug": SLUG, "intent_type": "report", "action": action,
            "rationale": ("Each raw event mapped to the controlled event-type vocabulary, severity normalised, confidence scored by source credibility and indicator specificity. "
                          "Source health is checked against the expected window; a silent required source is a blind spot that invalidates negative findings. Read-only transform."),
            "confidence": 0.85, "severity": severity, "key_findings": key, "evidence_references": evidence,
            "next_agents": ["detection-engineering"] if gaps else [], "human_approval_required": False, "timestamp_utc": _now(),
            "normalized": normalized, "data_gaps": gaps, "mitre_ttps": [], "affected_assets": [], "_exit": exit_code}


def main() -> int:
    ap = argparse.ArgumentParser(description="USAP telemetry-signal-quality")
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
    print(json.dumps(p, indent=2) if args.output == "json" else f"telemetry-signal-quality: severity={p['severity']}")
    return code


if __name__ == "__main__":
    raise SystemExit(main())
