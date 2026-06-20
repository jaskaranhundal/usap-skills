# api-security-posture

Static posture scoring of an API surface against OWASP API Security Top 10. Outputs a 100-point scorecard plus the single highest-leverage downstream USAP skill.

```bash
python3 scripts/api-security-posture_tool.py --output json
python3 scripts/api-security-posture_tool.py --input my-api.json --output json
python3 scripts/api-security-posture_tool.py --output human
```

Full scoring rubric in [`SKILL.md`](SKILL.md).
