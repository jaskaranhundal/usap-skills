#!/usr/bin/env python3
"""USAP MCP Server — Phase 1 (read-only discovery + load).

Exposes USAP as a Model Context Protocol server over stdio. Any MCP-compatible
client (Claude Code, Cursor, Codex CLI, Gemini CLI, Goose, OpenCode) can:

  * Discover the 80 USAP skills and 13 cs-* orchestrator agents
  * Load any skill or agent definition into the client's LLM context
  * Validate a payload against the 11-field output contract

Phase 1 is read-only — no mutating actions, no specialist-MCP routing. That is
the Phase 2 work that turns USAP into the master MCP orchestrating other
vendor MCPs (SIEM, EDR, firewall, etc.) with the contract's
`human_approval_required` field enforcing the human gate.

Stdlib only. JSON-RPC 2.0 over stdio. No external dependencies.

Spec: https://modelcontextprotocol.io/specification

Usage::

    python3 tools/mcp_server.py

The server reads JSON-RPC frames from stdin (one JSON object per line) and
writes responses to stdout. Clients launch it via stdio transport — see
``docs/mcp-server.md`` for client config examples.
"""
from __future__ import annotations

import json
import sys
import traceback
from pathlib import Path
from typing import Any, Optional

REPO_ROOT = Path(__file__).resolve().parent.parent

PROTOCOL_VERSION = "2025-06-18"
SERVER_NAME = "usap"
SERVER_VERSION = "1.13.0"

ACTIVE_DOMAINS = [
    "appsec-devsecops", "cloud-infra", "detection", "governance",
    "identity-access", "pentest", "platform-ai", "red-team", "response",
    "risk-compliance", "system-security", "webapp-security",
]

CS_AGENTS = [
    ("security", "cs-security-analyst"),
    ("security", "cs-incident-responder"),
    ("security", "cs-red-teamer"),
    ("security", "cs-blue-team-analyst"),
    ("security", "cs-cloud-investigator"),
    ("security", "cs-supply-chain-defender"),
    ("security", "cs-threat-intel-lead"),
    ("security", "cs-purple-team-lead"),
    ("appsec", "cs-appsec-engineer"),
    ("devsecops", "cs-devsecops-engineer"),
    ("executive", "cs-ciso-advisor"),
    ("governance", "cs-security-program-manager"),
    ("meta", "cs-usap-next"),
]


# ─── Frontmatter parsing ────────────────────────────────────────────────

def parse_frontmatter(text: str) -> dict:
    """Minimal YAML frontmatter parser.

    Handles simple key: value pairs and folded (>) / literal (|) scalars.
    Not a full YAML implementation; sufficient for USAP's frontmatter shape.
    Returns an empty dict on any parse difficulty.
    """
    if not text.startswith("---"):
        return {}
    end = text.find("\n---", 4)
    if end == -1:
        return {}
    fm_text = text[4:end].strip()
    fm: dict = {}
    lines = fm_text.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i]
        if not line.strip() or line.lstrip().startswith("#"):
            i += 1
            continue
        if ":" in line and not line.startswith((" ", "\t")):
            key, _, val = line.partition(":")
            key = key.strip()
            val = val.strip()
            if val in (">", "|"):
                # Folded / literal scalar — collect indented lines
                fold = val == ">"
                i += 1
                collected = []
                while i < len(lines) and (
                    lines[i].startswith((" ", "\t")) or not lines[i].strip()
                ):
                    if lines[i].strip():
                        collected.append(lines[i].strip())
                    i += 1
                fm[key] = " ".join(collected) if fold else "\n".join(collected)
            else:
                fm[key] = val.strip('"\'')
                i += 1
        else:
            i += 1
    return fm


# ─── Skill / agent loaders ─────────────────────────────────────────────

