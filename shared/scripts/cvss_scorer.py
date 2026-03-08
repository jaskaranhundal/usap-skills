#!/usr/bin/env python3
"""
cvss_scorer.py — USAP CVSS v3.1 Base Score Calculator

Implements the full CVSS v3.1 base score formula per FIRST.org specification.
Maps scores to USAP intent_type and mutating_category for pipeline integration.

Usage:
    python cvss_scorer.py --vector "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H"
    python cvss_scorer.py --severity critical
    python cvss_scorer.py --vector "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H" --json
    python cvss_scorer.py --bulk vectors.json
    python cvss_scorer.py --interactive

Exit codes:
    0  Score = None or Low  (< 4.0)
    1  Score = Medium        (4.0 – 6.9)
    2  Score = High          (7.0 – 8.9)
    3  Score = Critical      (9.0 – 10.0)
"""

import argparse
import json
import math
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple


# ── CVSS v3.1 metric weights ──────────────────────────────────────────────────
# Reference: https://www.first.org/cvss/v3.1/specification-document

# Attack Vector
AV_WEIGHTS: Dict[str, float] = {
    "N": 0.85,   # Network
    "A": 0.62,   # Adjacent
    "L": 0.55,   # Local
    "P": 0.20,   # Physical
}

# Attack Complexity
AC_WEIGHTS: Dict[str, float] = {
    "L": 0.77,   # Low
    "H": 0.44,   # High
}

# Privileges Required (scope-dependent)
PR_UNCHANGED: Dict[str, float] = {"N": 0.85, "L": 0.62, "H": 0.27}
PR_CHANGED:   Dict[str, float] = {"N": 0.85, "L": 0.50, "H": 0.50}

# User Interaction
UI_WEIGHTS: Dict[str, float] = {
    "N": 0.85,   # None
    "R": 0.62,   # Required
}

# Confidentiality / Integrity / Availability Impact
CIA_WEIGHTS: Dict[str, float] = {
    "N": 0.00,   # None
    "L": 0.22,   # Low
    "H": 0.56,   # High
}

# CVSS score range → severity label
SEVERITY_LABELS: List[Tuple[float, float, str]] = [
    (0.1,  3.9,  "Low"),
    (4.0,  6.9,  "Medium"),
    (7.0,  8.9,  "High"),
    (9.0, 10.0,  "Critical"),
]

# Metric human-readable descriptions
METRIC_DESCRIPTIONS = {
    "AV": {"N": "Network", "A": "Adjacent Network", "L": "Local", "P": "Physical"},
    "AC": {"L": "Low", "H": "High"},
    "PR": {"N": "None", "L": "Low", "H": "High"},
    "UI": {"N": "None", "R": "Required"},
    "S":  {"U": "Unchanged", "C": "Changed"},
    "C":  {"N": "None", "L": "Low", "H": "High"},
    "I":  {"N": "None", "L": "Low", "H": "High"},
    "A":  {"N": "None", "L": "Low", "H": "High"},
}

# Representative "worst case" vectors per severity (for --severity shorthand)
REPRESENTATIVE_VECTORS: Dict[str, str] = {
    "critical": "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H",   # 9.8
    "high":     "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:N/A:N",   # 7.5
    "medium":   "CVSS:3.1/AV:N/AC:L/PR:L/UI:N/S:U/C:L/I:L/A:N",   # 6.4
    "low":      "CVSS:3.1/AV:L/AC:H/PR:H/UI:R/S:U/C:L/I:N/A:N",   # 1.8
}


# ── Data classes ──────────────────────────────────────────────────────────────

@dataclass
class CVSSMetrics:
    AV: str   # Attack Vector:           N|A|L|P
    AC: str   # Attack Complexity:       L|H
    PR: str   # Privileges Required:     N|L|H
    UI: str   # User Interaction:        N|R
    S:  str   # Scope:                   U|C
    C:  str   # Confidentiality Impact:  N|L|H
    I:  str   # Integrity Impact:        N|L|H
    A:  str   # Availability Impact:     N|L|H

    def vector_string(self) -> str:
        return (
            f"CVSS:3.1/AV:{self.AV}/AC:{self.AC}/PR:{self.PR}"
            f"/UI:{self.UI}/S:{self.S}/C:{self.C}/I:{self.I}/A:{self.A}"
        )


