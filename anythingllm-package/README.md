# USAP AnythingLLM Package

Auto-generated plugin package for the [Unified Security Agent Platform (USAP)](https://github.com/jaskaranhundal/usap).

## What's Included

| Item | Count | Description |
|---|---|---|
| Agent Skills (JS plugins) | 69 | One JS wrapper per Python `_tool.py` (across 71 skills) |
| Workspace | 1 | `cs-usap-orchestrator` — master router over all 7 cs-* agents |

## Architecture

```
cs-usap-orchestrator (AnythingLLM Workspace)
    |
    +-- cs-security-program-manager   governance, roadmaps, debt
    +-- cs-security-analyst           SOC, threat hunting, alerts
    +-- cs-incident-responder         incidents, containment, forensics
    +-- cs-red-teamer                 offensive, attack simulation
    +-- cs-blue-team-analyst          DFIR, detection eng, hunt
    +-- cs-devsecops-engineer         pipeline, AppSec, supply chain
    +-- cs-ciso-advisor               executive, board reports
```

The master orchestrator has access to **all 71 USAP skills** and routes requests to the appropriate specialized agent.

## Quick Start

### 1. Generate the package (from repo root)

```bash
python3 shared/scripts/generate_anythingllm_package.py
```

### 2. Install skill plugins

```bash
cd anythingllm-package
bash install.sh
```

Optionally set a custom storage path:
```bash
ANYTHINGLLM_STORAGE=/path/to/storage bash install.sh
```

### 3. Reload AnythingLLM

Reload the browser tab (or restart the desktop app). Skills appear under **Agent Skills** in settings.

### 4. Configure each skill

In AnythingLLM → Settings → Agent Skills, set `USAP_REPO_PATH` to the absolute path of your `usap-skills` repo for each enabled skill.

### 5. Create the workspace

```bash
python3 anythingllm-package/setup_workspaces.py --api-key <key> --url http://localhost:3001
```

Get your API key from AnythingLLM → Settings → API Keys.

Dry run (no changes):
```bash
python3 anythingllm-package/setup_workspaces.py --api-key <key> --dry-run
```

### 6. Start using USAP

Open AnythingLLM → select **USAP Master Orchestrator** workspace → start a conversation.

Example prompts:
- `Run a proactive security scan` → routes to cs-security-program-manager
- `Triage this alert: <paste alert>` → routes to cs-security-analyst
- `Generate a board-level CISO brief` → routes to cs-ciso-advisor
- `Plan a red team exercise` → routes to cs-red-teamer

## Storage Paths

| Platform | Default Path |
|---|---|
| macOS Desktop | `~/Library/Application Support/anythingllm-desktop/storage/plugins/agent-skills/` |
| Docker/Server | `/app/server/storage/plugins/agent-skills/` |
| Linux | `~/.config/anythingllm/storage/plugins/agent-skills/` |

Override with: `export ANYTHINGLLM_STORAGE=/your/path`

## Verification

```bash
# Validate all plugin.json files
python3 -c "
import json, glob
files = glob.glob('anythingllm-package/skills/*/plugin.json')
[json.load(open(f)) for f in files]
print(f'All {len(files)} plugin.json files valid')
"

# Count generated skills
ls anythingllm-package/skills/ | wc -l

# Check workspace config
python3 -c "
import json
w = json.load(open('anythingllm-package/workspaces/cs-usap-orchestrator.json'))
print(f'Workspace: {w["name"]}')
print(f'Skills enabled: {len(w["agent_skills"])}')
print(f'Subordinate agents: {w["subordinate_agents"]}')
"
```

## Regenerating

Re-run the generator any time skills are added or updated:
```bash
python3 shared/scripts/generate_anythingllm_package.py
bash anythingllm-package/install.sh
```
