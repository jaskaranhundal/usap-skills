#!/usr/bin/env python3
"""USAP Scheduled Persistence Runner — Phase 4.

Cron-style scheduler that fires skill workflows on a clock and dispatches
the result through the USAP routing layer to a downstream specialist MCP.

This is the "always-on coverage" tier — what you turn on when you want
USAP running attack-surface scans every hour, secrets sweeps every morning,
and SIEM anomaly checks every fifteen minutes, posting deltas to Slack /
GitHub issues / PagerDuty without a human starting each run.

Phase 4 ships:

  * Job schema (runner/runner.yaml).
  * Lightweight cron parser supporting:
      - "M H * * *"    fixed minute/hour daily
      - "*/N * * * *"  every N minutes
      - "@every Ns"    every N seconds (testing)
      - "@hourly", "@daily" macros
  * One-shot mode (--once <job-id>) for testing.
  * Foreground daemon mode (--run) that polls every 30s.
  * Audit chain integration: every job execution writes a signed audit line.

Stdlib only.
"""
from __future__ import annotations

import argparse
import json
import re
import signal
import subprocess
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_RUNNER_CONFIG = REPO_ROOT / "runner" / "runner.yaml"

sys.path.insert(0, str(REPO_ROOT / "tools"))
from mcp_registry import parse_yaml, load_registry  # noqa: E402
from mcp_router import dispatch_unattended  # noqa: E402
from mcp_audit import write_audit  # noqa: E402

VALID_INTENTS = {"detect", "respond", "analyze", "advise", "escalate", "report", "block"}

ACTIVE_DOMAINS = [
    "appsec-devsecops", "cloud-infra", "detection", "governance", "identity-access",
    "pentest", "platform-ai", "red-team", "response", "risk-compliance",
    "system-security", "webapp-security",
]
TOOL_TIMEOUT_SECONDS = 60
MAX_STDOUT_BYTES = 512 * 1024
from output_contract import validate_payload  # noqa: E402


# ─── Schedule parsing ──────────────────────────────────────────────

@dataclass
class Schedule:
    """Parsed cron-like schedule. Phase 4 supports a deliberately small subset."""
    kind: str           # "every_seconds" | "every_minutes" | "daily_at" | "macro"
    seconds: int = 0
    minute: int = 0
    hour: int = 0
    macro: str = ""

    def fires_at(self, now: datetime, last_fire: Optional[datetime]) -> bool:
        if self.kind == "every_seconds":
            if last_fire is None:
                return True
            return (now - last_fire).total_seconds() >= self.seconds
        if self.kind == "every_minutes":
            if last_fire is None:
                return True
            return (now - last_fire).total_seconds() >= self.minute * 60
        if self.kind == "daily_at":
            if now.hour != self.hour or now.minute != self.minute:
                return False
            if last_fire is None:
                return True
            return last_fire.date() != now.date()
        if self.kind == "macro":
            if self.macro == "@hourly":
                if last_fire is None:
                    return True
                return (now - last_fire).total_seconds() >= 3600
            if self.macro == "@daily":
                if last_fire is None:
                    return True
                return last_fire.date() != now.date()
        return False


def parse_schedule(spec: str) -> Schedule:
    spec = spec.strip()
    if spec.startswith("@every"):
        m = re.match(r"@every\s+(\d+)s", spec)
        if not m:
            raise ValueError(f"@every must be @every Ns, got {spec!r}")
        return Schedule(kind="every_seconds", seconds=int(m.group(1)))
    if spec == "@hourly":
        return Schedule(kind="macro", macro="@hourly")
    if spec == "@daily":
        return Schedule(kind="macro", macro="@daily")
    parts = spec.split()
    if len(parts) != 5:
        raise ValueError(f"Cron must have 5 fields or be a supported macro, got {spec!r}")
    m, h, dom, mon, dow = parts
    if dom != "*" or mon != "*" or dow != "*":
        raise ValueError("Phase 4 supports only daily/minutely schedules (* * * for DoM/Month/DoW).")
    if m.startswith("*/"):
        try:
            n = int(m[2:])
        except ValueError as exc:
            raise ValueError(f"Bad */N expression: {m!r}") from exc
        if h != "*":
            raise ValueError("*/N is only supported in the minute field with hour=*.")
        return Schedule(kind="every_minutes", minute=n)
    try:
        return Schedule(kind="daily_at", minute=int(m), hour=int(h))
    except ValueError as exc:
        raise ValueError(f"Couldn't parse cron {spec!r}") from exc


# ─── Job loader ────────────────────────────────────────────────────

