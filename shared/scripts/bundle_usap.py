#!/usr/bin/env python3
"""USAP Bundle Generator — builds a universal system prompt from all agents and skills."""

import argparse
import sys
from pathlib import Path
from typing import List, Optional, Tuple

REPO_ROOT = Path(__file__).resolve().parents[2]

MAIN_AGENT = REPO_ROOT / "agents" / "security" / "cs-security-analyst.md"

# Ordered list of cs-* agents excluding Alex (cs-security-analyst is bundled as
# MAIN_AGENT). Update when a new orchestrator agent ships.
OTHER_AGENTS = [
    ("cs-incident-responder",       REPO_ROOT / "agents" / "security"   / "cs-incident-responder.md"),
    ("cs-red-teamer",               REPO_ROOT / "agents" / "security"   / "cs-red-teamer.md"),
    ("cs-blue-team-analyst",        REPO_ROOT / "agents" / "security"   / "cs-blue-team-analyst.md"),
    ("cs-cloud-investigator",       REPO_ROOT / "agents" / "security"   / "cs-cloud-investigator.md"),
    ("cs-supply-chain-defender",    REPO_ROOT / "agents" / "security"   / "cs-supply-chain-defender.md"),
    ("cs-threat-intel-lead",        REPO_ROOT / "agents" / "security"   / "cs-threat-intel-lead.md"),
    ("cs-purple-team-lead",         REPO_ROOT / "agents" / "security"   / "cs-purple-team-lead.md"),
    ("cs-appsec-engineer",          REPO_ROOT / "agents" / "appsec"     / "cs-appsec-engineer.md"),
    ("cs-devsecops-engineer",       REPO_ROOT / "agents" / "devsecops"  / "cs-devsecops-engineer.md"),
    ("cs-ciso-advisor",             REPO_ROOT / "agents" / "executive"  / "cs-ciso-advisor.md"),
    ("cs-security-program-manager", REPO_ROOT / "agents" / "governance" / "cs-security-program-manager.md"),
]

# Active domains. Kept in sync with tools/validate_skill.py::ACTIVE_DOMAINS.
DOMAINS = [
    "appsec-devsecops",
    "cloud-infra",
    "detection",
    "governance",
    "identity-access",
    "pentest",
    "platform-ai",
    "red-team",
    "response",
    "risk-compliance",
    "system-security",
    "webapp-security",
]

MODE_OUTPUT_MAP = {
    "lite": "dist/USAP_LITE.md",
    "pro":  "dist/USAP_PRO.md",
    "full": "dist/USAP_BUNDLE.md",
}


def collect_skills(domain_filter: Optional[str] = None) -> List[Tuple[str, str, Path]]:
    """Return list of (domain, slug, path) tuples sorted by domain then slug."""
    domains = [domain_filter] if domain_filter else DOMAINS
    skills = []
    for domain in domains:
        domain_dir = REPO_ROOT / domain
        if not domain_dir.is_dir():
            continue
        for skill_md in sorted(domain_dir.glob("*/SKILL.md")):
            slug = skill_md.parent.name
            skills.append((domain, slug, skill_md))
    return skills


def collect_agents() -> List[Tuple[str, Path, bool]]:
    """Return list of (name, path, is_main) tuples."""
    agents = [("cs-security-analyst", MAIN_AGENT, True)]
    for name, path in OTHER_AGENTS:
        agents.append((name, path, False))
    return agents


def cmd_list_agents(_args: argparse.Namespace) -> None:
    for name, path, is_main in collect_agents():
        rel = path.relative_to(REPO_ROOT)
        tag = "  [MAIN]" if is_main else ""
        print(f"{name:<35} {rel}{tag}")


def cmd_list_skills(args: argparse.Namespace) -> None:
    domain_filter = getattr(args, "domain", None)
    skills = collect_skills(domain_filter)
    if not skills:
        domain_msg = f" in domain '{domain_filter}'" if domain_filter else ""
        print(f"No skills found{domain_msg}.", file=sys.stderr)
        sys.exit(1)
    current_domain = None
    for domain, slug, path in skills:
        if domain != current_domain:
            print(f"\n[{domain}]")
            current_domain = domain
        print(f"  {slug}")


