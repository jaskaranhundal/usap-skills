#!/usr/bin/env python3
"""USAP persona gate: router, hook handlers, and pass recorder.

The operator rule "every security-relevant decision routes through a USAP
persona pass" had no mechanism. This file is the mechanism. It is invoked
three ways:

  * As Claude Code hooks (see hooks.json next to this file):
      usap_gate.py prompt    UserPromptSubmit  - classify the prompt, inject the
                                                  persona instruction as context
      usap_gate.py pretool   PreToolUse        - block Edit/Write on gated paths
                                                  until a DR pass is recorded for
                                                  this session
      usap_gate.py stop      Stop              - report a session that wrote
                                                  gated paths with no pass
  * As a CLI:
      usap_gate.py classify "<prompt text>"
      usap_gate.py check-skill <slug> [--root DIR]
      usap_gate.py record --session-id ID --persona SLUG --pass DR
                          --residual-risk low|medium|high --summary "..."

Design and review: docs/design/2026-09-04-persona-gate-hooks-design.md and
docs/design/2026-09-04-persona-gate-hooks-dr.md (residual risk medium, nine
conditions; every condition is marked DR-n below where it is implemented).

Stdlib only. Never reads the network. Writes only under the audit directory
(USAP_AUDIT_DIR or ~/.usap/audit). Hook input arrives as JSON on stdin; no
prompt text is ever passed through a shell.
"""
from __future__ import annotations

import argparse
import hashlib
import hmac
import json
import os
import re
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

SELF = Path(__file__).resolve()
PLUGIN_ROOT = SELF.parent.parent            # plugins/usap
REPO_ROOT = PLUGIN_ROOT.parent.parent       # repo root when run from a checkout

ACTIVE_DOMAINS = [
    "appsec-devsecops", "cloud-infra", "detection", "governance",
    "identity-access", "pentest", "platform-ai", "red-team", "response",
    "risk-compliance", "system-security", "webapp-security",
]

GATED_WRITE_TOOLS = {"Edit", "Write", "MultiEdit", "NotebookEdit"}
PASS_EVENT = "persona_pass"
RESIDUAL_RISKS = ("low", "medium", "high")

# --------------------------------------------------------------------------
# Trigger table. Mirrors the operator rule (global CLAUDE.md section 11.0).
# Word-boundary matching only; the August pre-analysis fix showed substring
# matching produces false hits. Order is precedence: an active incident
# outranks everything else.
# --------------------------------------------------------------------------
TRIGGERS: List[Tuple[str, str, str, re.Pattern]] = [
    ("usap-incident-responder", "IR", "incident",
     re.compile(r"\b(incident|breach|compromised?|ransomware|intrusion|exfiltration)\b", re.I)),
    ("usap-red-teamer", "RT", "offensive",
     re.compile(r"\b(red[ -]team(?:ing)?|pentest(?:ing)?|penetration test(?:ing)?|attack path|adversary emulation)\b", re.I)),
    ("usap-ciso", "RG", "risk governance",
     re.compile(r"\b(residual risk|risk acceptance|risk register|iso ?27001|iso ?13485|board report)\b", re.I)),
    ("usap-devsecops", "PR", "pre-report",
     re.compile(r"\b(findings?)\b.{0,60}\b(ticket|issue|jira)\b|\b(ticket|issue|jira)\b.{0,60}\b(findings?)\b", re.I | re.S)),
    ("usap-devsecops", "PA", "post-assessment",
     re.compile(r"\b(audit results?|assessment results?|scan results?|sweep results?|pilot results?)\b", re.I)),
    ("usap-devsecops", "DR", "design review",
     re.compile(
         r"\b(security controls?|access control|guard(?:rail)?s?|gates?|gating|credentials?|secrets?|"
         r"api tokens?|access tokens?|oauth|pipelines?|ci/?cd|gitlab-ci|github actions|workflow files?|"
         r"runners?|iac|terraform|dockerfiles?|permissions?|firewall|harden(?:ing)?|hooks?|protections?|"
         r"branch protection|signing|sbom|rbac)\b", re.I)),
]