@dataclass
class Job:
    id: str
    skill: str
    schedule: Schedule
    intent_type: str
    dispatch_to: str
    dispatch_args: dict
    enabled: bool
    input: Optional[str] = None


def load_jobs(path: Path | None = None) -> list[Job]:
    path = path or DEFAULT_RUNNER_CONFIG
    if not path.is_file():
        raise FileNotFoundError(f"Runner config not found: {path}")
    parsed = parse_yaml(path.read_text(encoding="utf-8"))
    if not isinstance(parsed, dict) or parsed.get("version") != 1:
        raise ValueError("Runner config must have version: 1")
    jobs_raw = parsed.get("jobs") or []
    jobs: list[Job] = []
    seen: set[str] = set()
    for raw in jobs_raw:
        if not isinstance(raw, dict):
            raise ValueError(f"Job entry must be a mapping: {raw!r}")
        jid = raw.get("id")
        if not jid:
            raise ValueError("Job missing `id`")
        if jid in seen:
            raise ValueError(f"Duplicate job id: {jid}")
        seen.add(jid)
        skill = raw.get("skill")
        if not skill:
            raise ValueError(f"Job {jid}: missing `skill`")
        schedule = parse_schedule(str(raw.get("schedule", "")))
        intent = raw.get("intent_type", "report")
        if intent not in VALID_INTENTS:
            raise ValueError(f"Job {jid}: invalid intent_type {intent!r}")
        jobs.append(Job(
            id=jid,
            skill=skill,
            schedule=schedule,
            intent_type=intent,
            dispatch_to=raw.get("dispatch_to", ""),
            dispatch_args=raw.get("dispatch_args") or {},
            enabled=bool(raw.get("enabled", False)),
            input=raw.get("input"),
        ))
    return jobs


# ─── Job execution ─────────────────────────────────────────────────

def _locate_tool(slug: str) -> Optional[Path]:
    for dom in ACTIVE_DOMAINS:
        cand = REPO_ROOT / dom / slug / "scripts" / f"{slug}_tool.py"
        if cand.is_file():
            return cand
    return None


def _resolve_input(job: Job) -> Optional[Path]:
    if not job.input:
        return None
    try:
        p = (REPO_ROOT / job.input).resolve()
        p.relative_to(REPO_ROOT)  # contain to the repo
    except (ValueError, OSError):
        return None
    return p if p.is_file() else None


def run_skill(job: Job) -> dict:
    """Run the skill's own tool and return {ok, payload|None, reason}.

    ok is True only when the tool produced a contract-conformant, non-stub
    payload. A stub, an unparseable payload, a gate failure, a timeout or a
    missing tool returns ok=False with a reason and is never dispatched
    (design: docs/design/2026-09-05-runner-real-tools-dr.md).
    """
    tool = _locate_tool(job.skill)
    if tool is None:
        return {"ok": False, "payload": None, "reason": f"no tool script for skill {job.skill!r} in any active domain"}
    if not job.input:
        return {"ok": False, "payload": None, "reason": "job has no `input`; a scheduled real run needs a fixture or live input to analyse"}
    inp = _resolve_input(job)
    if inp is None:
        return {"ok": False, "payload": None, "reason": f"input {job.input!r} not found under the repository"}
    cmd = [sys.executable, str(tool), "--output", "json", "--input", str(inp)]
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=TOOL_TIMEOUT_SECONDS, cwd=str(REPO_ROOT))
    except subprocess.TimeoutExpired:
        return {"ok": False, "payload": None, "reason": f"tool timed out after {TOOL_TIMEOUT_SECONDS}s"}
    except OSError as exc:
        return {"ok": False, "payload": None, "reason": f"tool could not be launched: {exc}"}
    out = proc.stdout or ""
    if len(out.encode("utf-8", "replace")) > MAX_STDOUT_BYTES:
        return {"ok": False, "payload": None, "reason": "tool output exceeded the size cap"}
    if proc.returncode == 3:
        return {"ok": False, "payload": None, "reason": "tool is a declared stub (exit 3)"}
    try:
        payload = json.loads(out)
    except json.JSONDecodeError:
        return {"ok": False, "payload": None, "reason": f"tool output was not JSON (exit {proc.returncode})"}
    if not isinstance(payload, dict) or payload.get("status") == "not_implemented":
        return {"ok": False, "payload": None, "reason": "tool reported not_implemented"}
    violations = validate_payload(payload, evidence_gate=True, score_checks=False)
    if violations:
        return {"ok": False, "payload": None, "reason": "payload failed the output contract: " + "; ".join(violations[:3])}
    return {"ok": True, "payload": payload, "reason": ""}


