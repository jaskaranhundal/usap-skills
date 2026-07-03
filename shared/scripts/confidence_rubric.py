#!/usr/bin/env python3
"""USAP confidence rubric — a written, reproducible way to score confidence.

USAP's output contract carries a ``confidence`` float in [0.0, 1.0]. Left to
the model, that number is narrated. This rubric makes it *computable* from the
evidence: how many independent sources corroborate the verdict, how reliable
each is, and whether any source disagrees.

Source reliability tiers (weights):
  * primary   (0.90) — direct authoritative evidence: a live MCP fetch of the
                       actual artifact, a vendor advisory, a CVE record.
  * secondary (0.70) — tool-derived: SAST/DAST scanner, SIEM correlation,
                       behavioural analytics, a threat-model mapping.
  * tertiary  (0.50) — indirect/inferred: reputation, heuristic, a single log
                       line, an unverified report.

Formula (deterministic):
  1. Among sources that AGREE with the verdict, take the best (highest) tier
     weight -> this is the confidence floor for a single source.
  2. Each ADDITIONAL agreeing independent source closes half the remaining gap
     to the ceiling (0.99): conf = best + (0.99 - best) * (1 - 0.5^(n-1)).
  3. Each DISAGREEING source multiplies confidence by 0.70 (dissent penalty).
  4. Clamp to [0.0, 0.99] — USAP never claims absolute certainty.

The ceiling is 0.99, not 1.0, on purpose: no finite evidence set justifies
certainty. A verdict below 0.5 is inconclusive per the output contract.

Stdlib only.

Usage::

    python3 shared/scripts/confidence_rubric.py --secondary 2
    python3 shared/scripts/confidence_rubric.py --primary 1 --tertiary 1 --disagree 1
    python3 shared/scripts/confidence_rubric.py --sources '[{"tier":"secondary"},{"tier":"secondary"}]'
"""
from __future__ import annotations

import argparse
import json
import sys

WEIGHTS = {"primary": 0.90, "secondary": 0.70, "tertiary": 0.50}
CEILING = 0.99


def score_confidence(sources: list[dict]) -> dict:
    """Compute a reproducible confidence from a list of evidence sources.

    ``sources`` is a list of ``{"tier": "primary|secondary|tertiary",
    "agrees": bool}`` (``agrees`` defaults to True). Returns
    ``{confidence, rationale, inputs}``.
    """
    agreeing = [s for s in sources if s.get("agrees", True)]
    disagreeing = [s for s in sources if not s.get("agrees", True)]

    if not agreeing:
        return {
            "confidence": 0.0,
            "rationale": "No agreeing evidence source — confidence 0.0 (inconclusive).",
            "inputs": {"agreeing": 0, "disagreeing": len(disagreeing)},
        }

    weights = [WEIGHTS.get(s.get("tier", "tertiary"), WEIGHTS["tertiary"]) for s in agreeing]
    best = max(weights)
    n = len(agreeing)
    conf = best + (CEILING - best) * (1 - 0.5 ** (n - 1))

    for _ in disagreeing:
        conf *= 0.70

    conf = max(0.0, min(CEILING, round(conf, 2)))

    best_tier = max(agreeing, key=lambda s: WEIGHTS.get(s.get("tier", "tertiary"), 0.5)).get("tier", "tertiary")
    rationale = (
        f"{n} agreeing source(s) (best tier={best_tier}, w={best:.2f}); "
        f"corroboration lift over {n - 1} extra source(s)"
    )
    if disagreeing:
        rationale += f"; {len(disagreeing)} disagreeing source(s) applied a 0.70x dissent penalty each"
    rationale += f" => confidence {conf:.2f}."

    return {
        "confidence": conf,
        "rationale": rationale,
        "inputs": {
            "agreeing": n,
            "disagreeing": len(disagreeing),
            "best_tier": best_tier,
        },
    }


def score_counts(primary: int = 0, secondary: int = 0, tertiary: int = 0,
                 disagreements: int = 0) -> dict:
    """Convenience wrapper: score from tier counts instead of a source list."""
    sources = (
        [{"tier": "primary"}] * primary
        + [{"tier": "secondary"}] * secondary
        + [{"tier": "tertiary"}] * tertiary
        + [{"tier": "tertiary", "agrees": False}] * disagreements
    )
    return score_confidence(sources)


def main() -> int:
    ap = argparse.ArgumentParser(description="Compute a reproducible USAP confidence score.")
    ap.add_argument("--primary", type=int, default=0)
    ap.add_argument("--secondary", type=int, default=0)
    ap.add_argument("--tertiary", type=int, default=0)
    ap.add_argument("--disagree", type=int, default=0)
    ap.add_argument("--sources", help="JSON list of {tier, agrees} objects (overrides counts)")
    ap.add_argument("--output", choices=["json", "text"], default="text")
    args = ap.parse_args()

    if args.sources:
        try:
            result = score_confidence(json.loads(args.sources))
        except json.JSONDecodeError as exc:
            print(f"invalid --sources JSON: {exc}", file=sys.stderr)
            return 2
    else:
        result = score_counts(args.primary, args.secondary, args.tertiary, args.disagree)

    if args.output == "json":
        print(json.dumps(result, indent=2))
    else:
        print(f"confidence: {result['confidence']:.2f}")
        print(f"rationale : {result['rationale']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