def load_skills() -> list[dict]:
    """Return a list of {slug, domain, description, path} for every active skill."""
    skills = []
    for domain in ACTIVE_DOMAINS:
        d = REPO_ROOT / domain
        if not d.is_dir():
            continue
        for sdir in sorted(p for p in d.iterdir() if p.is_dir()):
            skill_md = sdir / "SKILL.md"
            if not skill_md.is_file():
                continue
            try:
                fm = parse_frontmatter(skill_md.read_text(encoding="utf-8"))
            except Exception:
                fm = {}
            skills.append({
                "slug": sdir.name,
                "domain": domain,
                "description": fm.get("description", ""),
                "path": str(skill_md.relative_to(REPO_ROOT)),
            })
    return skills


def load_agents() -> list[dict]:
    """Return a list of {slug, group, description, path} for the 13 cs-* agents."""
    agents = []
    for group, slug in CS_AGENTS:
        agent_md = REPO_ROOT / "agents" / group / f"{slug}.md"
        if not agent_md.is_file():
            continue
        try:
            fm = parse_frontmatter(agent_md.read_text(encoding="utf-8"))
        except Exception:
            fm = {}
        agents.append({
            "slug": slug,
            "group": group,
            "description": fm.get("description", ""),
            "path": str(agent_md.relative_to(REPO_ROOT)),
        })
    return agents


def read_file(rel_path: str) -> str:
    p = REPO_ROOT / rel_path
    if not p.is_file():
        raise FileNotFoundError(f"File not found: {rel_path}")
    return p.read_text(encoding="utf-8")


# ─── MCP method handlers ───────────────────────────────────────────────

def handle_initialize(params: dict) -> dict:
    return {
        "protocolVersion": PROTOCOL_VERSION,
        "capabilities": {
            "tools": {},
            "resources": {},
        },
        "serverInfo": {
            "name": SERVER_NAME,
            "version": SERVER_VERSION,
        },
    }


TOOLS = [
    {
        "name": "list_skills",
        "description": (
            "List USAP skills with one-line descriptions. Optionally filter by "
            "domain (one of: appsec-devsecops, cloud-infra, detection, "
            "governance, identity-access, pentest, platform-ai, red-team, "
            "response, risk-compliance, system-security, webapp-security)."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "domain": {
                    "type": "string",
                    "description": "Optional domain filter",
                },
            },
        },
    },
    {
        "name": "list_agents",
        "description": "List the 12 cs-* USAP orchestrator agents.",
        "inputSchema": {"type": "object", "properties": {}},
    },
    {
        "name": "get_skill",
        "description": (
            "Return the full SKILL.md content for one skill. Use this to load "
            "a skill as a system prompt in the client's LLM context."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "slug": {
                    "type": "string",
                    "description": "The skill slug, e.g. 'vuln-scan' or 'threat-hunting'",
                },
            },
            "required": ["slug"],
        },
    },
    {
        "name": "get_agent",
        "description": (
            "Return the full agent definition for one cs-* orchestrator agent. "
            "Use this to activate the agent persona in the client's LLM."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "slug": {
                    "type": "string",
                    "description": "The agent slug, e.g. 'cs-security-analyst'",
                },
            },
            "required": ["slug"],
        },
    },
    {
        "name": "validate_payload",
        "description": (
            "Validate a JSON payload against the USAP 11-field output contract "
            "(agent_slug, intent_type, action, rationale, confidence, severity, "
            "key_findings, evidence_references, next_agents, "
            "human_approval_required, timestamp_utc). Returns 'PASS' or a list "
            "of violations."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "payload": {
                    "type": "object",
                    "description": "The payload to validate against the contract",
                },
            },
            "required": ["payload"],
        },
    },
    {
        "name": "route_payload",
        "description": (
            "Phase 2 routing. Take an 11-field USAP payload and look up which "
            "specialist MCP would handle it (Splunk / CrowdStrike / FortiGate "
            "/ Okta / Slack / GitHub / AWS Security Hub, etc.) per the "
            "registry at registry/usap-mcp-registry.yaml. If the payload or "
            "the matched capability sets human_approval_required: true, "
            "returns an approval prompt instead of dispatching. Phase 3 will "
            "actually invoke the adapter; Phase 2 confirms routing logic + "
            "approval gate. Every decision is written to "
            "~/.usap/audit/YYYY-MM-DD.jsonl."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "payload": {
                    "type": "object",
                    "description": "The 11-field USAP payload from a skill or agent.",
                },
            },
            "required": ["payload"],
        },
    },
    {
        "name": "list_mcps",
        "description": (
            "List all specialist MCPs the router knows about, with their "
            "enabled/disabled status, declared capabilities, and which "
            "intent_type values route to them."
        ),
        "inputSchema": {"type": "object", "properties": {}},
    },
    {
        "name": "dispatch_after_approval",
        "description": (
            "Phase 3 explicit dispatch. After `route_payload` returned an "
            "approval_required decision and the calling client surfaced the "
            "prompt to the user, the client calls this to actually invoke "
            "the downstream capability. Writes approval_granted + dispatch "
            "audit lines so the chain is recoverable end-to-end."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "mcp_id": {"type": "string", "description": "The MCP id from the prior route decision."},
                "capability_id": {"type": "string", "description": "The capability id to invoke."},
                "arguments": {"type": "object", "description": "Arguments passed to the capability."},
                "approval_token": {"type": "string", "description": "Audit token for the approval. Phase 4 will require this to be USAP-signed."},
            },
            "required": ["mcp_id", "capability_id"],
        },
    },
]


