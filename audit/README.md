# `audit/` — USAP skill audit ledger

The `audit/` directory is the maintainer-owned ledger for periodic quality reviews
of the USAP skill catalog. It is separate from the runtime audit log
(`~/.usap/audit/<date>.jsonl`) — that one records skill invocations; this one
records the human read-through of skill **quality**.

## Cadence

Quarterly. Each cycle gets its own subdirectory (`audit/<YYYY>-Q<N>/`).

## What gets scored

Every skill in the catalog is read end-to-end and scored on the 7-dimension
rubric in [`2026-Q2/RUBRIC.md`](2026-Q2/RUBRIC.md):

1. Trigger quality — does the description name a clear "Use when" condition?
2. Context economy — what's loaded vs needed?
3. Tool wiring — does `scripts/<slug>_tool.py` emit a contract-compliant payload?
4. Verification loop — can the LLM check its own output?
5. Real-world expertise — does the body reflect SOC / IR practice?
6. Freshness — last `updated:` ≤ 12 months ago?
7. No filler — signal-to-noise ratio.

Each skill receives one of four verdicts: **KEEP**, **OPTIMIZE**, **REWRITE**,
or **CUT-OR-MERGE**.

## How to run a cycle

1. Open `<cycle>/00-MASTER.md` and fill the per-domain rows as you finish them.
2. For each domain, create `<cycle>/<domain>.md` and score each skill against
   the rubric.
3. Roll up verdict counts in the master table.
4. Open PRs against the skills that need OPTIMIZE / REWRITE / CUT-OR-MERGE.

The audit ledger is read-only history once a cycle closes — do not retroactively
edit scored verdicts; open follow-up cycles instead.
