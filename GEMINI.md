# USAP Skills Library (Gemini Context)

This directory contains the public skill library for the **Unified Security Agent Platform (USAP)**. It is a collection of 66 standalone LLM skill packages and 5 specialized orchestrator agents designed for security, DevSecOps, and executive advisory tasks.

## Project Overview

The project is structured as a modular library where each "skill" is a self-contained package including an LLM system prompt (`SKILL.md`), human-readable documentation (`README.md`), analysis workflows (`references/`), and automation scripts (`scripts/`).

- **Architecture:** Modular, domain-driven skill packages.
- **Core Components:**
    - **Skills:** 66 packages across domains like Detection, Response, Red Team, Governance, and AppSec.
    - **Orchestrators:** 5 `cs-*` agents that coordinate multiple skills for specific roles (e.g., `cs-security-analyst`).
    - **Shared Utilities:** Common Python scripts in `shared/scripts/` for tasks like CVSS scoring and scope enforcement.

## Directory Structure

```
.
├── agents/                 # Orchestrator agents (cs-*)
├── shared/                 # Shared Python utilities
├── standards/              # Specifications for frontmatter, naming, and output
├── templates/              # Boilerplates for new agents and skills
├── <domain-folders>/       # Categorized skill packages (e.g., red-team, governance)
│   └── <skill-slug>/       # Individual skill package
│       ├── SKILL.md        # Core LLM prompt + Metadata
│       ├── README.md       # Skill description
│       ├── references/     # Detailed workflows
│       ├── scripts/        # Skill-specific Python tools
│       └── expected_outputs/ # Sample LLM outputs
└── domains/                # Domain-specific index files
```

## Using Skills and Agents

### Standalone Skill Usage
You can use any skill by providing its `SKILL.md` as a system prompt to an LLM. 
- **Input:** Structured JSON containing `event_type`, `severity`, and `raw_payload`.
- **Output:** Structured JSON conforming to the [Output Contract](standards/output-contract.md).

### Python Tools
Many skills include Python CLI tools. These are generally standalone and use only the Python standard library.
- **Example (CVSS Scorer):**
  ```bash
  python shared/scripts/cvss_scorer.py --vector "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:C/C:H/I:H/A:H"
  ```
- **Example (Skill Tool):**
  ```bash
  python <skill-slug>/scripts/<skill-slug>_tool.py --help
  ```

### Orchestrator Agents
Orchestrators (`cs-*`) coordinate multiple skills. They are documented in `agents/<domain>/cs-<agent>.md`.

## Development Conventions

### Creating a New Skill
1. Use `templates/skill-template.md` as a base.
2. Follow the [Frontmatter Specification](standards/frontmatter-spec.md).
3. Ensure `SKILL.md` includes:
    - Identity, Classification Tables, Reasoning Procedure, and Intent Classification.
    - A Runtime Contract line pointing to its future USAP platform manifest.
4. Provide a `references/workflow.md` describing the manual analyst process.

### Metadata Standards
- **Levels (L1-L4):** L1 (Executive) to L4 (Technical/Tool).
- **Phases:** mvp, phase1, phase2.
- **Planes:** work, control, governance.

### Security and Quality
- **No Secrets:** Never include API keys or sensitive credentials.
- **MITRE Mapping:** Detection and offensive skills should map to MITRE ATT&CK techniques.
- **Deterministic Logic:** Prefer Python scripts in `scripts/` for deterministic analysis that supports the LLM's reasoning.

## Key Files for Reference
- `README.md`: Main index of all skills and agents.
- `CONTRIBUTING.md`: Detailed guide for authors.
- `standards/`: Full specifications for metadata and output formats.
- `agents/CLAUDE.md`: The orchestrator agent development guide.
