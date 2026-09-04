#!/usr/bin/env python3
"""persona-coverage-audit_tool.py

Measures whether security-relevant sessions carried a USAP persona pass.
Reads the hash-chained audit log written by the persona gate and, optionally,
Claude Code session transcripts, and emits the 11-field payload.

Two modes:

  Fixture mode (deterministic, used in CI):
      python3 persona-coverage-audit_tool.py --input fixture.json --output json

  Live mode (collects, then analyses with the same code path):
      python3 persona-coverage-audit_tool.py --audit-dir ~/.usap/audit \
          --transcripts-dir ~/.claude/projects --since-days 7 --output json

Input schema (fixture mode; live mode produces the same structure):
  {
    "since_days": 7,
    "audit_entries": [ {"event": "persona_pass", "session_id": "...", "pass": "DR",
                        "residual_risk": "medium", "timestamp_utc": "..."} ],
    "sessions": [ {"session_id": "...", "started_utc": "...",
                   "tools_used": ["Edit", "Bash"],
                   "gated_paths_touched": ["/repo/.github/workflows/x.yml"],
                   "hook_seen": true} ]
  }

Privacy (DR-5): the transcript collector reads JSON keys only. Message text
is never assigned to a variable that reaches the output; only session ids,
timestamps, tool names and gated file paths are kept.

Exit codes: 0 every gated session has a pass; 1 some do not; 2 gated
sessions exist and no pass was recorded at all.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Dict, List, Optional

SLUG = "persona-coverage-audit"
REPO_ROOT = Path(__file__).resolve().parents[3]
GATE = REPO_ROOT / "plugins" / "usap" / "hooks" / "usap_gate.py"
WRITE_TOOLS = {"Edit", "Write", "MultiEdit", "NotebookEdit"}


def _load_is_gated():
    """Reuse the gate's path rules so the audit measures exactly what the gate enforces."""
    if GATE.exists():
        import importlib.util
        spec = importlib.util.spec_from_file_location("usap_gate", GATE)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)  # type: ignore[union-attr]
        return mod.is_gated_path
    return lambda p, cwd=None: False


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


# ---------------------------------------------------------------- collectors
def collect_audit(audit_dir: Path, since_days: int) -> List[dict]:
    out: List[dict] = []
    if not audit_dir.is_dir():
        return out
    cutoff = datetime.now(timezone.utc) - timedelta(days=since_days)
    for f in sorted(audit_dir.glob("*.jsonl")):
        try:
            day = datetime.strptime(f.stem, "%Y-%m-%d").replace(tzinfo=timezone.utc)
        except ValueError:
            continue
        if day < cutoff - timedelta(days=1):
            continue
        for ln in f.read_text(encoding="utf-8").splitlines():
            try:
                e = json.loads(ln)
            except json.JSONDecodeError:
                continue
            if e.get("event") in ("persona_pass", "gate_prompt"):
                out.append({k: e.get(k) for k in ("event", "session_id", "persona", "pass", "residual_risk", "timestamp_utc")})
    return out


def collect_sessions(transcripts_dir: Path, since_days: int) -> List[dict]:
    is_gated = _load_is_gated()
    cutoff = datetime.now(timezone.utc) - timedelta(days=since_days)
    sessions: Dict[str, dict] = {}
    if not transcripts_dir.is_dir():
        return []
    for f in transcripts_dir.rglob("*.jsonl"):
        try:
            if datetime.fromtimestamp(f.stat().st_mtime, tz=timezone.utc) < cutoff:
                continue
        except OSError:
            continue
        with f.open(encoding="utf-8", errors="replace") as fh:
            for ln in fh:
                try:
                    rec = json.loads(ln)
                except json.JSONDecodeError:
                    continue
                sid = rec.get("sessionId") or rec.get("session_id")
                if not sid:
                    continue
                s = sessions.setdefault(sid, {"session_id": sid, "started_utc": rec.get("timestamp"),
                                              "tools_used": set(), "gated_paths_touched": set(), "hook_seen": False})
                msg = rec.get("message") or {}
                content = msg.get("content") if isinstance(msg, dict) else None
                if isinstance(content, list):
                    for item in content:
                        if not isinstance(item, dict) or item.get("type") != "tool_use":
                            continue
                        name = item.get("name")
                        if isinstance(name, str):
                            s["tools_used"].add(name)
                        inp = item.get("input") if isinstance(item.get("input"), dict) else {}
                        path = inp.get("file_path") or inp.get("notebook_path")
                        if name in WRITE_TOOLS and isinstance(path, str) and is_gated(path, rec.get("cwd")):
                            s["gated_paths_touched"].add(path)
                # Hook output is recorded as a system/user record naming the gate; we only test for the marker string in a known key.
                if isinstance(rec.get("hook_event_name"), str) or rec.get("type") == "hook":
                    s["hook_seen"] = True
    out = []
    for s in sessions.values():
        out.append({"session_id": s["session_id"], "started_utc": s["started_utc"],
                    "tools_used": sorted(s["tools_used"]), "gated_paths_touched": sorted(s["gated_paths_touched"]),
                    "hook_seen": bool(s["hook_seen"])})
    return sorted(out, key=lambda x: (x["started_utc"] or "", x["session_id"]))


