#!/usr/bin/env python3
"""End-to-end USAP master-MCP loop demo (read-only, evidence-producing).

Exercises every phase in one run and writes:

  reports/iso27001-comparison/loop_decisions.json   one entry per step
  $USAP_AUDIT_DIR/<YYYY-MM-DD>.jsonl                live audit chain

Steps:

  1. Phase 1 discovery: list_skills, list_agents, validate_payload on a real
     committed sample (read-only).
  2. Phase 2 routing: route a non-mutating detect payload (auto-dispatched).
  3. Phase 3 dispatch_after_approval: dispatch a mutating slack/post_message
     after surfacing the approval gate.
  4. Phase 4 scheduled-run: simulate one runner tick via
     mcp_router.dispatch_after_approval (the same path the runner uses) and
     emit a 'scheduled_run' event marker.
  5. Phase 4 verify: tools/mcp_audit.verify() on the produced chain.

No registry edits, no mutating actions outside the gated dispatch path, no
remote calls. Adapters run in USAP_ADAPTER_MODE=fixture.

Stdlib only.
"""
from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "tools"))

import mcp_audit  # noqa: E402
import mcp_router  # noqa: E402
import mcp_registry  # noqa: E402


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")


def main() -> int:
    report_dir = REPO / "reports" / "iso27001-comparison"
    report_dir.mkdir(parents=True, exist_ok=True)

    steps = []

    # ── Phase 1: discovery / validation ──────────────────────────────
    sample_path = REPO / "appsec-devsecops/vuln-scan/expected_outputs/sample_output.json"
    sample = json.loads(sample_path.read_text())
    from output_contract import validate_payload  # type: ignore
    violations = validate_payload(sample)
    steps.append({
        "phase": 1,
        "step": "validate_payload(vuln-scan sample)",
        "evidence_path": str(sample_path.relative_to(REPO)),
        "violations": violations,
        "ok": not violations,
    })

    # ── Phase 2: routing a non-mutating detect payload ───────────────
    detect_payload = {
        "agent_slug": "cs-security-analyst",
        "intent_type": "detect",
        "action": "Hunt for failed Okta logins in the last hour",
        "rationale": "Looped demo for ISO 27001 comparison",
        "confidence": 0.92,
        "severity": "informational",
        "key_findings": ["loop-demo synthetic event"],
        "evidence_references": [],
        "next_agents": ["cs-security-analyst"],
        "human_approval_required": False,
        "timestamp_utc": _now(),
        "dispatch_args": {"spl": "index=okta_logs failed_login earliest=-1h"},
    }
    reg = mcp_registry.load_registry()
    decision = mcp_router.route(detect_payload, reg)
    steps.append({
        "phase": 2,
        "step": "route_payload(detect → splunk)",
        "status": decision.get("status"),
        "selected_mcp": decision.get("selected_mcp"),
        "selected_capability": decision.get("selected_capability"),
        "outcome_ok": decision.get("outcome", {}).get("ok"),
    })

    # ── Phase 3: gated dispatch ──────────────────────────────────────
    gated = mcp_router.dispatch_after_approval(
        mcp_id="slack",
        capability_id="post_message",
        arguments={"channel": "#ir-channel", "text": "Loop demo (no human in loop, audit-only)"},
        approval_token="loop-demo-approved",
        registry=reg,
    )
    steps.append({
        "phase": 3,
        "step": "dispatch_after_approval(slack/post_message)",
        "status": gated.get("status"),
        "outcome_ok": gated.get("outcome", {}).get("ok"),
    })

    # ── Phase 4: scheduled-run marker (what the runner emits) ────────
    mcp_audit.write_audit({
        "event": "scheduled_run",
        "job_id": "loop-demo-synthetic-job",
        "payload": detect_payload,
        "decision": {"status": "synthetic", "note": "demo-only marker"},
    })
    scheduled = mcp_router.dispatch_after_approval(
        mcp_id="splunk",
        capability_id="search",
        arguments={"spl": "index=ad_logs auth_failure | stats count by user"},
        approval_token="loop-demo-scheduled",
        registry=reg,
    )
    steps.append({
        "phase": 4,
        "step": "scheduled_run → dispatch (splunk/search)",
        "status": scheduled.get("status"),
        "outcome_ok": scheduled.get("outcome", {}).get("ok"),
    })

    # ── Phase 4: verify the chain we just built ──────────────────────
    log_paths = sorted(mcp_audit.audit_dir().glob("*.jsonl"))
    chain_ok, errors = (False, ["no log produced"])
    if log_paths:
        chain_ok, errors = mcp_audit.verify(log_paths[-1])
    steps.append({
        "phase": 4,
        "step": "mcp_audit.verify(latest log)",
        "log": str(log_paths[-1]) if log_paths else None,
        "ok": chain_ok,
        "errors": errors[:5],
    })

    report = {
        "generated_utc": _now(),
        "audit_dir": str(mcp_audit.audit_dir()),
        "audit_key_set": bool(os.environ.get("USAP_AUDIT_KEY")),
        "steps": steps,
        "audit_entries": [],
    }
    if log_paths:
        for raw in log_paths[-1].read_text().splitlines():
            if raw.strip():
                report["audit_entries"].append(json.loads(raw))

    out = report_dir / "loop_decisions.json"
    out.write_text(json.dumps(report, indent=2) + "\n")
    print(f"Wrote {out.relative_to(REPO)}")
    print(f"Audit log:  {log_paths[-1] if log_paths else '(none)'}")
    print(f"Chain ok:   {chain_ok}")
    print(f"Signed:     {bool(os.environ.get('USAP_AUDIT_KEY'))}")
    return 0 if chain_ok and not any(s.get("status") == "dispatch_failed" for s in steps) else 1


if __name__ == "__main__":
    sys.exit(main())
