#!/usr/bin/env python3
"""
generate_anythingllm_package.py

Auto-generates an AnythingLLM-compatible plugin package from the usap-skills repo.

Outputs:
  anythingllm-package/
    skills/usap-<slug>/plugin.json + handler.js   (one per _tool.py)
    workspaces/cs-usap-orchestrator.json           (single master workspace)
    install.sh
    setup_workspaces.py
    README.md

Run from repo root:
  python3 shared/scripts/generate_anythingllm_package.py
"""

import json
import os
import re
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
OUT_DIR = REPO_ROOT / "anythingllm-package"
SKILLS_OUT = OUT_DIR / "skills"
WORKSPACES_OUT = OUT_DIR / "workspaces"

# Domains to exclude (not USAP security skills)
EXCLUDE_DIRS = {"references", "templates", "standards", "shared", "domains", "tests"}

# cs-* agent slugs → friendly name + relevant skill slugs
AGENT_SKILL_MAP = {
    "cs-security-program-manager": [
        "security-debt-tracker",
        "security-roadmap-planner",
        "security-posture-score",
        "vulnerability-management",
        "attack-surface-management",
        "findings-tracker",
        "metrics-reporting",
        "ciso-brief-generator",
    ],
    "cs-security-analyst": [
        "threat-hunting",
        "behavioral-analytics",
        "incident-classification",
        "telemetry-signal-quality",
        "threat-intelligence",
        "secrets-exposure",
        "network-exposure",
    ],
    "cs-incident-responder": [
        "incident-classification",
        "containment-advisor",
        "forensics",
        "zero-day-response",
        "incident-commander",
    ],
    "cs-red-teamer": [
        "red-team-planner",
        "safe-exploitation",
        "attack-path-analysis",
        "red-team-operations",
        "ai-red-teaming",
    ],
    "cs-devsecops-engineer": [
        "appsec-code-review",
        "pipeline-security-scan",
        "security-requirements-review",
        "sast-dast-coordinator",
        "build-integrity",
        "supply-chain-risk",
    ],
    "cs-ciso-advisor": [
        "ciso-brief-generator",
        "metrics-reporting",
        "security-posture-score",
        "security-roadmap-planner",
        "enterprise-risk-assessment",
        "compliance-mapping",
    ],
}

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def slug_to_title(slug: str) -> str:
    return slug.replace("-", " ").title()


def extract_frontmatter(skill_md: Path) -> dict:
    """Parse YAML frontmatter from SKILL.md (simple line-by-line, no deps)."""
    if not skill_md.exists():
        return {}
    text = skill_md.read_text(encoding="utf-8")
    if not text.startswith("---"):
        return {}
    end = text.find("\n---", 3)
    if end == -1:
        return {}
    fm_block = text[3:end].strip()
    result = {}
    for line in fm_block.splitlines():
        if ":" in line and not line.startswith(" "):
            key, _, val = line.partition(":")
            result[key.strip()] = val.strip().strip('"')
    return result


def extract_metadata_field(skill_md: Path, field: str) -> str:
    """Extract indented metadata field like '  agent_slug: ...'"""
    if not skill_md.exists():
        return ""
    text = skill_md.read_text(encoding="utf-8")
    match = re.search(rf"^\s+{re.escape(field)}:\s*[\"']?(.+?)[\"']?\s*$", text, re.MULTILINE)
    return match.group(1).strip() if match else ""


def read_agent_file(agent_md: Path) -> tuple[str, str, str]:
    """Return (slug, description, full_content) from a cs-* agent .md file."""
    text = agent_md.read_text(encoding="utf-8")
    # slug from filename
    slug = agent_md.stem
    # description from frontmatter
    desc_match = re.search(r"^description:\s*(.+)$", text, re.MULTILINE)
    description = desc_match.group(1).strip() if desc_match else f"USAP {slug} orchestrator"
    return slug, description, text


# ---------------------------------------------------------------------------
# Discovery
# ---------------------------------------------------------------------------

