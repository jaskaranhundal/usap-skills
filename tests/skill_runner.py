#!/usr/bin/env python3
"""
skill_runner.py — USAP LLM Test Harness (Qwen3 / Ollama)

Loads a SKILL.md system prompt, sends an input fixture to Qwen3 via Ollama,
and validates the response against the 11-field USAP output contract.

Usage:
    python tests/skill_runner.py --skill secrets-exposure --domain detection [options]

Options:
    --skill <slug>           Skill slug to test (required)
    --domain <domain>        Domain directory (required)
    --model <model>          Ollama model (default: qwen3:latest)
    --ollama-url <url>       Ollama base URL (default: http://localhost:11434)
    --input <path>           Input fixture JSON path (default: <domain>/<slug>/expected_outputs/sample_output.json)
    --pre-analysis           Run scripts/pre_analysis.py before LLM call
    --validate-only          Validate input JSON against output contract, skip LLM
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


# ── ANSI colour helpers ───────────────────────────────────────────────────────

RESET  = "\033[0m"
GREEN  = "\033[92m"
RED    = "\033[91m"
YELLOW = "\033[93m"
CYAN   = "\033[96m"
BOLD   = "\033[1m"


def green(s: str) -> str:  return f"{GREEN}{s}{RESET}"
def red(s: str) -> str:    return f"{RED}{s}{RESET}"
def yellow(s: str) -> str: return f"{YELLOW}{s}{RESET}"
def cyan(s: str) -> str:   return f"{CYAN}{s}{RESET}"
def bold(s: str) -> str:   return f"{BOLD}{s}{RESET}"


# ── Data types ────────────────────────────────────────────────────────────────

@dataclass
class FieldResult:
    field: str
    status: str          # "PASS" | "FAIL" | "WARN"
    value: Any
    message: str


# ── SKILL.md body extraction ──────────────────────────────────────────────────

def extract_skill_body(skill_path: Path) -> str:
    """
    Strip YAML frontmatter and return the body of the SKILL.md.

    Strategy: find the opening `---` on line 1, find the closing `---` that
    ends the frontmatter block, return everything after it.  Any `---`
    horizontal-rule dividers in the body are left intact.
    """
    text = skill_path.read_text(encoding="utf-8")
    lines = text.splitlines(keepends=True)

    # Must start with a frontmatter fence
    if not lines or lines[0].strip() != "---":
        return text  # no frontmatter — return as-is

    # Scan for the closing fence (second `---`)
    close_idx: Optional[int] = None
    for i, line in enumerate(lines[1:], start=1):
        if line.strip() == "---":
            close_idx = i
            break

    if close_idx is None:
        return text  # malformed — return as-is

    body = "".join(lines[close_idx + 1:]).lstrip("\n")
    return body


# ── Pre-analysis subprocess ───────────────────────────────────────────────────

def run_pre_analysis(script_path: Path, input_json: Dict[str, Any]) -> Tuple[Dict[str, Any], int]:
    """
    Run <script_path> as a subprocess.
    Passes input_json via stdin (UTF-8).
    Returns (parsed_output_dict, exit_code).
    If the script is not found or crashes, returns ({}, -1).
    """
    if not script_path.exists():
        print(yellow(f"  [WARN] pre_analysis.py not found at {script_path} — skipping"))
        return {}, -1

    input_str = json.dumps(input_json)
    result = subprocess.run(
        [sys.executable, str(script_path)],
        input=input_str,
        capture_output=True,
        text=True,
    )

    exit_code = result.returncode
    stdout = result.stdout.strip()
    stderr = result.stderr.strip()

    if stderr:
        print(yellow(f"  [pre_analysis stderr] {stderr[:400]}"))

    parsed: Dict[str, Any] = {}
    if stdout:
        try:
            parsed = json.loads(stdout)
        except json.JSONDecodeError:
            print(yellow(f"  [WARN] pre_analysis stdout is not valid JSON: {stdout[:200]}"))

    label = {0: "clean", 1: "high findings", 2: "critical findings"}.get(exit_code, f"exit {exit_code}")
    print(cyan(f"  [pre_analysis] exit={exit_code} ({label})"))
    return parsed, exit_code


# ── Message building ──────────────────────────────────────────────────────────

def build_messages(
    system_prompt: str,
    input_json: Dict[str, Any],
    pre_analysis: Optional[Dict[str, Any]] = None,
) -> List[Dict[str, str]]:
    """
    Build the Ollama chat messages list.

    The system message is the full SKILL.md body.
    The user message contains the input JSON and, optionally, pre-analysis output.
    A final explicit instruction is appended to ensure the LLM outputs a single
    valid JSON object — critical for reliable parsing.
    """
    user_parts = [
        "Analyze the following security event and return your findings.",
        "",
        "Input JSON:",
        "```json",
        json.dumps(input_json, indent=2),
        "```",
    ]

    if pre_analysis:
        user_parts += [
            "",
            "Pre-analysis findings (deterministic algorithmic scan — treat as ground truth):",
            "```json",
            json.dumps(pre_analysis, indent=2),
            "```",
        ]

    user_parts += [
        "",
        "IMPORTANT: Respond with a single valid JSON object only. "
        "Do not include any explanation, prose, or markdown outside the JSON object. "
        "The JSON must conform to the USAP output contract with all required fields: "
        "agent_slug, intent_type, action, rationale, confidence, severity, "
        "key_findings, evidence_references, next_agents, human_approval_required, timestamp_utc.",
    ]

    return [
        {"role": "system",  "content": system_prompt},
        {"role": "user",    "content": "\n".join(user_parts)},
    ]


# ── Ollama API call ───────────────────────────────────────────────────────────

def call_ollama(
    messages: List[Dict[str, str]],
    model: str,
    ollama_url: str,
) -> Tuple[str, float]:
    """
    POST to /api/chat.
    Returns (response_content_str, elapsed_seconds).
    Raises urllib.error.URLError if Ollama is unreachable.
    """
    url = ollama_url.rstrip("/") + "/api/chat"
    payload = {
        "model": model,
        "messages": messages,
        "stream": False,
        "options": {"temperature": 0.1},
    }
    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    t0 = time.monotonic()
    with urllib.request.urlopen(req, timeout=300) as resp:
        raw = resp.read().decode("utf-8")
    elapsed = time.monotonic() - t0

    data = json.loads(raw)
    content: str = data.get("message", {}).get("content", "")
    return content, elapsed


# ── JSON parsing (3-pass) ─────────────────────────────────────────────────────

def parse_json_from_response(raw: str) -> Optional[Dict[str, Any]]:
    """
    3-pass JSON extraction:
      1. Direct json.loads on the whole string.
      2. Extract content between ```json ... ``` fences.
      3. Extract from first `{` to last `}`.
    Returns parsed dict or None on failure.
    """
    # Pass 1 — direct
    stripped = raw.strip()
    try:
        obj = json.loads(stripped)
        if isinstance(obj, dict):
            return obj
    except json.JSONDecodeError:
        pass

    # Pass 2 — JSON fence
    import re
    fence_match = re.search(r"```json\s*(\{.*?\})\s*```", stripped, re.DOTALL)
    if fence_match:
        try:
            obj = json.loads(fence_match.group(1))
            if isinstance(obj, dict):
                return obj
        except json.JSONDecodeError:
            pass

    # Pass 3 — brace extraction
    start = stripped.find("{")
    end   = stripped.rfind("}")
    if start != -1 and end != -1 and end > start:
        try:
            obj = json.loads(stripped[start:end + 1])
            if isinstance(obj, dict):
                return obj
        except json.JSONDecodeError:
            pass

    return None


# ── Output contract validation ────────────────────────────────────────────────

VALID_INTENT_TYPES = {"detect", "respond", "analyze", "advise", "escalate", "report", "block"}
VALID_SEVERITIES   = {"critical", "high", "medium", "low", "informational"}
HIGH_SEVERITY_SET  = {"critical", "high"}


def validate_output_contract(data: Dict[str, Any], slug: str) -> List[FieldResult]:
    """
    Validate all 11 required output contract fields.
    Returns a list of FieldResult entries (one per field).
    """
    results: List[FieldResult] = []

    def check(field: str, status: str, value: Any, message: str) -> None:
        results.append(FieldResult(field=field, status=status, value=value, message=message))

    # 1. agent_slug
    v = data.get("agent_slug")
    if isinstance(v, str) and v.strip():
        status = "PASS" if v == slug else "WARN"
        msg = "OK" if v == slug else f"expected '{slug}', got '{v}'"
        check("agent_slug", status, v, msg)
    else:
        check("agent_slug", "FAIL", v, "missing or empty string")

    # 2. intent_type
    v = data.get("intent_type")
    if isinstance(v, str) and v in VALID_INTENT_TYPES:
        check("intent_type", "PASS", v, f"valid: {v}")
    else:
        check("intent_type", "FAIL", v, f"must be one of {sorted(VALID_INTENT_TYPES)}, got {v!r}")

    # 3. action
    v = data.get("action")
    if isinstance(v, str) and v.strip():
        check("action", "PASS", v[:80] + ("…" if len(v) > 80 else ""), "non-empty string")
    else:
        check("action", "FAIL", v, "missing or empty string")

    # 4. rationale
    v = data.get("rationale")
    if isinstance(v, str) and v.strip():
        check("rationale", "PASS", v[:80] + ("…" if len(v) > 80 else ""), "non-empty string")
    else:
        check("rationale", "FAIL", v, "missing or empty string")

    # 5. confidence
    v = data.get("confidence")
    if isinstance(v, (int, float)) and 0.0 <= float(v) <= 1.0:
        status = "PASS" if float(v) >= 0.5 else "WARN"
        msg = "OK" if float(v) >= 0.5 else f"below 0.5 — inconclusive ({v})"
        check("confidence", status, v, msg)
    else:
        check("confidence", "FAIL", v, f"must be float 0.0–1.0, got {v!r}")

    # 6. severity
    v = data.get("severity")
    if isinstance(v, str) and v in VALID_SEVERITIES:
        check("severity", "PASS", v, f"valid: {v}")
    else:
        check("severity", "FAIL", v, f"must be one of {sorted(VALID_SEVERITIES)}, got {v!r}")

    # 7. key_findings
    v = data.get("key_findings")
    if isinstance(v, list) and len(v) >= 1:
        check("key_findings", "PASS", f"[{len(v)} items]", f"{len(v)} finding(s)")
    else:
        check("key_findings", "FAIL", v, "must be array with at least 1 entry")

    # 8. evidence_references — always present; non-empty if severity critical/high
    v = data.get("evidence_references")
    sev = data.get("severity", "")
    if not isinstance(v, list):
        check("evidence_references", "FAIL", v, "must be an array")
    elif sev in HIGH_SEVERITY_SET and len(v) == 0:
        check("evidence_references", "FAIL", v, f"severity is '{sev}' — evidence_references must be non-empty")
    else:
        check("evidence_references", "PASS", f"[{len(v)} items]", f"{len(v)} reference(s)")

    # 9. next_agents
    v = data.get("next_agents")
    if isinstance(v, list):
        check("next_agents", "PASS", f"[{len(v)} items]", "array present (can be empty)")
    else:
        check("next_agents", "FAIL", v, "must be an array (can be empty)")

    # 10. human_approval_required
    v = data.get("human_approval_required")
    if isinstance(v, bool):
        check("human_approval_required", "PASS", v, "boolean present")
    else:
        check("human_approval_required", "FAIL", v, f"must be boolean, got {type(v).__name__} {v!r}")

    # 11. timestamp_utc
    v = data.get("timestamp_utc")
    if isinstance(v, str):
        try:
            # fromisoformat requires Z → +00:00 in Python < 3.11
            ts_str = v.replace("Z", "+00:00")
            datetime.fromisoformat(ts_str)
            check("timestamp_utc", "PASS", v, "parseable ISO 8601")
        except ValueError:
            check("timestamp_utc", "FAIL", v, "not parseable as ISO 8601")
    else:
        check("timestamp_utc", "FAIL", v, "missing or not a string")

    return results


# ── Report rendering ──────────────────────────────────────────────────────────

def render_report(slug: str, domain: str, results: List[FieldResult], elapsed: Optional[float]) -> bool:
    """
    Print a coloured validation report.
    Returns True if all fields PASS (WARN is acceptable).
    """
    passes = sum(1 for r in results if r.status == "PASS")
    warns  = sum(1 for r in results if r.status == "WARN")
    fails  = sum(1 for r in results if r.status == "FAIL")
    total  = len(results)

    print()
    print(cyan(bold(f"=== {domain}/{slug} — Output Contract Validation ===")))
    if elapsed is not None:
        print(f"  LLM response time: {elapsed:.1f}s")
    print()

    for r in results:
        if r.status == "PASS":
            icon = green("[PASS]")
        elif r.status == "WARN":
            icon = yellow("[WARN]")
        else:
            icon = red("[FAIL]")
        print(f"  {icon}  {r.field:<28}  {r.message}")

    print()
    summary = f"  {passes}/{total} PASS  |  {warns} WARN  |  {fails} FAIL"
    overall_pass = fails == 0
    if overall_pass:
        print(green(bold(f"  RESULT: PASS")) + f"  {summary}")
    else:
        print(red(bold(f"  RESULT: FAIL")) + f"  {summary}")
    print()
    return overall_pass


# ── Default input fixture path ────────────────────────────────────────────────

def default_input_path(domain: str, slug: str) -> Path:
    root = Path(__file__).parent.parent
    return root / domain / slug / "expected_outputs" / "sample_output.json"


def fixture_path(domain: str, slug: str) -> Path:
    root = Path(__file__).parent
    fixture_name = f"{slug}-input.json"
    return root / "fixtures" / fixture_name


# ── Main ──────────────────────────────────────────────────────────────────────

def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="USAP LLM Test Harness — Qwen3 / Ollama")
    p.add_argument("--skill",         required=True,  help="Skill slug (e.g. secrets-exposure)")
    p.add_argument("--domain",        required=True,  help="Domain directory (e.g. detection)")
    p.add_argument("--model",         default="qwen3:latest", help="Ollama model tag")
    p.add_argument("--ollama-url",    default="http://localhost:11434", help="Ollama base URL")
    p.add_argument("--input",         default=None,   help="Input fixture JSON path override")
    p.add_argument("--pre-analysis",  action="store_true", help="Run pre_analysis.py before LLM call")
    p.add_argument("--validate-only", action="store_true", help="Validate input file, skip LLM call")
    return p.parse_args()


def main() -> int:
    args = parse_args()
    slug   = args.skill
    domain = args.domain
    root   = Path(__file__).parent.parent

    # ── Locate SKILL.md ───────────────────────────────────────────────────────
    skill_md_path = root / domain / slug / "SKILL.md"
    if not skill_md_path.exists():
        print(red(f"[ERROR] SKILL.md not found: {skill_md_path}"))
        return 1

    # ── Locate input fixture ──────────────────────────────────────────────────
    if args.input:
        input_path = Path(args.input)
    else:
        # Prefer tests/fixtures/<slug>-input.json, fall back to expected_outputs
        fp = fixture_path(domain, slug)
        input_path = fp if fp.exists() else default_input_path(domain, slug)

    if not input_path.exists():
        print(red(f"[ERROR] Input fixture not found: {input_path}"))
        return 1

    print(cyan(bold(f"\n{'='*60}")))
    print(cyan(bold(f"  USAP Test Harness — {domain}/{slug}")))
    print(cyan(bold(f"{'='*60}")))
    print(f"  SKILL.md : {skill_md_path.relative_to(root)}")
    print(f"  Input    : {input_path}")
    print(f"  Model    : {args.model}")

    # ── Load input JSON ───────────────────────────────────────────────────────
    try:
        input_json: Dict[str, Any] = json.loads(input_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as e:
        print(red(f"[ERROR] Could not load input fixture: {e}"))
        return 1

    # ── validate-only mode ────────────────────────────────────────────────────
    if args.validate_only:
        print(yellow("\n  [validate-only] Validating input file against output contract..."))
        results = validate_output_contract(input_json, slug)
        overall = render_report(slug, domain, results, elapsed=None)
        return 0 if overall else 1

    # ── Pre-analysis ──────────────────────────────────────────────────────────
    pre_analysis_data: Optional[Dict[str, Any]] = None
    if args.pre_analysis:
        pre_script = root / domain / slug / "scripts" / "pre_analysis.py"
        print(cyan(f"\n  [pre-analysis] Running {pre_script.relative_to(root)}"))
        pre_analysis_data, exit_code = run_pre_analysis(pre_script, input_json)

    # ── Extract SKILL.md body ─────────────────────────────────────────────────
    print(cyan(f"\n  [skill] Loading SKILL.md body..."))
    system_prompt = extract_skill_body(skill_md_path)
    body_lines = system_prompt.count("\n")
    print(f"  Body length: {len(system_prompt)} chars, ~{body_lines} lines")

    # ── Build messages ────────────────────────────────────────────────────────
    messages = build_messages(system_prompt, input_json, pre_analysis_data)

    # ── Call Ollama ───────────────────────────────────────────────────────────
    print(cyan(f"\n  [ollama] Calling {args.model} at {args.ollama_url}..."))
    try:
        raw_response, elapsed = call_ollama(messages, args.model, args.ollama_url)
    except urllib.error.URLError as e:
        print(red(f"\n[ERROR] Cannot reach Ollama at {args.ollama_url}: {e}"))
        print(yellow("  Is Ollama running?  Try: ollama serve"))
        print(yellow(f"  Model available?   Try: ollama pull {args.model}"))
        return 1

    print(f"  Response received in {elapsed:.1f}s ({len(raw_response)} chars)")

    # ── Parse response ────────────────────────────────────────────────────────
    print(cyan(f"\n  [parse] Extracting JSON from response..."))
    parsed = parse_json_from_response(raw_response)
    if parsed is None:
        print(red("[FAIL] Could not extract valid JSON from LLM response."))
        print(yellow("  Raw response (first 600 chars):"))
        print(f"  {raw_response[:600]}")
        return 1
    print(f"  JSON extracted successfully ({len(parsed)} top-level keys)")

    # ── Validate output contract ──────────────────────────────────────────────
    print(cyan(f"\n  [validate] Checking output contract..."))
    results = validate_output_contract(parsed, slug)
    overall = render_report(slug, domain, results, elapsed=elapsed)

    return 0 if overall else 1


if __name__ == "__main__":
    raise SystemExit(main())