@dataclass
class CVSSResult:
    vector_string: str
    base_score: float
    severity: str
    iss: float                          # Impact Sub-Score
    impact_score: float
    exploitability_score: float
    scope_changed: bool
    metrics: CVSSMetrics
    usap_intent_type: str               # mutating | read_only
    usap_mutating_category: Optional[str]
    cvss_url: str                       # NVD calculator link
    attack_narrative: str


# ── Core calculation ──────────────────────────────────────────────────────────

def roundup_cvss(x: float) -> float:
    """
    CVSS v3.1 Roundup function: ceiling to exactly 1 decimal place.
    Equivalent to: ceil(x * 10) / 10, using integer arithmetic to avoid
    floating-point rounding artifacts.
    """
    # Multiply by 100000, round to avoid FP issues, take ceiling at 10000s
    int_input = round(x * 100000)
    if int_input % 10000 == 0:
        return int_input / 100000
    return (math.floor(int_input / 10000) + 1) / 10.0


def severity_label(score: float) -> str:
    if score == 0.0:
        return "None"
    for low, high, label in SEVERITY_LABELS:
        if low <= score <= high:
            return label
    return "Critical" if score > 9.0 else "None"


def parse_vector(vector: str) -> CVSSMetrics:
    """Parse a CVSS v3.1 vector string into CVSSMetrics."""
    # Strip version prefix
    for prefix in ("CVSS:3.1/", "CVSS:3.0/", "CVSS:"):
        if vector.upper().startswith(prefix.upper()):
            vector = vector[len(prefix):]
            break

    parts: Dict[str, str] = {}
    for component in vector.split("/"):
        if ":" in component:
            key, val = component.split(":", 1)
            parts[key.strip().upper()] = val.strip().upper()

    required = ["AV", "AC", "PR", "UI", "S", "C", "I", "A"]
    missing = [r for r in required if r not in parts]
    if missing:
        raise ValueError(f"Vector missing required metrics: {', '.join(missing)}")

    return CVSSMetrics(
        AV=parts["AV"], AC=parts["AC"], PR=parts["PR"], UI=parts["UI"],
        S=parts["S"], C=parts["C"], I=parts["I"], A=parts["A"],
    )


def validate_metrics(m: CVSSMetrics) -> None:
    """Raise ValueError if any metric has an invalid value."""
    checks = [
        ("AV", m.AV, AV_WEIGHTS),
        ("AC", m.AC, AC_WEIGHTS),
        ("PR", m.PR, PR_UNCHANGED),
        ("UI", m.UI, UI_WEIGHTS),
        ("C",  m.C,  CIA_WEIGHTS),
        ("I",  m.I,  CIA_WEIGHTS),
        ("A",  m.A,  CIA_WEIGHTS),
    ]
    for name, value, valid_dict in checks:
        if value not in valid_dict:
            raise ValueError(f"Invalid {name} value: '{value}'. Valid: {list(valid_dict.keys())}")
    if m.S not in ("U", "C"):
        raise ValueError(f"Invalid S value: '{m.S}'. Valid: U, C")


