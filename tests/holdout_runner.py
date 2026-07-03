#!/usr/bin/env python3
"""USAP independent evaluation harness.

Grades USAP against a HELD-OUT, hand-labeled corpus that USAP did not write
itself (`tests/holdout/cases/*.json`). This is the antidote to the
fortigate/challenge/compare commands, which grade USAP against USAP's own
canonical answers (circular). Here the ground truth comes from public
incidents, classic CVEs, and deliberately benign-but-noisy activity — so the
numbers mean something.

Metrics (per run, written to tests/holdout/runs/<label>.json):
  * precision, recall, F1  — on the binary "is this a real, actionable threat?"
  * false_positive_rate    — FP / (FP + TN); the SOC's alert-fatigue metric
  * severity_accuracy      — exact + within-one-band
  * intent_accuracy        — predicted intent_type vs label
  * mttd_minutes           — mean detection latency over true positives that
                             carry a predicted latency (else reported n/a)

A "prediction" is a USAP 11-field payload. Predictions come from a *responder*:
  * ``--responder synthetic --predictions <file.json>`` — score pre-supplied
    payloads. Used to unit-test the scoring engine and to grade an offline
    batch a persona produced elsewhere.
  * ``--responder llm`` — drive each cs-* persona live. Requires an LLM
    endpoint (USAP_LLM_ENDPOINT or a local Ollama); NOT run in CI. This is the
    integration seam, documented in tests/holdout/README.md.

Stdlib only.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
CASES_DIR = REPO_ROOT / "tests" / "holdout" / "cases"
RUNS_DIR = REPO_ROOT / "tests" / "holdout" / "runs"

SEVERITY_ORDER = ["informational", "low", "medium", "high", "critical"]
# A prediction "flags" a case as an actionable threat when its severity is
# high/critical OR it routes to an active-response intent.
FLAGGING_INTENTS = {"respond", "escalate", "block"}


def _sev_rank(s: str) -> int:
    try:
        return SEVERITY_ORDER.index(s)
    except ValueError:
        return -1


def load_cases() -> list[dict]:
    cases = []
    for p in sorted(CASES_DIR.glob("*.json")):
        cases.append(json.loads(p.read_text()))
    return cases


def prediction_flags_threat(pred: dict) -> bool:
    """Did USAP treat this case as a real, actionable threat?"""
    sev = pred.get("severity", "")
    if _sev_rank(sev) >= _sev_rank("high"):
        return True
    if pred.get("intent_type") in FLAGGING_INTENTS:
        return True
    return False


def score(cases: list[dict], predictions: dict[str, dict]) -> dict:
    """Compare predictions (keyed by case id) against the corpus labels."""
    tp = fp = fn = tn = 0
    sev_exact = sev_within1 = intent_ok = graded = 0
    missing = []
    latencies = []
    per_case = []

    for case in cases:
        cid = case["id"]
        labels = case["labels"]
        truth_positive = bool(labels.get("is_true_positive"))
        pred = predictions.get(cid)
        if pred is None:
            missing.append(cid)
            continue
        graded += 1
        flagged = prediction_flags_threat(pred)

        # Confusion matrix on the binary threat decision.
        if truth_positive and flagged:
            tp += 1
        elif truth_positive and not flagged:
            fn += 1
        elif not truth_positive and flagged:
            fp += 1
        else:
            tn += 1

        # Severity accuracy (only meaningful on true-positive cases).
        outcome = {"id": cid, "truth_positive": truth_positive, "flagged": flagged}
        if truth_positive and "severity" in labels:
            exp, got = labels["severity"], pred.get("severity", "")
            if got == exp:
                sev_exact += 1
                sev_within1 += 1
            elif abs(_sev_rank(got) - _sev_rank(exp)) == 1:
                sev_within1 += 1
            outcome["severity"] = {"expected": exp, "got": got}

        # Intent accuracy.
        if "intent_type" in labels:
            if pred.get("intent_type") == labels["intent_type"]:
                intent_ok += 1
            outcome["intent"] = {"expected": labels["intent_type"], "got": pred.get("intent_type")}

        # MTTD: use a predicted latency if the payload carries one.
        lat = pred.get("detection_latency_minutes")
        if truth_positive and isinstance(lat, (int, float)):
            latencies.append(float(lat))

        per_case.append(outcome)

    def _ratio(n, d):
        return round(n / d, 4) if d else None

    precision = _ratio(tp, tp + fp)
    recall = _ratio(tp, tp + fn)
    fpr = _ratio(fp, fp + tn)
    f1 = (
        round(2 * precision * recall / (precision + recall), 4)
        if precision and recall else 0.0
    )
    mttd = round(sum(latencies) / len(latencies), 1) if latencies else None

    return {
        "graded": graded,
        "missing_predictions": missing,
        "confusion": {"tp": tp, "fp": fp, "fn": fn, "tn": tn},
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "false_positive_rate": fpr,
        "severity_accuracy_exact": _ratio(sev_exact, tp + fn),
        "severity_accuracy_within1": _ratio(sev_within1, tp + fn),
        "intent_accuracy": _ratio(intent_ok, graded),
        "mttd_minutes": mttd,
        "mttd_note": None if latencies else "no predicted latencies — needs live timing",
        "per_case": per_case,
    }


def _synthetic_predictions(path: Path) -> dict[str, dict]:
    data = json.loads(path.read_text())
    # Accept either {case_id: payload} or [{"id":..., ...payload}]
    if isinstance(data, dict):
        return data
    return {p["id"]: p for p in data if isinstance(p, dict) and "id" in p}


def main() -> int:
    ap = argparse.ArgumentParser(description="Grade USAP against the held-out corpus.")
    ap.add_argument("--responder", choices=["synthetic", "llm"], default="synthetic")
    ap.add_argument("--predictions", type=Path,
                    help="JSON file of predictions (required for --responder synthetic)")
    ap.add_argument("--label", default="adhoc", help="Run label (names the results file)")
    ap.add_argument("--write", action="store_true", help="Persist results under tests/holdout/runs/")
    ap.add_argument("--output", choices=["json", "text"], default="text")
    args = ap.parse_args()

    cases = load_cases()
    if not cases:
        print(f"No cases in {CASES_DIR}", file=sys.stderr)
        return 1

    if args.responder == "llm":
        print(
            "The 'llm' responder drives each cs-* persona live and needs an LLM "
            "endpoint (USAP_LLM_ENDPOINT or a local Ollama). It is not wired in "
            "this environment. See tests/holdout/README.md for the integration "
            "seam. Use --responder synthetic to score a pre-produced batch.",
            file=sys.stderr,
        )
        return 2

    if not args.predictions:
        ap.error("--responder synthetic requires --predictions <file.json>")
    predictions = _synthetic_predictions(args.predictions)
    result = score(cases, predictions)
    result["label"] = args.label
    result["corpus_size"] = len(cases)

    if args.write:
        RUNS_DIR.mkdir(parents=True, exist_ok=True)
        out = RUNS_DIR / f"{args.label}.json"
        out.write_text(json.dumps(result, indent=2) + "\n")
        print(f"wrote {out.relative_to(REPO_ROOT)}")

    if args.output == "json":
        print(json.dumps(result, indent=2))
    else:
        c = result["confusion"]
        print(f"USAP held-out evaluation — {result['corpus_size']} cases, {result['graded']} graded")
        print(f"  confusion    TP={c['tp']} FP={c['fp']} FN={c['fn']} TN={c['tn']}")
        print(f"  precision    {result['precision']}")
        print(f"  recall       {result['recall']}")
        print(f"  F1           {result['f1']}")
        print(f"  FPR          {result['false_positive_rate']}")
        print(f"  severity acc {result['severity_accuracy_exact']} exact / {result['severity_accuracy_within1']} within-1")
        print(f"  intent acc   {result['intent_accuracy']}")
        print(f"  MTTD (min)   {result['mttd_minutes']}  {result['mttd_note'] or ''}")
        if result["missing_predictions"]:
            print(f"  MISSING preds: {result['missing_predictions']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