# --------------------------------------------------------------------------
# Gated paths (DR-3: narrow, with explicit exclusions so fixtures and docs
# never trip the block). Rules are (kind, value) so they read as a list.
# --------------------------------------------------------------------------
EXCLUDED_PARTS = {"tests", "fixtures", "expected_outputs", "node_modules", ".git"}
EXCLUDED_SUFFIXES = (".md", ".example")


def is_gated_path(raw: str, cwd: Optional[str] = None) -> bool:
    if not raw:
        return False
    p = Path(raw)
    if not p.is_absolute() and cwd:
        p = Path(cwd) / p
    parts = p.parts
    name = p.name
    lower = name.lower()
    if any(part in EXCLUDED_PARTS for part in parts):
        return False
    if lower.endswith(EXCLUDED_SUFFIXES):
        return False
    parent = p.parent.name
    grand = p.parent.parent.name if len(parts) > 2 else ""
    if parent == "workflows" and grand == ".github":
        return True
    if lower == ".gitlab-ci.yml" or lower.endswith(".gitlab-ci.yml"):
        return True
    if lower.endswith((".tf", ".tfvars")):
        return True
    if lower == "dockerfile" or lower.startswith("dockerfile."):
        return True
    if parent == ".claude" and (re.match(r"settings.*\.json$", lower) or name == "CLAUDE.md"):
        return True
    if lower == "hooks.json":
        return True
    if lower == ".env" or (lower.startswith(".env.") and not lower.endswith(".example")):
        return True
    if "credentials" in lower:
        return True
    if re.search(r"secrets.*\.ya?ml$", lower):
        return True
    if parent in ("registry", "runner") and lower.endswith((".yaml", ".yml")):
        return True
    return False


# --------------------------------------------------------------------------
# Audit log. Uses tools/mcp_audit.py when running from a checkout so the
# chain format has one owner; falls back to an inline writer with the same
# line format (sorted keys, compact separators, prev_hash = SHA-256 of the
# previous full line, "GENESIS" for the first, optional HMAC) inside an
# installed plugin.
# --------------------------------------------------------------------------
def audit_dir() -> Path:
    return Path(os.environ.get("USAP_AUDIT_DIR", str(Path.home() / ".usap" / "audit")))


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")


def _inline_write(entry: dict) -> Path:
    d = audit_dir()
    d.mkdir(parents=True, exist_ok=True)
    entry = dict(entry)
    entry["timestamp_utc"] = entry.get("timestamp_utc") or _now()
    log = d / f"{entry['timestamp_utc'].split('T')[0]}.jsonl"
    prev = "GENESIS"
    if log.exists():
        lines = [ln for ln in log.read_text(encoding="utf-8").splitlines() if ln.strip()]
        if lines:
            prev = hashlib.sha256(lines[-1].encode()).hexdigest()
    entry["prev_hash"] = prev
    key = os.environ.get("USAP_AUDIT_KEY")
    if key:
        content = json.dumps(entry, separators=(",", ":"), sort_keys=True)
        entry["sig"] = hmac.new(key.encode(), content.encode(), hashlib.sha256).hexdigest()
    with log.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(entry, separators=(",", ":"), sort_keys=True) + "\n")
    return log


def write_audit(entry: dict) -> Path:
    tools_dir = REPO_ROOT / "tools"
    if (tools_dir / "mcp_audit.py").exists():
        sys.path.insert(0, str(tools_dir))
        try:
            from mcp_audit import write_audit as _wa  # type: ignore
            return _wa(entry)
        except Exception:  # pragma: no cover - fall back to the inline writer
            pass
    return _inline_write(entry)