# ------------------------------------------------------------------ analysis
def analyse(data: dict) -> dict:
    since = int(data.get("since_days", 7))
    entries = data.get("audit_entries") or []
    sessions = data.get("sessions") or []
    passes = [e for e in entries if e.get("event") == "persona_pass"]
    prompts_flagged = [e for e in entries if e.get("event") == "gate_prompt"]
    pass_sessions = {e.get("session_id") for e in passes}

    gated = [s for s in sessions if s.get("gated_paths_touched")]
    covered = [s for s in gated if s["session_id"] in pass_sessions]
    uncovered = [s for s in gated if s["session_id"] not in pass_sessions]
    no_hook = [s for s in gated if not s.get("hook_seen")]

    by_pass: Dict[str, int] = {}
    for e in passes:
        by_pass[e.get("pass") or "?"] = by_pass.get(e.get("pass") or "?", 0) + 1
    risks = [e.get("residual_risk") for e in passes if e.get("residual_risk")]

    if gated and not passes:
        severity, exit_code = "high", 2
        action = "Zero persona passes were recorded while gated paths were written. Treat as a control failure: verify the plugin hooks are loaded, then review each listed session's changes with a DR pass before the next release."
    elif uncovered:
        severity, exit_code = "medium", 1
        action = f"{len(uncovered)} of {len(gated)} gated sessions carry no pass. Review those changes retrospectively and record the pass; check why the PreToolUse block did not fire (hook_seen false means the plugin was not loaded)."
    elif gated:
        severity, exit_code = "low", 0
        action = "Every gated session carries a recorded pass. Keep the weekly cadence; no action."
    else:
        severity, exit_code = "informational", 0
        action = "No gated paths were written in the window. Nothing to review."

    findings = [
        f"{len(sessions)} session(s) in the last {since} day(s); {len(gated)} wrote gated paths",
        f"{len(passes)} persona pass(es) recorded" + (f" by pass code {json.dumps(by_pass, sort_keys=True)}" if by_pass else ""),
        f"{len(covered)} gated session(s) covered, {len(uncovered)} uncovered",
    ]
    if no_hook:
        findings.append(f"{len(no_hook)} gated session(s) show no hook activity: the plugin gate was not loaded there (DR-7 condition b)")
    if prompts_flagged:
        findings.append(f"{len(prompts_flagged)} prompt(s) matched a trigger and received the gate instruction")
    if risks:
        findings.append("Residual-risk ratings recorded: " + ", ".join(sorted(set(risks))))

    confidence = 0.9 if sessions or entries else 0.5
    return {
        "agent_slug": SLUG,
        "intent_type": "report",
        "action": action,
        "rationale": (
            "Coverage is measured as gated sessions (sessions that wrote CI, IaC, hooks, settings or credential paths) "
            "that carry a persona_pass audit entry with the same session_id. A pass recorded in a different session does not count. "
            "Sessions without hook activity indicate the gate was absent, which is the bypass the design accepted as residual risk."
        ),
        "confidence": confidence,
        "severity": severity,
        "key_findings": findings,
        "evidence_references": [
            {"source": "local://plugins/usap/hooks/hooks.json", "ref": "gate definition (UserPromptSubmit, PreToolUse, Stop)"},
            {"source": "local://standards/output-contract.md", "ref": "human_approval_required hold that the DR chain ends at"},
        ],
        "next_agents": ["metrics-reporting"] if severity in ("high", "medium") else [],
        "human_approval_required": False,
        "timestamp_utc": _now(),
        "coverage": {
            "window_days": since,
            "sessions_total": len(sessions),
            "sessions_gated": len(gated),
            "sessions_covered": len(covered),
            "sessions_uncovered": [s["session_id"] for s in uncovered],
            "sessions_without_hook": [s["session_id"] for s in no_hook],
            "passes_by_code": by_pass,
        },
        "_exit_code": exit_code,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="USAP persona coverage audit")
    ap.add_argument("--input", help="fixture JSON (see module docstring)")
    ap.add_argument("--audit-dir", default=None)
    ap.add_argument("--transcripts-dir", default=None)
    ap.add_argument("--since-days", type=int, default=7)
    ap.add_argument("--output", choices=["text", "json"], default="text")
    args = ap.parse_args()

    if args.input:
        data = json.loads(Path(args.input).read_text(encoding="utf-8"))
    elif args.audit_dir or args.transcripts_dir:
        adir = Path(os.path.expanduser(args.audit_dir or "~/.usap/audit"))
        tdir = Path(os.path.expanduser(args.transcripts_dir or "~/.claude/projects"))
        data = {"since_days": args.since_days,
                "audit_entries": collect_audit(adir, args.since_days),
                "sessions": collect_sessions(tdir, args.since_days)}
    else:
        data = json.loads(sys.stdin.read() or "{}")

    payload = analyse(data)
    exit_code = payload.pop("_exit_code")
    if args.output == "json":
        print(json.dumps(payload, indent=2))
    else:
        print(f"persona-coverage-audit: severity={payload['severity']}")
        for f in payload["key_findings"]:
            print(f"  - {f}")
        print(f"  action: {payload['action']}")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
