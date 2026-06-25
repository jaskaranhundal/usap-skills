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

## How to install

```
/plugin marketplace add jaskaranhundal/usap-skills
/plugin install usap-skills@usap
```

The marketplace manifest sits at the repo root (`/.claude-plugin/marketplace.json`) and points here via `source: "./plugins/usap-skills"`.

## Source of truth

The skills, agents, and standards the orchestrator commands operate on all live at the **repo root** (`appsec-devsecops/`, `detection/`, `agents/security/`, etc.). This plugin directory only carries the Claude Code surface — the slash commands and orchestrator-skill loaders. When a command reads a domain skill, it walks back to the repo root via the relative paths in the agent definitions.

For the full project — 79 skills across 12 domains, 12 `cs-*` orchestrator agents, the typed 11-field output contract, framework mappings, validators, the design system, and the docs site — see the parent repo's [`README.md`](../../README.md).
