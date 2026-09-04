#!/usr/bin/env python3
"""Build the machine-readable USAP skill registries.

Walks every active-domain ``<domain>/<slug>/SKILL.md`` and every agent
markdown file under ``agents/**/cs-*.md``, parses frontmatter via the
validator's stdlib YAML parser, and emits three files:

* ``index.json`` at the **repo root** — the canonical discovery payload
  read by external tools (agentskills.io, awesome-list scrapers).
* ``index.summary.json`` at the **repo root** — a reduced counts-only
  payload for badges and lightweight consumers.
* ``api/index.json`` — the legacy per-skill registry preserved for
  existing tooling that already points at it.

Root ``index.json`` shape::

    {
      "schema_version": "1",
      "generated_at_utc": "<ISO 8601 UTC>",
      "repository": "github.com/jaskaranhundal/usap-skills",
      "usap_version": "1.13.0",
      "total_skills": 79,
      "total_agents": 12,
      "total_domains": 12,
      "domains": ["appsec-devsecops", "cloud-infra", ...],
      "skills": [
        {
          "name": "<slug>",
          "domain": "<domain>",
          "description": "<from frontmatter>",
          "level": "L1|L2|L3|L4|null",
          "category": "<metadata.category>",
          "frontmatter_path": "<domain>/<slug>/SKILL.md"
        },
        ...
      ],
      "agents": [
        {
          "name": "<slug>",
          "domain": "<dir>",
          "description": "<from frontmatter>",
          "path": "agents/<dir>/<file>.md"
        },
        ...
      ]
    }

Usage::

    python3 tools/build_index.py                # regen index.json + index.summary.json + api/index.json
    python3 tools/build_index.py --check        # CI drift gate (exit 1 on diff)
    python3 tools/build_index.py --output X.json  # override root index path

The ``--check`` flag normalises the ``generated_at_utc`` field before
diffing so timestamps alone never cause drift; any content change in
skills or agents will still surface.

Stdlib only. Shares the frontmatter parser with ``tools/validate_skill.py``
so YAML rules stay in one place.
"""
from __future__ import annotations

import argparse
import difflib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Tuple

# Re-use the validator's parser to keep YAML rules in one place.
sys.path.insert(0, str(Path(__file__).resolve().parent))
from validate_skill import (  # noqa: E402  (import after sys.path tweak)
    ACTIVE_DOMAINS,
    parse_frontmatter,
)

REPO_ROOT = Path(__file__).resolve().parent.parent

# Default output paths.
ROOT_INDEX_PATH = REPO_ROOT / "index.json"
ROOT_SUMMARY_PATH = REPO_ROOT / "index.summary.json"
LEGACY_API_INDEX_PATH = REPO_ROOT / "api" / "index.json"

USAP_VERSION = "1.13.0"
REPOSITORY = "github.com/jaskaranhundal/usap-skills"
SCHEMA_VERSION = "1"

# Stable placeholder substituted for `generated_at_utc` during --check
# comparisons so wall-clock drift never trips the CI gate.
TIMESTAMP_PLACEHOLDER = "__GENERATED_AT_UTC__"

# Optional skill-frontmatter keys to surface in the legacy api/index.json.
# Required keys (name, description, license, metadata.*) are always emitted.
OPTIONAL_SKILL_KEYS = (
    "compatibility",
    "allowed-tools",
)


def _read_frontmatter(path: Path) -> Dict[str, Any]:
    try:
        text = path.read_text(encoding="utf-8")
    except (UnicodeDecodeError, OSError):
        return {}
    parsed = parse_frontmatter(text)
    return parsed if isinstance(parsed, dict) else {}


# ---------------------------------------------------------------------------
# Root index.json (agentskills.io / awesome-list discovery format)
# ---------------------------------------------------------------------------

def _root_skill_entry(domain: str, skill_dir: Path) -> Dict[str, Any]:
    skill_md = skill_dir / "SKILL.md"
    fm = _read_frontmatter(skill_md)
    metadata = fm.get("metadata") if isinstance(fm.get("metadata"), dict) else {}

    level_value = fm.get("level")
    if isinstance(level_value, str) and level_value.upper() in {"L1", "L2", "L3", "L4"}:
        level: Any = level_value.upper()
    else:
        level = None

    category = metadata.get("category", "") if isinstance(metadata, dict) else ""

    return {
        "name": fm.get("name", skill_dir.name),
        "domain": domain,
        "description": fm.get("description", ""),
        "level": level,
        "category": category or "",
        "frontmatter_path": f"{domain}/{skill_dir.name}/SKILL.md",
    }


