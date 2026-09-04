# persona-coverage-audit

Measures whether sessions that changed security-relevant files (CI, IaC, hooks, settings, credentials) carried a recorded USAP persona pass. Read-only, L2, governance domain.

## Why

The persona gate in `plugins/usap/hooks/` blocks gated writes until a design-review pass is recorded. Its accepted residual risk is that the gate exists only where the plugin is loaded. This skill makes both the coverage and that bypass measurable every week.

## Run

```bash
# CI fixture
python3 scripts/persona-coverage-audit_tool.py --input ../../tests/fixtures/persona-coverage-audit/input.json --output json

# Live, last 7 days
python3 scripts/persona-coverage-audit_tool.py --audit-dir ~/.usap/audit --transcripts-dir ~/.claude/projects --since-days 7
```

Exit codes: `0` every gated session covered or nothing gated; `1` some uncovered; `2` gated sessions with zero passes.

## Privacy

The transcript collector reads JSON keys only: session id, timestamp, tool names, file paths of write tools. Message content never reaches memory that is output.

## Files

- `SKILL.md` — persona, classification table, reasoning procedure
- `scripts/persona-coverage-audit_tool.py` — collector and analyser
- `references/workflow.md` — weekly procedure
- `assets/templates/output-template.json` — payload shape
- `expected_outputs/sample_output.json` — recorded output of the fixture run