def handle_tools_list(params: Optional[dict] = None) -> dict:
    return {"tools": TOOLS}


def handle_tools_call(params: dict) -> dict:
    name = params.get("name")
    args = params.get("arguments", {}) or {}

    if name == "list_skills":
        skills = load_skills()
        domain = args.get("domain")
        if domain:
            skills = [s for s in skills if s["domain"] == domain]
        if not skills:
            text = f"No skills found{' in domain ' + repr(domain) if domain else ''}."
        else:
            lines = [
                f"- {s['domain']}/{s['slug']} — {s['description']}".rstrip(" —")
                for s in skills
            ]
            text = "\n".join(lines)
        return {"content": [{"type": "text", "text": text}]}

    if name == "list_agents":
        agents = load_agents()
        lines = [
            f"- {a['slug']} ({a['group']}/) — {a['description']}".rstrip(" —")
            for a in agents
        ]
        return {"content": [{"type": "text", "text": "\n".join(lines)}]}

    if name == "get_skill":
        slug = args.get("slug")
        if not slug:
            return _err(f"Missing required argument: slug")
        for s in load_skills():
            if s["slug"] == slug:
                return {"content": [{"type": "text", "text": read_file(s["path"])}]}
        return _err(f"No skill found: {slug}")

    if name == "get_agent":
        slug = args.get("slug")
        if not slug:
            return _err(f"Missing required argument: slug")
        for a in load_agents():
            if a["slug"] == slug:
                return {"content": [{"type": "text", "text": read_file(a["path"])}]}
        return _err(f"No agent found: {slug}")

    if name == "validate_payload":
        payload = args.get("payload")
        if not isinstance(payload, dict):
            return _err("payload must be a JSON object")
        sys.path.insert(0, str(REPO_ROOT / "tools"))
        from output_contract import validate_payload as vp  # noqa: E402
        # Runtime contract boundary — enforce the hardest-line evidence gate.
        violations = vp(payload, evidence_gate=True)
        text = "PASS" if not violations else "\n".join(violations)
        return {"content": [{"type": "text", "text": text}]}

    if name == "route_payload":
        payload = args.get("payload")
        if not isinstance(payload, dict):
            return _err("payload must be a JSON object")
        sys.path.insert(0, str(REPO_ROOT / "tools"))
        from mcp_router import route  # noqa: E402
        decision = route(payload)
        return {"content": [{"type": "text", "text": json.dumps(decision, indent=2)}]}

    if name == "list_mcps":
        sys.path.insert(0, str(REPO_ROOT / "tools"))
        from mcp_registry import load_registry  # noqa: E402
        try:
            reg = load_registry()
        except (FileNotFoundError, ValueError) as exc:
            return _err(str(exc))
        lines = []
        for m in reg["mcps"]:
            status = "enabled" if m.get("enabled") else "disabled"
            caps = ", ".join(c["id"] for c in m["capabilities"])
            lines.append(
                f"- {m['id']:<20} {status:<10} "
                f"intents={m['routes_intent']} caps=[{caps}]"
            )
        return {"content": [{"type": "text", "text": "\n".join(lines)}]}

    if name == "dispatch_after_approval":
        mcp_id = args.get("mcp_id")
        capability_id = args.get("capability_id")
        arguments = args.get("arguments", {}) or {}
        approval_token = args.get("approval_token", "approved")
        if not mcp_id or not capability_id:
            return _err("mcp_id and capability_id are required")
        sys.path.insert(0, str(REPO_ROOT / "tools"))
        from mcp_router import dispatch_after_approval  # noqa: E402
        result = dispatch_after_approval(mcp_id, capability_id, arguments, approval_token)
        return {"content": [{"type": "text", "text": json.dumps(result, indent=2)}]}

    return _err(f"Unknown tool: {name}")


