#!/usr/bin/env python3
"""USAP specialist-MCP adapter: GitHub (Phase 3 fixture mode).

Capabilities:
  - list_repos    Read-only.
  - get_pr_diff   Read-only.
  - open_issue    Mutating. Gated.

Live mode would use GITHUB_TOKEN (PAT or App token).

Stdlib only.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from _lib import run_adapter  # noqa: E402


CAPABILITIES = [
    {
        "name": "list_repos",
        "description": "List repositories visible to the configured token.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "org": {"type": "string"},
                "visibility": {"type": "string", "enum": ["all", "public", "private"]},
            },
        },
    },
    {
        "name": "get_pr_diff",
        "description": "Fetch the unified diff for a pull request.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "repo": {"type": "string", "description": "owner/repo"},
                "number": {"type": "integer"},
            },
            "required": ["repo", "number"],
        },
    },
    {
        "name": "open_issue",
        "description": "Open a new issue. Mutating.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "repo": {"type": "string"},
                "title": {"type": "string"},
                "body": {"type": "string"},
                "labels": {"type": "array", "items": {"type": "string"}},
            },
            "required": ["repo", "title"],
        },
    },
]


FIXTURES = {
    "list_repos": {
        "repos": [
            {"full_name": "acme/payments-api", "default_branch": "main", "private": True},
            {"full_name": "acme/web-frontend", "default_branch": "main", "private": True},
            {"full_name": "acme/security-tools", "default_branch": "main", "private": True},
        ],
    },
    "get_pr_diff": {
        "diff": (
            "diff --git a/src/config.py b/src/config.py\n"
            "@@ -10,3 +10,4 @@\n"
            "+PASSWORD = 'changeme-prod'   # ← USAP would flag this\n"
        ),
        "changed_files": 1,
        "additions": 1,
        "deletions": 0,
    },
    "open_issue": {
        "ok": True,
        "html_url": "https://github.com/<repo>/issues/<number>",
        "number": 1234,
        "title": "<title>",
    },
}


def main() -> int:
    return run_adapter(
        name="github",
        version="1.6.0",
        capabilities=CAPABILITIES,
        fixtures=FIXTURES,
    )


if __name__ == "__main__":
    sys.exit(main())
