# Design review: persona gate hooks and router

Reviewer: cs-devsecops-engineer (Riley), DR workflow (Document Security Review). Date: 2026-09-04. Subject: the draft of [`2026-09-04-persona-gate-hooks-design.md`](2026-09-04-persona-gate-hooks-design.md) (issues #137, #141). Audit line: `~/.usap/audit/2026-09-04.jsonl`, event `persona_pass`, SHA-256 prefix `69ba17f9dfcdc94a`.

## Step 2 and 3, deterministic pass

| Signal | Value |
|---|---|
| Document type | prd |
| Word count | 845 |
| Trust boundaries described | yes |
| Data flows described | yes |
| Technology keywords | terraform, python |
| Critical keywords | none |
| Deterministic severity | informational, confidence 0.55 |
| Tool routing suggestion | appsec-code-review |

The deterministic pass found no hard-coded credentials, no missing-auth phrases and no compliance keywords. That is expected for a control-design document and says nothing about whether the control works. The findings below are the design-level review.

## Step 4, findings

| # | Severity | Finding | Location | Required change |
|---|---|---|---|---|
| DR-1 | high | Session-start detection relies on a `CLAUDE_SESSION_START` environment variable that Claude Code does not set. Hooks receive `session_id` in the JSON on stdin. Keying on a non-existent variable would make the PreToolUse check pass or fail for the wrong reason. | §2, PreToolUse row | Every audit entry written by `--record` carries `session_id` from the hook input; PreToolUse accepts a pass only when `session_id` matches the current session. Add `session_id` to the `persona_pass` event schema. |
| DR-2 | high | Fail-closed on an unreadable audit directory locks a fresh machine out of every CI, IaC and settings edit with no recovery path other than reading the source. | §2, PreToolUse fail mode | Missing directory: create it, then block with a message that states the exact `--record` command. Unreadable (permissions): block, same message. Never an environment-variable bypass; a silent off switch is the failure mode this control exists to remove. |
| DR-3 | medium | Gated globs are too wide. `**/settings*.json` matches application settings in unrelated repos. `**/*secret*` matches this repository's own `tests/fixtures/secrets-exposure-input.json` and every `expected_outputs/` file under `detection/secrets-exposure/`. False blocks erode trust faster than missed ones. | §2, PreToolUse matcher | Narrow to `.claude/settings*.json`, `**/.env`, `**/.env.*` (not `.env.example`), `**/*credentials*`, `**/*secrets*.y*ml`; exclude `tests/`, `**/fixtures/`, `**/expected_outputs/`. Keep the CI, IaC, Dockerfile, `hooks.json`, `registry/`, `runner/` entries. |
| DR-4 | medium | The design gates `hooks.json` but the pull request that introduces `hooks.json` is itself the first gated write. Without a recorded pass the implementation would be blocked by the control it introduces, or would be written before any hook exists and therefore unreviewed. | §3 threat table | This review is that pass. Record it in the audit chain before the first commit of hook code; the PR body cites the audit line. |
| DR-5 | medium | The coverage skill reads session transcripts. Transcript tool outputs can contain fetched secrets, diffs and ticket text. The design promises to store only ids, timestamps and tool names; nothing enforces that. | §3 component 3 | Parser walks JSON keys only; message `content` is never read into a variable that reaches output. Add a unit assertion that no output field contains a substring longer than 64 characters from any transcript `content`. Output schema is fixed: `session_id`, `started_utc`, `tools_used`, `gated_paths_touched`, `pass_recorded`. |
| DR-6 | medium | UserPromptSubmit injects a line into context on a match. If the injected line echoes matched terms, attacker-controlled prompt text reaches the model as hook-authored context. | §2 UserPromptSubmit | Injected text is a fixed template containing only the persona slug and pass code from the router's own table. Matched terms go to the audit log, never to context. |
| DR-7 | high | Bypass by not loading the plugin. The gate exists only in sessions where the `usap` plugin is enabled; any other project directory, or a session started with plugins disabled, has no gate. | §3 threat table (missing row) | Accepted residual, with two conditions: (a) the operator installs the same three hooks in user-level `~/.claude/settings.json` so the gate follows the operator across projects; (b) the weekly coverage audit counts sessions in which gated paths were written and no hook marker exists, and reports them as a `high` finding. |
| DR-8 | low | Per-session `.touched` marker files accumulate indefinitely. | §2 Stop row | Coverage audit deletes markers older than 30 days; Stop hook removes its own marker after reporting. |
| DR-9 | low | No timeout stated for hook commands. A hung router blocks every prompt. | §2 | `timeout: 5` on every hook entry in `hooks.json`; router self-limits to a single regex pass. |
| DR-10 | informational | Routing per Workflow 4: the document describes trust boundaries, so the `threat-model` skill applies, and it references pipeline files, so `pipeline-security-scan` applies. `pipeline-security-scan` is a stub and was not run. `threat-model` was not run in this pass; the threat table in §3 stands in for it and is accepted as sufficient for a control of this size. | §3 | None required. Recorded so the omission is visible. |

## Step 5, decision

**Residual risk after DR-1 to DR-6, DR-8 and DR-9 are applied: medium.**

Why medium and not low: the hard control (PreToolUse block on gated paths) is sound and fails closed, but its reach ends where the plugin is not loaded (DR-7). The compensating control is detective, weekly, and depends on the operator reading the Monday report. That is an honest medium.

Why medium and not high: the control's failure modes are visible. UserPromptSubmit failing open produces a log line the audit counts; a missing pass produces a block with the recovery command printed; a missing plugin produces a `high` finding in the weekly report. Nothing fails silently.

**Conditions attached to the rating**

1. DR-1, DR-2, DR-3, DR-5 and DR-6 are implemented before the hooks ship. DR-4 is satisfied by the audit line recording this review.
2. DR-7 condition (a) is documented in the plugin README as an operator setup step; condition (b) is implemented in `persona-coverage-audit`.
3. The pull request body carries this rating and the audit line id.
4. Re-review on any change to the gated-path list or the fail modes. Changes to the trigger table do not require re-review.

**Handoff.** `next_agents: []`. Terminal for the design phase. Implementation proceeds under the conditions above.
