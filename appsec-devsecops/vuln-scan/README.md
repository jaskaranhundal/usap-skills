# vuln-scan

Runs threat-model-scoped static analysis against a target tree. Reads `<target>/THREAT_MODEL.md`, emits `<target>/VULN-FINDINGS.json` plus the contract payload.

```bash
python3 scripts/vuln-scan_tool.py --output json
python3 scripts/vuln-scan_tool.py --input target.json --output json
python3 scripts/vuln-scan_tool.py --output human
```

Full methodology in [`SKILL.md`](SKILL.md).
