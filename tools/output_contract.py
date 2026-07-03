#!/usr/bin/env python3
"""Validate USAP skill JSON output against the 11-field output contract.

Implements the contract defined in ``standards/output-contract.md``. Exposes:

  validate_payload(payload: dict) -> list[str]
      Returns a list of human-readable violation strings. Empty list means
      the payload is contract-compliant. Stable, deterministic ordering so
      CI snapshots are diff-friendly.

CLI usage::

    python3 tools/output_contract.py path/to/payload.json
    cat payload.json | python3 tools/output_contract.py -
    python3 tools/output_contract.py --all-samples   # walk every
                                                     # expected_outputs/sample_output.json

Exit codes:
  0 = clean
  1 = at least one payload has violations
  2 = malformed input (not JSON)
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, List

REPO_ROOT = Path(__file__).resolve().parent.parent

REQUIRED_FIELDS = (
    "agent_slug",
    "intent_type",
    "action",
    "rationale",
    "confidence",
    "severity",
    "key_findings",
    "evidence_references",
    "next_agents",
    "human_approval_required",
    "timestamp_utc",
)

INTENT_TYPES = {
    "detect",
    "respond",
    "analyze",
    "advise",
    "escalate",
    "report",
    "block",
}

SEVERITIES = ("critical", "high", "medium", "low", "informational")
HIGH_OR_ABOVE = {"critical", "high"}

# ISO 8601 in UTC. Accepts either "Z" or "+00:00" terminator. Matches the
# date-time patterns USAP samples actually use; rejects bare date-only.
ISO_UTC_RE = re.compile(
    r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{1,6})?(?:Z|\+00:?00)$"
)

KEBAB_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")

# ─── Evidence-gate source forms (hardest-line gate) ─────────────────
# Every verdict must cite >=1 evidence_references entry whose `source`
# matches one of these resolvable forms. See standards/output-contract.md.
#   local://<repo-relative-path>   — must exist in the repo
#   https://<url> / s3://<bucket>  — structural check only (no fetch)
#   mcp:<group>:<tool>:<call_id>   — <group>.<tool> must be a declared
#                                    logical name in the MCP registry
_LOCAL_SRC_RE = re.compile(r"^local://(.+)$")
_HTTPS_SRC_RE = re.compile(r"^https://\S+$", re.IGNORECASE)
_S3_SRC_RE = re.compile(r"^s3://\S+$", re.IGNORECASE)
_MCP_SRC_RE = re.compile(r"^mcp:[a-z0-9_.-]+:[a-z0-9_.-]+:\S+$", re.IGNORECASE)

_REGISTRY_CACHE: Any = None
_REGISTRY_LOAD_FAILED = False


def _default_registry() -> Any:
    """Lazily load + cache the MCP registry for logical-name checks.

    Never raises: if the registry can't be loaded (odd cwd, missing file),
    returns None and the gate falls back to structural mcp: validation only.
    """
    global _REGISTRY_CACHE, _REGISTRY_LOAD_FAILED
    if _REGISTRY_CACHE is not None or _REGISTRY_LOAD_FAILED:
        return _REGISTRY_CACHE
    try:
        sys.path.insert(0, str(REPO_ROOT / "tools"))
        from mcp_registry import load_registry  # noqa: E402
        _REGISTRY_CACHE = load_registry()
    except Exception:
        _REGISTRY_LOAD_FAILED = True
        _REGISTRY_CACHE = None
    return _REGISTRY_CACHE


def _source_is_resolvable(source: Any, registry: Any, repo_root: Any) -> tuple[bool, str]:
    """Return (ok, reason). ``reason`` is meaningful only when not ok."""
    if not isinstance(source, str) or not source.strip():
        return False, "source missing or not a string"
    s = source.strip()

    m = _LOCAL_SRC_RE.match(s)
    if m:
        rel = m.group(1).lstrip("/")
        if repo_root is None:
            return True, ""  # cannot verify path; accept structurally
        if (repo_root / rel).exists():
            return True, ""
        return False, f"local:// path not found in repo: {rel}"

    if _HTTPS_SRC_RE.match(s) or _S3_SRC_RE.match(s):
        return True, ""

    if s.lower().startswith("mcp:"):
        if not _MCP_SRC_RE.match(s):
            return False, f"mcp: source malformed (want mcp:<group>:<tool>:<call_id>): {s}"
        parts = s.split(":")
        logical = f"{parts[1]}.{parts[2]}"
        reg = registry if registry is not None else _default_registry()
        if reg is not None:
            from mcp_registry import logical_names as _ln  # noqa: E402
            if logical not in _ln(reg):
                return False, (
                    f"mcp: logical name '{logical}' is not declared in the "
                    "registry logical_names block"
                )
        return True, ""

    return False, (
        f"source '{s}' is not a resolvable URI "
        "(want mcp:… / https://… / s3://… / local://…)"
    )


def validate_evidence_resolvable(
    payload: Any, registry: Any = None, repo_root: Any = None
) -> List[str]:
    """Hardest-line evidence gate.

    Every verdict — at ANY severity, including ``informational`` — must carry
    at least one ``evidence_references`` entry whose ``source`` resolves to a
    real artifact. No verdict may rest on an unverifiable model assertion.
    Returns violation strings (empty = passes the gate).
    """
    if not isinstance(payload, dict):
        return ["payload must be a JSON object"]
    if repo_root is None:
        repo_root = REPO_ROOT
    er = payload.get("evidence_references")
    if not isinstance(er, list) or len(er) == 0:
        return [
            "evidence gate: evidence_references must contain at least one entry "
            "with a resolvable source (mcp:/https:/s3:/local://) — no verdict "
            "may rest on unverifiable assertion"
        ]
    resolvable = 0
    reasons: List[str] = []
    for i, item in enumerate(er):
        if not isinstance(item, dict):
            reasons.append(f"[{i}] is not an object")
            continue
        ok, why = _source_is_resolvable(item.get("source"), registry, repo_root)
        if ok:
            resolvable += 1
        else:
            reasons.append(f"[{i}] {why}")
    if resolvable == 0:
        return [
            "evidence gate: no resolvable evidence source found — every verdict "
            "must cite >=1 source of form mcp:/https:/s3:/local://. Offending "
            "entries: " + "; ".join(reasons[:6])
        ]
    return []


# ─── Reproducible-scoring checks ────────────────────────────────────
# A payload that claims a cvss_score must match the CVSS vector it cites.
# Narrowly scoped: fires only when a numeric cvss_score AND a vector are
# both present, so it catches fabricated numbers without touching payloads
# that carry neither.
_CVSS_VECTOR_RE = re.compile(r"CVSS:3\.[01]/[A-Z]{1,2}:[A-Z](?:/[A-Z]{1,2}:[A-Z])+")


def _find_cvss_vector(payload: dict) -> str | None:
    v = payload.get("cvss_vector")
    if isinstance(v, str):
        m = _CVSS_VECTOR_RE.search(v)
        if m:
            return m.group(0)
    for e in payload.get("evidence_references") or []:
        if isinstance(e, dict):
            m = _CVSS_VECTOR_RE.search(json.dumps(e))
            if m:
                return m.group(0)
    m = _CVSS_VECTOR_RE.search(str(payload.get("rationale", "")))
    return m.group(0) if m else None


def validate_scores_reproducible(payload: Any) -> List[str]:
    """FAIL when a claimed cvss_score disagrees with the vector it cites.

    Only fires when the payload carries BOTH a numeric ``cvss_score`` and a
    resolvable CVSS vector; otherwise returns [] (nothing to reproduce).
    """
    if not isinstance(payload, dict):
        return []
    cs = payload.get("cvss_score")
    if isinstance(cs, bool) or not isinstance(cs, (int, float)):
        return []
    vector = _find_cvss_vector(payload)
    if not vector:
        return []
    try:
        sys.path.insert(0, str(REPO_ROOT / "shared" / "scripts"))
        from cvss_scorer import score_from_vector  # noqa: E402
        computed = float(score_from_vector(vector).base_score)
    except Exception:
        return []  # scorer unavailable — don't block on an environment issue
    if abs(float(cs) - computed) > 0.1:
        return [
            f"cvss_score {cs} does not match its vector {vector} "
            f"(cvss_scorer computes {computed:.1f}) — scores must be reproducible, not narrated"
        ]
    return []


def _is_str(v: Any) -> bool:
    return isinstance(v, str)


def _is_list_of_str(v: Any) -> bool:
    return isinstance(v, list) and all(isinstance(x, str) for x in v)


def _is_list_of_obj(v: Any) -> bool:
    return isinstance(v, list) and all(isinstance(x, dict) for x in v)


def validate_payload(
    payload: Any,
    *,
    evidence_gate: bool = True,
    score_checks: bool = True,
    registry: Any = None,
    repo_root: Any = None,
) -> List[str]:
    """Return human-readable violations of the 11-field contract.

    The function never raises on bad input — malformed structures yield a
    descriptive violation string instead. Callers should treat a non-empty
    return as failure.

    ``evidence_gate`` (default True) additionally enforces the hardest-line
    evidence gate: every verdict must cite >=1 resolvable evidence source.
    Batch/corpus callers that only want structural conformance during an
    incremental rollout pass ``evidence_gate=False``.
    """
    if not isinstance(payload, dict):
        return [f"payload must be a JSON object, got {type(payload).__name__}"]

    violations: List[str] = []

    # 1. Required fields present.
    for field in REQUIRED_FIELDS:
        if field not in payload:
            violations.append(f"missing required field: {field}")

    # 2. agent_slug — non-empty kebab-case string.
    slug = payload.get("agent_slug")
    if "agent_slug" in payload:
        if not _is_str(slug) or not slug:
            violations.append("agent_slug must be a non-empty string")
        elif not KEBAB_RE.match(slug):
            violations.append(
                f"agent_slug '{slug}' must be kebab-case"
            )

    # 3. intent_type — enum.
    it = payload.get("intent_type")
    if "intent_type" in payload and it not in INTENT_TYPES:
        violations.append(
            f"intent_type '{it}' must be one of {sorted(INTENT_TYPES)}"
        )

    # 4. action and rationale — non-empty strings.
    for field in ("action", "rationale"):
        v = payload.get(field)
        if field in payload and (not _is_str(v) or not v.strip()):
            violations.append(f"{field} must be a non-empty string")

    # 5. confidence — float in [0.0, 1.0].
    if "confidence" in payload:
        c = payload["confidence"]
        if isinstance(c, bool) or not isinstance(c, (int, float)):
            violations.append("confidence must be a number")
        elif not (0.0 <= float(c) <= 1.0):
            violations.append(
                f"confidence {c} is outside [0.0, 1.0]"
            )

    # 6. severity — enum.
    sev = payload.get("severity")
    if "severity" in payload and sev not in SEVERITIES:
        violations.append(
            f"severity '{sev}' must be one of {list(SEVERITIES)}"
        )

    # 7. key_findings — array of strings, at least one.
    if "key_findings" in payload:
        kf = payload["key_findings"]
        if not _is_list_of_str(kf):
            violations.append("key_findings must be an array of strings")
        elif len(kf) == 0:
            violations.append("key_findings must contain at least one entry")

    # 8. evidence_references — array of objects; required >= high.
    if "evidence_references" in payload:
        er = payload["evidence_references"]
        if not _is_list_of_obj(er):
            violations.append("evidence_references must be an array of objects")
        elif sev in HIGH_OR_ABOVE and len(er) == 0:
            violations.append(
                f"evidence_references must contain at least one entry "
                f"when severity is '{sev}'"
            )

    # 9. next_agents — array of strings (empty allowed for terminal skills).
    if "next_agents" in payload and not _is_list_of_str(payload["next_agents"]):
        violations.append("next_agents must be an array of strings")

    # 10. human_approval_required — boolean.
    har = payload.get("human_approval_required")
    if "human_approval_required" in payload and not isinstance(har, bool):
        violations.append("human_approval_required must be a boolean")

    # 11. timestamp_utc — ISO 8601 UTC string.
    ts = payload.get("timestamp_utc")
    if "timestamp_utc" in payload:
        if not _is_str(ts) or not ISO_UTC_RE.match(ts):
            violations.append(
                f"timestamp_utc '{ts}' must be ISO 8601 UTC "
                "(e.g., 2026-06-20T10:30:00Z or 2026-06-20T10:30:00+00:00)"
            )

    # 12. Evidence gate (hardest line) — enforced at the contract boundary.
    if evidence_gate:
        violations.extend(
            validate_evidence_resolvable(payload, registry, repo_root)
        )

    # 13. Reproducible scoring — a claimed cvss_score must match its vector.
    #     Independent of the evidence gate: correctness, not rollout.
    if score_checks:
        violations.extend(validate_scores_reproducible(payload))

    return violations


def _load_json_from(path_or_dash: str) -> Any:
    if path_or_dash == "-":
        return json.load(sys.stdin)
    return json.loads(Path(path_or_dash).read_text(encoding="utf-8"))


def _sample_paths() -> List[Path]:
    """All ``expected_outputs/sample_output.json`` files in active domains."""
    domains = (
        REPO_ROOT / d
        for d in (
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
        )
    )
    samples: List[Path] = []
    for domain in domains:
        if not domain.is_dir():
            continue
        for skill in sorted(domain.iterdir()):
            sample = skill / "expected_outputs" / "sample_output.json"
            if sample.is_file():
                samples.append(sample)
    return samples


def _report(path: str, violations: List[str]) -> None:
    if violations:
        print(f"FAIL {path}")
        for v in violations:
            print(f"      x {v}")
    else:
        print(f"PASS {path}")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate JSON against the USAP 11-field output contract."
    )
    parser.add_argument(
        "path",
        nargs="?",
        help="Path to a JSON file. Use '-' to read from stdin.",
    )
    parser.add_argument(
        "--all-samples",
        action="store_true",
        help="Walk every active-domain skill's expected_outputs/sample_output.json.",
    )
    parser.add_argument(
        "--structural-only",
        action="store_true",
        help="Skip the hardest-line evidence gate; check 11-field structure only. "
             "Used by the corpus CI during the incremental evidence-gate rollout.",
    )
    args = parser.parse_args()
    gate = not args.structural_only

    if not args.path and not args.all_samples:
        parser.error("provide a JSON path (or '-') or use --all-samples")

    if args.all_samples:
        samples = _sample_paths()
        if not samples:
            print("error: no sample_output.json files found", file=sys.stderr)
            return 1
        passed = failed = 0
        for s in samples:
            try:
                payload = _load_json_from(str(s))
            except json.JSONDecodeError as exc:
                _report(str(s.relative_to(REPO_ROOT)), [f"invalid JSON: {exc}"])
                failed += 1
                continue
            v = validate_payload(payload, evidence_gate=gate)
            _report(str(s.relative_to(REPO_ROOT)), v)
            if v:
                failed += 1
            else:
                passed += 1
        print()
        print("=" * 60)
        print(f"Total: {passed + failed}  Passed: {passed}  Failed: {failed}")
        return 0 if failed == 0 else 1

    # Single-file mode.
    try:
        payload = _load_json_from(args.path)
    except FileNotFoundError:
        print(f"error: file not found: {args.path}", file=sys.stderr)
        return 2
    except json.JSONDecodeError as exc:
        print(f"error: invalid JSON: {exc}", file=sys.stderr)
        return 2

    violations = validate_payload(payload, evidence_gate=gate)
    _report(args.path, violations)
    return 0 if not violations else 1


if __name__ == "__main__":
    sys.exit(main())
