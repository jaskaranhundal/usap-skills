#!/usr/bin/env python3
"""Build a machine-readable skill registry at the repo root.

Walks every active-domain ``<domain>/<slug>/SKILL.md`` plus every ``cs-*``
agent under ``agents/``, parses frontmatter via the validator's stdlib YAML
parser, and emits ``index.json`` at the repo root.

The registry is the canonical answer to "what does USAP ship?" — every
external client (Claude Code, Cursor, Goose, OpenCode, search engines)
fetches one URL instead of crawling the repo.

Shape::

    {
      "version": "1.0",
      "generated_by": "tools/build_index.py",
      "counts": {
        "skills": 74,
        "agents": 12,
        "domains": 12
      },
      "domains": [
        {"slug": "appsec-devsecops", "skill_count": 9}, ...
      ],
      "skills": [
        {
          "name": "threat-hunting",
          "domain": "detection",
          "path": "detection/threat-hunting",
          "description": "...",
          "license": "MIT",
          "category": "usap-operations",
          "version": "1.0.0",
          "frameworks": {"mitre_attack": [...], "nist_csf": [...]},
          "agent_slug": "threat-hunting"
        },
        ...
      ],
      "agents": [
        {
          "name": "cs-security-analyst",
          "domain": "security",
          "path": "agents/security/cs-security-analyst.md",
          "description": "..."
        },
        ...
      ]
    }

Usage::

    python3 tools/build_index.py             # write index.json
    python3 tools/build_index.py --check     # CI drift gate (exit 1 on diff)

Stdlib only. Shares the frontmatter parser with ``tools/validate_skill.py``
so YAML rules stay in one place.
"""
from __future__ import annotations

import argparse
import difflib
import json
import sys
from pathlib import Path
from typing import Any, Dict, List

# Re-use the validator's parser to keep YAML rules in one place.
sys.path.insert(0, str(Path(__file__).resolve().parent))
from validate_skill import (  # noqa: E402  (import after sys.path tweak)
    ACTIVE_DOMAINS,
    parse_frontmatter,
)

REPO_ROOT = Path(__file__).resolve().parent.parent
INDEX_PATH = REPO_ROOT / "index.json"

# Optional skill-frontmatter keys to surface in the index. Required keys
# (name, description, license, metadata.*) are always emitted.
OPTIONAL_SKILL_KEYS = (
    "compatibility",
    "allowed-tools",
)

# Agents catalog. Mirrors agents/CLAUDE.md to avoid silently dropping agents
# from the registry; bump when a new orchestrator ships.
AGENTS = [
    ("cs-security-analyst",         "agents/security/cs-security-analyst.md"),
    ("cs-incident-responder",       "agents/security/cs-incident-responder.md"),
    ("cs-red-teamer",               "agents/security/cs-red-teamer.md"),
    ("cs-blue-team-analyst",        "agents/security/cs-blue-team-analyst.md"),
    ("cs-cloud-investigator",       "agents/security/cs-cloud-investigator.md"),
    ("cs-supply-chain-defender",    "agents/security/cs-supply-chain-defender.md"),
    ("cs-threat-intel-lead",        "agents/security/cs-threat-intel-lead.md"),
    ("cs-purple-team-lead",         "agents/security/cs-purple-team-lead.md"),
    ("cs-appsec-engineer",          "agents/appsec/cs-appsec-engineer.md"),
    ("cs-devsecops-engineer",       "agents/devsecops/cs-devsecops-engineer.md"),
    ("cs-ciso-advisor",             "agents/executive/cs-ciso-advisor.md"),
    ("cs-security-program-manager", "agents/governance/cs-security-program-manager.md"),
]


def _read_frontmatter(path: Path) -> Dict[str, Any]:
    try:
        text = path.read_text(encoding="utf-8")
    except (UnicodeDecodeError, OSError):
        return {}
    parsed = parse_frontmatter(text)
    return parsed if isinstance(parsed, dict) else {}


