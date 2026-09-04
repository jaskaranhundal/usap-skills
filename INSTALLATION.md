# Installing USAP

USAP runs anywhere an LLM runs. Every skill is a self-contained `SKILL.md` system prompt — no runtime is *required*. The optional Python tooling is stdlib-only (Python 3.9+, zero pip dependencies). Pick your platform.

---

## Claude Code (richest experience — one command, no clone)

```
/plugin marketplace add jaskaranhundal/usap-skills
/plugin install usap@usap
```

Activates 7 slash commands (`/usap:run`, `/usap:fortigate`, `/usap:orchestrate`, `/usap:challenge`, `/usap:compare`, `/usap:test`, `/usap:README`), 6 orchestrator personas (`@usap-alex`, `@usap-ciso`, `@usap-devsecops`, `@usap-incident-responder`, `@usap-program-manager`, `@usap-red-teamer`), and the bundled MCP server (Splunk/GitHub/Slack reference adapters in safe fixture mode).

---

## Cursor / Windsurf / Codex / Gemini CLI / Aider (polyglot)

USAP mirrors its skill tree into each client's convention. Clone, then point your client at the pre-generated index:

```bash
git clone https://github.com/jaskaranhundal/usap-skills && cd usap-skills
ls .cursor/skills-index.json .windsurf/skills-index.json .codex/skills-index.json .gemini/skills-index.json .aider/skills-index.json
```

Each `.<client>/skills/<slug>.md` symlinks back to the one canonical `SKILL.md`, so all clients read the same source of truth. Regenerate after edits with `python3 scripts/sync_all.py`.

---

## ChatGPT (Custom GPT)

See [`custom-gpt/README.md`](custom-gpt/README.md) — paste the provided instructions into a new Custom GPT and it will operate under USAP's 11-field output contract, loading skills on request.

---

## Ollama / AnythingLLM / any chat LLM (zero-install)

Open any `<domain>/<slug>/SKILL.md`, copy its contents, and paste it as the system prompt. That is the whole install. The skill will produce the typed 11-field output contract on its own.

```bash
cat detection/threat-hunting/SKILL.md      # paste into your model's system prompt
```

---

## The Python tooling (optional — validation, scoring, MCP runtime)

Stdlib only, nothing to install:

```bash
python3 tools/mcp_server.py                 # run USAP as an MCP server over stdio
python3 tools/mcp_server_test.py            # 32-assertion end-to-end smoke test
python3 tools/output_contract.py <payload>  # validate a payload against the contract + evidence gate
python3 shared/scripts/epss_scorer.py --cve CVE-2021-44228   # reproducible EPSS from the FIRST feed
python3 tools/validate_skill.py --all       # validate all 81 skills
```

---

## MCP server (connect USAP to any MCP client)

USAP exposes itself as a Model Context Protocol server. Register it with any MCP-capable client:

```jsonc
{
  "mcpServers": {
    "usap": { "command": "python3", "args": ["/path/to/usap-skills/tools/mcp_server.py"] }
  }
}
```

The client can then `list_skills`, `get_skill`, `list_agents`, `validate_payload`, `route_payload`, and `dispatch_after_approval`. See [`docs/mcp-server.md`](docs/mcp-server.md).

---

## Verify your install

```bash
python3 tools/mcp_server_test.py     # expect: "All smoke tests passed." (32 assertions)
```