def _err(message: str) -> dict:
    return {
        "content": [{"type": "text", "text": message}],
        "isError": True,
    }


def handle_resources_list(params: Optional[dict] = None) -> dict:
    resources = []
    for s in load_skills():
        resources.append({
            "uri": f"usap://skill/{s['domain']}/{s['slug']}",
            "name": s["slug"],
            "description": s["description"],
            "mimeType": "text/markdown",
        })
    for a in load_agents():
        resources.append({
            "uri": f"usap://agent/{a['slug']}",
            "name": a["slug"],
            "description": a["description"],
            "mimeType": "text/markdown",
        })
    return {"resources": resources}


def handle_resources_read(params: dict) -> dict:
    uri = params.get("uri", "")
    if uri.startswith("usap://skill/"):
        rest = uri[len("usap://skill/"):]
        domain, _, slug = rest.partition("/")
        path = REPO_ROOT / domain / slug / "SKILL.md"
    elif uri.startswith("usap://agent/"):
        slug = uri[len("usap://agent/"):]
        path = None
        for a in load_agents():
            if a["slug"] == slug:
                path = REPO_ROOT / a["path"]
                break
        if path is None:
            raise ValueError(f"Unknown agent: {slug}")
    else:
        raise ValueError(f"Unknown URI scheme: {uri}")

    if not path.is_file():
        raise FileNotFoundError(f"Resource not found: {uri}")
    return {
        "contents": [{
            "uri": uri,
            "mimeType": "text/markdown",
            "text": path.read_text(encoding="utf-8"),
        }],
    }


# ─── JSON-RPC dispatch ─────────────────────────────────────────────────

HANDLERS = {
    "initialize": handle_initialize,
    "tools/list": handle_tools_list,
    "tools/call": handle_tools_call,
    "resources/list": handle_resources_list,
    "resources/read": handle_resources_read,
}


def handle_message(msg: dict) -> Optional[dict]:
    method = msg.get("method")
    msg_id = msg.get("id")
    params = msg.get("params") or {}

    # Notifications (no id, no response expected)
    if msg_id is None:
        return None

    if method not in HANDLERS:
        return {
            "jsonrpc": "2.0",
            "id": msg_id,
            "error": {
                "code": -32601,
                "message": f"Method not found: {method}",
            },
        }

    try:
        result = HANDLERS[method](params)
        return {"jsonrpc": "2.0", "id": msg_id, "result": result}
    except Exception as exc:
        return {
            "jsonrpc": "2.0",
            "id": msg_id,
            "error": {
                "code": -32000,
                "message": str(exc),
                "data": traceback.format_exc(),
            },
        }


def main() -> int:
    for raw in sys.stdin:
        line = raw.strip()
        if not line:
            continue
        try:
            msg = json.loads(line)
        except json.JSONDecodeError as exc:
            sys.stderr.write(f"usap-mcp: invalid JSON: {exc}\n")
            continue
        response = handle_message(msg)
        if response is not None:
            sys.stdout.write(json.dumps(response) + "\n")
            sys.stdout.flush()
    return 0


if __name__ == "__main__":
    sys.exit(main())