def _root_agent_entry(agent_path: Path) -> Dict[str, Any]:
    rel_path = agent_path.relative_to(REPO_ROOT).as_posix()
    fm = _read_frontmatter(agent_path)
    return {
        "name": fm.get("name", agent_path.stem),
        "domain": fm.get("domain", agent_path.parent.name),
        "description": fm.get("description", ""),
        "path": rel_path,
    }


def _discover_root_payload(timestamp: str) -> Dict[str, Any]:
    skill_records: List[Dict[str, Any]] = []
    populated_domains: List[str] = []

    for domain in ACTIVE_DOMAINS:
        droot = REPO_ROOT / domain
        if not droot.is_dir():
            continue
        skills_in_domain = sorted(
            p for p in droot.iterdir()
            if p.is_dir() and (p / "SKILL.md").is_file()
        )
        if not skills_in_domain:
            continue
        populated_domains.append(domain)
        for sdir in skills_in_domain:
            skill_records.append(_root_skill_entry(domain, sdir))

    skill_records.sort(key=lambda e: (e["domain"], e["name"]))

    agents_dir = REPO_ROOT / "agents"
    agent_paths: List[Path] = []
    if agents_dir.is_dir():
        agent_paths = sorted(
            p for p in agents_dir.rglob("cs-*.md") if p.is_file()
        )
    agent_records = [_root_agent_entry(p) for p in agent_paths]
    agent_records.sort(key=lambda e: (e["domain"], e["name"]))

    return {
        "schema_version": SCHEMA_VERSION,
        "generated_at_utc": timestamp,
        "repository": REPOSITORY,
        "usap_version": USAP_VERSION,
        "total_skills": len(skill_records),
        "total_agents": len(agent_records),
        "total_domains": len(populated_domains),
        "domains": sorted(populated_domains),
        "skills": skill_records,
        "agents": agent_records,
    }


def _summary_payload(root_index: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "generated_at_utc": root_index["generated_at_utc"],
        "repository": REPOSITORY,
        "usap_version": USAP_VERSION,
        "total_skills": root_index["total_skills"],
        "total_agents": root_index["total_agents"],
        "total_domains": root_index["total_domains"],
        "domains": list(root_index["domains"]),
        "index_path": "index.json",
        "legacy_index_path": "api/index.json",
    }


# ---------------------------------------------------------------------------
# Legacy api/index.json (preserved for tooling already pointed at it)
# ---------------------------------------------------------------------------

def _legacy_skill_entry(domain: str, skill_dir: Path) -> Dict[str, Any]:
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

    if isinstance(metadata, dict):
        frameworks = metadata.get("frameworks")
        if isinstance(frameworks, dict) and frameworks:
            entry["frameworks"] = {
                k: v for k, v in frameworks.items()
                if isinstance(v, list) and v
            }

    for key in OPTIONAL_SKILL_KEYS:
        if key in fm and fm[key]:
            entry[key] = fm[key]

    return entry


def _legacy_agent_entry(agent_path: Path) -> Dict[str, Any]:
    rel_path = agent_path.relative_to(REPO_ROOT).as_posix()
    fm = _read_frontmatter(agent_path)
    entry: Dict[str, Any] = {
        "name": fm.get("name", agent_path.stem),
        "domain": fm.get("domain", agent_path.parent.name),
        "path": rel_path,
        "description": fm.get("description", ""),
        "model": fm.get("model", "") if "model" in fm else "",
    }
    if "skills" in fm and fm["skills"]:
        entry["skills"] = fm["skills"]
    return entry


def _build_legacy_index() -> Dict[str, Any]:
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
            skill_records.append(_legacy_skill_entry(domain, sdir))
        domain_records.append({
            "slug": domain,
            "skill_count": len(skills_in_domain),
        })

    skill_records.sort(key=lambda e: (e["domain"], e["name"]))

    agents_dir = REPO_ROOT / "agents"
    agent_paths: List[Path] = []
    if agents_dir.is_dir():
        agent_paths = sorted(
            p for p in agents_dir.rglob("cs-*.md") if p.is_file()
        )
    agent_records = [_legacy_agent_entry(p) for p in agent_paths]
    agent_records.sort(key=lambda e: (e["domain"], e["name"]))

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


