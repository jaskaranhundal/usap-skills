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
  - ``mappings/mitre-attack/ATTACK_COVERAGE.md`` — per-tactic coverage
    report (Reconnaissance through Impact) with covered-vs-uncovered
    bars and per-tactic technique tables.
  - ``mappings/nist-csf/csf-alignment.md`` — per-subcategory skill counts.

For MITRE ATT&CK, T-IDs are sourced from BOTH the frontmatter
``metadata.frameworks.mitre_attack`` array AND any ``T\\d{4}(\\.\\d{3})?``
patterns regex-scanned from the SKILL.md body. Body and frontmatter IDs
are deduplicated before counting.

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
import re
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
ATTACK_TACTIC_COVERAGE = MAPPINGS_ROOT / "mitre-attack" / "ATTACK_COVERAGE.md"
CSF_ALIGNMENT = MAPPINGS_ROOT / "nist-csf" / "csf-alignment.md"

# Regex used to scavenge T-IDs from SKILL.md body markdown. Matches both
# parent IDs ("T1078") and subtechniques ("T1078.004"). Word-boundary
# anchors prevent false positives from longer identifiers.
TID_RE = re.compile(r"\bT\d{4}(?:\.\d{3})?\b")

# MITRE ATT&CK Enterprise tactics in kill-chain order with v16
# technique-count denominators. Counts are pinned manually because the
# extractor is stdlib-only and never reaches the live MITRE TAXII feed.
# Update alongside ``NAVIGATOR_ATTACK_VERSION`` when bumping the ATT&CK
# version pin. "Other / ICS" catches T0xxx (ICS ATT&CK) and any T-ID not
# in TID_TO_TACTICS so the report stays honest about uncategorised IDs.
TACTIC_DEFS: List[Tuple[str, str, int]] = [
    ("TA0043", "Reconnaissance", 10),
    ("TA0042", "Resource Development", 8),
    ("TA0001", "Initial Access", 10),
    ("TA0002", "Execution", 14),
    ("TA0003", "Persistence", 20),
    ("TA0004", "Privilege Escalation", 13),
    ("TA0005", "Defense Evasion", 43),
    ("TA0006", "Credential Access", 17),
    ("TA0007", "Discovery", 32),
    ("TA0008", "Lateral Movement", 9),
    ("TA0009", "Collection", 17),
    ("TA0011", "Command and Control", 16),
    ("TA0010", "Exfiltration", 9),
    ("TA0040", "Impact", 14),
    ("OTHER", "Other / ICS / Uncategorised", 0),
]

# Parent technique -> list of tactic IDs it belongs to. Subtechniques
# inherit their parent's tactic set, so only parent T-IDs are listed.
# Sourced from ATT&CK v16 enterprise-attack.json; pinned manually because
# the extractor never reaches the live MITRE TAXII feed.
TID_TO_TACTICS: Dict[str, List[str]] = {
    "T1003": ["TA0006"],
    "T1005": ["TA0009"],
    "T1021": ["TA0008"],
    "T1039": ["TA0009"],
    "T1040": ["TA0006", "TA0007"],
    "T1041": ["TA0010"],
    "T1046": ["TA0007"],
    "T1047": ["TA0002"],
    "T1048": ["TA0010"],
    "T1053": ["TA0002", "TA0003", "TA0004"],
    "T1055": ["TA0004", "TA0005"],
    "T1059": ["TA0002"],
    "T1068": ["TA0004"],
    "T1070": ["TA0005"],
    "T1078": ["TA0001", "TA0003", "TA0004", "TA0005"],
    "T1082": ["TA0007"],
    "T1090": ["TA0011"],
    "T1098": ["TA0003", "TA0004"],
    "T1110": ["TA0006"],
    "T1133": ["TA0001", "TA0003"],
    "T1134": ["TA0004", "TA0005"],
    "T1136": ["TA0003"],
    "T1190": ["TA0001"],
    "T1195": ["TA0001"],
    "T1203": ["TA0002"],
    "T1210": ["TA0008"],
    "T1218": ["TA0005"],
    "T1222": ["TA0005"],
    "T1484": ["TA0004", "TA0005"],
    "T1486": ["TA0040"],
    "T1530": ["TA0009"],
    "T1547": ["TA0003", "TA0004"],
    "T1548": ["TA0004", "TA0005"],
    "T1550": ["TA0005", "TA0008"],
    "T1552": ["TA0006"],
    "T1556": ["TA0003", "TA0005", "TA0006"],
    "T1562": ["TA0005"],
    "T1563": ["TA0008"],
    "T1565": ["TA0040"],
    "T1566": ["TA0001"],
    "T1567": ["TA0010"],
    "T1574": ["TA0003", "TA0004", "TA0005"],
    "T1590": ["TA0043"],
    "T1592": ["TA0043"],
    "T1619": ["TA0007"],
}

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