def _iter_recent_entries(days: int = 2) -> Iterable[dict]:
    d = audit_dir()
    if not d.is_dir():
        return
    today = datetime.now(timezone.utc).date()
    for i in range(days + 1):
        f = d / f"{(today - timedelta(days=i)).isoformat()}.jsonl"
        if not f.exists():
            continue
        for ln in f.read_text(encoding="utf-8").splitlines():
            ln = ln.strip()
            if not ln:
                continue
            try:
                yield json.loads(ln)
            except json.JSONDecodeError:
                continue


def find_pass(session_id: str, passes: Iterable[str]) -> Optional[dict]:
    """DR-1: a pass counts only when its session_id matches this session."""
    wanted = set(passes)
    for e in _iter_recent_entries():
        if e.get("event") == PASS_EVENT and e.get("session_id") == session_id and e.get("pass") in wanted:
            return e
    return None


def marker_path(session_id: str) -> Path:
    safe = re.sub(r"[^A-Za-z0-9_.-]", "_", session_id or "unknown")
    return audit_dir() / f"session-{safe}.touched"


# --------------------------------------------------------------------------
# Router
# --------------------------------------------------------------------------
def classify(text: str) -> dict:
    for persona, code, label, rx in TRIGGERS:
        hits = sorted({m.group(0).lower() for m in rx.finditer(text or "")})
        if hits:
            return {
                "persona": persona,
                "pass": code,
                "label": label,
                "matched": hits,
                "confidence": round(min(0.95, 0.6 + 0.1 * len(hits)), 2),
            }
    return {"persona": None, "pass": None, "label": None, "matched": [], "confidence": 0.0}


def find_skill(slug: str, root: Path) -> Optional[Path]:
    for dom in ACTIVE_DOMAINS:
        cand = root / dom / slug / "SKILL.md"
        if cand.exists():
            return cand
    return None


def block_payload(slug: str, root: Path) -> dict:
    return {
        "agent_slug": "orchestrator",
        "intent_type": "block",
        "action": f"Stop the chain. '{slug}' is not installed under {root}; install the full skill tree or route to an installed skill.",
        "rationale": (
            f"next_agents named '{slug}', which does not resolve to <domain>/{slug}/SKILL.md in any active domain "
            f"under {root}. Output-contract rule 7 requires next_agents to reference valid USAP skill slugs; "
            "routing to an absent skill would silently fall through."
        ),
        "confidence": 1.0,
        "severity": "high",
        "key_findings": [
            f"Skill '{slug}' absent from the resolved tree at {root}",
            f"Searched {len(ACTIVE_DOMAINS)} active domains",
            "Chain halted with intent_type=block; no fallback skill selected",
        ],
        "evidence_references": [
            {"source": "local://standards/output-contract.md", "ref": "rule 7: next_agents must only reference valid USAP skill slugs"}
        ],
        "next_agents": [],
        "human_approval_required": False,
        "timestamp_utc": _now(),
    }


# --------------------------------------------------------------------------
# Hook handlers. Each reads one JSON object from stdin.
# --------------------------------------------------------------------------
def _read_stdin_json() -> dict:
    try:
        raw = sys.stdin.read()
        return json.loads(raw) if raw.strip() else {}
    except json.JSONDecodeError:
        return {}


def record_command(session_id: str, persona: str, code: str) -> str:
    return (
        f"python3 {SELF} record --session-id {session_id} --persona {persona} --pass {code} "
        f"--residual-risk <low|medium|high> --summary '<one line>'"
    )


def hook_prompt() -> int:
    data = _read_stdin_json()
    sid = str(data.get("session_id") or "unknown")
    result = classify(str(data.get("prompt") or ""))
    if not result["persona"]:
        return 0
    try:
        write_audit({"event": "gate_prompt", "session_id": sid, "persona": result["persona"],
                     "pass": result["pass"], "matched": result["matched"]})
    except Exception:
        pass  # advisory hook fails open by design; the coverage audit counts the gap
    # DR-6: fixed template; matched terms go to the audit log, never to context.
    line = (
        f"USAP gate: this request matches the {result['pass']} ({result['label']}) trigger. "
        f"Run /usap:{result['persona']}, complete the {result['pass']} pass, then record it with: "
        f"{record_command(sid, result['persona'], result['pass'])}. "
    )
    if result["pass"] == "DR":
        line += "Edits to CI, IaC, hooks, settings and credential files are blocked in this session until a DR pass is recorded."
    print(line)
    return 0


