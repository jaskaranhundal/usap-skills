# Self-audit

USAP runs its own validators against its own tree. This file records the live result as of the date below. Failures are reported as-is, never hidden.

**Date:** 2026-06-22
**Branch under audit:** `chore/security-md-and-self-audit` off `dev` (immediately ahead of the live `dev` tree)

| Check | Tool | Scope | Result |
|---|---|---|---|
| Canonical frontmatter conformance | `tools/validate_skill.py --all` | 79 active-domain `SKILL.md` files | **79 PASS / 0 FAIL / 0 WARN** |
| Invocation-control invariants (L1-L4) | `tools/validate_invocation_control.py --all --strict` | 79 active-domain `SKILL.md` files | **79 OK / 0 WARN / 0 FAIL** |
| Python syntax across every tool script | `python3 -m py_compile` | 77 `*_tool.py` scripts + 2 `shared/scripts/*.py` | **0 failures** |
| 11-field output-contract conformance | `tools/output_contract.py` | 77 committed `expected_outputs/sample_output.json` files | **18 PASS / 59 FAIL** |

## What the contract failures actually mean

The 59 failing samples are stubs left over from the original 71-skill seed: two- or three-field placeholder JSON containing only `agent_slug`, `status`, and `notes`. They predate the v1 output contract and were never backfilled. The new skills built since (the AppSec chain, the three `webapp-security/` skills, the new `cs-*` orchestrator-paired skills) emit the full 11-field payload from day one.

The contract validator is *not* yet wired into the blocking CI gate. If it were, those 59 stubs would have failed the build long before this audit ran. The gap is honest and known:

- `tools/output_contract.py` is implemented and ships in the tree.
- `.github/workflows/validate-skills.yml` does not currently invoke it against the committed samples.
- Backfilling the 59 stubs is tracked as an outstanding cleanup, not a release blocker.

A future PR will (a) regenerate the 59 stub samples by actually running each `_tool.py --output json` and capturing the live payload, then (b) extend the CI gate to fail on any committed sample that does not pass `tools/output_contract.py`. This SELF-AUDIT.md will then show all four rows at full PASS.

## How to reproduce this audit locally

```bash
# 1. Canonical frontmatter
python3 tools/validate_skill.py --all

# 2. Invocation-control invariants — strict mode = WARNs become errors
python3 tools/validate_invocation_control.py --all --strict

# 3. Python syntax check
find appsec-devsecops cloud-infra detection governance identity-access \
     pentest platform-ai red-team response risk-compliance system-security \
     webapp-security -name '*_tool.py' -exec python3 -m py_compile {} \;

# 4. Output-contract sweep
for f in $(find . -path ./references -prune -o -name "sample_output.json" -print | grep expected_outputs); do
  python3 tools/output_contract.py "$f"
done
```

## Why this file exists

A security-tooling repo whose marketing claims sit downstream of "we have a typed 11-field contract" needs to be able to *prove* it on its own tree. The CI workflow proves it for the validators that are wired in; this file fills the gap for the ones that are not yet wired and surfaces the count honestly. Quality over hype.