def discover_tools() -> list[dict]:
    """Find all *_tool.py files in domain directories."""
    tools = []
    for tool_path in sorted(REPO_ROOT.rglob("scripts/*_tool.py")):
        # Skip excluded dirs
        parts = tool_path.parts
        domain = parts[len(REPO_ROOT.parts)] if len(parts) > len(REPO_ROOT.parts) else ""
        if domain in EXCLUDE_DIRS:
            continue
        if "references" in str(tool_path):
            continue

        skill_dir = tool_path.parent.parent  # scripts/ -> skill dir
        skill_slug = skill_dir.name
        domain_dir = skill_dir.parent.name
        skill_md = skill_dir / "SKILL.md"

        fm = extract_frontmatter(skill_md)
        agent_slug = fm.get("agent_slug") or extract_metadata_field(skill_md, "agent_slug") or skill_slug
        description = fm.get("description") or f"USAP skill for {slug_to_title(skill_slug)}"

        rel_tool_path = tool_path.relative_to(REPO_ROOT)

        tools.append({
            "slug": skill_slug,
            "agent_slug": agent_slug,
            "domain": domain_dir,
            "description": description,
            "rel_tool_path": str(rel_tool_path),
            "tool_path": tool_path,
        })

    return tools


def discover_agents() -> list[dict]:
    """Find all cs-* agent .md files."""
    agents = []
    agents_dir = REPO_ROOT / "agents"
    for agent_md in sorted(agents_dir.rglob("cs-*.md")):
        if agent_md.name in ("CLAUDE.md",):
            continue
        slug, description, content = read_agent_file(agent_md)
        agents.append({
            "slug": slug,
            "description": description,
            "content": content,
            "path": agent_md,
        })
    return agents


# ---------------------------------------------------------------------------
# Generators
# ---------------------------------------------------------------------------

def build_plugin_json(slug: str, title: str, description: str) -> str:
    """Build plugin.json as a dict and serialize to valid JSON."""
    plugin = {
        "active": True,
        "name": f"USAP: {title}",
        "hubId": f"usap-{slug}",
        "schema": "skill-1.0.0",
        "version": "1.0.0",
        "description": description,
        "author": "USAP Team",
        "license": "MIT",
        "entrypoint": {
            "file": "handler.js",
            "params": {
                "input": {
                    "description": "JSON input for the skill (findings, posture data, etc.)",
                    "type": "string",
                    "required": False,
                }
            },
        },
        "setup_args": {
            "USAP_REPO_PATH": {
                "type": "string",
                "required": True,
                "input": {
                    "label": "USAP repo path",
                    "description": "Absolute path to your usap-skills repo",
                    "placeholder": "/Users/you/usap-skills",
                },
            }
        },
        "examples": [
            {"prompt": f"Run the {slug} skill", "call": "{}"},
            {"prompt": f"Analyze with {slug} using this data", "call": '{"input": "{}"}'},
        ],
    }
    return json.dumps(plugin, indent=2, ensure_ascii=False)

HANDLER_JS_TEMPLATE = """\
// AnythingLLM Custom Agent Skill
// USAP: {title}
// Domain: {domain}
// Tool: {rel_tool_path}

const {{ execSync }} = require('child_process');
const path = require('path');
const fs = require('fs');

module.exports.runtime = {{
  handler: async function ({{ input }}) {{
    try {{
      const repoPath = this.runtimeArgs?.USAP_REPO_PATH || process.env.USAP_REPO_PATH;
      if (!repoPath) {{
        return JSON.stringify({{
          error: 'USAP_REPO_PATH not configured. Set it in the skill settings panel.',
          skill: '{slug}'
        }});
      }}

      const toolPath = path.join(repoPath, '{rel_tool_path}');

      if (!fs.existsSync(toolPath)) {{
        return JSON.stringify({{
          error: `Tool not found at ${{toolPath}}. Check USAP_REPO_PATH.`,
          skill: '{slug}'
        }});
      }}

      let result;
      const hasInput = input && input.trim() !== '' && input.trim() !== '{{}}';

      if (hasInput) {{
        // Write input to temp file to prevent shell injection
        const tmpFile = path.join(require('os').tmpdir(), `usap_input_${{Date.now()}}.json`);
        try {{
          // Validate JSON before writing
          JSON.parse(input);
          fs.writeFileSync(tmpFile, input, 'utf-8');
          result = execSync(
            `python3 "${{toolPath}}" --input "${{tmpFile}}" --output json`,
            {{ encoding: 'utf-8', timeout: 30000, cwd: repoPath }}
          ).trim();
        }} finally {{
          if (fs.existsSync(tmpFile)) fs.unlinkSync(tmpFile);
        }}
      }} else {{
        result = execSync(
          `python3 "${{toolPath}}" --output json`,
          {{ encoding: 'utf-8', timeout: 30000, cwd: repoPath }}
        ).trim();
      }}

      return result || JSON.stringify({{ status: 'completed', skill: '{slug}', output: 'no output' }});
    }} catch (e) {{
      return JSON.stringify({{
        error: e.message,
        skill: '{slug}',
        hint: 'Ensure Python 3 is available and USAP_REPO_PATH is correct.'
      }});
    }}
  }}
}};
"""


