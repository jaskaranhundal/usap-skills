#!/usr/bin/env python3
"""threat-hunting_tool.py

Evaluates one hunt package per the SKILL.md methodology: hypothesis priority
(actor relevance x3 + control gap x2 + data availability x1), data-source
health (a gap invalidates a clean verdict), two-source corroboration for a
confirmed finding, dwell-time bracket, and the escalation and cascade rules.
Emits the USAP 11-field payload.

  python3 threat-hunting_tool.py --input hunt.json --output json
  python3 threat-hunting_tool.py --output json       # no input: informational, exit 0

Input (see tests/fixtures/threat-hunting-input.json):
  hunt_id, sprint, hypothesis{statement, ttp[], actor_relevance, control_gap, data_availability},
  time_window{start, end}, data_sources[]: {name, required, last_event_utc, retention_days},
  observations[]: {source, host, account, indicator, technique, timestamp_utc, playbook, detail},
  ioc_matches[]: {type, value, source, confidence, expires_utc}

Exit codes: 0 clean hunt; 1 unconfirmed or inconclusive; 2 confirmed active
threat. Queries nothing; reasons over supplied telemetry summaries. Stdlib only.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

SLUG = "threat-hunting"
HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parents[2]
LATERAL = {"T1047", "T1021", "T1021.002", "T1021.006", "T1550.002", "T1570"}
ATTACK = "https://attack.mitre.org/techniques/"


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _parse(ts: Optional[str]) -> Optional[datetime]:
    if not ts:
        return None
    try:
        return datetime.fromisoformat(str(ts).replace("Z", "+00:00")).astimezone(timezone.utc)
    except ValueError:
        return None


def _dwell_bracket(days: float) -> Dict[str, str]:
    if days < 1:
        return {"bracket": "< 1 day", "blast_radius": "low, initial access only", "evidence_scope": "7-day lookback"}
    if days <= 7:
        return {"bracket": "1-7 days", "blast_radius": "moderate, reconnaissance complete", "evidence_scope": "30-day lookback"}
    if days <= 30:
        return {"bracket": "7-30 days", "blast_radius": "high, lateral movement likely", "evidence_scope": "90-day lookback + backup media"}
    return {"bracket": "> 30 days", "blast_radius": "critical, full environment compromise assumed", "evidence_scope": "full historical + offline media"}


def analyse(target: dict, input_path: Optional[str] = None) -> Dict[str, Any]:
    hunt_id = target.get("hunt_id", "HUNT-UNSET")
    hyp = target.get("hypothesis") or {}
    win = target.get("time_window") or {}
    w_start, w_end = _parse(win.get("start")), _parse(win.get("end")) or datetime.now(timezone.utc)
    sources = [s for s in (target.get("data_sources") or []) if isinstance(s, dict)]
    obs = [o for o in (target.get("observations") or []) if isinstance(o, dict)]
    iocs = [i for i in (target.get("ioc_matches") or []) if isinstance(i, dict)]

    # Hypothesis priority
    ar, cg, da = int(hyp.get("actor_relevance") or 0), int(hyp.get("control_gap") or 0), int(hyp.get("data_availability") or 0)
    priority = ar * 3 + cg * 2 + da
    pursue = priority >= 5

    # Data-source health: required sources must have data within 24 h of the window end.
    gaps: List[str] = []
    healthy: List[str] = []
    for s in sources:
        last = _parse(s.get("last_event_utc"))
        if s.get("required", True) and (last is None or (w_end - last) > timedelta(hours=24)):
            gaps.append(f"{s.get('name')} (last event {s.get('last_event_utc') or 'none'})")
        else:
            healthy.append(str(s.get("name")))

    # Corroboration: distinct sources per entity (host or account).
    entities: Dict[str, dict] = {}
    for o in obs:
        key = str(o.get("host") or o.get("account") or "unknown")
        e = entities.setdefault(key, {"entity": key, "sources": set(), "techniques": set(), "earliest": None, "indicators": []})
        e["sources"].add(str(o.get("source")))
        if o.get("technique"):
            e["techniques"].add(str(o["technique"]))
        ts = _parse(o.get("timestamp_utc"))
        if ts and (e["earliest"] is None or ts < e["earliest"]):
            e["earliest"] = ts
        e["indicators"].append(f"{o.get('source')}: {o.get('indicator')}" + (f" ({o.get('playbook')})" if o.get("playbook") else ""))
    confirmed = [e for e in entities.values() if len(e["sources"]) >= 2]
    unconfirmed = [e for e in entities.values() if len(e["sources"]) == 1]

    earliest = min((e["earliest"] for e in confirmed if e["earliest"]), default=None)
    dwell_days = round((w_end - earliest).total_seconds() / 86400, 1) if earliest else None
    dwell = _dwell_bracket(dwell_days) if dwell_days is not None else None
    techniques = sorted({t for e in confirmed for t in e["techniques"]} | set(hyp.get("ttp") or []))

    if confirmed:
        verdict = "confirmed"
        severity = "critical" if (dwell_days or 0) > 7 or any(t in LATERAL for e in confirmed for t in e["techniques"]) else "high"
        intent = "escalate"
        dwell_txt = f", estimated dwell {dwell_days} days ({dwell['bracket']})" if dwell else ""
        scope_txt = dwell["evidence_scope"] if dwell else "30-day lookback"
        action = (f"Escalate {hunt_id} to incident-commander now: {len(confirmed)} entity/entities corroborated by two or more sources{dwell_txt}. "
                  f"Evidence scope: {scope_txt}. Containment options are the incident commander's decision, not this hunt's.")
    elif unconfirmed or iocs:
        verdict = "unconfirmed"
        severity = "medium"
        intent = "detect"
        action = (f"{len(unconfirmed)} single-source observation(s) and {len(iocs)} IOC match(es): add to the monitored watchlist and re-hunt within 48 hours; "
                  "request the second data source before any escalation.")
    elif gaps:
        verdict = "inconclusive"
        severity = "low"
        intent = "report"
        action = f"Hunt cannot be closed clean: data gap in {', '.join(gaps)}. Restore the source and re-run over the same window."
    else:
        verdict = "not_observed"
        severity = "informational"
        intent = "report"
        action = "Clean hunt: archive the evidence package and update the ATT&CK coverage map for the tested techniques."
    if verdict == "not_observed" and not sources:
        verdict, severity, intent = "inconclusive", "low", "report"
        action = "No data-source attestation supplied; a clean verdict without source health is not valid."
    if not obs and not sources and not hyp:
        # Nothing to hunt is an absence of input, not a hunt outcome (exit 0).
        verdict, severity, intent = "no_input", "informational", "report"
        action = "Supply a hunt package (hypothesis, data sources, observations); nothing was provided."

    key = [f"{hunt_id} ({target.get('sprint', 'sprint n/a')}): hypothesis priority {priority} ({'pursue' if pursue else 'defer'}); "
           f"{len(obs)} observation(s) over {len(entities)} entity/entities; sources healthy {len(healthy)}, gaps {len(gaps)}; verdict {verdict}"]
    key.append(f"Hypothesis: {hyp.get('statement', 'n/a')}")
    for e in confirmed[:4]:
        key.append(f"CONFIRMED {e['entity']}: {len(e['sources'])} sources ({', '.join(sorted(e['sources']))}), techniques {', '.join(sorted(e['techniques'])) or 'n/a'}, earliest {e['earliest'].strftime('%Y-%m-%dT%H:%M:%SZ') if e['earliest'] else 'n/a'}")
    for e in unconfirmed[:3]:
        key.append(f"unconfirmed {e['entity']}: single source {', '.join(e['sources'])}; watchlist")
    if dwell:
        key.append(f"Dwell estimate {dwell_days} days -> {dwell['bracket']}: {dwell['blast_radius']}; {dwell['evidence_scope']}")
    if gaps:
        key.append(f"Data gap(s): {', '.join(gaps)}; clean verdict not available for the affected period")
    for i in iocs[:3]:
        key.append(f"IOC match {i.get('type')} {i.get('value')} in {i.get('source')} (confidence {i.get('confidence', 'n/a')}): block-list recommendation requires approval")

    rel = None
    if input_path:
        try:
            rel = Path(input_path).resolve().relative_to(REPO_ROOT).as_posix()
        except ValueError:
            rel = None
    src = f"local://{rel}" if rel else "local://detection/threat-hunting/SKILL.md"
    evidence = [{"source": src, "ref": f"{e['entity']}", "quote": "; ".join(e["indicators"][:3])} for e in (confirmed + unconfirmed)[:6]]
    evidence += [{"source": f"{ATTACK}{t.replace('.', '/')}/", "ref": t} for t in techniques[:4]]
    evidence.append({"source": "local://detection/threat-hunting/references/hunt-playbooks.md", "ref": "playbooks and dwell-time brackets"})

    conf, factors = 0.50, ["base 0.50"]
    if confirmed:
        conf += 0.30; factors.append("two or more independent sources agree (+0.30)")
    elif unconfirmed:
        conf += 0.10; factors.append("single source only (+0.10)")
    if not gaps and sources:
        conf += 0.10; factors.append("all required sources healthy (+0.10)")
    elif gaps:
        conf -= 0.10; factors.append(f"{len(gaps)} data gap(s) (-0.10)")
    if not obs and not sources:
        conf, factors = 0.30, ["no hunt data supplied (0.30)"]
    conf = round(max(0.2, min(conf, 0.93)), 2)

    next_agents = []
    if confirmed:
        next_agents += ["incident-commander", "detection-engineering"]
    elif unconfirmed or iocs:
        next_agents += ["threat-intelligence"]
    elif verdict == "not_observed":
        next_agents += ["detection-engineering"]
    if gaps:
        next_agents.append("telemetry-signal-quality")

    return {
        "agent_slug": SLUG, "intent_type": intent, "action": action,
        "rationale": (f"Verdict rule: confirmed needs two or more independent sources on the same entity; a single source is a watchlist item; a clean verdict requires every required "
                      f"data source healthy within 24 h of the window end, otherwise inconclusive. Dwell from the earliest corroborated indicator to the window end. "
                      f"Confidence factors: {', '.join(factors)}."),
        "confidence": conf, "severity": severity, "key_findings": key, "evidence_references": evidence,
        "next_agents": next_agents, "human_approval_required": bool(iocs), "timestamp_utc": _now(),
        "hunt": {"hunt_id": hunt_id, "verdict": verdict, "hypothesis_priority": priority, "pursue": pursue,
                 "window": {"start": win.get("start"), "end": win.get("end")}, "sources_healthy": healthy, "data_gaps": gaps,
                 "confirmed_entities": [{"entity": e["entity"], "sources": sorted(e["sources"]), "techniques": sorted(e["techniques"]),
                                         "earliest_indicator_utc": e["earliest"].strftime("%Y-%m-%dT%H:%M:%SZ") if e["earliest"] else None} for e in confirmed],
                 "watchlist_entities": [e["entity"] for e in unconfirmed],
                 "estimated_dwell_days": dwell_days, "dwell": dwell, "ioc_matches": len(iocs)},
        "mitre_ttps": techniques, "affected_assets": [e["entity"] for e in confirmed + unconfirmed],
    }


def _exit(p: dict) -> int:
    v = p["hunt"]["verdict"]
    return 2 if v == "confirmed" else (1 if v in ("unconfirmed", "inconclusive") else 0)


def main() -> int:
    ap = argparse.ArgumentParser(description="USAP threat-hunting: evaluate a hunt package")
    ap.add_argument("--input"); ap.add_argument("--output", choices=["json", "text"], default="text")
    args = ap.parse_args()
    if args.input:
        try:
            target = json.loads(Path(args.input).read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            print(f"error: cannot read --input: {exc}", file=sys.stderr); return 2
    else:
        raw = "" if sys.stdin.isatty() else sys.stdin.read()
        try:
            target = json.loads(raw) if raw.strip() else {}
        except json.JSONDecodeError:
            target = {}
    p = analyse(target, args.input)
    if args.output == "json":
        print(json.dumps(p, indent=2))
    else:
        print(f"threat-hunting: verdict={p['hunt']['verdict']} severity={p['severity']}")
        for f in p["key_findings"]:
            print(f"  - {f}")
    return _exit(p)


if __name__ == "__main__":
    raise SystemExit(main())
