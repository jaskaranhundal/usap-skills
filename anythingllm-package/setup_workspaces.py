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