def generate_skill_plugin(tool: dict) -> None:
    slug = tool["slug"]
    title = slug_to_title(slug)
    out_dir = SKILLS_OUT / f"usap-{slug}"
    out_dir.mkdir(parents=True, exist_ok=True)

    # plugin.json
    (out_dir / "plugin.json").write_text(
        build_plugin_json(slug, title, tool["description"]), encoding="utf-8"
    )

    # handler.js
    handler_js = HANDLER_JS_TEMPLATE.format(
        title=title,
        slug=slug,
        domain=tool["domain"],
        rel_tool_path=tool["rel_tool_path"].replace("\\", "/"),
    )
    (out_dir / "handler.js").write_text(handler_js, encoding="utf-8")


def build_master_orchestrator_prompt(agents: list[dict], tools: list[dict]) -> str:
    """Build the system prompt for the single top-level USAP orchestrator workspace."""
    all_skill_slugs = sorted({t["slug"] for t in tools})
    skill_list_by_domain = _group_skills_by_domain(tools)

    agent_blocks = []
    for a in agents:
        slug = a["slug"]
        desc = a["description"]
        # Extract Command Menu section from agent content
        content = a["content"]
        if content.startswith("---"):
            end = content.find("\n---", 3)
            if end != -1:
                content = content[end + 4:].strip()

        # Pull workflow codes from Command Menu section
        menu_match = re.search(r"## Command Menu(.+?)(?=\n##|\Z)", content, re.DOTALL)
        menu_snippet = menu_match.group(1).strip()[:600] if menu_match else ""

        # Pull NOT-for constraints from Critical Actions / NEVER section
        never_match = re.search(r"\*\*NEVER:\*\*(.+?)(?=\n##|\n\*\*|\Z)", content, re.DOTALL)
        never_snippet = never_match.group(1).strip()[:400] if never_match else ""

        agent_blocks.append(
            f"### {slug}\n"
            f"**Role:** {desc}\n\n"
            f"**Workflows:**\n{menu_snippet}\n\n"
            f"**Hard constraints (NEVER):**\n{never_snippet}"
        )

    agent_detail = "\n\n---\n\n".join(agent_blocks)

    return f"""# USAP Master Orchestrator — v2.2

You are the top-level security operations orchestrator for the Unified Security Agent Platform (USAP). You coordinate six specialized security agents across all security domains: detection, response, governance, offensive security, DevSecOps, and executive advisory.

---

## STEP 0: REASON BEFORE YOU WRITE — MANDATORY FOR EVERY RESPONSE

Before writing a single word of your response, work through these questions internally. Do not skip this. This is your internal reasoning pass — it is not shown to the user, but it determines the quality of everything that follows.

**Reasoning Pass (complete mentally before responding):**

1. WHAT IS ACTUALLY BEING ASKED?
   - Is this an active incident, a planning request, a threat model, a board report, or something else?
   - Who is the likely audience — SOC analyst, CISO, developer, executive?
   - What is the single most important thing they need to know?

2. WHAT PLATFORMS ARE IN SCOPE?
   - List every named technology. For each one, ask: what OS/firmware does it run?
   - FortiGate = FortiOS (not Linux). AWS = cloud APIs (not bash). Okta = SaaS API (not file system).
   - If the platform is unfamiliar, state your uncertainty rather than guessing.

3. WHAT ARE MY ASSUMPTIONS — AND ARE THEY JUSTIFIED?
   - Challenge every assumption before using it. Ask: "Do I actually know this, or am I inferring it?"
   - Flag any assumption that could be wrong as ASSUMED — requires verification.
   - Never state an assumption as a confirmed fact.

4. WHAT ATTACK SURFACES HAVE I NOT THOUGHT ABOUT YET?
   - Run through: network → identity → cloud → containers → CI/CD → endpoints → data → supply chain
   - For each surface: is it named in the request? If yes, have I covered it?
   - What would an attacker try that I haven't considered?

5. WHAT COULD GO WRONG WITH MY ANALYSIS?
   - What is the most likely mistake I could make in this response?
   - Am I using the right vendor syntax? Am I fabricating numbers? Am I missing a layer?
   - Would a senior security engineer reviewing my output find errors in the first paragraph?

6. WHAT IS MY CONFIDENCE LEVEL — AND WHY?
   - What evidence do I actually have vs what am I inferring?
   - If I have no data, my confidence is LOW. Say so explicitly.
   - Do not assign a confidence number unless I can explain what data it comes from.

7. WHAT IS THE ONE THING THEY MUST DO RIGHT NOW?
   - Formulate the BOTTOM LINE before writing anything else.
   - If I cannot state it in one sentence, I do not understand the problem well enough yet.

Only after completing this reasoning pass should you begin writing your response.

---

## MANDATORY OPERATING RULES — ENFORCED AFTER REASONING PASS

### 1. SCOPE DISCOVERY FIRST
Before any analysis, explicitly enumerate every asset, platform, and technology named in the request. Map each to the correct domain. Do not begin analysis until you have listed all in-scope surfaces.

### 2. PLATFORM-AGNOSTIC REASONING — NEVER ASSUME
- A firewall (FortiGate, Palo Alto, Cisco ASA, pfSense) runs vendor firmware — NOT Linux. Never apply Linux commands (`/var/log/auth.log`, `useradd`, `grep /etc/passwd`) to network appliances.
- Cloud environments (AWS, Azure, GCP) have native APIs and CLI tools — NOT generic server commands.
- Kubernetes forensics use `kubectl`, not host OS commands.
- Windows endpoints use Event IDs, PowerShell, WMI — not Linux log paths.
- SaaS platforms (Okta, GitHub, Salesforce) expose APIs and audit logs — not file system access.
- Always state the platform explicitly before giving any command or procedure.

### 3. NO FABRICATED NUMBERS
- Never invent financial figures (ALE, risk reduction %) without calculation inputs explicitly provided in the request.
- Never state confidence scores without grounding them in actual cited evidence.
- If calculation inputs are absent, say: "Risk quantification requires: [list of inputs needed]."
- Estimates must be labeled ESTIMATED and show the reasoning chain.

### 4. NO FAKE TOOL SYNTAX
- USAP skills are Python scripts: `python3 <domain>/<slug>/scripts/<slug>_tool.py --input file.json --output json`
- Never invent CLI flags, commands, or tool APIs that don't exist.
- When referencing a skill, describe WHAT it would analyze and WHAT JSON input it needs — not a fabricated one-liner.

### 5. BREADTH BEFORE DEPTH
Every asset named in the request must be addressed before going deep on any single one.
Coverage checklist for security incidents:
  [ ] Network/Firewall layer
  [ ] Identity/SSO layer (Okta, Azure AD, etc.)
  [ ] Cloud infrastructure (AWS/Azure/GCP)
  [ ] Kubernetes / container layer
  [ ] CI/CD pipeline (GitHub Actions, Jenkins, etc.)
  [ ] Endpoint/workstation layer
  [ ] Application/API layer
  [ ] Data layer (databases, S3, storage)
  [ ] Supply chain (dependencies, build artifacts)

### 6. OUTPUT FORMAT — BOTTOM LINE FIRST
Every response must open with:
  BOTTOM LINE: [One sentence verdict or recommendation]
Then: WHAT | WHY THIS MATTERS | HOW TO ACT | YOUR DECISION (if needed)
Never open with status boxes, tables, or decorative banners.

### 7. EVIDENCE-ANCHORED CLAIMS
- Every finding must cite a specific data source, log type, or observable.
- Uncertainty must be explicit: "UNVERIFIED — requires [specific data source]"
- Do not present assumptions as facts.

### 8. HUMAN APPROVAL GATES
Any action that modifies systems, rotates credentials, isolates segments, or changes configurations requires:
  [HUMAN APPROVAL REQUIRED] — Action: [description] | Risk if skipped: [impact] | Reversal: [how to undo]

---

## SPECIALIZED AGENTS & THEIR DOMAINS

{agent_detail}

---

## ROUTING LOGIC

Request type                               Route to
────────────────────────────────────────────────────────────────
Active incident / SEV declaration          cs-incident-responder (IT)
Alert received, needs triage               cs-security-analyst (AT)
Threat hunt needed                         cs-security-analyst (TH)
Attack paths / adversary simulation        cs-red-teamer (AP or ES)
CI/CD / pipeline / supply chain            cs-devsecops-engineer (PR or RS)
Board report / CISO brief / regulatory     cs-ciso-advisor (BR or RG)
Roadmap / program planning / posture       cs-security-program-manager (PL or SC)
Multi-domain (most real incidents)         Coordinate sequentially, state order

For multi-domain incidents: lead with cs-incident-responder for active threats,
cs-security-analyst for detection gaps, cs-red-teamer for attack path validation,
cs-devsecops-engineer for pipeline implications, cs-ciso-advisor for executive output.

---

## VENDOR-SPECIFIC FORENSIC REFERENCES

### FortiGate (FortiOS) — CRITICAL SYNTAX RULES
FortiOS is NOT Linux. There are NO Unix pipes, NO grep, NO awk, NO /var/log paths.
Two command families exist — never mix them:
  - `get` / `diagnose` / `show` → read-only, no config mode needed
  - `config ... / edit ... / set ... / next / end` → configuration changes
  - `execute` → one-time actions only (backup, ping, reboot, log commands)

READ-ONLY (use for investigation — no approval needed):
  get system info                          # Firmware version + serial number
  get user local                           # ALL local accounts — primary backdoor check
  get system admin                         # Admin accounts + access rights
  show full-configuration system admin     # Full admin config with permissions
  diagnose debug crashlog read             # Crash/exploit indicators
  diagnose sys session list                # Active sessions (no | head, use built-in filter)
  execute log filter field subtype admin   # Set log filter to admin events
  execute log display                      # Display filtered logs (FortiOS pipe equivalent)
  get router info routing-table all        # Verify no unauthorized routes
  get system interface physical            # Interface states
  execute backup config ftp <ip> <file>    # Config backup for baseline diff

CONFIGURATION CHANGES (require human approval — use config mode):
  config system admin
    edit <admin_name>
    set accprofile "no_access"             # Restrict permissions
    set trusthost1 <trusted_ip>/32         # Restrict to trusted IPs only
    next
  end

  config system interface
    edit <interface_name>
    set allowaccess ping                   # Remove ssh https — NOT "set enable ssh false"
    next
  end

  config log syslogd setting              # Enable real-time syslog (fix SIEM 5-min gap)
    set status enable
    set server <siem_ip>
    set reliable enable                    # TCP syslog for guaranteed delivery
    set port 514
  end

MULTI-FIREWALL COORDINATION (when 2+ firewalls in scope):
  - Never isolate both simultaneously — failover risk
  - Isolate secondary first, verify traffic fails over, then isolate primary
  - Keep one clean admin path open during incident for recovery

### AWS
  aws cloudtrail lookup-events --lookup-attributes AttributeKey=EventName,AttributeValue=CreateUser
  aws guardduty list-findings --detector-id <id>
  aws ec2 describe-security-groups --filters Name=ip-permission.cidr,Values=0.0.0.0/0
  aws iam get-account-authorization-details

### Kubernetes
  kubectl get events --all-namespaces --sort-by='.lastTimestamp'
  kubectl get rolebindings,clusterrolebindings --all-namespaces
  kubectl auth can-i --list --namespace=default
  kubectl get pods --all-namespaces -o json | jq '.items[].spec.serviceAccountName'

### Okta
  GET /api/v1/logs?filter=eventType+eq+"user.account.privilege.grant"
  GET /api/v1/users?filter=status+eq+"ACTIVE"&q=admin
  GET /api/v1/logs?filter=eventType+eq+"user.session.start"&since=<ISO8601>

### GitHub Actions
  gh api repos/{{owner}}/{{repo}}/actions/secrets
  gh api repos/{{owner}}/{{repo}}/actions/permissions
  gh api orgs/{{org}}/audit-log?phrase=action:secrets

---

## AVAILABLE SKILLS ({len(all_skill_slugs)} total)

{skill_list_by_domain}

---

## DETECTION GAP AWARENESS
When SIEM polling interval > attacker exploit window, flag this explicitly:
  - SIEM 5-min batch + 3-min exploit window = attacker achieves persistence before first log
  - Mitigation: Switch to real-time TCP syslog push (config log syslogd setting → reliable enable)
  - Until fixed: treat the gap window as a blind spot in any confidence assessment

## HUMAN APPROVAL GATE — CORRECT USAGE
Apply [HUMAN APPROVAL REQUIRED] ONLY to mutating actions (changes, deletions, rotations, isolation).
NEVER apply it to read-only actions (get, show, diagnose, log review, API reads).
Misapplying the gate to read-only operations trains operators to ignore it.

Mutating = requires gate:    config changes, account creation/deletion, route changes,
                             credential rotation, network isolation, service restarts
Read-only = no gate needed:  get system info, log review, kubectl get, aws describe,
                             Okta GET API, CloudTrail read, session list

## SELF-CHECK BEFORE RESPONDING

Before finalizing any response, verify:
- [ ] Did I start with BOTTOM LINE?
- [ ] Did I cover every asset/platform named in the request?
- [ ] Did I use vendor-correct syntax? (FortiOS: config/get/diagnose/execute — no pipes, no grep)
- [ ] Did I label all unverified claims as UNVERIFIED?
- [ ] Did I avoid inventing financial figures without calculation inputs?
- [ ] Did I avoid inventing USAP tool CLI syntax?
- [ ] Did human approval gates appear ONLY on mutating actions (not on read-only)?
- [ ] If multiple devices of the same type, did I address coordination between them?
- [ ] If SIEM polling interval > exploit window, did I flag the detection gap?
- [ ] Is every confidence score grounded in cited evidence?
"""


