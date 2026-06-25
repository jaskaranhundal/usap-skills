---
description: Before/after comparison of zero-day-response SKILL.md v1 (broken) vs v2 (fixed) against the FortiGate zero-day scenario. Outputs a scored table.
---

You are running a before/after comparison for `zero-day-response`.

---

## Phase 1 — v1 Baseline (pre-fix)

1. Read `tests/fixtures/zero-day-response-v1.md` in full.
2. Read `tests/scenarios/fortigate-zero-day.json` in full.
3. Apply the scenario using **only v1's reasoning procedure** — do not import knowledge from v2.
4. Produce abbreviated output covering only the sections relevant to the 6 known problems:
   - How actions are expressed (intent blocks vs raw CLI)
   - AWS lateral movement attack path
   - Okta session theft handling
   - Logging change recommendations
   - Immediate traffic control options
   - Any vendor-specific syntax used
5. For each of the 6 problems, identify and quote the specific v1 text that demonstrates the failure (or note its absence).

---

## Phase 2 — v2 Fixed (current)

6. Read `response/zero-day-response/SKILL.md` in full.
7. Apply the same FortiGate scenario using v2's reasoning procedure.
8. Produce equivalent abbreviated output sections for direct comparison with Phase 1.
9. For each of the 6 problems, quote the specific v2 text that demonstrates the fix.

---

## Phase 3 — Scorecard Table

Output the following comparison table:

```
Before/After Scorecard — zero-day-response
==========================================

| Problem                              | v1 (pre-fix)  | v2 (fixed)    |
|--------------------------------------|---------------|---------------|
| P1: Raw CLI commands in output       | FAIL          | PASS          |
| P2: AWS IAM prerequisite missing     | FAIL          | PASS          |
| P3: Okta theft without TLS check     | FAIL          | PASS          |
| P4: No logging pre-flight            | FAIL          | PASS          |
| P5: No immediate traffic controls    | FAIL          | PASS          |
| P6: Incorrect vendor syntax          | FAIL          | PASS          |
|--------------------------------------|---------------|---------------|
| TOTAL                                | 0/6           | 6/6           |
```

For each row, add a sub-line:
- v1 evidence: `"<quote from Phase 1 output showing the failure>"`
- v2 evidence: `"<quote from Phase 2 output showing the fix>"`

---

## Summary

Conclude with a one-paragraph plain-English summary of what changed between v1 and v2 and why each fix matters operationally.
