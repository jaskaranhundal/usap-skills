# USAP Skills — Gemini CLI Context

81 standalone LLM skill packages + 13 cs-* orchestrator agents for the Unified
Security Agent Platform (USAP).

## Repo layout

- `<domain>/<slug>/SKILL.md` — LLM system prompt for each of the 81 skills
- `agents/<domain>/cs-*.md` — orchestrator agents (cs-security-analyst, etc.)
- `dist/USAP_LITE.md` — bundled Alex kit (32 KB, paste-anywhere)
- `dist/USAP_PRO.md` — Alex + all 6 specialist agents (121 KB)
- `dist/USAP_BUNDLE.md` — all 81 skills embedded (684 KB)
- `shared/scripts/` — CLI tools (cvss_scorer.py, bb_scope_enforcer.py)

## Available USAP commands (Gemini CLI skills)

| Command | Agent | Use for |
|---|---|---|
| `/usap-alex` | cs-security-analyst | Any security question — universal entry point |
| `/usap-incident-responder` | cs-incident-responder | Active incidents, forensics, containment |
| `/usap-red-teamer` | cs-red-teamer | Red team planning and offensive security |
| `/usap-devsecops` | cs-devsecops-engineer | Pipeline security, SAST/DAST, PR gates |
| `/usap-ciso` | cs-ciso-advisor | Board reports, risk posture, executive briefs |
| `/usap-program-manager` | cs-security-program-manager | Security roadmap and program planning |

Start with `/usap-alex` for any security question — Alex routes to the right
specialist automatically.

## Conventions

- All skill tools: `python3 <domain>/<slug>/scripts/<slug>_tool.py --output json`
- Commit style: Conventional Commits (`feat(skills):`, `fix(scripts):`, `docs:`)
- Output contract required fields: `agent_slug`, `intent_type`, `action`,
  `rationale`, `confidence`, `severity`, `key_findings`, `timestamp_utc`
- Skill levels: L1=Board/advisory, L2=CISO/management, L3=SOC/analyst,
  L4=Technical/tool-execution

## 11 skill domains

`appsec-devsecops`, `cloud-infra`, `detection`, `governance`,
`identity-access`, `pentest`, `platform-ai`, `red-team`, `response`,
`risk-compliance`, `system-security`

## Project structure

```
.
├── agents/                 # Orchestrator agents (cs-*)
├── shared/                 # Shared Python utilities
├── standards/              # Frontmatter, naming, and output specs
├── templates/              # Boilerplates for new agents and skills
├── <domain-folders>/       # Categorized skill packages
│   └── <skill-slug>/
│       ├── SKILL.md        # Core LLM prompt + metadata
│       ├── README.md
│       ├── references/     # Detailed workflows
│       ├── scripts/        # Skill-specific Python tools
│       └── expected_outputs/
└── domains/                # Domain-specific index files
```

## Key files

- `README.md` — main index of all skills and agents
- `CONTRIBUTING.md` — authoring guide (frontmatter, quality checklist)
- `standards/output-contract.md` — required output JSON schema
- `agents/CLAUDE.md` — orchestrator agent development guide