def _group_skills_by_domain(tools: list[dict]) -> str:
    """Group skill slugs by domain for readable skill list in prompt."""
    from collections import defaultdict
    by_domain: dict[str, list[str]] = defaultdict(list)
    for t in tools:
        by_domain[t["domain"]].append(f"usap-{t['slug']}")
    lines = []
    for domain in sorted(by_domain):
        skills = ", ".join(sorted(by_domain[domain]))
        lines.append(f"**{domain}:** {skills}")
    return "\n".join(lines)


def generate_master_workspace(agents: list[dict], tools: list[dict]) -> None:
    all_skill_slugs = sorted({f"usap-{t['slug']}" for t in tools})

    workspace = {
        "slug": "cs-usap-orchestrator",
        "name": "USAP Master Orchestrator",
        "system_prompt": build_master_orchestrator_prompt(agents, tools),
        "chat_mode": "chat",
        "agent_skills": all_skill_slugs,
        "subordinate_agents": [a["slug"] for a in agents],
    }

    WORKSPACES_OUT.mkdir(parents=True, exist_ok=True)
    out_file = WORKSPACES_OUT / "cs-usap-orchestrator.json"
    out_file.write_text(json.dumps(workspace, indent=2, ensure_ascii=False), encoding="utf-8")
    return workspace


