#!/usr/bin/env python3
"""Generate USAP framework-coverage artifacts from SKILL.md frontmatter.

Reads ``metadata.frameworks.{mitre_attack, nist_csf, mitre_atlas,
owasp_top10, d3fend, nist_ai_rmf}`` arrays across every active-domain
``SKILL.md`` and emits:

  - ``mappings/mitre-attack/attack-navigator-layer.json`` — MITRE ATT&CK
    Navigator v4.5 layer; the per-technique ``score`` is the number of
    USAP skills covering that technique.
  - ``mappings/mitre-attack/coverage-summary.md`` — per-technique skill
    counts plus a domain x technique tally.
  - ``mappings/nist-csf/csf-alignment.md`` — per-subcategory skill counts.

Stdlib only. Frontmatter parsing is delegated to ``tools.validate_skill``
so the two tools stay in sync on YAML rules. Adding a new framework is a
two-file change: update the spec + the extractor's ``EMITTERS`` table.

Usage::

    python3 tools/framework_extractor.py --emit navigator
    python3 tools/framework_extractor.py --emit coverage
    python3 tools/framework_extractor.py --emit all
    python3 tools/framework_extractor.py --check          # CI drift gate

``--check`` regenerates in-memory and compares against the committed files.
Exits 1 if any drift is detected; prints a unified diff. Use this in CI to
forbid hand-maintained coverage docs — the source of truth lives in each
skill's ``metadata.frameworks.*`` frontmatter, never in these artifacts.
"""
from __future__ import annotations

import argparse
import difflib
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Dict, List, Tuple

# Re-use the validator's parser to keep YAML rules in one place.
sys.path.insert(0, str(Path(__file__).resolve().parent))
from validate_skill import (  # noqa: E402  (import after sys.path tweak)
    ACTIVE_DOMAINS,
    parse_frontmatter,
)

REPO_ROOT = Path(__file__).resolve().parent.parent
MAPPINGS_ROOT = REPO_ROOT / "mappings"

NAVIGATOR_LAYER = MAPPINGS_ROOT / "mitre-attack" / "attack-navigator-layer.json"
ATTACK_COVERAGE = MAPPINGS_ROOT / "mitre-attack" / "coverage-summary.md"
CSF_ALIGNMENT = MAPPINGS_ROOT / "nist-csf" / "csf-alignment.md"

# MITRE Navigator schema version USAP pins to. Bumping requires a manual
# review of the json shape (some keys move between minor versions).
NAVIGATOR_LAYER_VERSION = "4.5"
NAVIGATOR_TOOL_VERSION = "4.9.5"
NAVIGATOR_ATTACK_VERSION = "16"


def _iter_skill_paths() -> List[Path]:
    """Every active-domain ``<domain>/<slug>/SKILL.md``."""
    paths: List[Path] = []
    for domain in ACTIVE_DOMAINS:
        droot = REPO_ROOT / domain
        if not droot.is_dir():
            continue
        for skill in sorted(droot.iterdir()):
            sm = skill / "SKILL.md"
            if sm.is_file():
                paths.append(sm)
    return paths


def _read_frameworks(path: Path) -> Tuple[str, str, Dict[str, List[str]]]:
    """Return ``(domain, slug, frameworks_dict)`` from one SKILL.md.

    Frameworks_dict is empty when the skill has no ``metadata.frameworks``
    block. Malformed values are silently dropped here — the validator is
    the single source of error reporting; the extractor only consumes
    well-formed input.
    """
    domain = path.parent.parent.name
    slug = path.parent.name

    try:
        text = path.read_text(encoding="utf-8")
    except (UnicodeDecodeError, OSError):
        return domain, slug, {}

    fm = parse_frontmatter(text)
    if not isinstance(fm, dict):
        return domain, slug, {}

    metadata = fm.get("metadata") if isinstance(fm.get("metadata"), dict) else {}
    if not isinstance(metadata, dict):
        return domain, slug, {}

    raw = metadata.get("frameworks") if isinstance(metadata.get("frameworks"), dict) else {}
    out: Dict[str, List[str]] = {}
    if isinstance(raw, dict):
        for k, v in raw.items():
            if isinstance(v, list):
                out[k] = [s for s in v if isinstance(s, str)]
    return domain, slug, out


def _gather() -> Dict[str, List[Tuple[str, str, List[str]]]]:
    """Collect ``{framework_key: [(domain, slug, [ids]), ...]}``."""
    out: Dict[str, List[Tuple[str, str, List[str]]]] = defaultdict(list)
    for sm in _iter_skill_paths():
        domain, slug, fw = _read_frameworks(sm)
        for fname, ids in fw.items():
            if ids:
                out[fname].append((domain, slug, ids))
    return out


