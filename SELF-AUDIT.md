# Self-audit

USAP runs its own validators against its own tree. This file records the live result as of the date below. Failures are reported as-is, never hidden.

**Date:** 2026-09-04
**Branch under audit:** `fix/counts-and-versions` (branched from `main` @ 7f0f7c7)

| Check | Tool | Scope | Result |
|---|---|---|---|
| Canonical frontmatter conformance | `tools/validate_skill.py --all` | 80 active-domain `SKILL.md` files | **80 PASS / 0 FAIL / 0 WARN** |
| Invocation-control invariants (L1-L4) | `tools/validate_invocation_control.py --all --strict` | 80 active-domain `SKILL.md` files | **80 OK / 0 WARN / 0 FAIL** |
| Python syntax across every tool script | `python3 -m py_compile` | 78 `*_tool.py` scripts + `shared/scripts/*.py` | **0 failures** |
| 11-field output-contract conformance (structural) | `tools/output_contract.py --structural-only` | 80 committed `expected_outputs/sample_output.json` files | **80 PASS / 0 FAIL** |
| Framework-mapping drift | `tools/framework_extractor.py --check` | `mappings/mitre-attack/*.{json,md}`, `mappings/nist-csf/*.md` | **OK — no drift** |
| Sample-generator drift | `tools/regen_samples.py --check` | 80 committed samples | **OK — no drift** |
| Executable-tool census | `grep -rl not_implemented --include='*_tool.py' <12 domains>` | 78 `*_tool.py` scripts | **12 implemented / 66 declared stubs** |

## What the census row means

A stub tool exits non-zero with `status: not_implemented`, confidence `0.0`, and an `action` string saying it did not read `--input`. That is the honest state of 66 scripts today. The 12 implemented tools are `appsec-customize`, `finding-triage`, `patch-candidate`, `security-requirements-review`, `threat-model`, `vuln-scan`, `container-image-scan`, `security-debt-tracker`, `security-roadmap-planner`, `api-security-posture`, `owasp-top10-classifier` and `webapp-risk-triage`. The row exists so that the skill count on the README can never again be read as an executable-tool count. Progress is tracked in [issue #138](https://github.com/jaskaranhundal/usap-skills/issues/138).

## What changed since the previous audit

The previous run (2026-06-22) reported 79 skills. The tree held 80: `cloud-infra/container-image-scan` was added after that audit and never counted. Every other check is unchanged in outcome; the contract sweep now runs in `--structural-only` mode, matching the CI gate, while the hardest-line evidence gate is reported non-blocking in CI during the connector-agnostic rollout.

The generator-emitted samples remain explicit baselines, not synthesized analyses. The `rationale` field in each generated payload states that a live run would substitute real findings derived from the operator-supplied input package.

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
