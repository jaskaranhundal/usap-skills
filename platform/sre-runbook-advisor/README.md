# SRE Runbook Advisor

Generate incident runbooks, analyze SLO burn rates, and facilitate blameless postmortems.

## When to use

- On-call alert fires and you need a structured runbook
- SLO burn rate is elevated and you need diagnosis guidance
- Facilitating a postmortem after a production incident
- Building runbook templates for common failure modes

## Quick Start

```bash
python scripts/sre-runbook-advisor_tool.py --help
python scripts/sre-runbook-advisor_tool.py --output json
python scripts/sre-runbook-advisor_tool.py --error-rate 0.05 --slo-target 0.999 --output json
```

## Skill Level: L3

Produces advisory runbooks and postmortem structures. No mutating actions.
