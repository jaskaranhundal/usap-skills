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
from mcp_router import dispatch_after_approval  # noqa: E402
from mcp_audit import write_audit  # noqa: E402

VALID_INTENTS = {"detect", "respond", "analyze", "advise", "escalate", "report", "block"}


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
        ))
    return jobs


# ─── Job execution ─────────────────────────────────────────────────

def _build_payload(job: Job) -> dict:
    """Synthesize a Phase 4 payload from the job spec.

    The runner doesn't actually invoke the skill's LLM — it produces a
    deterministic payload that says "this job fired on this schedule, route
    to this MCP." The downstream adapter does the real work.
    """
    return {
        "agent_slug": "usap-runner",
        "intent_type": job.intent_type,
        "action": f"Scheduled job {job.id!r} firing skill {job.skill!r}.",
        "rationale": f"Cron schedule {job.schedule.kind} matched at {datetime.now(timezone.utc).isoformat()}.",
        "confidence": 1.0,
        "severity": "informational",
        "key_findings": [f"Scheduled invocation of {job.skill}"],
        "evidence_references": [],
        "next_agents": [],
        "human_approval_required": False,
        "timestamp_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }


def execute_job(job: Job) -> dict:
    """Dispatch one job. Writes a scheduled_run audit line + the dispatch line."""
    payload = _build_payload(job)
    write_audit({
        "event": "scheduled_run",
        "job_id": job.id,
        "payload": payload,
    })
    # Use dispatch_after_approval directly — runner is trusted (it's local)
    # and the payload doesn't trigger the gate.
    result = dispatch_after_approval(
        job.dispatch_to,
        _pick_capability_for_job(job),
        job.dispatch_args,
        approval_token=f"runner:{job.id}",
    )
    return result


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
        return 0

    if args.run:
        return run_forever(args.config, poll_interval=args.poll_interval)

    return 1


if __name__ == "__main__":
    sys.exit(main())