INSTALL_SH = """\
#!/usr/bin/env bash
# install.sh — Install USAP AnythingLLM skill plugins
# Run from anythingllm-package/ directory

set -euo pipefail

# Detect storage path
if [[ -n "${ANYTHINGLLM_STORAGE:-}" ]]; then
  STORAGE="$ANYTHINGLLM_STORAGE"
elif [[ "$(uname)" == "Darwin" ]]; then
  STORAGE="$HOME/Library/Application Support/anythingllm-desktop/storage"
elif [[ -d "/app/server/storage" ]]; then
  STORAGE="/app/server/storage"
else
  STORAGE="$HOME/.config/anythingllm/storage"
fi

SKILLS_DIR="$STORAGE/plugins/agent-skills"

echo "Installing USAP skills to: $SKILLS_DIR"
mkdir -p "$SKILLS_DIR"

# Copy all usap-* skill folders
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
COUNT=0
for skill_dir in "$SCRIPT_DIR/skills"/usap-*/; do
  skill_name=$(basename "$skill_dir")
  cp -r "$skill_dir" "$SKILLS_DIR/$skill_name"
  COUNT=$((COUNT + 1))
done

echo "Installed $COUNT skills."
echo ""
echo "Next steps:"
echo "  1. Reload the AnythingLLM browser tab (or restart the app)"
echo "  2. In Agent Skills settings, configure USAP_REPO_PATH for each skill"
echo "  3. Run: python3 setup_workspaces.py --api-key <key> --url http://localhost:3001"
"""


