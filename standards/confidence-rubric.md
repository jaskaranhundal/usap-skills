# USAP Confidence Rubric

Every USAP verdict carries a `confidence` float in `[0.0, 1.0]`. This document is the **written, reproducible** basis for that number. Confidence is not narrated — it is computed from the evidence by `shared/scripts/confidence_rubric.py`, which implements exactly the rules below.

Why a rubric: a model asked for "a confidence score" will produce a plausible number that cannot be reproduced or audited. Tying confidence to *how many independent sources corroborate the verdict and how reliable each is* makes the number defensible — the same evidence always yields the same score.

---

## Source reliability tiers

| Tier | Weight | What qualifies |
|---|---|---|
| **primary** | 0.90 | Direct, authoritative evidence: a live MCP fetch of the actual artifact (`mcp:siem:search` returning the log line itself), a vendor advisory, a CVE record, an NVD CVSS vector |
| **secondary** | 0.70 | Tool-derived evidence: a SAST/DAST scanner finding, a SIEM correlation, behavioural analytics, a threat-model mapping |
| **tertiary** | 0.50 | Indirect or inferred: reputation data, a heuristic match, a single unverified log line, a third-party report |

---

## The formula

Given a set of evidence sources, each tagged with a tier and whether it **agrees** with the verdict:

1. Among the sources that **agree**, take the highest tier weight — call it `best`. This is the floor for a single source.
2. Each **additional** agreeing independent source closes half the remaining gap to the ceiling:

   ```
   confidence = best + (0.99 - best) * (1 - 0.5 ^ (n - 1))
   ```

   where `n` is the number of agreeing sources.
3. Each **disagreeing** source multiplies confidence by `0.70` (the dissent penalty).
4. Clamp to `[0.0, 0.99]`.

The ceiling is **0.99, never 1.0** — no finite evidence set justifies absolute certainty. Per the output contract, a verdict below **0.5** is flagged inconclusive.

---

## Worked examples

| Evidence | Result | Reading |
|---|---|---|
| 1 secondary source | **0.70** | A single scanner finding, no corroboration |
| 2 secondary sources | **0.84** | Scanner finding corroborated by a threat-model mapping |
| 1 primary source | **0.90** | The actual artifact, fetched live via MCP |
| 1 primary + 2 secondary | **0.97** | Live artifact plus two corroborating tools |
| 1 tertiary + 1 disagreeing | **0.35** | A weak signal contradicted by another source |
| only disagreeing sources | **0.00** | Nothing supports the verdict |

Reproduce any row:

```bash
python3 shared/scripts/confidence_rubric.py --secondary 2
# confidence: 0.84
# rationale : 2 agreeing source(s) (best tier=secondary, w=0.70); corroboration lift over 1 extra source(s) => confidence 0.84.
```

---

## How skills use it

A skill classifies each of its evidence sources into a tier, then calls the rubric instead of hard-coding a heuristic:

```python
import sys; sys.path.insert(0, "shared/scripts")
from confidence_rubric import score_confidence

result = score_confidence([
    {"tier": "secondary"},                 # the scanner
    {"tier": "secondary"},                 # threat-model mapping (agrees)
])
payload["confidence"] = result["confidence"]     # 0.84
payload["rationale"] += " " + result["rationale"]  # audit trail
```

The `rationale` string it returns is meant to be appended to the payload's `rationale` field, so the confidence number always travels with its own justification.

---

## Relationship to the other reproducible scores

- **CVSS** — computed from the published vector by `shared/scripts/cvss_scorer.py`. The output contract cross-checks any `cvss_score` a payload claims against the vector in its evidence and rejects mismatches.
- **EPSS** — fetched from the FIRST feed by `shared/scripts/epss_scorer.py`; unreachable/unknown returns *qualitative*, never a fabricated number.
- **Confidence** — this rubric.

Together they enforce the thesis rule: *if a number can be computed, compute it; if it cannot, say "qualitative" — never fabricate.*
