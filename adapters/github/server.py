#!/usr/bin/env python3
"""USAP specialist-MCP adapter: GitHub.

Capabilities:
  - list_repos    Read-only.   Live: GET /orgs/{org}/repos | /users/{user}/repos
  - get_pr_diff   Read-only.   Live: GET /repos/{owner}/{repo}/pulls/{n}.diff
  - open_issue    Mutating.    Gated; live not yet implemented (fixture only).

Live mode (USAP_ADAPTER_MODE=live) requires GITHUB_TOKEN in env. The token
needs `repo` + `read:org` for the read-only capabilities. `gh auth token`
provides a token with those scopes if `gh auth login` was completed.

Stdlib only.
"""
from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request
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
                "org": {"type": "string", "description": "GitHub org OR user login"},
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


API = "https://api.github.com"


def _gh_request(path: str, *, accept: str = "application/vnd.github+json") -> tuple[int, str, dict]:
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        raise RuntimeError(
            "GITHUB_TOKEN missing — set it (e.g. `export GITHUB_TOKEN=$(gh auth token)`) "
            "or fall back to USAP_ADAPTER_MODE=fixture."
        )
    req = urllib.request.Request(
        f"{API}{path}",
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": accept,
            "User-Agent": "usap-github-adapter/1.7.0",
            "X-GitHub-Api-Version": "2022-11-28",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return resp.status, resp.read().decode("utf-8", "replace"), dict(resp.headers)
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", "replace") if hasattr(exc, "read") else ""
        return exc.code, body, dict(exc.headers or {})


def _live(capability: str, args: dict) -> dict:
    if capability == "list_repos":
        owner = args.get("org") or ""
        visibility = args.get("visibility", "all")
        if not owner:
            # /user/repos lists everything visible to the token
            path = f"/user/repos?per_page=100&visibility={visibility}"
        else:
            # Try as org; if 404, retry as user
            path = f"/orgs/{owner}/repos?per_page=100&type={visibility}"
        status, body, _ = _gh_request(path)
        if status == 404 and owner:
            path = f"/users/{owner}/repos?per_page=100&type={visibility}"
            status, body, _ = _gh_request(path)
        if status >= 400:
            return {"ok": False, "status": status, "error": body[:500]}
        repos = json.loads(body) if body else []
        return {
            "ok": True,
            "count": len(repos),
            "repos": [
                {
                    "full_name": r.get("full_name"),
                    "default_branch": r.get("default_branch"),
                    "private": r.get("private"),
                    "pushed_at": r.get("pushed_at"),
                    "language": r.get("language"),
                }
                for r in repos
            ],
        }

    if capability == "get_pr_diff":
        repo = args.get("repo")
        number = args.get("number")
        if not repo or number is None:
            return {"ok": False, "error": "repo and number are required"}
        status, body, _ = _gh_request(
            f"/repos/{repo}/pulls/{number}", accept="application/vnd.github.v3.diff"
        )
        if status >= 400:
            return {"ok": False, "status": status, "error": body[:500]}
        return {
            "ok": True,
            "repo": repo,
            "number": number,
            "diff": body,
            "diff_bytes": len(body.encode()),
        }

    if capability == "open_issue":
        # Mutating — explicitly refused in live mode for now. Surface a clear
        # error so the gated dispatch path doesn't silently no-op.
        return {
            "ok": False,
            "error": "open_issue live mode not implemented (mutating capability — "
                     "implement deliberately when a downstream workflow needs it).",
        }

    return {"ok": False, "error": f"Unknown capability: {capability}"}


def main() -> int:
    return run_adapter(
        name="github",
        version="1.7.1",
        capabilities=CAPABILITIES,
        fixtures=FIXTURES,
        live_fn=_live,
    )


if __name__ == "__main__":
    sys.exit(main())