# Backwards-compatible alias for any external import.
def build_index() -> Dict[str, Any]:
    """Return the legacy api/index.json payload (unchanged shape)."""
    return _build_legacy_index()


# ---------------------------------------------------------------------------
# IO helpers
# ---------------------------------------------------------------------------

def _serialize(payload: Dict[str, Any]) -> str:
    return json.dumps(payload, indent=2, sort_keys=False, ensure_ascii=False) + "\n"


def _normalize_timestamp_for_diff(text: str) -> str:
    """Replace `generated_at_utc` value with a stable placeholder.

    Used only by --check so wall-clock drift never causes a false-positive
    drift report; structural changes still surface.
    """
    out_lines = []
    for line in text.splitlines(keepends=True):
        stripped = line.lstrip()
        if stripped.startswith('"generated_at_utc":'):
            indent = line[: len(line) - len(stripped)]
            trailing_comma = "," if line.rstrip().endswith(",") else ""
            out_lines.append(
                f'{indent}"generated_at_utc": "{TIMESTAMP_PLACEHOLDER}"{trailing_comma}\n'
            )
        else:
            out_lines.append(line)
    return "".join(out_lines)


def _build_payloads(timestamp: str) -> Tuple[Dict[str, Any], Dict[str, Any], Dict[str, Any]]:
    root = _discover_root_payload(timestamp)
    summary = _summary_payload(root)
    legacy = _build_legacy_index()
    return root, summary, legacy


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _check_file(target: Path, fresh: str) -> Tuple[bool, str]:
    rel = target.relative_to(REPO_ROOT)
    if not target.is_file():
        return False, f"MISS {rel} does not exist on disk\n"
    on_disk = target.read_text(encoding="utf-8")
    a = _normalize_timestamp_for_diff(on_disk)
    b = _normalize_timestamp_for_diff(fresh)
    if a == b:
        return True, f"OK   {rel}\n"
    diff = "".join(difflib.unified_diff(
        a.splitlines(keepends=True),
        b.splitlines(keepends=True),
        fromfile=f"{rel} (committed)",
        tofile=f"{rel} (regenerated)",
        n=3,
    ))
    return False, f"DRIFT {rel}\n{diff}"


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Build the USAP skill registries: root index.json + "
            "root index.summary.json + legacy api/index.json. "
            "Default invocation regenerates all three files in place. "
            "Use --check to gate CI on registry drift; the "
            "`generated_at_utc` timestamp is normalised before diff so "
            "only structural changes fail the check."
        ),
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help=(
            "Regenerate in memory; exit 1 if any committed registry file "
            "differs from the freshly built payload."
        ),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT_INDEX_PATH,
        help=(
            "Path for the root index.json (default: <repo>/index.json). "
            "The companion index.summary.json is always written next to it."
        ),
    )
    args = parser.parse_args()

    timestamp = _utc_now_iso()
    root_payload, summary_payload, legacy_payload = _build_payloads(timestamp)

    root_text = _serialize(root_payload)
    summary_text = _serialize(summary_payload)
    legacy_text = _serialize(legacy_payload)

    root_out: Path = args.output
    summary_out: Path = root_out.parent / "index.summary.json"
    legacy_out: Path = LEGACY_API_INDEX_PATH

    if args.check:
        results = [
            _check_file(root_out, root_text),
            _check_file(summary_out, summary_text),
            _check_file(legacy_out, legacy_text),
        ]
        ok = all(r[0] for r in results)
        report = "".join(r[1] for r in results)
        stream = sys.stdout if ok else sys.stderr
        stream.write(report)
        if not ok:
            sys.stderr.write(
                "\nRun: python3 tools/build_index.py  # then commit.\n"
            )
            return 1
        return 0

    legacy_out.parent.mkdir(parents=True, exist_ok=True)
    root_out.write_text(root_text, encoding="utf-8")
    summary_out.write_text(summary_text, encoding="utf-8")
    legacy_out.write_text(legacy_text, encoding="utf-8")

    def _rel(p: Path) -> str:
        try:
            return str(p.relative_to(REPO_ROOT))
        except ValueError:
            return str(p)

    print(f"wrote {_rel(root_out)} ({len(root_text):,} bytes)")
    print(f"wrote {_rel(summary_out)} ({len(summary_text):,} bytes)")
    print(f"wrote {_rel(legacy_out)} ({len(legacy_text):,} bytes)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
