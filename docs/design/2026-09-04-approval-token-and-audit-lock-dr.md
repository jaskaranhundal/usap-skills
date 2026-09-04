# Design review: approval tokens and audit-chain append serialisation

Reviewer: cs-devsecops-engineer (Riley), DR workflow. Date: 2026-09-04. Subject: Codex review threads 3936208945 (PR #149) and 3936197783 (PR #148). Both change controls, so they are reviewed before they are written. Companion, non-control fixes from the same review (runner exit code 3936197828, scanner evidence URIs 3936197803) are noted in section 4 and need no review.

## 1. Findings confirmed

| # | File | Defect | Impact |
|---|---|---|---|
| A-1 | `tools/mcp_server.py`, `tools/mcp_router.py` | `dispatch_after_approval` accepts any string as `approval_token`; the server substitutes the literal `"approved"` when the argument is omitted; the router records that value as `approval_granted` and dispatches. | Any MCP client can invoke an enabled mutating capability (`post_message`, `open_issue`) without the advertised human gate ever being shown. The audit log records an approval that did not happen. This is the gate the whole contract advertises. |
| A-2 | `tools/mcp_audit.py` | `write_audit` reads the predecessor hash and appends without a lock. | Two concurrent writers (server request plus scheduled runner, or two hooks) can both read the same predecessor; `verify()` then reports a broken chain during ordinary operation, which trains the operator to ignore chain failures. |

## 2. Required shape

### A-1: server-issued, single-use approval tokens

- `route()` issues a token whenever it returns `approval_required`: `secrets.token_urlsafe(24)`, persisted in `audit_dir()/approvals/<token>.json` with `mcp`, `capability`, SHA-256 of the canonical JSON of `arguments`, `issued_utc`, `expires_utc` (issued + 1 h). The token is returned in the decision next to the approval prompt, and the `route` audit line records its SHA-256, never the token.
- `dispatch_after_approval(mcp_id, capability_id, arguments, approval_token)` requires a token. Validation, in order: file exists; not expired; `mcp` and `capability` match; arguments hash matches; not consumed. Any failure returns `dispatch_failed` with the reason and writes `approval_rejected` to the audit log. On success the token file is marked consumed (renamed to `.used`) before dispatch, so a token cannot dispatch twice.
- The server no longer defaults the argument. Missing token is a tool error.
- The scheduled runner never dispatched mutating capabilities by design, but it reused `dispatch_after_approval` with a synthetic token. It moves to a new `dispatch_unattended(mcp_id, capability_id, arguments)` that dispatches only when the capability is not `approval_required` and returns `dispatch_failed` otherwise. Unattended dispatch writes an `unattended_dispatch` audit line.
- Tests: route → approval_required carries a token; dispatch with that token succeeds once and fails the second time; wrong capability, wrong arguments, expired and missing tokens all fail; runner path refuses a gated capability.

### A-2: exclusive per-log lock across read-predecessor, sign, append

- `fcntl.flock(LOCK_EX)` on `<log>.lock` held from `_last_hash` through the append and flush. Where `fcntl` is unavailable (Windows) the writer proceeds unlocked and writes one `audit_lock_unavailable` warning to stderr per process; that platform is not in scope for the runtime.
- Test: 8 processes append 25 entries each to one log concurrently; `verify()` passes and 200 lines are present.

## 3. Threats considered

| Threat | Position |
|---|---|
| Token exfiltrated from the audit directory | Files hold the token as their name; the directory is the operator's home. Same trust boundary as the audit log itself, which already gates everything. Expiry (1 h) and single use bound the window. |
| Client replays an old approval for new arguments | Arguments hash is part of the token binding; a changed payload fails. |
| Runner regression | Runner jobs already skip `approval_required` capabilities when picking one; the new function enforces it instead of trusting the picker. |
| Lock file left behind | Lock files are empty and reused; never deleted while a writer may hold them. |
| Latency | One flock per audit line; sub-millisecond on local disk. |

## 4. Non-control fixes from the same review

- Runner `--once` exits 2 when the dispatch result is not `dispatched` (was 0), so automation cannot record success for a failed one-shot job.
- `container-image-scan` emits resolvable evidence: NVD or GitHub Advisory URLs for CVE and GHSA ids, the `local://` fixture path when the input lives in the repository, and a `local://` reference to the skill's own SKILL.md for the classification rule; the scanner name moves to `ref`. Recorded fixture and manifest row added so the fixture runner proves it.

## 5. Decision

**Residual risk after A-1 and A-2: low.** The approval gate becomes cryptographically bound to the routing decision instead of a free-text field, and the audit chain becomes reliable under concurrency. Conditions: (1) tests above land with the code; (2) the runner path is covered by a test; (3) `mcp_server_test.py` is updated to obtain the token from `route_payload` rather than passing a literal. Re-review on any change to token binding fields or expiry.

`next_agents: []`.
