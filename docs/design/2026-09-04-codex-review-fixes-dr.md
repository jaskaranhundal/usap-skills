# Design review: three runtime fixes from the Codex review of PR #147

Reviewer: cs-devsecops-engineer (Riley), DR workflow. Date: 2026-09-04. Subject: review comments 3936200728, 3936200734, 3936200739 on the dispatch path. Two of the three change guard or gate behaviour, so they are reviewed before they are written. Audit line: `~/.usap/audit/2026-09-04.jsonl`, event `persona_pass`, pass DR, subject `codex-review-fixes`.

## Findings confirmed

| # | File | Defect | Impact |
|---|---|---|---|
| C-1 | `adapters/_lib.py` | `mode == "live" and live_fn is not None` falls through to the fixture branch when an adapter has no live handler. Slack and Splunk pass no handler. | An operator who sets `USAP_ADAPTER_MODE=live` receives a canned success for `post_message` or `search`; the router records `dispatched`; nothing was sent or queried. A silent false positive on a mutating capability. |
| C-2 | `tools/mcp_dispatch.py` | `_recv` calls `readline()` inside the deadline loop; an adapter that stays alive without emitting a newline blocks forever. | `dispatch(timeout=…)` is not a bound. A stalled live integration hangs the routing request and its caller. |
| C-3 | `tools/output_contract.py` | `local://` paths are joined to the repo root and tested with `exists()` only; `..` segments are not contained. | `local://../../etc/passwd` passes the evidence gate when the file exists on the validating host. The gate's repo-artifact requirement is bypassable. |

## Required shape of each fix

- **C-1.** Live mode with no handler returns a JSON-RPC error (`-32001`, "live mode is not implemented for this adapter; no call was made") and never touches fixtures. A stderr line at startup states the same once. The router already maps adapter errors to `dispatch_failed`, so the audit trail records the failure rather than a success. Fixture mode is unchanged.
- **C-2.** Replace blocking `readline()` with non-blocking reads on the pipe descriptor (`selectors` plus `os.read`) accumulating a byte buffer until a newline; check the deadline between reads; treat EOF as premature exit. The deadline becomes a real bound regardless of adapter behaviour. `finally` still terminates the process.
- **C-3.** Resolve the candidate path and require it to remain under the resolved repository root before `exists()`; reject with a distinct reason ("escapes the repository root"). Symlinks that resolve inside the repository (the polyglot mirrors) remain valid; symlinks that resolve outside are rejected, which is the intended reading of "repository artifact".

## Threats considered

| Threat | Position |
|---|---|
| A fixture accidentally shipped as production evidence | C-1 makes live-without-handler loud; the remaining risk is an adapter whose live handler itself returns canned data, which this review cannot detect and the fixture-runner PR does not cover. Accepted, recorded. |
| Deadline enforcement kills a slow but healthy adapter | Timeout default stays 20 s and is per-call configurable; the change only makes the existing contract true. |
| Containment breaks legitimate evidence | The only rejected sources are those resolving outside the repository. Existing samples cite in-repo paths; the corpus gate is the regression test. |
| Windows path semantics | `Path.resolve()` and `is_relative_to` behave on Windows; the polyglot symlinks are POSIX-only already. |

## Decision

**Residual risk after the three fixes: low.** Each fix closes a specific silent-failure path and adds a regression test that reproduces the defect first. Conditions: (1) each PR carries the test that fails before and passes after; (2) the unit tests run in both CI pipelines; (3) the accepted residual on live handlers returning canned data is listed in the C-1 PR body. Re-review on any change to adapter mode selection or to the resolvable-source rules.

`next_agents: []`.