SETUP_WORKSPACES_PY = '''\
#!/usr/bin/env python3
"""
setup_workspaces.py — Create USAP workspaces in AnythingLLM via REST API

Usage:
  python3 setup_workspaces.py --api-key <key> --url http://localhost:3001

Requirements:
  pip install requests   (or: python3 -m pip install requests)
"""

import argparse
import json
import sys
from pathlib import Path

try:
    import requests
except ImportError:
    print("ERROR: 'requests' package required. Run: pip install requests")
    sys.exit(1)

WORKSPACES_DIR = Path(__file__).parent / "workspaces"


def create_workspace(base_url: str, headers: dict, workspace: dict) -> str:
    """POST /api/v1/workspace/new — returns workspace slug."""
    resp = requests.post(
        f"{base_url}/api/v1/workspace/new",
        headers=headers,
        json={"name": workspace["name"]},
        timeout=30,
    )
    resp.raise_for_status()
    data = resp.json()
    slug = data.get("workspace", {}).get("slug") or workspace["slug"]
    print(f"  Created workspace: {slug}")
    return slug


def update_workspace(base_url: str, headers: dict, slug: str, workspace: dict) -> None:
    """POST /api/v1/workspace/:slug/update — set system prompt + agent skills."""
    payload = {
        "openAiPrompt": workspace.get("system_prompt", ""),
        "chatMode": workspace.get("chat_mode", "chat"),
        "agentSkills": workspace.get("agent_skills", []),
    }
    resp = requests.post(
        f"{base_url}/api/v1/workspace/{slug}/update",
        headers=headers,
        json=payload,
        timeout=30,
    )
    resp.raise_for_status()
    print(f"  Updated workspace: {slug} ({len(workspace.get('agent_skills', []))} skills enabled)")


def main():
    parser = argparse.ArgumentParser(description="Create USAP workspaces in AnythingLLM")
    parser.add_argument("--api-key", required=True, help="AnythingLLM API key")
    parser.add_argument("--url", default="http://localhost:3001", help="AnythingLLM base URL")
    parser.add_argument("--dry-run", action="store_true", help="Print actions without executing")
    args = parser.parse_args()

    base_url = args.url.rstrip("/")
    headers = {
        "Authorization": f"Bearer {args.api_key}",
        "Content-Type": "application/json",
    }

    workspace_files = sorted(WORKSPACES_DIR.glob("*.json"))
    if not workspace_files:
        print("No workspace configs found in workspaces/")
        sys.exit(1)

    print(f"AnythingLLM: {base_url}")
    print(f"Workspaces to create: {len(workspace_files)}")
    print()

    for wf in workspace_files:
        workspace = json.loads(wf.read_text())
        print(f"Processing: {workspace['name']}")

        if args.dry_run:
            print(f"  [dry-run] Would create workspace: {workspace['slug']}")
            print(f"  [dry-run] Would enable {len(workspace.get('agent_skills', []))} skills")
            continue

        try:
            slug = create_workspace(base_url, headers, workspace)
            update_workspace(base_url, headers, slug, workspace)
        except requests.HTTPError as e:
            print(f"  ERROR: {e.response.status_code} {e.response.text[:200]}")
        except Exception as e:
            print(f"  ERROR: {e}")

    print()
    print("Done. Open AnythingLLM and select the USAP Master Orchestrator workspace.")


if __name__ == "__main__":
    main()
'''

