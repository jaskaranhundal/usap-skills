# webapp-risk-triage

First-pass triage for webapp security findings. Classifies the finding, scores severity, scopes blast radius, and routes to the right downstream USAP skill.

```bash
# Triage the bundled sample finding
python3 scripts/webapp-risk-triage_tool.py --output json

# Triage a real finding payload
python3 scripts/webapp-risk-triage_tool.py --input my-finding.json --output json

# Human-readable summary
python3 scripts/webapp-risk-triage_tool.py --output human
```

Output conforms to USAP's 11-field contract — see `standards/output-contract.md`. Full methodology in [`SKILL.md`](SKILL.md).