def _split_body(text: str) -> str:
    """Return the markdown body with the leading YAML frontmatter stripped."""
    if not text.startswith("---"):
        return text
    # Find the closing ``---`` of the frontmatter block.
    nl = text.find("\n")
    if nl == -1:
        return ""
    end = text.find("\n---", nl)
    if end == -1:
        return text
    return text[end + len("\n---"):]


def _scan_body_tids(body: str) -> List[str]:
    """Regex-scan body markdown for T-IDs; dedup preserving sort order."""
    return sorted({m.group(0) for m in TID_RE.finditer(body)})


def _read_frameworks(
    path: Path,
) -> Tuple[str, str, Dict[str, List[str]], List[str]]:
    """Return ``(domain, slug, frameworks_dict, body_tids)`` from one SKILL.md.

    ``frameworks_dict`` is empty when the skill has no
    ``metadata.frameworks`` block. ``body_tids`` is the deduplicated
    list of T-IDs scavenged from the SKILL.md body via ``TID_RE``.
    Malformed frontmatter values are silently dropped here — the
    validator is the single source of error reporting; the extractor
    only consumes well-formed input.
    """
    domain = path.parent.parent.name
    slug = path.parent.name

    try:
        text = path.read_text(encoding="utf-8")
    except (UnicodeDecodeError, OSError):
        return domain, slug, {}, []

    fm = parse_frontmatter(text)
    body = _split_body(text)
    body_tids = _scan_body_tids(body)

    if not isinstance(fm, dict):
        return domain, slug, {}, body_tids

    metadata = fm.get("metadata") if isinstance(fm.get("metadata"), dict) else {}
    if not isinstance(metadata, dict):
        return domain, slug, {}, body_tids

    raw = metadata.get("frameworks") if isinstance(metadata.get("frameworks"), dict) else {}
    out: Dict[str, List[str]] = {}
    if isinstance(raw, dict):
        for k, v in raw.items():
            if isinstance(v, list):
                out[k] = [s for s in v if isinstance(s, str)]

    # Top-level ``mitre_attack`` is accepted as an alternate location
    # (some skills may declare it outside ``metadata.frameworks`` per
    # the bundled-PR spec); merged into the mitre_attack list.
    top_tids = fm.get("mitre_attack")
    if isinstance(top_tids, list):
        existing = out.get("mitre_attack", [])
        merged = list(existing)
        for tid in top_tids:
            if isinstance(tid, str) and tid not in merged:
                merged.append(tid)
        if merged:
            out["mitre_attack"] = merged

    return domain, slug, out, body_tids


def _gather() -> Dict[str, List[Tuple[str, str, List[str]]]]:
    """Collect ``{framework_key: [(domain, slug, [ids]), ...]}``.

    For ``mitre_attack``, T-IDs from frontmatter are merged with T-IDs
    scavenged from the SKILL.md body so skills that document techniques
    in prose but haven't backfilled the frontmatter array still count.
    Per-skill dedup is preserved by routing through a ``set``.
    """
    out: Dict[str, List[Tuple[str, str, List[str]]]] = defaultdict(list)
    for sm in _iter_skill_paths():
        domain, slug, fw, body_tids = _read_frameworks(sm)

        # Merge body T-IDs into the mitre_attack bucket.
        merged_attack = list(fw.get("mitre_attack", []))
        for tid in body_tids:
            if tid not in merged_attack:
                merged_attack.append(tid)
        if merged_attack:
            out["mitre_attack"].append((domain, slug, merged_attack))

        for fname, ids in fw.items():
            if fname == "mitre_attack":
                continue  # already handled with body merge
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
        "Auto-generated by `tools/framework_extractor.py` from "
        "`metadata.frameworks.mitre_attack` arrays AND from any "
        "`T\\d{4}(\\.\\d{3})?` patterns scavenged from each active-domain "
        "`SKILL.md` body. Do not edit by hand; CI fails on drift.",
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


def _parent_tid(tid: str) -> str:
    """Return the parent T-ID for a (sub)technique. ``T1078.004`` -> ``T1078``."""
    return tid.split(".", 1)[0]


def _tactics_for(tid: str) -> List[str]:
    """Return the tactic IDs a T-ID belongs to. Falls back to ``OTHER``."""
    return TID_TO_TACTICS.get(_parent_tid(tid), ["OTHER"])


def _ascii_bar(covered: int, total: int, width: int = 20) -> str:
    """Render a 20-cell ASCII bar for the covered/total ratio."""
    if total <= 0:
        # Buckets with no denominator (Other / ICS) just show the count.
        return "[" + ("-" * width) + "]"
    filled = max(0, min(width, round((covered / total) * width)))
    return "[" + ("#" * filled) + ("-" * (width - filled)) + "]"