README_MD = """\
# USAP AnythingLLM Package

Auto-generated plugin package for the [Unified Security Agent Platform (USAP)](https://github.com/jaskaranhundal/usap).

## What's Included

| Item | Count | Description |
|---|---|---|
| Agent Skills (JS plugins) | 69 | One JS wrapper per Python `_tool.py` |
| Workspace | 1 | `cs-usap-orchestrator` — master router over all 6 cs-* agents |

## Architecture

```
cs-usap-orchestrator (AnythingLLM Workspace)
    |
    +-- cs-security-program-manager   governance, roadmaps, debt
    +-- cs-security-analyst           SOC, threat hunting, alerts
    +-- cs-incident-responder         incidents, containment, forensics
    +-- cs-red-teamer                 offensive, attack simulation
    +-- cs-devsecops-engineer         pipeline, AppSec, supply chain
    +-- cs-ciso-advisor               executive, board reports
```

The master orchestrator has access to **all 69 USAP skills** and routes requests to the appropriate specialized agent.

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
print(f'Workspace: {w[\"name\"]}')
print(f'Skills enabled: {len(w[\"agent_skills\"])}')
print(f'Subordinate agents: {w[\"subordinate_agents\"]}')
"
```

## Regenerating

Re-run the generator any time skills are added or updated:
```bash
python3 shared/scripts/generate_anythingllm_package.py
bash anythingllm-package/install.sh
```
"""


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    print(f"USAP AnythingLLM Package Generator")
    print(f"Repo root: {REPO_ROOT}")
    print()

    # Discover
    print("Discovering tools...")
    tools = discover_tools()
    print(f"  Found {len(tools)} Python tools")

    print("Discovering agents...")
    agents = discover_agents()
    print(f"  Found {len(agents)} cs-* agents")
    print()

    # Create output dirs
    SKILLS_OUT.mkdir(parents=True, exist_ok=True)
    WORKSPACES_OUT.mkdir(parents=True, exist_ok=True)

    # Generate skill plugins
    print("Generating skill plugins...")
    for tool in tools:
        generate_skill_plugin(tool)
        print(f"  usap-{tool['slug']}")
    print()

    # Generate master workspace
    print("Generating master orchestrator workspace...")
    generate_master_workspace(agents, tools)
    print(f"  cs-usap-orchestrator.json ({len(agents)} subordinate agents, {len(tools)} skills)")
    print()

    # Write install.sh
    install_sh = OUT_DIR / "install.sh"
    install_sh.write_text(INSTALL_SH, encoding="utf-8")
    install_sh.chmod(0o755)
    print(f"Generated: install.sh")

    # Write setup_workspaces.py
    setup_py = OUT_DIR / "setup_workspaces.py"
    setup_py.write_text(SETUP_WORKSPACES_PY, encoding="utf-8")
    setup_py.chmod(0o755)
    print(f"Generated: setup_workspaces.py")

    # Write README
    readme = OUT_DIR / "README.md"
    readme.write_text(README_MD, encoding="utf-8")
    print(f"Generated: README.md")

    print()
    print("Package ready at: anythingllm-package/")
    print()
    print("Next steps:")
    print("  1. bash anythingllm-package/install.sh")
    print("  2. Reload AnythingLLM → configure USAP_REPO_PATH in each skill")
    print("  3. python3 anythingllm-package/setup_workspaces.py --api-key <key>")


if __name__ == "__main__":
    main()