def _skill_entry(domain: str, skill_dir: Path) -> Dict[str, Any]:
    skill_md = skill_dir / "SKILL.md"
    fm = _read_frontmatter(skill_md)
    metadata = fm.get("metadata") if isinstance(fm.get("metadata"), dict) else {}

    entry: Dict[str, Any] = {
        "name": fm.get("name", skill_dir.name),
        "domain": domain,
        "path": f"{domain}/{skill_dir.name}",
        "description": fm.get("description", ""),
        "license": fm.get("license", ""),
        "category": metadata.get("category", "") if isinstance(metadata, dict) else "",
        "version": metadata.get("version", "") if isinstance(metadata, dict) else "",
        "agent_slug": metadata.get("agent_slug", "") if isinstance(metadata, dict) else "",
    }

    # Frameworks block, if present.
    if isinstance(metadata, dict):
        frameworks = metadata.get("frameworks")
        if isinstance(frameworks, dict) and frameworks:
            # Drop empty arrays for cleanliness.
            entry["frameworks"] = {
                k: v for k, v in frameworks.items()
                if isinstance(v, list) and v
            }

    # Spec-conformance optional fields, if present.
    for key in OPTIONAL_SKILL_KEYS:
        if key in fm and fm[key]:
            entry[key] = fm[key]

    return entry


def _agent_entry(name: str, rel_path: str) -> Dict[str, Any]:
    path = REPO_ROOT / rel_path
    fm = _read_frontmatter(path)

    entry: Dict[str, Any] = {
        "name": fm.get("name", name),
        "domain": fm.get("domain", path.parent.name),
        "path": rel_path,
        "description": fm.get("description", ""),
        "model": fm.get("model", "") if "model" in fm else "",
    }
    if "skills" in fm and fm["skills"]:
        entry["skills"] = fm["skills"]
    return entry


def build_index() -> Dict[str, Any]:
    domain_records = []
    skill_records: List[Dict[str, Any]] = []

    for domain in ACTIVE_DOMAINS:
        droot = REPO_ROOT / domain
        if not droot.is_dir():
            domain_records.append({"slug": domain, "skill_count": 0})
            continue
        skills_in_domain = sorted(
            p for p in droot.iterdir()
            if p.is_dir() and (p / "SKILL.md").is_file()
        )
        for sdir in skills_in_domain:
            skill_records.append(_skill_entry(domain, sdir))
        domain_records.append({
            "slug": domain,
            "skill_count": len(skills_in_domain),
        })

    skill_records.sort(key=lambda e: (e["domain"], e["name"]))

    agent_records = [
        _agent_entry(name, rel) for name, rel in AGENTS
        if (REPO_ROOT / rel).is_file()
    ]

    return {
        "version": "1.0",
        "generated_by": "tools/build_index.py",
        "spec": "agentskills.io 1.0",
        "repository": "https://github.com/jaskaranhundal/usap-skills",
        "counts": {
            "skills": len(skill_records),
            "agents": len(agent_records),
            "domains": sum(1 for d in domain_records if d["skill_count"] > 0),
        },
        "domains": domain_records,
        "skills": skill_records,
        "agents": agent_records,
    }


def _serialize(index: Dict[str, Any]) -> str:
    return json.dumps(index, indent=2, sort_keys=False, ensure_ascii=False) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Build index.json from every active-domain SKILL.md."
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Regenerate in memory; fail if committed index.json drifted.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=INDEX_PATH,
        help="Where to write index.json (default: <repo>/index.json).",
    )
    args = parser.parse_args()

    serialized = _serialize(build_index())

    if args.check:
        if not args.output.is_file():
            print(f"FAIL {args.output.relative_to(REPO_ROOT)} does not exist", file=sys.stderr)
            print("Run: python3 tools/build_index.py", file=sys.stderr)
            return 1
        on_disk = args.output.read_text(encoding="utf-8")
        if on_disk == serialized:
            print(
                f"OK   {args.output.relative_to(REPO_ROOT)} matches "
                f"source-of-truth frontmatter."
            )
            return 0
        print(
            f"DRIFT {args.output.relative_to(REPO_ROOT)} differs from "
            "the freshly regenerated registry:",
            file=sys.stderr,
        )
        diff = difflib.unified_diff(
            on_disk.splitlines(keepends=True),
            serialized.splitlines(keepends=True),
            fromfile=str(args.output.relative_to(REPO_ROOT)) + " (committed)",
            tofile=str(args.output.relative_to(REPO_ROOT)) + " (regenerated)",
            n=3,
        )
        sys.stderr.writelines(diff)
        print(
            "\nRun: python3 tools/build_index.py — then commit.",
            file=sys.stderr,
        )
        return 1

    args.output.write_text(serialized, encoding="utf-8")
    print(f"wrote {args.output.relative_to(REPO_ROOT)} ({len(serialized):,} bytes)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
