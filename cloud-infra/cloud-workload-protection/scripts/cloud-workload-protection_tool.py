#!/usr/bin/env python3
"""cloud-workload-protection_tool.py

Assesses container and serverless workloads for runtime threats per the SKILL.md:
container-escape indicators, runtime anomalies, and CWPP coverage gaps. Read-only
detection. Emits the USAP 11-field payload.

  python3 cloud-workload-protection_tool.py --input workloads.json --output json
  python3 cloud-workload-protection_tool.py --output json    # no input: informational, exit 0

Input (see tests/fixtures/cloud-workload-protection-input.json): workloads[]:
{name, type (container|serverless), cwpp_coverage, runtime_signals[]
(escape_indicator|reverse_shell|crypto_mining|privileged_syscall|
drift_from_image|new_binary|c2_egress)}.

Exit codes: 0 low; 1 high; 2 critical (escape or C2). Stdlib only.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

SLUG = "cloud-workload-protection"
HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parents[2]
SIGNAL = {"escape_indicator": ("critical", "T1611"), "c2_egress": ("critical", "T1071"), "reverse_shell": ("critical", "T1059"),
          "privileged_syscall": ("high", "T1611"), "crypto_mining": ("high", "T1496"), "drift_from_image": ("high", "T1525"),
          "new_binary": ("medium", "T1105")}
SEV_RANK = {"critical": 4, "high": 3, "medium": 2, "low": 1, "informational": 0}


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def analyse(t: dict, input_path: Optional[str] = None) -> Dict[str, Any]:
    rel = None
    if input_path:
        try:
            rel = Path(input_path).resolve().relative_to(REPO_ROOT).as_posix()
        except ValueError:
            rel = None
    wls = [w for w in (t.get("workloads") or []) if isinstance(w, dict)]
    if not t or not wls:
        return {"agent_slug": SLUG, "intent_type": "detect", "action": "Supply workloads; nothing was provided.",
                "rationale": "No workloads supplied.", "confidence": 0.30, "severity": "informational", "key_findings": ["No workloads supplied"],
                "evidence_references": [{"source": "local://cloud-infra/cloud-workload-protection/SKILL.md", "ref": "runtime signals (not applied)"}],
                "next_agents": [], "human_approval_required": False, "timestamp_utc": _now(), "workloads": [], "_exit": 0}
    findings: List[dict] = []
    no_cwpp: List[str] = []
    for w in wls:
        if not w.get("cwpp_coverage"):
            no_cwpp.append(str(w.get("name")))
        for sig in [str(s).lower() for s in (w.get("runtime_signals") or [])]:
            sev, mitre = SIGNAL.get(sig, ("medium", "T1105"))
            findings.append({"workload": w.get("name"), "type": w.get("type"), "signal": sig, "severity": sev, "mitre": mitre})
    findings.sort(key=lambda f: -SEV_RANK[f["severity"]])
    counts = {k: sum(1 for f in findings if f["severity"] == k) for k in SEV_RANK}
    severity = findings[0]["severity"] if findings else ("medium" if no_cwpp else "informational")
    exit_code = 2 if counts["critical"] else 1 if (counts["high"] or no_cwpp) else 0
    action = (f"{counts['critical']} critical runtime threat(s) (escape/C2/reverse shell); isolate the affected workload and escalate: "
              + ", ".join(sorted({f['workload'] for f in findings if f['severity']=='critical'}))[:120] + "." if counts["critical"] else
              f"{counts['high']} high runtime anomaly(ies) to triage." if counts["high"] else
              (f"No runtime threat, but {len(no_cwpp)} workload(s) have no CWPP coverage." if no_cwpp else "No runtime threats; CWPP coverage complete."))
    key = [f"{len(wls)} workload(s): {len(findings)} runtime signal(s) ({counts['critical']} critical, {counts['high']} high); {len(no_cwpp)} without CWPP coverage"]
    key += [f"{f['severity']} {f['workload']} ({f['type']}): {f['signal']} [{f['mitre']}]" for f in findings[:6]]
    if no_cwpp:
        key.append("No runtime protection on: " + ", ".join(no_cwpp[:5]))
    evidence = [{"source": f"local://{rel}" if rel else "local://cloud-infra/cloud-workload-protection/SKILL.md", "ref": "workload runtime telemetry"},
                {"source": "local://cloud-infra/cloud-workload-protection/SKILL.md", "ref": "runtime threat signals and CWPP coverage model"}]
    return {"agent_slug": SLUG, "intent_type": "detect", "action": action,
            "rationale": ("Each runtime signal is scored against the SKILL.md model: container escape, C2 egress and reverse shell are critical; privileged syscalls, crypto-mining and "
                          "image drift are high. Workloads without CWPP coverage are a detection blind spot. Read-only; isolation is a downstream gated action."),
            "confidence": 0.85, "severity": severity, "key_findings": key, "evidence_references": evidence,
            "next_agents": (["incident-commander", "containment-advisor"] if counts["critical"] else ["threat-hunting"] if findings else []),
            "human_approval_required": False, "timestamp_utc": _now(),
            "workloads": findings, "mitre_ttps": sorted({f["mitre"] for f in findings}), "affected_assets": sorted({str(f["workload"]) for f in findings}), "_exit": exit_code}


def main() -> int:
    ap = argparse.ArgumentParser(description="USAP cloud-workload-protection")
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
    print(json.dumps(p, indent=2) if args.output == "json" else f"cloud-workload-protection: severity={p['severity']}")
    return code


if __name__ == "__main__":
    raise SystemExit(main())
