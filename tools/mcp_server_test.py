#!/usr/bin/env python3
"""Smoke test for tools/mcp_server.py.

Spawns the MCP server as a subprocess, walks the JSON-RPC handshake, exercises
each tool, and reads one resource. Asserts every step succeeds.

Exit code 0 = all good. Non-zero = something to fix.

Stdlib only — no external dependencies.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


def send(proc: subprocess.Popen, msg: dict) -> None:
    proc.stdin.write(json.dumps(msg) + "\n")
    proc.stdin.flush()


def recv(proc: subprocess.Popen, timeout: float = 10.0) -> dict:
    start = time.time()
    while time.time() - start < timeout:
        line = proc.stdout.readline()
        if line:
            return json.loads(line)
    raise TimeoutError("MCP server did not respond within timeout")


def main() -> int:
    proc = subprocess.Popen(
        [sys.executable, str(REPO_ROOT / "tools" / "mcp_server.py")],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        cwd=str(REPO_ROOT),
    )

    failures = []

    def check(name, cond, detail=""):
        status = "PASS" if cond else "FAIL"
        line = f"  {status}  {name}"
        if detail and not cond:
            line += f" — {detail}"
        print(line)
        if not cond:
            failures.append(name)

    try:
        # 1. initialize
        send(proc, {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {"protocolVersion": "2025-06-18", "capabilities": {}},
        })
        r = recv(proc)
        check(
            "initialize → serverInfo.name == 'usap'",
            r.get("id") == 1 and r.get("result", {}).get("serverInfo", {}).get("name") == "usap",
            json.dumps(r)[:200],
        )

        # 2. tools/list
        send(proc, {"jsonrpc": "2.0", "id": 2, "method": "tools/list"})
        r = recv(proc)
        tools = r.get("result", {}).get("tools", [])
        tool_names = {t["name"] for t in tools}
        check("tools/list returns 8 tools", len(tools) == 8, f"got {len(tools)}")
        for expected in (
            "list_skills", "list_agents", "get_skill", "get_agent",
            "validate_payload", "route_payload", "list_mcps",
            "dispatch_after_approval",
        ):
            check(f"tools/list includes {expected!r}", expected in tool_names)

        # 3. resources/list
        send(proc, {"jsonrpc": "2.0", "id": 3, "method": "resources/list"})
        r = recv(proc)
        resources = r.get("result", {}).get("resources", [])
        check(
            "resources/list returns ≥79 skills + 12 agents",
            len(resources) >= 91,
            f"got {len(resources)}",
        )

        # 4. tools/call list_skills filtered by domain
        send(proc, {
            "jsonrpc": "2.0", "id": 4, "method": "tools/call",
            "params": {"name": "list_skills", "arguments": {"domain": "detection"}},
        })
        r = recv(proc)
        text = r.get("result", {}).get("content", [{}])[0].get("text", "")
        check("list_skills(domain=detection) mentions threat-hunting", "threat-hunting" in text)

        # 5. tools/call list_agents
        send(proc, {
            "jsonrpc": "2.0", "id": 5, "method": "tools/call",
            "params": {"name": "list_agents", "arguments": {}},
        })
        r = recv(proc)
        text = r.get("result", {}).get("content", [{}])[0].get("text", "")
        check("list_agents mentions cs-security-analyst", "cs-security-analyst" in text)
        check("list_agents mentions cs-ciso-advisor", "cs-ciso-advisor" in text)

        # 6. tools/call get_agent (Alex)
        send(proc, {
            "jsonrpc": "2.0", "id": 6, "method": "tools/call",
            "params": {"name": "get_agent", "arguments": {"slug": "cs-security-analyst"}},
        })
        r = recv(proc)
        text = r.get("result", {}).get("content", [{}])[0].get("text", "")
        check("get_agent(cs-security-analyst) returns 'Alex'", "Alex" in text)

        # 7. tools/call get_skill (vuln-scan)
        send(proc, {
            "jsonrpc": "2.0", "id": 7, "method": "tools/call",
            "params": {"name": "get_skill", "arguments": {"slug": "vuln-scan"}},
        })
        r = recv(proc)
        text = r.get("result", {}).get("content", [{}])[0].get("text", "")
        check("get_skill(vuln-scan) returns persona section", "## Persona" in text)

        # 8. tools/call validate_payload (a real committed sample)
        sample = json.loads((REPO_ROOT / "appsec-devsecops/vuln-scan/expected_outputs/sample_output.json").read_text())
        send(proc, {
            "jsonrpc": "2.0", "id": 8, "method": "tools/call",
            "params": {"name": "validate_payload", "arguments": {"payload": sample}},
        })
        r = recv(proc)
        text = r.get("result", {}).get("content", [{}])[0].get("text", "")
        check("validate_payload(vuln-scan sample) returns 'PASS'", text.strip() == "PASS")

        # 9. tools/call validate_payload (broken payload — missing required fields)
        send(proc, {
            "jsonrpc": "2.0", "id": 9, "method": "tools/call",
            "params": {"name": "validate_payload", "arguments": {"payload": {"agent_slug": "test"}}},
        })
        r = recv(proc)
        text = r.get("result", {}).get("content", [{}])[0].get("text", "")
        check("validate_payload(missing fields) reports violations", text != "PASS" and len(text) > 0)

        # 10. resources/read on a skill URI
        send(proc, {
            "jsonrpc": "2.0", "id": 10, "method": "resources/read",
            "params": {"uri": "usap://skill/appsec-devsecops/vuln-scan"},
        })
        r = recv(proc)
        contents = r.get("result", {}).get("contents", [])
        text = contents[0].get("text", "") if contents else ""
        check("resources/read(vuln-scan) returns SKILL.md body", "vuln-scan" in text.lower())

        # 11. unknown method returns -32601
        send(proc, {"jsonrpc": "2.0", "id": 99, "method": "no/such/method"})
        r = recv(proc)
        check(
            "unknown method returns JSON-RPC -32601",
            r.get("error", {}).get("code") == -32601,
            json.dumps(r)[:200],
        )

        # ─── Phase 2 routing assertions ─────────────────────────────────
        # 12. list_mcps shows 7 entries from the registry
        send(proc, {
            "jsonrpc": "2.0", "id": 12, "method": "tools/call",
            "params": {"name": "list_mcps", "arguments": {}},
        })
        r = recv(proc)
        text = r.get("result", {}).get("content", [{}])[0].get("text", "")
        check("list_mcps mentions slack + github + crowdstrike",
              all(x in text for x in ("slack", "github", "crowdstrike")))

        # 13. route_payload — detect intent dispatches to splunk (enabled in Phase 3)
        detect_payload = {
            "intent_type": "detect",
            "next_agents": ["cs-security-analyst"],
            "human_approval_required": False,
            "dispatch_args": {"spl": "index=okta_logs failed_login"},
        }
        send(proc, {
            "jsonrpc": "2.0", "id": 13, "method": "tools/call",
            "params": {"name": "route_payload", "arguments": {"payload": detect_payload}},
        })
        r = recv(proc, timeout=30.0)
        text = r.get("result", {}).get("content", [{}])[0].get("text", "")
        decision = json.loads(text)
        check("route_payload(detect) dispatches to splunk",
              decision.get("status") == "dispatched" and decision.get("selected_mcp") == "splunk",
              f"got {decision}")
        check("route_payload(detect) dispatch outcome is ok",
              decision.get("outcome", {}).get("ok") is True)

        # 14. route_payload — human_approval_required: true on a real sample
        sample = json.loads((REPO_ROOT / "appsec-devsecops/threat-model/expected_outputs/sample_output.json").read_text())
        send(proc, {
            "jsonrpc": "2.0", "id": 14, "method": "tools/call",
            "params": {"name": "route_payload", "arguments": {"payload": sample}},
        })
        r = recv(proc)
        text = r.get("result", {}).get("content", [{}])[0].get("text", "")
        # The contract: routing returns a known status, not an error.
        # Valid Phase 3 statuses: dispatched, dispatch_failed, approval_required,
        # no_match (and the legacy would_dispatch from Phase 2 if anyone holds an
        # old client open).
        decision = json.loads(text)
        check("route_payload returns a known status",
              decision.get("status") in (
                  "no_match", "approval_required", "would_dispatch",
                  "dispatched", "dispatch_failed",
              ),
              f"got {decision.get('status')!r}")
        check("route_payload result includes a phase marker",
              decision.get("phase") in (2, 3) or decision.get("status") == "no_match")

        # ─── Phase 3 dispatch assertions ─────────────────────────────────
        # 15. approval gate: route_payload issues a single-use token; dispatch
        #     works with it once and never with a literal.
        gated = {
            "intent_type": "escalate", "next_agents": ["cs-incident-responder"],
            "human_approval_required": True,
            "dispatch_args": {"channel": "#ir-channel", "text": "SEV-2 declared at 15:24Z"},
        }
        send(proc, {"jsonrpc": "2.0", "id": 150, "method": "tools/call",
                    "params": {"name": "route_payload", "arguments": {"payload": gated}}})
        r = recv(proc, timeout=30.0)
        gate = json.loads(r.get("result", {}).get("content", [{}])[0].get("text", "{}"))
        check("route_payload(gated) returns approval_required with a token",
              gate.get("status") == "approval_required" and bool(gate.get("approval_token")),
              f"got {gate}")
        dispatch_args = {"mcp_id": gate.get("selected_mcp"), "capability_id": gate.get("selected_capability"),
                         "arguments": gated["dispatch_args"], "approval_token": gate.get("approval_token")}
        send(proc, {"jsonrpc": "2.0", "id": 15, "method": "tools/call",
                    "params": {"name": "dispatch_after_approval", "arguments": dispatch_args}})
        r = recv(proc, timeout=30.0)
        decision = json.loads(r.get("result", {}).get("content", [{}])[0].get("text", "{}"))
        check("dispatch_after_approval with the issued token dispatches",
              decision.get("status") == "dispatched" and decision.get("outcome", {}).get("ok") is True,
              f"got {decision}")
        send(proc, {"jsonrpc": "2.0", "id": 151, "method": "tools/call",
                    "params": {"name": "dispatch_after_approval", "arguments": dispatch_args}})
        r = recv(proc, timeout=30.0)
        decision = json.loads(r.get("result", {}).get("content", [{}])[0].get("text", "{}"))
        check("a consumed token is rejected",
              decision.get("status") == "dispatch_failed" and "already used" in decision.get("error", ""),
              f"got {decision}")
        send(proc, {"jsonrpc": "2.0", "id": 152, "method": "tools/call",
                    "params": {"name": "dispatch_after_approval",
                               "arguments": {**dispatch_args, "approval_token": "smoke-test-approved"}}})
        r = recv(proc, timeout=30.0)
        decision = json.loads(r.get("result", {}).get("content", [{}])[0].get("text", "{}"))
        check("a literal token is rejected",
              decision.get("status") == "dispatch_failed" and "approval token" in decision.get("error", ""),
              f"got {decision}")

        # 16. dispatch_after_approval on a disabled MCP fails cleanly
        send(proc, {
            "jsonrpc": "2.0", "id": 16, "method": "tools/call",
            "params": {
                "name": "dispatch_after_approval",
                "arguments": {
                    "mcp_id": "crowdstrike",
                    "capability_id": "isolate_host",
                    "arguments": {"host_id": "abc123"},
                },
            },
        })
        r = recv(proc, timeout=15.0)
        text = r.get("result", {}).get("content", [{}])[0].get("text", "")
        decision = json.loads(text)
        check("dispatch_after_approval on disabled MCP returns dispatch_failed",
              decision.get("status") == "dispatch_failed" and "disabled" in decision.get("error", ""))

        # ─── Phase 4 audit chain assertions ─────────────────────────────
        # 17. Audit chain has the expected events from this run.
        audit_dir = os.environ.get("USAP_AUDIT_DIR")
        if audit_dir:
            log_paths = list(Path(audit_dir).glob("*.jsonl"))
            check("audit log file exists", bool(log_paths))
            if log_paths:
                events = []
                for raw in log_paths[0].read_text().splitlines():
                    if raw.strip():
                        events.append(json.loads(raw))
                check("audit log non-empty", len(events) > 0)
                check("every audit entry has prev_hash",
                      all("prev_hash" in e for e in events))
                # First entry's prev_hash is GENESIS
                check("first audit entry prev_hash is GENESIS",
                      events[0].get("prev_hash") == "GENESIS")

                # 18. Verify chain
                sys.path.insert(0, str(REPO_ROOT / "tools"))
                from mcp_audit import verify  # noqa: E402
                ok, errors = verify(log_paths[0])
                check("audit chain verifies", ok, f"errors: {errors[:3]}")

    finally:
        try:
            proc.stdin.close()
        except Exception:
            pass
        try:
            proc.terminate()
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()

    print()
    if failures:
        print(f"FAILED: {len(failures)}")
        for f in failures:
            print(f"  • {f}")
        return 1
    print("All smoke tests passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