def _navigator_layer(att_entries: List[Tuple[str, str, List[str]]]) -> dict:
    """Build a MITRE Navigator v4.5 layer from per-skill ATT&CK lists.

    Score = number of distinct USAP skills covering each technique. Comment
    lists the covering skill slugs (Navigator renders comments on hover).
    Techniques are sorted by ID for stable JSON diffs.
    """
    tech_to_skills: Dict[str, List[str]] = defaultdict(list)
    for domain, slug, ids in att_entries:
        for tid in ids:
            tech_to_skills[tid].append(f"{domain}/{slug}")

    techniques = []
    for tid in sorted(tech_to_skills.keys()):
        covering = sorted(set(tech_to_skills[tid]))
        techniques.append({
            "techniqueID": tid,
            "score": len(covering),
            "color": "",
            "comment": "USAP skills covering: " + ", ".join(covering),
            "enabled": True,
            "metadata": [],
            "links": [],
            "showSubtechniques": True,
        })

    return {
        "name": "USAP MITRE ATT&CK Coverage",
        "versions": {
            "attack": NAVIGATOR_ATTACK_VERSION,
            "navigator": NAVIGATOR_TOOL_VERSION,
            "layer": NAVIGATOR_LAYER_VERSION,
        },
        "domain": "enterprise-attack",
        "description": (
            "Auto-generated by tools/framework_extractor.py from "
            "metadata.frameworks.mitre_attack across every active USAP "
            "skill. Do not edit by hand; CI will fail on drift."
        ),
        "filters": {"platforms": [
            "Windows", "Linux", "macOS",
            "Containers", "Network", "Office 365",
            "SaaS", "IaaS", "Google Workspace", "Azure AD",
        ]},
        "sorting": 3,
        "layout": {
            "layout": "side",
            "aggregateFunction": "average",
            "showID": False,
            "showName": True,
            "showAggregateScores": False,
            "countUnscored": False,
        },
        "hideDisabled": False,
        "techniques": techniques,
        "gradient": {
            "colors": ["#ff6666ff", "#ffe766ff", "#8ec843ff"],
            "minValue": 1,
            "maxValue": max((t["score"] for t in techniques), default=1),
        },
        "legendItems": [],
        "metadata": [],
        "links": [],
        "showTacticRowBackground": False,
        "tacticRowBackground": "#dddddd",
        "selectTechniquesAcrossTactics": True,
        "selectSubtechniquesWithParent": False,
    }


def _attack_summary_md(att_entries: List[Tuple[str, str, List[str]]]) -> str:
    """Build the MITRE ATT&CK per-technique markdown table."""
    tech_to_skills: Dict[str, List[str]] = defaultdict(list)
    domain_to_techniques: Dict[str, List[str]] = defaultdict(list)
    for domain, slug, ids in att_entries:
        for tid in ids:
            tech_to_skills[tid].append(f"`{domain}/{slug}`")
            domain_to_techniques[domain].append(tid)

    total_skills = len({(d, s) for d, s, _ in att_entries})
    total_techniques = len(tech_to_skills)

    lines = [
        "# MITRE ATT&CK Coverage",
        "",
        "Auto-generated by `tools/framework_extractor.py` from every "
        "`metadata.frameworks.mitre_attack` array in the active-domain "
        "`SKILL.md` files. Do not edit by hand; CI fails on drift.",
        "",
        f"- Distinct techniques covered: **{total_techniques}**",
        f"- Skills with at least one ATT&CK ID: **{total_skills}**",
        "",
        "## Per-technique coverage",
        "",
        "| Technique ID | Skill count | Covering skills |",
        "|---|---:|---|",
    ]
    for tid in sorted(tech_to_skills.keys()):
        covering = sorted(set(tech_to_skills[tid]))
        lines.append(
            f"| `{tid}` | {len(covering)} | "
            + ", ".join(covering)
            + " |"
        )

    lines += [
        "",
        "## Per-domain technique counts",
        "",
        "| Domain | Distinct ATT&CK IDs cited |",
        "|---|---:|",
    ]
    for domain in sorted(domain_to_techniques.keys()):
        unique = len(set(domain_to_techniques[domain]))
        lines.append(f"| `{domain}` | {unique} |")
    lines.append("")

    return "\n".join(lines)


