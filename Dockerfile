# USAP MCP server — stdio transport, stdlib-only (zero dependencies).
#
# Builds a container that runs the USAP Model Context Protocol server. Any MCP
# client (Claude Code, Cursor, Codex, Gemini, Goose) — and Glama's introspection
# checks — can start this container and speak JSON-RPC 2.0 over stdio:
#   initialize -> tools/list -> tools/call / resources/list / resources/read
#
# The server exposes list_skills, list_agents, get_skill, get_agent,
# validate_payload, route_payload, and dispatch_after_approval.
FROM python:3.12-slim

WORKDIR /app
COPY . /app

# Stdlib only — nothing to install. The server reads newline-delimited JSON-RPC
# from stdin and writes responses to stdout.
ENTRYPOINT ["python3", "tools/mcp_server.py"]