def calculate(m: CVSSMetrics) -> CVSSResult:
    """
    Calculate CVSS v3.1 base score using the official formula.
    Reference: FIRST CVSS v3.1 Specification, Section 7.1
    """
    validate_metrics(m)

    # 1. Impact Sub-Score (ISS)
    iss = 1.0 - ((1.0 - CIA_WEIGHTS[m.C]) * (1.0 - CIA_WEIGHTS[m.I]) * (1.0 - CIA_WEIGHTS[m.A]))

    # 2. Impact score (scope-dependent)
    scope_changed = (m.S == "C")
    if not scope_changed:
        impact = 6.42 * iss
    else:
        impact = 7.52 * (iss - 0.029) - 3.25 * ((iss - 0.02) ** 15)

    # 3. Exploitability score
    pr_weights = PR_UNCHANGED if not scope_changed else PR_CHANGED
    exploitability = 8.22 * AV_WEIGHTS[m.AV] * AC_WEIGHTS[m.AC] * pr_weights[m.PR] * UI_WEIGHTS[m.UI]

    # 4. Base Score
    if impact <= 0:
        base_score = 0.0
    elif not scope_changed:
        base_score = roundup_cvss(min(impact + exploitability, 10.0))
    else:
        base_score = roundup_cvss(min(1.08 * (impact + exploitability), 10.0))

    severity = severity_label(base_score)

    # 5. USAP intent classification
    if severity in ("Critical", "High"):
        usap_intent = "mutating"
        usap_category = "remediation_action"
    elif severity == "Medium":
        usap_intent = "read_only"
        usap_category = None
    else:
        usap_intent = "read_only"
        usap_category = None

    # 6. Build attack narrative
    av_desc = METRIC_DESCRIPTIONS["AV"][m.AV]
    ac_desc = METRIC_DESCRIPTIONS["AC"][m.AC].lower() + " complexity"
    pr_desc = METRIC_DESCRIPTIONS["PR"][m.PR].lower() + " privileges"
    ui_desc = ("no user interaction" if m.UI == "N" else "requires user interaction")
    scope_desc = "scope changed (can affect other components)" if scope_changed else "scope unchanged"
    cia_desc = (
        f"Confidentiality: {METRIC_DESCRIPTIONS['C'][m.C]}, "
        f"Integrity: {METRIC_DESCRIPTIONS['I'][m.I]}, "
        f"Availability: {METRIC_DESCRIPTIONS['A'][m.A]}"
    )
    narrative = (
        f"{severity} ({base_score}/10.0). "
        f"Attack vector: {av_desc}, {ac_desc}, {pr_desc}, {ui_desc}. "
        f"{scope_desc.capitalize()}. "
        f"Impact — {cia_desc}."
    )

    # 7. NVD calculator link
    vec_str = m.vector_string()
    nvd_url = f"https://nvd.nist.gov/vuln-metrics/cvss/v3-calculator?vector={vec_str}&version=3.1"

    return CVSSResult(
        vector_string=vec_str,
        base_score=base_score,
        severity=severity,
        iss=round(iss, 4),
        impact_score=round(impact, 4),
        exploitability_score=round(exploitability, 4),
        scope_changed=scope_changed,
        metrics=m,
        usap_intent_type=usap_intent,
        usap_mutating_category=usap_category,
        cvss_url=nvd_url,
        attack_narrative=narrative,
    )


def score_from_vector(vector_string: str) -> CVSSResult:
    return calculate(parse_vector(vector_string))


def score_from_severity(severity_name: str) -> CVSSResult:
    vec = REPRESENTATIVE_VECTORS.get(severity_name.lower())
    if not vec:
        raise ValueError(f"Unknown severity: {severity_name}. Valid: critical, high, medium, low")
    return calculate(parse_vector(vec))


# ── Output formatting ─────────────────────────────────────────────────────────

_COLORS = {
    "Critical": "\033[91m",
    "High":     "\033[33m",
    "Medium":   "\033[36m",
    "Low":      "\033[37m",
    "None":     "\033[32m",
}
_RESET = "\033[0m"


def print_result(r: CVSSResult) -> None:
    color = _COLORS.get(r.severity, "")
    print(f"\nUSAP CVSS v3.1 Score")
    print(f"Vector     : {r.vector_string}")
    print(f"Base Score : {color}{r.base_score:.1f} — {r.severity}{_RESET}")
    print(f"ISS        : {r.iss:.4f}  Impact: {r.impact_score:.4f}  Exploitability: {r.exploitability_score:.4f}")
    print(f"USAP Intent: {r.usap_intent_type}"
          + (f"  Category: {r.usap_mutating_category}" if r.usap_mutating_category else ""))
    print(f"\nNarrative  : {r.attack_narrative}")
    print(f"NVD Calc   : {r.cvss_url}")
    print()


def result_to_dict(r: CVSSResult) -> dict:
    return {
        "vector_string": r.vector_string,
        "base_score": r.base_score,
        "severity": r.severity,
        "iss": r.iss,
        "impact_score": r.impact_score,
        "exploitability_score": r.exploitability_score,
        "scope_changed": r.scope_changed,
        "usap_intent_type": r.usap_intent_type,
        "usap_mutating_category": r.usap_mutating_category,
        "attack_narrative": r.attack_narrative,
        "cvss_url": r.cvss_url,
        "metrics": {
            "AV": r.metrics.AV, "AC": r.metrics.AC,
            "PR": r.metrics.PR, "UI": r.metrics.UI,
            "S":  r.metrics.S,
            "C":  r.metrics.C, "I":  r.metrics.I, "A":  r.metrics.A,
        },
    }


