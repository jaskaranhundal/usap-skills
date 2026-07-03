# USAP held-out evaluation

This is USAP's **independent** accuracy measurement. It grades USAP against a hand-labeled corpus of real incidents and benign-but-noisy activity that **USAP did not write itself**.

## Why this exists

The `usap:fortigate`, `usap:challenge`, and `usap:compare` commands grade USAP against USAP's own canonical scorecards (`tests/expected/*.md`). That is circular — a model that agrees with its own answer key learns nothing. The held-out corpus fixes this: the ground truth comes from public postmortems, classic CVEs, and deliberately-authorized activity, labeled independently of any USAP run. When USAP scores well here, the number means something.

## The corpus

`tests/holdout/cases/*.json` — one file per case. Currently 12 cases: 7 real threats (true positives) and 5 benign activities that look suspicious (true negatives — the false-positive traps that make a precision/FPR number honest).

Each case:

```json
{
  "id": "log4shell-2021",
  "source": "public: Apache Log4j CVE-2021-44228 (Log4Shell), Dec 2021",
  "input": { "description": "...", "signals": ["...", "..."] },
  "labels": {
    "intent_type": "detect",
    "severity": "critical",
    "is_true_positive": true,
    "min_evidence_sources": 2,
    "detection_deadline_minutes": 30,
    "rationale_for_label": "why this label is defensible"
  }
}
```

### Labeling rules

1. **Ground truth, not opinion.** Every case is anchored to a public incident, a published CVE, or an unambiguously-authorized activity. `source` names it; `rationale_for_label` defends the label.
2. **Include the false-positive traps.** A corpus of only real attacks measures recall but not precision. Half the value is the benign cases (authorized scans, sanctioned bulk admin, CI bursts, contracted pentests, the AWS example key) that a naive detector over-flags.
3. **Never derive a case from a USAP output.** If USAP produced it, it cannot grade USAP. Cases come from outside.
4. **Label the decision, not the prose.** `is_true_positive` (is this a real, actionable threat?) plus expected `severity` and `intent_type` are what get scored.

### Adding a case

Drop a new `<id>.json` in `cases/` following the shape above. Keep the input realistic and the label defensible. Rebalance so the corpus keeps a meaningful mix of positives and negatives.

## Running it

The harness scores USAP **predictions** (11-field payloads) against the labels.

```bash
# Score a batch of predictions produced elsewhere (also how the engine is tested):
python3 tests/holdout_runner.py --responder synthetic \
    --predictions tests/holdout/example_predictions.json --label demo --write

# Drive each cs-* persona live (needs an LLM endpoint — see below):
python3 tests/holdout_runner.py --responder llm --label v1.12.0 --write
```

### Metrics

- **precision / recall / F1** on the binary "is this a real, actionable threat?" (a prediction *flags* a case when its severity is high/critical or its intent is respond/escalate/block).
- **false_positive_rate** = FP / (FP + TN) — the alert-fatigue metric the benign cases exist to measure.
- **severity_accuracy** (exact + within-one-band) and **intent_accuracy** on the labeled fields.
- **mttd_minutes** — mean detection latency over true positives whose prediction carries a `detection_latency_minutes`.

### The LLM integration seam (not wired in CI)

`--responder llm` is the only part that needs a model: it feeds each case's `input` to a cs-* persona and collects the 11-field payload. That requires an LLM endpoint (`USAP_LLM_ENDPOINT`, or a local Ollama) and is deliberately **not** run in CI — CI stays deterministic and offline. The scoring engine (everything else) is pure stdlib and fully tested via the synthetic responder. Wiring a concrete endpoint is the remaining integration step; the engine, corpus, and metrics are complete.

## Per-release tracking

`RELEASES.md` records precision / recall / FPR / MTTD per release tag, so regressions and improvements are visible over time. The whole point of the 7.5→9.5 arc is that these numbers move in the right direction as the data backend and evidence gate roll out.
