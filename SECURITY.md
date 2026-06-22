# Security Policy

USAP is a library of LLM system prompts and stdlib Python tools. The threat surface this policy covers is:

1. **The skill code itself** — `*_tool.py` scripts, shared utilities under `shared/scripts/`, and the validator/extractor tooling under `tools/`.
2. **The prompt content** — `SKILL.md` and `agents/**/cs-*.md` files. A prompt-injection vulnerability in a skill is in scope (e.g. a skill that, when fed crafted input, breaks its own intent-classification logic in a way that would mislead a downstream agent or operator).
3. **The output contract** — any payload that fails to honor `human_approval_required` on a mutating intent, or that leaks data outside the documented 11 fields, is a security bug.

## Reporting a vulnerability

Send a report to **jaskarn.singh@lindera.de** with subject prefix `[USAP-SEC]`. Use any of:

- A minimal reproducer (input file + expected vs. actual output).
- A patch as a private fork link.
- A signed PGP message if you prefer; key available on request.

**Please do not file vulnerability reports as public GitHub issues.** Use the email address above and we will track the issue privately until a fix lands.

If your report is in scope, you will receive:

- An acknowledgment within **3 business days**.
- A triage assessment within **7 business days** (accepted / needs-more-info / out-of-scope, with reasoning).
- A fix or formal "won't-fix" decision within **30 days** for High-severity reports, **90 days** for Medium/Low.

Credit is attached to the merged fix unless you ask to remain anonymous.

## Out of scope

- Vulnerabilities in upstream LLMs (Claude, GPT, Gemini, etc.) — report those to the model vendor.
- Vulnerabilities in user-installed adapters (AnythingLLM, mcp servers, etc.) — report to that project.
- General threat-model improvements without a concrete reproducer.
- Findings that depend on the operator deliberately ignoring `human_approval_required: true`.

## Self-audit

USAP eats its own dog food. Every commit to `main` runs the validators shipped in `tools/` against the entire skill tree via `.github/workflows/validate-skills.yml`. The current state of that audit is recorded in [`SELF-AUDIT.md`](SELF-AUDIT.md). Failures are tracked openly — gaps are disclosed, not hidden.

## Supported versions

USAP is pre-1.0 and currently lives on a rolling-release model. Security fixes ship on `main`. There is no separate LTS branch yet; this section will be revised at the v1.0.0 cut.
