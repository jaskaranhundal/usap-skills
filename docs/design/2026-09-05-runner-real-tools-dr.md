# Design review: the scheduled runner executes the real skill tool (#139)

Reviewer: cs-devsecops-engineer (Riley), DR workflow. Date: 2026-09-05. Subject: `tools/usap_runner.py`. This changes the autonomy loop, so it is reviewed before it is written. Audit line: `~/.usap/audit/2026-09-05.jsonl`, event `persona_pass`, pass DR.

## Problem (F-03)

`_build_payload` synthesises a contract-shaped payload from the job spec and dispatches it. No skill tool runs. A scheduled `secrets-exposure` job therefore posts a payload with no findings, and the audit trail records a `scheduled_run` that analysed nothing. The runner is autonomy theatre.

## Change

`execute_job` runs the skill's own tool before dispatch:

1. **Locate the tool.** `<domain>/<slug>/scripts/<slug>_tool.py` across the twelve active domains. A slug that resolves to no tool is a `runner_error`, recorded, not dispatched.
2. **Run it.** `python3 <tool> --output json` plus `--input <job.input>` when the job names a fixture, with a timeout (default 60 s). The subprocess never inherits a shell; the argument list is fixed.
3. **Read the verdict.** Parse stdout as the 11-field payload and pass it through `tools/output_contract.validate_payload` in structural mode. A tool that exits 3, emits `status: not_implemented`, produces unparseable output, or fails the structural gate is recorded as `runner_skipped` with the reason and is **not** dispatched — an absence of analysis is never posted as a clean result.
4. **Dispatch.** Only a real, conformant payload goes to `dispatch_unattended`, which already refuses any capability that requires approval. The payload's own `intent_type` and `severity` ride along; the job's `intent_type` is a fallback only.

The `scheduled_run` audit line now carries the real payload. A new `runner_skipped` / `runner_error` event carries the reason when nothing was dispatched.

## Job schema

One optional field: `input` (a repo-relative fixture path). Absent, the tool runs with no input and most tools return an informational "no input" payload, which is correctly skipped rather than dispatched. The default `runner/runner.yaml` gains an `input` on the daily secrets job pointing at its fixture so the dogfood job produces a real verdict.

## Threats considered

| Threat | Position |
|---|---|
| A tool hangs and stalls the daemon | 60 s timeout; `TimeoutExpired` is caught and recorded as `runner_error`; the loop continues |
| A tool prints a huge payload | stdout captured with a size cap; over-cap output is a `runner_skipped` |
| A stub dispatched as a clean scan | The structural gate plus the `not_implemented` / exit-3 check block it; this is the core fix, tested |
| A tool with a real finding auto-dispatches a mutating capability | `dispatch_unattended` refuses approval-required capabilities; unchanged |
| Arbitrary code via the slug | The slug comes from the operator's own runner.yaml, and the path is composed, not shell-interpolated; only `<slug>_tool.py` under a known domain runs |
| Input path traversal | `input` is resolved and must stay under the repository root, same rule as the evidence gate |

## Decision

**Residual risk: low.** The change makes the runner honest: it either dispatches a real verdict or records why it did not. The one irreducible risk — a de-stubbed tool with a latent bug producing a wrong verdict — is bounded by the evidence gate and by read-only dispatch, and is the same risk the tool carries when a human runs it. Conditions: the four listed in the audit line, all met by the implementation and `tools/usap_runner_test.py`.

`next_agents: []`.
