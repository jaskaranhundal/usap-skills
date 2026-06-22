# Self-audit

USAP runs its own validators against its own tree. This file records the live result as of the date below. Failures are reported as-is, never hidden.

**Date:** 2026-06-22
**Branch under audit:** `dev` (post-cascade)

| Check | Tool | Scope | Result |
|---|---|---|---|
| Canonical frontmatter conformance | `tools/validate_skill.py --all` | 79 active-domain `SKILL.md` files | **79 PASS / 0 FAIL / 0 WARN** |
| Invocation-control invariants (L1-L4) | `tools/validate_invocation_control.py --all --strict` | 79 active-domain `SKILL.md` files | **79 OK / 0 WARN / 0 FAIL** |
| Python syntax across every tool script | `python3 -m py_compile` | 77 `*_tool.py` scripts + 2 `shared/scripts/*.py` | **0 failures** |
| 11-field output-contract conformance | `tools/output_contract.py` | 79 committed `expected_outputs/sample_output.json` files | **79 PASS / 0 FAIL** |
| Framework-mapping drift | `tools/framework_extractor.py --check` | `mappings/mitre-attack/*.{json,md}`, `mappings/nist-csf/*.md` | **OK — no drift** |
| Sample-generator drift | `tools/regen_samples.py --check` | 79 committed samples | **OK — no drift** |

## What changed since the previous audit

The previous run (2026-06-22 morning) reported **18 PASS / 59 FAIL** on the output-contract sweep. The 59 failures were stubs left over from the original 71-skill seed — two- or three-field placeholder JSON containing only `agent_slug`, `status`, and `notes`.

This audit closes that gap:

- `tools/regen_samples.py` was added. It reads each skill's `SKILL.md` frontmatter (`metadata.frameworks.*`) plus the Persona and Overview prose, derives `intent_type` and `severity` from the slug, and emits a contract-conformant 11-field payload. The output is deterministic per skill; running the generator twice produces byte-identical JSON.
- The generator preserves hand-authored faithful samples (such as `appsec-devsecops/vuln-scan/expected_outputs/sample_output.json` and `appsec-devsecops/threat-model/expected_outputs/sample_output.json`) by skipping any existing sample that already passes the contract.
- `.github/workflows/validate-skills.yml` was upgraded to:
  - Run `tools/output_contract.py` against **every** committed sample, blocking on any failure (previously `continue-on-error: true` and only checking changed samples).
  - Run `tools/regen_samples.py --check` to fail the build if the generator would produce a different payload than what is committed for any skill whose sample was generated (drift detection).

The generator-emitted samples are explicit baselines, not synthesized analyses. The `rationale` field in each generated payload states: *"Representative output for the {skill} skill. … This payload is a contract-conformant baseline emitted by the sample generator; a live run would substitute real findings derived from the operator-supplied input package."* This keeps the contract gate honest while not pretending the skill has analyzed any specific input.

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

# 4. Output-contract sweep across every committed sample
find appsec-devsecops cloud-infra detection governance identity-access \
     pentest platform-ai red-team response risk-compliance system-security \
     webapp-security -name sample_output.json -path '*/expected_outputs/*' \
     -exec python3 tools/output_contract.py {} \;

# 5. Generator drift check
python3 tools/regen_samples.py --check

# 6. Framework-mapping drift check
python3 tools/framework_extractor.py --check
```

## Why this file exists

A security-tooling repo whose marketing claims sit downstream of "we have a typed 11-field contract" needs to be able to prove it on its own tree. Every check in the table above runs on every PR and every push to `main` via [`.github/workflows/validate-skills.yml`](.github/workflows/validate-skills.yml). The CI gate is the canonical source of truth; this file is a human-readable snapshot for anyone evaluating the project.