def execute_job(job: Job) -> dict:
    """Run the skill tool, then dispatch a real payload — or record why not."""
    result = run_skill(job)
    if not result["ok"]:
        decision = {"status": "skipped", "job_id": job.id, "skill": job.skill, "reason": result["reason"]}
        write_audit({"event": "runner_skipped", "job_id": job.id, "decision": decision})
        return decision
    payload = result["payload"]
    write_audit({"event": "scheduled_run", "job_id": job.id, "payload": payload})
    dispatched = dispatch_unattended(
        job.dispatch_to,
        _pick_capability_for_job(job),
        job.dispatch_args,
    )
    dispatched.setdefault("skill", job.skill)
    dispatched.setdefault("skill_severity", payload.get("severity"))
    return dispatched


def _pick_capability_for_job(job: Job) -> str:
    """Use the registry to pick the right capability for a job."""
    reg = load_registry()
    mcp = next((m for m in reg["mcps"] if m["id"] == job.dispatch_to), None)
    if not mcp:
        return ""
    # If the dispatch_args mention a known capability hint, use it.
    for cap in mcp["capabilities"]:
        if cap.get("approval_required"):
            continue  # runner never invokes mutating capabilities
        return cap["id"]
    return mcp["capabilities"][0]["id"] if mcp["capabilities"] else ""


# ─── Daemon loop ───────────────────────────────────────────────────

def run_forever(config: Path, poll_interval: float = 30.0) -> int:
    jobs = load_jobs(config)
    enabled = [j for j in jobs if j.enabled]
    if not enabled:
        print("[runner] no enabled jobs; nothing to do.", file=sys.stderr)
        return 0
    last_fire: dict[str, datetime] = {}
    stop = {"flag": False}

    def _on_sig(_sig, _frame):
        stop["flag"] = True
        print("[runner] received stop signal; finishing current cycle.")

    signal.signal(signal.SIGINT, _on_sig)
    signal.signal(signal.SIGTERM, _on_sig)

    print(f"[runner] starting with {len(enabled)} job(s) at {datetime.now(timezone.utc).isoformat()}")
    while not stop["flag"]:
        now = datetime.now(timezone.utc)
        for job in enabled:
            if job.schedule.fires_at(now, last_fire.get(job.id)):
                print(f"[runner] firing job {job.id}")
                try:
                    res = execute_job(job)
                    print(f"[runner]   → {res.get('status')} via {job.dispatch_to}")
                except Exception as exc:  # noqa: BLE001 — daemon should keep running
                    print(f"[runner]   ! job {job.id} crashed: {exc}", file=sys.stderr)
                last_fire[job.id] = now
        for _ in range(int(poll_interval)):
            if stop["flag"]:
                break
            time.sleep(1)
    print("[runner] stopped.")
    return 0


# ─── CLI ───────────────────────────────────────────────────────────

def main() -> int:
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--validate", action="store_true", help="Validate the runner config and exit.")
    g.add_argument("--list", action="store_true", help="List configured jobs.")
    g.add_argument("--once", metavar="JOB_ID", help="Run one job once, ignoring schedule.")
    g.add_argument("--run", action="store_true", help="Run the scheduler in the foreground.")
    ap.add_argument("--config", type=Path, default=DEFAULT_RUNNER_CONFIG)
    ap.add_argument("--poll-interval", type=float, default=30.0,
                    help="Seconds between schedule checks in --run mode.")
    args = ap.parse_args()

    try:
        jobs = load_jobs(args.config)
    except (FileNotFoundError, ValueError) as exc:
        print(f"Config error: {exc}", file=sys.stderr)
        return 1

    if args.validate:
        print(f"OK  {len(jobs)} job(s) loaded ({sum(1 for j in jobs if j.enabled)} enabled)")
        return 0

    if args.list:
        for j in jobs:
            status = "enabled" if j.enabled else "disabled"
            print(f"  {j.id:<28} {status:<10} skill={j.skill:<28} schedule={j.schedule.kind}  dispatch_to={j.dispatch_to}")
        return 0

    if args.once:
        target = next((j for j in jobs if j.id == args.once), None)
        if not target:
            print(f"Unknown job id: {args.once}", file=sys.stderr)
            return 1
        result = execute_job(target)
        print(json.dumps(result, indent=2))
        # A one-shot job that did not dispatch is a failure for whatever
        # automation invoked it (Codex review on PR #148, comment 3936197828).
        return 0 if result.get("status") == "dispatched" else 2

    if args.run:
        return run_forever(args.config, poll_interval=args.poll_interval)

    return 1


if __name__ == "__main__":
    sys.exit(main())
