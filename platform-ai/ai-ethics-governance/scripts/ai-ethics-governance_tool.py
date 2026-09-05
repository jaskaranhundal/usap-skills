#!/usr/bin/env python3
"""ai-ethics-governance_tool.py

Assesses AI-system ethics and governance readiness per the SKILL.md: EU AI Act
risk tier, fairness metrics, model-card completeness and human oversight.
Read-only assessment; suspension, tier change and mandatory retraining are
mutating policy changes requiring approval. Emits the USAP 11-field payload.

  python3 ai-ethics-governance_tool.py --input system.json --output json
  python3 ai-ethics-governance_tool.py --output json    # no input: informational, exit 0

Input (see tests/fixtures/ai-ethics-governance-input.json):
{system, risk_tier (unacceptable|high|limited|minimal), fairness_gap (bool),
model_card_complete (bool), human_oversight (bool), explainability (bool)}.

Exit codes: 0 governed; 1 gaps; 2 unacceptable tier, or high-risk with a
fairness gap or no human oversight. Stdlib only.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

SLUG = "ai-ethics-governance"
HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parents[2]
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
    if not t or not t.get("system"):
        return {"agent_slug": SLUG, "intent_type": "advise", "action": "Supply an AI system descriptor; nothing was provided.",
                "rationale": "No system supplied.", "confidence": 0.30, "severity": "informational", "key_findings": ["No system supplied"],
                "evidence_references": [{"source": "local://platform-ai/ai-ethics-governance/SKILL.md", "ref": "EU AI Act tiers (not applied)"}],
                "next_agents": [], "human_approval_required": False, "timestamp_utc": _now(), "gaps": [], "_exit": 0}
    system = t.get("system")
    tier = str(t.get("risk_tier", "minimal")).lower()
    high = tier in ("unacceptable", "high")
    gaps: List[dict] = []
    if tier == "unacceptable":
        gaps.append({"gap": "prohibited_practice", "severity": "critical", "note": "EU AI Act prohibits this practice; recommend suspension (mutating, approval required)"})
    if t.get("fairness_gap"):
        gaps.append({"gap": "fairness_gap", "severity": "critical" if high else "high", "note": "measured fairness disparity; recommend mandatory retraining (mutating)"})
    if not t.get("human_oversight", True):
        gaps.append({"gap": "no_human_oversight", "severity": "critical" if high else "medium", "note": "high-risk systems require human oversight (Art. 14)" if high else "add human oversight"})
    if not t.get("model_card_complete", True):
        gaps.append({"gap": "model_card_incomplete", "severity": "high" if high else "medium", "note": "complete the model card / technical documentation (Art. 11)"})
    if not t.get("explainability", True):
        gaps.append({"gap": "no_explainability", "severity": "high" if high else "low", "note": "add decision explainability"})
    gaps.sort(key=lambda g: -SEV_RANK[g["severity"]])
    crit = [g for g in gaps if g["severity"] == "critical"]
    mutating = tier == "unacceptable" or any(g["gap"] in ("fairness_gap",) for g in gaps)
    severity = gaps[0]["severity"] if gaps else "low"
    exit_code = 2 if crit else 1 if gaps else 0
    action = (f"{system}: {len(crit)} critical governance gap(s) — " + "; ".join(g["note"] for g in crit[:2])[:180] + ". Mutating remediation requires approval." if crit else
              f"{system}: {len(gaps)} governance gap(s) to close." if gaps else
              f"{system}: EU AI Act governance complete for tier '{tier}'.")
    key = [f"{system}: risk tier '{tier}'; {len(gaps)} gap(s) ({len(crit)} critical)"]
    key += [f"{g['severity']} {g['gap']}: {g['note']}" for g in gaps[:6]]
    evidence = [{"source": f"local://{rel}" if rel else "local://platform-ai/ai-ethics-governance/SKILL.md", "ref": "AI system descriptor"},
                {"source": "https://artificialintelligenceact.eu/", "ref": "EU AI Act risk tiers"},
                {"source": "local://platform-ai/ai-ethics-governance/SKILL.md", "ref": "action classification table"}]
    return {"agent_slug": SLUG, "intent_type": "advise", "action": action,
            "rationale": ("Governance gaps are scored against the EU AI Act risk tier: an unacceptable-tier practice is critical and prohibited, and for a high-risk system a fairness gap or "
                          "absent human oversight is critical. Assessment is read-only; suspension, tier change and mandatory retraining are mutating policy changes requiring approval."),
            "confidence": 0.85, "severity": severity, "key_findings": key, "evidence_references": evidence,
            "next_agents": ["ciso-brief-generator"] if crit else [], "human_approval_required": bool(mutating and crit), "timestamp_utc": _now(),
            "risk_tier": tier, "gaps": gaps, "mitre_ttps": [], "affected_assets": [str(system)], "_exit": exit_code}


def main() -> int:
    ap = argparse.ArgumentParser(description="USAP ai-ethics-governance")
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
    print(json.dumps(p, indent=2) if args.output == "json" else f"ai-ethics-governance: severity={p['severity']}")
    return code


if __name__ == "__main__":
    raise SystemExit(main())
