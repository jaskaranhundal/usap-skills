# USAP held-out evaluation — per-release scores

Precision / recall / FPR / MTTD against the independent corpus in `cases/`, one row per release. Produced by `tests/holdout_runner.py --responder llm` once an LLM endpoint is wired (see `README.md`).

| Release | Corpus | Precision | Recall | F1 | FPR | Severity acc | Intent acc | MTTD (min) | Notes |
|---|---|---|---|---|---|---|---|---|---|
| _baseline pending_ | 12 | — | — | — | — | — | — | — | Awaiting a live `--responder llm` run; scoring engine + corpus complete and verified. |

## Engine self-check (not a USAP score)

The synthetic run in `example_predictions.json` exists only to prove the scoring math, not to score USAP. It encodes a deliberately-imperfect predictor (6 correct threat calls, 1 miss, 4 correct benign calls, 1 false flag) and must always produce:

| | TP | FP | FN | TN | Precision | Recall | F1 | FPR | MTTD |
|---|---|---|---|---|---|---|---|---|---|
| example | 6 | 1 | 1 | 4 | 0.8571 | 0.8571 | 0.8571 | 0.20 | 17.5 |

Reproduce:

```bash
python3 tests/holdout_runner.py --responder synthetic \
    --predictions tests/holdout/example_predictions.json --label example
```

If these numbers ever change without a corpus change, the scoring engine has regressed.
