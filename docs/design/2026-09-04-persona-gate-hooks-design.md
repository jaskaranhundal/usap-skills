# Design: persona gate hooks and router

Date: 2026-09-04. Status: reviewed (cs-devsecops-engineer DR, residual risk medium, see [the review](2026-09-04-persona-gate-hooks-dr.md)). Tracks issues #137 (F-01) and #141 (F-05). This is the revised design with the review's conditions applied; the original draft is recorded in the review.

## Problem

The operating rule "every security-relevant decision routes through a USAP persona pass" existed only as prose. The plugin shipped no hooks. Across every local session transcript since July, one session listed the persona names and none invoked a DR, PA or PR pass. A rule with no mechanism is not a control.

## Goal

Make the persona pass fire mechanically, on the local machine, with no paid API, under Claude Code, and make its absence visible.

## Components

### 1. `plugins/usap/hooks/usap_gate.py` (stdlib; `tools/usap_router.py` is a shim to it)

- `classify "<text>"`: prints persona, pass code, matched tokens and a confidence. The trigger table mirrors the operator rule. Word-boundary matching only. Precedence: incident, red team, risk governance, pre-report, post-assessment, design review.
- `check-skill <slug> [--root DIR]`: exit 0 when `<root>/<domain>/<slug>/SKILL.md` exists in an active domain; otherwise prints a contract-conformant `block` payload naming the missing slug and exits 3 (F-05).
- `record --session-id ID --persona SLUG --pass CODE --residual-risk low|medium|high --summary "..."`: appends `event: persona_pass` to the hash-chained audit log. The residual-risk field is mandatory (score first, claim second). The session id is mandatory (DR-1).
- Never reads the network; writes only under `USAP_AUDIT_DIR` or `~/.usap/audit`.

### 2. `plugins/usap/hooks/hooks.json`

| Event | Matcher | Behaviour | Fail mode |
|---|---|---|---|
| UserPromptSubmit | all | Classifies the prompt. On a match prints a fixed template naming the persona, the pass and the exact `record` command including this session's id (DR-1, DR-6: matched terms go to the audit log, never to context). | Fails open; the gap is a missing `gate_prompt` line the coverage audit can count. |
| PreToolUse | Edit, Write, MultiEdit, NotebookEdit | If the target path is gated, require a `persona_pass` with `pass: DR` and this `session_id` in the last two days of the log. Missing → exit 2 with the reason and the record command on stderr (blocks the write). Touches a per-session marker. | Missing audit directory is created, then blocked with instructions (DR-2). Unreadable directory blocks with instructions. No environment-variable bypass. |
| Stop | all | If the session touched a gated path and holds no DR or PA pass, emits `systemMessage: "USAP: gated paths were written this session and no persona pass was recorded."`. Removes the marker (DR-8). | Never blocks. |

Every hook has `timeout: 5` (DR-9).

**Gated paths (DR-3).** `.github/workflows/*`, `.gitlab-ci.yml`, `*.tf`, `*.tfvars`, `Dockerfile*`, `.claude/settings*.json`, `.claude/CLAUDE.md`, `hooks.json`, `.env` and `.env.*` (not `.env.example`), any name containing `credentials`, `*secrets*.y*ml`, and `*.yaml` under `registry/` or `runner/`. Excluded: anything under `tests/`, `fixtures/`, `expected_outputs/`, `node_modules/`, `.git/`, and any `.md` or `.example` file. The repository's own secrets fixtures do not trip the gate; `tools/usap_gate_test.py` asserts both lists.

### 3. `governance/persona-coverage-audit` skill (L2, read-only)

- Fixture mode for CI; live mode reads the audit directory and transcript JSONL files.
- Pairs gated sessions with passes by `session_id`; reports sessions with no hook activity separately (DR-7 condition b).
- Transcript collector reads JSON keys only: session id, timestamp, tool names, write-tool file paths (DR-5). Output schema is fixed.
- Severity `high` and exit 2 when gated sessions exist and zero passes were recorded.

## Threat model of the control itself

| Threat | Mitigation |
|---|---|
| Hook bypassed by editing hooks.json | `hooks.json` is a gated path; the shipped copy is inside the plugin whose drift gate covers agents and tools, and the file itself is versioned |
| Forged pass entry | Audit log is hash-chained; HMAC when `USAP_AUDIT_KEY` is set; `mcp_audit.py --verify` runs first in the weekly workflow |
| Prompt injection through prompt text | Router matches tokens only; injected context is a fixed template; matched terms are logged, not echoed |
| Latency or hang | One regex pass; `timeout: 5` on every hook |
| Fail-open hides failures | Only the advisory hook fails open, and its absence is countable; the write block fails closed |
| Plugin not loaded (DR-7) | Accepted residual. Condition a: operator installs the same three hooks in user-level `~/.claude/settings.json` (documented in `plugins/usap/README.md`). Condition b: coverage audit reports gated sessions without hook activity as `high` |
| Operator disables the gate to move faster | Stop line and Monday report make it visible; zero is a defect (operator rules section 16) |
| Self-referential first commit (DR-4) | This design's review is recorded in the audit chain before the hook code was committed; the PR body cites the line |

## Out of scope

- Enforcing the gate in other runtimes. The router is reusable; the hook wiring is Claude Code only.
- Blocking on prompt content. Only file paths block.

## Acceptance (all covered by `tools/usap_gate_test.py`)

- `classify "harden the runner against direct push"` → `usap-devsecops`, `DR`.
- `check-skill not-a-skill` → exit 3 with a `block` payload carrying all 11 fields.
- A gated write with no pass for the session is blocked with the record command in the message; after `record` for the same session it proceeds; a pass from another session or a PA pass does not unlock it.
- Fixture paths, `.md`, `.env.example` and application `settings.json` files are not gated; CI, Dockerfile, `.claude/settings*.json`, `hooks.json`, `.env`, registry YAML and credential files are.
- A missing audit directory is created and the write is still blocked.
- The audit log written by the gate verifies with `mcp_audit.verify`.
- `persona-coverage-audit_tool.py --input tests/fixtures/persona-coverage-audit/input.json` passes `tools/output_contract.py` and exits 1 on the fixture (one uncovered session, one without hook).