def hook_pretool() -> int:
    data = _read_stdin_json()
    if data.get("tool_name") not in GATED_WRITE_TOOLS:
        return 0
    ti = data.get("tool_input") or {}
    path = ti.get("file_path") or ti.get("notebook_path") or ""
    if not is_gated_path(path, data.get("cwd")):
        return 0
    sid = str(data.get("session_id") or "unknown")
    try:
        audit_dir().mkdir(parents=True, exist_ok=True)   # DR-2: create, never bypass
        marker_path(sid).touch()
        found = find_pass(sid, {"DR"})
    except OSError as exc:
        sys.stderr.write(
            f"USAP gate: cannot read the audit directory {audit_dir()} ({exc}). "
            f"Gated write to {path} is blocked. Fix the directory permissions, then record the pass: "
            f"{record_command(sid, 'usap-devsecops', 'DR')}\n")
        return 2
    if found:
        return 0
    sys.stderr.write(
        f"USAP gate: {path} is a gated path (CI, IaC, hooks, settings or credentials) and no design-review pass "
        f"is recorded for session {sid}. Run /usap:usap-devsecops DR on the change, then record it: "
        f"{record_command(sid, 'usap-devsecops', 'DR')}\n")
    return 2


def hook_stop() -> int:
    data = _read_stdin_json()
    sid = str(data.get("session_id") or "unknown")
    m = marker_path(sid)
    if not m.exists():
        return 0
    has_pass = find_pass(sid, {"DR", "PA"}) is not None
    try:
        m.unlink()  # DR-8
    except OSError:
        pass
    if not has_pass:
        print(json.dumps({"systemMessage": "USAP: gated paths were written this session and no persona pass was recorded."}))
    return 0


# --------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------
def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(description="USAP persona gate")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("prompt"); sub.add_parser("pretool"); sub.add_parser("stop")
    c = sub.add_parser("classify"); c.add_argument("text")
    k = sub.add_parser("check-skill"); k.add_argument("slug"); k.add_argument("--root", default=None)
    r = sub.add_parser("record")
    r.add_argument("--session-id", required=True)
    r.add_argument("--persona", required=True)
    r.add_argument("--pass", dest="code", required=True, choices=["DR", "PA", "PR", "RG", "IR", "RT"])
    r.add_argument("--residual-risk", required=True, choices=RESIDUAL_RISKS)
    r.add_argument("--summary", required=True)
    r.add_argument("--report", default=None, help="repo-relative path of the written review")
    args = ap.parse_args(argv)

    if args.cmd == "prompt":
        return hook_prompt()
    if args.cmd == "pretool":
        return hook_pretool()
    if args.cmd == "stop":
        return hook_stop()
    if args.cmd == "classify":
        print(json.dumps(classify(args.text)))
        return 0
    if args.cmd == "check-skill":
        root = Path(args.root).resolve() if args.root else (REPO_ROOT if (REPO_ROOT / "standards").exists() else PLUGIN_ROOT)
        hit = find_skill(args.slug, root)
        if hit:
            print(json.dumps({"found": str(hit)}))
            return 0
        print(json.dumps(block_payload(args.slug, root), indent=2))
        return 3
    if args.cmd == "record":
        if not args.summary.strip():
            ap.error("--summary must not be empty")
        log = write_audit({
            "event": PASS_EVENT, "session_id": args.session_id, "persona": args.persona,
            "pass": args.code, "residual_risk": args.residual_risk,
            "summary": args.summary.strip(), "report": args.report,
        })
        print(json.dumps({"recorded": True, "log": str(log), "pass": args.code, "residual_risk": args.residual_risk}))
        return 0
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
