#!/usr/bin/env python3
"""Regenerate `expected_outputs/sample_output.json` for every active-domain skill.

Reads each ``SKILL.md`` frontmatter + Persona/Overview prose and emits a
contract-conformant 11-field representative payload. The output is
deterministic per skill — re-running the generator produces byte-identical
JSON, so CI can detect drift.

Stdlib only. Mirrors the parser in ``tools/validate_skill.py``.

Usage::

    python3 tools/regen_samples.py            # regenerate every failing sample
    python3 tools/regen_samples.py --all      # regenerate *every* sample (overwrite)
    python3 tools/regen_samples.py --check    # exit 1 if any sample differs

Design choices:
- key_findings are derived from the skill's Persona / Overview noun phrases plus its
  domain — never invented out of thin air.
- intent_type and severity are inferred from skill name keywords; the mapping is
  documented in INTENT_RULES / SEVERITY_RULES below.
- evidence_references is populated only when severity >= "high" (the contract
  requires it then). Refs cite the skill's own SKILL.md + workflow.md — real,
  inspectable files.
- timestamp_utc is fixed at SAMPLE_TIMESTAMP so the output is reproducible.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Dict, List, Optional

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "tools"))
from validate_skill import ACTIVE_DOMAINS, parse_frontmatter  # noqa: E402

SAMPLE_TIMESTAMP = "2026-06-22T12:00:00Z"

# Map keywords in the skill slug → intent_type per standards/output-contract.md.
# Order matters: first match wins.
INTENT_RULES = [
    ("hunt",           "detect"),
    ("detection",      "detect"),
    ("exposure",       "detect"),
    ("scan",           "detect"),
    ("classifier",     "detect"),
    ("monitor",        "detect"),
    ("honeypot",       "detect"),
    ("response",       "respond"),
    ("incident",       "respond"),
    ("containment",    "respond"),
    ("forensics",      "analyze"),
    ("triage",         "analyze"),
    ("posture",        "analyze"),
    ("audit",          "analyze"),
    ("assessment",     "analyze"),
    ("model",          "analyze"),
    ("analysis",       "analyze"),
    ("analytics",      "analyze"),
    ("review",         "analyze"),
    ("classification", "analyze"),
    ("risk",           "advise"),
    ("debt",           "advise"),
    ("advisor",        "advise"),
    ("planner",        "advise"),
    ("policy",         "advise"),
    ("roadmap",        "advise"),
    ("management",     "advise"),
    ("requirements",   "advise"),
    ("brief",          "report"),
    ("report",         "report"),
    ("metrics",        "report"),
    ("tracker",        "report"),
    ("dpia",           "report"),
    ("orchestrator",   "escalate"),
    ("guardrail",      "block"),
    ("broker",         "block"),
]

# Severity defaults by skill family. Most analytical skills default to "medium";
# active-response / red-team / cloud-protection skills default "high".
SEVERITY_RULES = [
    ("incident",     "high"),
    ("zero-day",     "high"),
    ("containment",  "high"),
    ("forensics",    "high"),
    ("red-team",     "high"),
    ("exploitation", "high"),
    ("pentest",      "high"),
    ("workload-protection", "high"),
    ("insider",      "high"),
    ("default",      "medium"),
]

# Default downstream next_agents by intent_type. Empty list is valid for
# terminal advisory skills.
NEXT_AGENT_HINTS = {
    "detect":   [],
    "respond":  [],
    "analyze":  [],
    "advise":   [],
    "report":   [],
    "escalate": [],
    "block":    [],
}

# A few high-confidence skill-specific chains (kept narrow, only when the
# downstream is obvious from the SKILL.md narrative).
CHAIN_OVERRIDES: Dict[str, List[str]] = {
    "threat-hunting":              ["incident-classification"],
    "behavioral-analytics":        ["threat-hunting"],
    "detection-engineering":       ["threat-hunting"],
    "secrets-exposure":            ["incident-classification"],
    "incident-classification":     ["incident-commander"],
    "incident-commander":          ["containment-advisor"],
    "containment-advisor":         ["forensics"],
    "zero-day-response":           ["zero-day-response-governance"],
    "red-team-planner":            ["red-team-operations"],
    "red-team-operations":         ["attack-path-analysis"],
    "attack-path-analysis":        ["safe-exploitation"],
    "safe-exploitation":           ["pentest-reporting"],
    "supply-chain-risk":           ["build-integrity"],
    "build-integrity":             ["supply-chain-simulation"],
    "secure-sdlc":                 ["sast-dast-coordinator"],
    "sast-dast-coordinator":       ["finding-triage"],
    "devsecops-pipeline":          ["sast-dast-coordinator"],
    "iac-security":                ["cloud-security-posture"],
    "cloud-security-posture":      ["cloud-workload-protection"],
    "endpoint-os-security":        ["telemetry-signal-quality"],
    "identity-access-risk":        ["cryptography-key-management"],
    "data-security-classification": ["privacy-dpia"],
    "privacy-dpia":                ["compliance-mapping"],
    "compliance-mapping":          ["metrics-reporting"],
    "metrics-reporting":           ["ciso-brief-generator"],
    "ciso-brief-generator":        [],
    "vulnerability-management":    ["security-debt-tracker"],
    "security-debt-tracker":       ["security-roadmap-planner"],
    "security-architecture":       ["security-roadmap-planner"],
    "telemetry-signal-quality":    ["detection-engineering"],
    "network-exposure":            ["attack-surface-management"],
    "attack-surface-management":   ["threat-hunting"],
    "ai-agent-security":           ["agent-integrity-monitor"],
    "agent-integrity-monitor":     ["ai-ethics-governance"],
    "guardrail":                   ["tool-execution-broker"],
    "tool-execution-broker":       [],
    "third-party-vendor-risk":     ["supply-chain-risk"],
    "orchestrator":                [],
    "ai-ethics-governance":        [],
    "enterprise-risk-assessment":  ["risk-threat-modeling"],
    "risk-threat-modeling":        ["compliance-mapping"],
    "cyber-insurance":             ["compliance-mapping"],
    "quantum-security-readiness": ["security-roadmap-planner"],
    "regulatory-horizon":          ["compliance-mapping"],
    "internal-audit-assurance":    ["metrics-reporting"],
    "knowledge-management":        [],
    "security-awareness":          ["metrics-reporting"],
    "security-policy-control":     ["compliance-mapping"],
    "findings-tracker":            [],
    "security-posture-score":     ["ciso-brief-generator"],
    "deception-honeypot":          ["incident-classification"],
    "ot-iot-device-security":      ["cloud-workload-protection"],
    "cryptography-key-management": [],
    "insider-physical-risk":       ["incident-classification"],
}

# Skills that recommend / execute mutating actions need human_approval_required: true.
MUTATING_SLUGS = {
    "containment-advisor",
    "incident-commander",
    "cryptography-key-management",
    "zero-day-response",
    "safe-exploitation",
}


def _slug_intent(slug: str) -> str:
    for needle, intent in INTENT_RULES:
        if needle in slug:
            return intent
    return "analyze"


def _slug_severity(slug: str) -> str:
    for needle, sev in SEVERITY_RULES[:-1]:
        if needle in slug:
            return sev
    return "medium"


def _extract_persona_line(body: str) -> Optional[str]:
    m = re.search(r"##\s*Persona\s*\n+(.+?)(?=\n##|\n---|\Z)", body, re.DOTALL)
    if not m:
        return None
    block = m.group(1).strip()
    # First non-empty line — the persona sentence.
    for line in block.splitlines():
        line = line.strip()
        if line and not line.startswith("**"):
            return line
    return None


def _extract_overview(body: str) -> Optional[str]:
    m = re.search(r"##\s*Overview\s*\n+(.+?)(?=\n##|\n---|\Z)", body, re.DOTALL)
    if not m:
        return None
    return m.group(1).strip().splitlines()[0].strip()


def _extract_mandate(body: str) -> Optional[str]:
    m = re.search(r"\*\*Primary mandate:\*\*\s*(.+?)(?:\n|$)", body)
    if m:
        return m.group(1).strip().rstrip(".")
    return None


def _slug_title(slug: str) -> str:
    return slug.replace("-", " ").title()


def _build_payload(skill_dir: Path) -> Dict:
    slug = skill_dir.name
    domain = skill_dir.parent.name
    skill_md = skill_dir / "SKILL.md"
    text = skill_md.read_text(encoding="utf-8")
    fm = parse_frontmatter(text) or {}
    body = text.split("---", 2)[-1] if text.startswith("---") else text

    intent = _slug_intent(slug)
    severity = _slug_severity(slug)

    metadata = fm.get("metadata") or {}
    frameworks = (metadata.get("frameworks") or {}) if isinstance(metadata, dict) else {}
    mitre = frameworks.get("mitre_attack") if isinstance(frameworks, dict) else None
    nist = frameworks.get("nist_csf") if isinstance(frameworks, dict) else None
    owasp = frameworks.get("owasp_top10") if isinstance(frameworks, dict) else None

    mandate = _extract_mandate(body) or _extract_overview(body) or _slug_title(slug)
    persona_line = _extract_persona_line(body) or ""

    title = _slug_title(slug)

    findings = [
        f"Representative finding for {title}: baseline pass against documented decision tables in SKILL.md",
        f"Skill mandate observed: {mandate}",
    ]
    if isinstance(mitre, list) and mitre:
        findings.append(f"MITRE ATT&CK techniques in scope for this run: {', '.join(map(str, mitre[:4]))}")
    if isinstance(nist, list) and nist:
        findings.append(f"NIST CSF 2.0 subcategories touched: {', '.join(map(str, nist[:4]))}")
    if isinstance(owasp, list) and owasp:
        findings.append(f"OWASP Top 10 categories in scope: {', '.join(map(str, owasp[:4]))}")

    # Always at least one entry per contract.
    findings = findings[:5]

    evidence_refs = []
    if severity in ("critical", "high"):
        evidence_refs = [
            {
                "source": "skill-md",
                "ref": f"{domain}/{slug}/SKILL.md",
                "quote": f"Persona: {persona_line[:160]}" if persona_line else f"Skill {slug} reference output.",
            },
            {
                "source": "workflow",
                "ref": f"{domain}/{slug}/references/workflow.md",
                "quote": "See workflow.md for the step-by-step procedure this payload illustrates.",
            },
        ]

    next_agents = CHAIN_OVERRIDES.get(slug, NEXT_AGENT_HINTS[intent])

    human_approval = slug in MUTATING_SLUGS

    action_phrase_map = {
        "detect":   "Surface candidate findings to the operator and hand off to triage.",
        "respond":  "Recommend the next containment step; require operator approval before any mutating action.",
        "analyze":  "Produce structured analysis with explicit assumptions and chain to the next analytical step.",
        "advise":   "Issue an advisory recommendation; flag any policy-blocking constraints for the operator.",
        "report":   "Emit a stakeholder-ready summary tied to the underlying evidence package.",
        "escalate": "Route the event to the matching specialist agent based on classification rules.",
        "block":    "Refuse the requested action and emit the policy violation that triggered the block.",
    }

    payload = {
        "agent_slug": slug,
        "intent_type": intent,
        "action": action_phrase_map[intent],
        "rationale": (
            f"Representative output for the {title} skill. {mandate}. "
            f"This payload is a contract-conformant baseline emitted by the sample generator; "
            f"a live run would substitute real findings derived from the operator-supplied input package."
        ),
        "confidence": 0.78,
        "severity": severity,
        "key_findings": findings,
        "evidence_references": evidence_refs,
        "next_agents": next_agents,
        "human_approval_required": human_approval,
        "timestamp_utc": SAMPLE_TIMESTAMP,
    }
    return payload


def _all_skill_dirs() -> List[Path]:
    out = []
    for domain in ACTIVE_DOMAINS:
        d = REPO_ROOT / domain
        if not d.is_dir():
            continue
        for s in sorted(d.iterdir()):
            if s.is_dir() and (s / "SKILL.md").is_file():
                out.append(s)
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--all", action="store_true",
                    help="Regenerate every sample, not just contract-failing ones.")
    ap.add_argument("--check", action="store_true",
                    help="Exit 1 if any sample would change.")
    args = ap.parse_args()

    sys.path.insert(0, str(REPO_ROOT / "tools"))
    from output_contract import validate_payload  # noqa: E402

    changed = 0
    written = 0
    skipped = 0
    for skill_dir in _all_skill_dirs():
        sample_path = skill_dir / "expected_outputs" / "sample_output.json"
        sample_path.parent.mkdir(parents=True, exist_ok=True)
        existing = None
        if sample_path.exists():
            try:
                existing = json.loads(sample_path.read_text())
            except Exception:
                existing = None
        # Structural validation only. The generator produces 11-field stubs;
        # the hardest-line evidence gate is a per-skill rollout concern (samples
        # gain resolvable evidence as their skill is wired to the data backend),
        # so generation must not depend on it. Mirrors the corpus CI, which
        # runs output_contract.py --structural-only.
        existing_violations = (
            validate_payload(existing, evidence_gate=False)
            if isinstance(existing, dict) else ["not a dict"]
        )
        # If existing is already a structurally-clean contract payload AND we're
        # not in --all mode, leave it alone — we don't want to clobber
        # hand-authored faithful samples like vuln-scan/threat-model.
        if not args.all and isinstance(existing, dict) and not existing_violations:
            skipped += 1
            continue
        new_payload = _build_payload(skill_dir)
        new_violations = validate_payload(new_payload, evidence_gate=False)
        if new_violations:
            print(f"GENERATOR ERROR: payload for {skill_dir} still has violations:")
            for v in new_violations:
                print(f"  - {v}")
            return 2
        new_text = json.dumps(new_payload, indent=2) + "\n"
        if existing == new_payload:
            continue
        if args.check:
            changed += 1
            print(f"DIFF {sample_path.relative_to(REPO_ROOT)}")
            continue
        sample_path.write_text(new_text)
        written += 1
    if args.check and changed:
        print(f"\n{changed} sample(s) would change. Run without --check to update.")
        return 1
    print(f"written: {written}  skipped (already clean): {skipped}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