def cmd_bundle(args: argparse.Namespace) -> None:
    mode: str = args.mode

    # Determine output path: explicit -o wins; otherwise derive from mode
    if args.output is not None:
        output_path = Path(args.output)
    else:
        output_path = REPO_ROOT / MODE_OUTPUT_MAP[mode]

    output_path.parent.mkdir(parents=True, exist_ok=True)

    sections: list[str] = []

    sections.append(
        "# USAP — Unified Security Agent Platform\n"
        "# Entry point: Alex (cs-security-analyst) — universal security advisor\n"
        "# Paste this entire file as your system prompt.\n"
        f"# Kit: {mode.upper()}\n"
    )

    agents_bundled = 0
    skills_bundled = 0

    # Alex always goes first in every kit
    if MAIN_AGENT.exists():
        sections.append("---\n[ALEX — USAP Security Expert]")
        sections.append(MAIN_AGENT.read_text(encoding="utf-8").strip())
        agents_bundled += 1
    else:
        print(f"Warning: main agent not found: {MAIN_AGENT}", file=sys.stderr)

    # Pro and Full: include other cs-* agents
    if mode in ("pro", "full"):
        other_sections: list[str] = []
        for name, path, _ in collect_agents()[1:]:
            if path.exists():
                other_sections.append(f"## {name}\n{path.read_text(encoding='utf-8').strip()}")
                agents_bundled += 1
            else:
                print(f"Warning: agent not found: {path}", file=sys.stderr)
        if other_sections:
            sections.append("---\n[AVAILABLE AGENTS]")
            sections.extend(other_sections)

    # Full only: include every active-domain SKILL.md.
    if mode == "full":
        skill_sections: list[str] = []
        for domain, slug, path in collect_skills():
            if path.exists():
                skill_sections.append(
                    f"## {slug} ({domain})\n{path.read_text(encoding='utf-8').strip()}"
                )
                skills_bundled += 1
            else:
                print(f"Warning: skill not found: {path}", file=sys.stderr)
        if skill_sections:
            sections.append("---\n[AVAILABLE SKILLS]")
            sections.extend(skill_sections)

    content = "\n\n".join(sections) + "\n"
    output_path.write_text(content, encoding="utf-8")

    size_kb = output_path.stat().st_size / 1024
    print(f"Bundle written to: {output_path}")
    print(f"  Mode           : {mode}")
    print(f"  Agents bundled : {agents_bundled}")
    print(f"  Skills bundled : {skills_bundled}")
    print(f"  File size      : {size_kb:.1f} KB")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="bundle_usap.py",
        description="USAP Bundle Generator — builds a universal system prompt from all agents and skills.",
    )
    sub = parser.add_subparsers(dest="command", metavar="command")
    sub.required = True

    # bundle
    p_bundle = sub.add_parser("bundle", help="Generate a USAP kit bundle")
    p_bundle.add_argument(
        "--mode",
        choices=["lite", "pro", "full"],
        default="full",
        help=(
            "Kit mode: "
            "lite = Alex only (dist/USAP_LITE.md); "
            "pro = Alex + all 11 other cs-* agents (dist/USAP_PRO.md); "
            "full = Alex + agents + every active-domain skill "
            "(dist/USAP_BUNDLE.md). "
            "Default: full"
        ),
    )
    p_bundle.add_argument(
        "-o", "--output",
        default=None,
        metavar="PATH",
        help="Override output file path (default: derived from --mode)",
    )
    p_bundle.set_defaults(func=cmd_bundle)

    # list-agents
    p_agents = sub.add_parser("list-agents", help="Print all cs-* agent names")
    p_agents.set_defaults(func=cmd_list_agents)

    # list-skills
    p_skills = sub.add_parser("list-skills", help="Print all skill slugs by domain")
    p_skills.add_argument(
        "--domain",
        metavar="DOMAIN",
        help="Filter by domain name (e.g. detection, response)",
    )
    p_skills.set_defaults(func=cmd_list_skills)

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
