---
title: USAP MCP Server
description: Run USAP as a Model Context Protocol server. Any MCP-compatible client (Claude Code, Cursor, Codex CLI, Gemini CLI, Goose) can discover the 79 USAP skills and 12 cs-* agents, load any of them as system prompts, and validate payloads against the 11-field output contract.
---

# USAP MCP Server

USAP exposes itself as a [Model Context Protocol](https://modelcontextprotocol.io) server. Any MCP-compatible client — Claude Code, Cursor, Codex CLI, Gemini CLI, Goose, OpenCode, and others — can:

- **Discover** — list the 79 USAP skills and 12 `cs-*` orchestrator agents
- **Activate** — load any skill or agent definition into the client's LLM context as a system prompt
- **Validate** — validate a JSON payload against the typed 11-field output contract

This is **Phase 1** — read-only discovery and load. No mutating actions, no specialist-MCP routing yet. Phase 2 (planned) turns USAP into the master MCP that routes security intents to downstream vendor MCPs (SIEM, EDR, firewall, etc.) with the contract's `human_approval_required` field enforcing the human gate.

## Install

Stdlib only — no `pip install`, no Docker, no API key.

```bash
git clone https://github.com/jaskaranhundal/usap-skills.git
```

Point your MCP client at `tools/mcp_server.py`. The same JSON shape works across every MCP-compatible client:

### Claude Code

Add to `.mcp.json` in your project, or `~/.claude/mcp_servers.json` globally:

```json
{
  "mcpServers": {
    "usap": {
      "command": "python3",
      "args": ["/absolute/path/to/usap-skills/tools/mcp_server.py"]
    }
  }
}
```

### Cursor

`.cursor/mcp.json`:

```json
{
  "mcpServers": {
    "usap": {
      "command": "python3",
      "args": ["/absolute/path/to/usap-skills/tools/mcp_server.py"]
    }
  }
}
```

### Codex CLI

`~/.codex/mcp_servers.json` — same shape.

### Gemini CLI

`.gemini/mcp_servers.json` — same shape.

### Goose / OpenCode / any other MCP client

Same shape — `command: python3`, `args: [<path>]`, no env vars.

## Available tools

After connecting, your client sees five MCP tools:

| Tool | What it does |
|---|---|
| `list_skills(domain?)` | Catalogue of the 79 skills with one-line descriptions; optionally filter by one of the 12 domains |
| `list_agents()` | The 12 `cs-*` orchestrator agents |
| `get_skill(slug)` | Full `SKILL.md` content for one skill — paste straight into the client's LLM context |
| `get_agent(slug)` | Full agent definition — activates the agent persona |
| `validate_payload(payload)` | Validates a JSON object against the typed 11-field output contract |

## Available resources

Every skill and agent is also exposed as an MCP resource. Use `resources/list` to enumerate, `resources/read` to fetch:

- `usap://skill/<domain>/<slug>` — e.g. `usap://skill/appsec-devsecops/vuln-scan`
- `usap://agent/<slug>` — e.g. `usap://agent/cs-security-analyst`

## Smoke test

After install, verify the server works:

```bash
python3 tools/mcp_server_test.py
```

Expected: every assertion passes (17 today).

## How to use it in practice

Once connected, talk to your client in plain English. Example flow in Cursor:

```
You: I want to triage an alert. Activate Alex.

Cursor (calls `get_agent('cs-security-analyst')` via MCP):
  → loads the full cs-security-analyst.md persona into the conversation

You: [paste alert JSON]

Cursor (now in Alex persona): walks the AT workflow, emits the 11-field payload, hands off to cs-incident-responder if severity is high
```

You never leave the chat. USAP routes the right persona for the question.

## What Phase 2 adds

Phase 2 turns this read-only server into the master security MCP that orchestrates other vendor MCPs:

- A registry of downstream specialist MCPs (Splunk, CrowdStrike, FortiGate, Okta, AWS Security Hub, GitHub, Slack)
- Routing: a skill's `intent_type` and `next_agents` fields drive which specialist MCP gets called next
- The `human_approval_required` contract field enforces the human gate before any mutating downstream call
- Cryptographically-signed audit log of every routing decision

The Phase 1 server is the foundation for that work — same transport, same discovery model, just gains the routing layer.

## Architecture

```
                    User chats with the MCP client
                                  │
                                  ▼
                  ┌──────────────────────────────┐
                  │      USAP MCP server         │  Phase 1: this file
                  │   (tools/mcp_server.py)      │
                  │                              │
                  │   • list_skills              │
                  │   • list_agents              │
                  │   • get_skill                │
                  │   • get_agent                │
                  │   • validate_payload         │
                  └──────────────────────────────┘
                                  │
                                  ▼
                   reads from the repo on disk
                   (79 skills · 12 agents · 11-field contract)
```

Phase 2 inserts a routing layer between USAP and downstream specialist MCPs. Phase 3 adds production specialist-MCP reference adapters. Phase 4 layers scheduled persistence on top.

## Stdlib-only is deliberate

The server uses no third-party Python dependencies. The MCP protocol's stdio transport is just JSON-RPC 2.0 over newline-delimited JSON, which the standard library handles natively. This keeps the install path one `git clone` away and removes any dependency-resolution friction.

If a future phase needs richer MCP features (sampling, subscriptions, prompts), we'll either implement them directly or add the optional `mcp` SDK behind a feature flag. The Phase 1 surface — discovery + load + validate — needs none of that.

## See also

- [`tools/mcp_server.py`](https://github.com/jaskaranhundal/usap-skills/blob/main/tools/mcp_server.py) — the server itself, ~440 lines
- [`tools/mcp_server_test.py`](https://github.com/jaskaranhundal/usap-skills/blob/main/tools/mcp_server_test.py) — the smoke test
- [`standards/output-contract.md`](https://github.com/jaskaranhundal/usap-skills/blob/main/standards/output-contract.md) — the 11-field contract `validate_payload` checks against
- [Model Context Protocol spec](https://modelcontextprotocol.io/specification)