def _attack_per_tactic_md(att_entries: List[Tuple[str, str, List[str]]]) -> str:
    """Build the per-tactic ATTACK_COVERAGE.md (kill-chain ordered).

    For each MITRE Enterprise tactic plus the catch-all OTHER bucket,
    emits:
      - a header line with the tactic name and a covered/total bar
      - a table of T-IDs USAP covers under that tactic with the
        contributing skill slugs
    Tactic membership for each T-ID comes from ``TID_TO_TACTICS``;
    sub-technique IDs inherit their parent's tactic set.
    """
    # tactic_id -> tid -> [skill_refs]
    bucket: Dict[str, Dict[str, List[str]]] = {
        tid: defaultdict(list) for tid, _, _ in TACTIC_DEFS
    }
    all_tids: set = set()
    skills_contributing: set = set()

    for domain, slug, ids in att_entries:
        ref = f"`{domain}/{slug}`"
        contributed = False
        for tid in ids:
            all_tids.add(tid)
            for tactic in _tactics_for(tid):
                bucket[tactic][tid].append(ref)
                contributed = True
        if contributed:
            skills_contributing.add(f"{domain}/{slug}")

    total_tids = len(all_tids)
    total_skills = len(skills_contributing)

    lines = [
        "# MITRE ATT&CK Coverage (per-tactic)",
        "",
        "Auto-generated by `tools/framework_extractor.py` from "
        "`metadata.frameworks.mitre_attack` arrays AND from any "
        "`T\\d{4}(\\.\\d{3})?` patterns scavenged from each active-domain "
        "SKILL.md body. Do not edit by hand; CI fails on drift.",
        "",
        f"- Distinct T-IDs covered: **{total_tids}**",
        f"- Skills contributing at least one T-ID: **{total_skills}**",
        f"- Tactics surveyed: **{len(TACTIC_DEFS) - 1}** Enterprise "
        "(plus an `OTHER` bucket for ICS / unmapped IDs)",
        "",
        "Bars are scaled against MITRE ATT&CK v16 Enterprise technique "
        "counts (parent techniques only — subtechniques roll up to their "
        "parent for the denominator).",
        "",
        "## Per-Tactic Coverage",
        "",
    ]

    for tactic_id, tactic_name, total in TACTIC_DEFS:
        tid_map = bucket.get(tactic_id, {})
        # Parent-technique dedup so the bar matches MITRE's denominator.
        covered_parents = {_parent_tid(t) for t in tid_map.keys()}
        covered = len(covered_parents)
        bar = _ascii_bar(covered, total)
        if total > 0:
            header = (
                f"### {tactic_id} - {tactic_name}\n\n"
                f"`{bar}` {covered} / {total} parent techniques covered"
            )
        else:
            distinct = len(tid_map)
            header = (
                f"### {tactic_id} - {tactic_name}\n\n"
                f"`{bar}` {distinct} unmapped T-ID(s) "
                "(ICS ATT&CK or unrecognised parent technique)"
            )
        lines.append(header)
        lines.append("")
        if not tid_map:
            lines.append("_No USAP skills reference techniques in this tactic._")
            lines.append("")
            continue
        lines.append("| Technique ID | Skill count | Covering skills |")
        lines.append("|---|---:|---|")
        for tid in sorted(tid_map.keys()):
            refs = sorted(set(tid_map[tid]))
            lines.append(
                f"| `{tid}` | {len(refs)} | " + ", ".join(refs) + " |"
            )
        lines.append("")

    lines += [
        "## Methodology",
        "",
        "- T-IDs come from two sources per skill: the "
        "`metadata.frameworks.mitre_attack` array (or a top-level "
        "`mitre_attack:` array) and a regex scan of the SKILL.md body "
        "for `T\\d{4}(\\.\\d{3})?` patterns.",
        "- The two sources are deduplicated per skill before counting.",
        "- Tactic membership is taken from the pinned `TID_TO_TACTICS` "
        "table in `tools/framework_extractor.py` (ATT&CK v16). Update "
        "that table when bumping `NAVIGATOR_ATTACK_VERSION`.",
        "- Denominators are parent-technique counts from MITRE ATT&CK "
        "v16 Enterprise; subtechniques roll up to their parent so a "
        "skill citing both `T1078` and `T1078.004` still counts as one "
        "covered parent.",
        "",
    ]

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
        ATTACK_TACTIC_COVERAGE: _attack_per_tactic_md(att),
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
            ATTACK_TACTIC_COVERAGE: rendered[ATTACK_TACTIC_COVERAGE],
            CSF_ALIGNMENT: rendered[CSF_ALIGNMENT],
        }
    else:  # all
        selection = rendered

    for path, content in selection.items():
        _write(path, content)
    return 0


if __name__ == "__main__":
    sys.exit(main())