def _csf_summary_md(csf_entries: List[Tuple[str, str, List[str]]]) -> str:
    """Build the NIST CSF 2.0 per-subcategory markdown."""
    sub_to_skills: Dict[str, List[str]] = defaultdict(list)
    func_to_count: Counter = Counter()  # GV/ID/PR/DE/RS/RC -> total IDs

    for domain, slug, ids in csf_entries:
        for sub in ids:
            sub_to_skills[sub].append(f"`{domain}/{slug}`")
            # Function code is the prefix before the dot (e.g., "DE" in "DE.CM-01")
            func_to_count[sub.split(".", 1)[0]] += 1

    total_skills = len({(d, s) for d, s, _ in csf_entries})
    total_subs = len(sub_to_skills)

    lines = [
        "# NIST CSF 2.0 Alignment",
        "",
        "Auto-generated by `tools/framework_extractor.py` from every "
        "`metadata.frameworks.nist_csf` array in the active-domain "
        "`SKILL.md` files. Do not edit by hand; CI fails on drift.",
        "",
        f"- Distinct subcategories cited: **{total_subs}**",
        f"- Skills with at least one CSF ID: **{total_skills}**",
        "",
        "## Per-function summary",
        "",
        "| Function | Skill citations |",
        "|---|---:|",
    ]
    func_order = ["GV", "ID", "PR", "DE", "RS", "RC"]
    for code in func_order:
        if func_to_count[code]:
            lines.append(f"| `{code}` | {func_to_count[code]} |")
    for code in sorted(func_to_count.keys()):
        if code not in func_order:
            lines.append(f"| `{code}` | {func_to_count[code]} |")

    lines += [
        "",
        "## Per-subcategory coverage",
        "",
        "| Subcategory | Skill count | Covering skills |",
        "|---|---:|---|",
    ]
    for sub in sorted(sub_to_skills.keys()):
        covering = sorted(set(sub_to_skills[sub]))
        lines.append(
            f"| `{sub}` | {len(covering)} | "
            + ", ".join(covering)
            + " |"
        )
    lines.append("")

    return "\n".join(lines)


def _render() -> Dict[Path, str]:
    """Return ``{path: serialised_content}`` for every artifact."""
    gathered = _gather()
    att = gathered.get("mitre_attack", [])
    csf = gathered.get("nist_csf", [])

    layer = _navigator_layer(att)
    return {
        NAVIGATOR_LAYER: json.dumps(layer, indent=2, sort_keys=False) + "\n",
        ATTACK_COVERAGE: _attack_summary_md(att),
        CSF_ALIGNMENT: _csf_summary_md(csf),
    }


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    print(f"  wrote {path.relative_to(REPO_ROOT)} ({len(content):,} bytes)")


def _check(rendered: Dict[Path, str]) -> int:
    """Return 0 if all on-disk artifacts match the freshly rendered content."""
    drift = []
    for path, expected in rendered.items():
        actual = path.read_text(encoding="utf-8") if path.is_file() else ""
        if actual != expected:
            drift.append((path, expected, actual))

    if not drift:
        print(
            f"OK  {len(rendered)} mapping artifact(s) match the source-of-truth "
            "frontmatter."
        )
        return 0

    for path, expected, actual in drift:
        print(f"DRIFT in {path.relative_to(REPO_ROOT)}:")
        diff = difflib.unified_diff(
            actual.splitlines(keepends=True),
            expected.splitlines(keepends=True),
            fromfile=str(path.relative_to(REPO_ROOT)) + " (committed)",
            tofile=str(path.relative_to(REPO_ROOT)) + " (regenerated)",
            n=3,
        )
        sys.stdout.writelines(diff)
        print()
    print(
        f"FAIL {len(drift)} artifact(s) drifted from the source-of-truth "
        "frontmatter. Run `python3 tools/framework_extractor.py --emit all` "
        "and commit the result."
    )
    return 1


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Generate USAP framework-coverage artifacts from "
            "metadata.frameworks.* across every active-domain SKILL.md."
        )
    )
    parser.add_argument(
        "--emit",
        choices=("navigator", "coverage", "all"),
        help="Write the corresponding artifact(s) under mappings/.",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Regenerate in-memory; fail if any committed artifact drifted.",
    )
    args = parser.parse_args()

    if not args.emit and not args.check:
        parser.error("provide --emit {navigator,coverage,all} or --check")

    rendered = _render()

    if args.check:
        return _check(rendered)

    selection: Dict[Path, str]
    if args.emit == "navigator":
        selection = {NAVIGATOR_LAYER: rendered[NAVIGATOR_LAYER]}
    elif args.emit == "coverage":
        selection = {
            ATTACK_COVERAGE: rendered[ATTACK_COVERAGE],
            CSF_ALIGNMENT: rendered[CSF_ALIGNMENT],
        }
    else:  # all
        selection = rendered

    for path, content in selection.items():
        _write(path, content)
    return 0


if __name__ == "__main__":
    sys.exit(main())
