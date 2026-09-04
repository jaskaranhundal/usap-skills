# usap-skills plugin

The Claude Code plugin payload for [USAP](https://github.com/jaskaranhundal/usap-skills) (Unified Security Agent Platform).

## What this directory is

Marketplace install reads from here. `commands/` and `skills/` follow the Claude Code plugin layout — directly under the plugin root, not under a nested `.claude/`.

```
plugins/usap-skills/
├── .claude-plugin/
│   └── plugin.json        # plugin manifest
├── commands/
│   └── usap/              # 7 slash commands (usap:run, usap:fortigate, …)
└── skills/                # 6 user-invocable orchestrator skills
    ├── usap-alex/
    ├── usap-ciso/
    ├── usap-devsecops/
    ├── usap-incident-responder/
    ├── usap-program-manager/
    └── usap-red-teamer/
```

## Persona gate hooks

`hooks/hooks.json` loads three hooks with the plugin:

| Hook | What it does |
|---|---|
| UserPromptSubmit | Classifies the prompt against the USAP trigger table and, on a match, tells the session which persona pass to run and the exact command to record it. |
| PreToolUse (Edit, Write, MultiEdit, NotebookEdit) | Blocks writes to CI workflows, `.gitlab-ci.yml`, Terraform, Dockerfiles, `.claude/settings*.json`, `hooks.json`, `.env`, credential and secrets files until a design-review pass is recorded for this session. The block message contains the record command. |
| Stop | If gated paths were written and no pass was recorded, shows "USAP: gated paths were written this session and no persona pass was recorded." |

Passes are recorded in the hash-chained audit log under `~/.usap/audit/` (override with `USAP_AUDIT_DIR`). `governance/persona-coverage-audit` reports coverage weekly. Design and review: `docs/design/2026-09-04-persona-gate-hooks-*.md`.

**Operator setup, required.** The plugin gate exists only in sessions where this plugin is loaded. To make the gate follow you across every project, add the same three entries to your user-level `~/.claude/settings.json` `hooks` block, pointing at the installed plugin's `hooks/usap_gate.py` (find it with `/plugin` or under `~/.claude/plugins/`). Without this step the weekly coverage report will list sessions with `hook_seen: false`.

## How to install

```
/plugin marketplace add jaskaranhundal/usap-skills
/plugin install usap-skills@usap
```

The marketplace manifest sits at the repo root (`/.claude-plugin/marketplace.json`) and points here via `source: "./plugins/usap-skills"`.

## Source of truth

The skills, agents, and standards the orchestrator commands operate on all live at the **repo root** (`appsec-devsecops/`, `detection/`, `agents/security/`, etc.). This plugin directory only carries the Claude Code surface — the slash commands and orchestrator-skill loaders. When a command reads a domain skill, it walks back to the repo root via the relative paths in the agent definitions.

For the full project — 81 skills across 12 domains, 13 `cs-*` orchestrator agents, the typed 11-field output contract, framework mappings, validators, the design system, and the docs site — see the parent repo's [`README.md`](../../README.md).