# ── Interactive mode ──────────────────────────────────────────────────────────

METRIC_PROMPTS = [
    ("AV", "Attack Vector",        {"N": "Network", "A": "Adjacent", "L": "Local", "P": "Physical"}),
    ("AC", "Attack Complexity",    {"L": "Low", "H": "High"}),
    ("PR", "Privileges Required",  {"N": "None", "L": "Low", "H": "High"}),
    ("UI", "User Interaction",     {"N": "None", "R": "Required"}),
    ("S",  "Scope",                {"U": "Unchanged", "C": "Changed"}),
    ("C",  "Confidentiality",      {"N": "None", "L": "Low", "H": "High"}),
    ("I",  "Integrity",            {"N": "None", "L": "Low", "H": "High"}),
    ("A",  "Availability",         {"N": "None", "L": "Low", "H": "High"}),
]


def interactive_mode() -> CVSSResult:
    print("\nUSAP CVSS v3.1 Interactive Scorer")
    print("Enter metric values when prompted (press Enter to accept default).\n")
    values: Dict[str, str] = {}
    for key, label, options in METRIC_PROMPTS:
        opts_str = "  ".join(f"{k}={v}" for k, v in options.items())
        while True:
            raw = input(f"  {label} [{opts_str}]: ").strip().upper()
            if raw in options:
                values[key] = raw
                break
            print(f"    Invalid — choose one of: {', '.join(options.keys())}")

    m = CVSSMetrics(**values)
    result = calculate(m)
    print()
    print_result(result)
    return result


# ── CLI entry point ───────────────────────────────────────────────────────────

def main() -> int:
    parser = argparse.ArgumentParser(
        description="USAP CVSS v3.1 Base Score Calculator",
        epilog="Exit codes: 0=None/Low, 1=Medium, 2=High, 3=Critical",
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--vector", "-v", metavar="VECTOR", help="CVSS v3.1 vector string")
    group.add_argument(
        "--severity", "-s",
        choices=["critical", "high", "medium", "low"],
        help="Use representative vector for a named severity",
    )
    group.add_argument(
        "--bulk", "-b",
        metavar="FILE",
        help="JSON file with list of vector strings [{vector: ...}] or plain list",
    )
    group.add_argument("--interactive", "-i", action="store_true", help="Prompt for each metric interactively")
    parser.add_argument("--json", action="store_true", help="Output results as JSON")
    parser.add_argument("--output", "-o", metavar="FILE", help="Write JSON output to file")
    args = parser.parse_args()

    try:
        if args.interactive:
            result = interactive_mode()
            if args.json:
                print(json.dumps(result_to_dict(result), indent=2))
            if result.base_score >= 9.0:
                return 3
            if result.base_score >= 7.0:
                return 2
            if result.base_score >= 4.0:
                return 1
            return 0

        if args.bulk:
            raw = json.loads(Path(args.bulk).read_text())
            if isinstance(raw, list):
                vectors = [v if isinstance(v, str) else v.get("vector", v.get("vector_string", "")) for v in raw]
            else:
                vectors = raw.get("vectors", [])

            results = [score_from_vector(v) for v in vectors if v]
            max_score = max((r.base_score for r in results), default=0.0)

            if args.json:
                output = json.dumps([result_to_dict(r) for r in results], indent=2)
                if args.output:
                    Path(args.output).write_text(output, encoding="utf-8")
                    print(f"Results written to {args.output}")
                else:
                    print(output)
            else:
                for r in results:
                    color = _COLORS.get(r.severity, "")
                    print(f"{r.base_score:4.1f}  {color}{r.severity:8s}{_RESET}  {r.vector_string}")

            if max_score >= 9.0:
                return 3
            if max_score >= 7.0:
                return 2
            if max_score >= 4.0:
                return 1
            return 0

        # Single vector or severity
        if args.vector:
            result = score_from_vector(args.vector)
        else:
            result = score_from_severity(args.severity)

        if args.json:
            output = json.dumps(result_to_dict(result), indent=2)
            if args.output:
                Path(args.output).write_text(output, encoding="utf-8")
                print(f"Results written to {args.output}")
            else:
                print(output)
        else:
            print_result(result)

        if result.base_score >= 9.0:
            return 3
        if result.base_score >= 7.0:
            return 2
        if result.base_score >= 4.0:
            return 1
        return 0

    except (ValueError, KeyError, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
