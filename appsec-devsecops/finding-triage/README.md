# finding-triage

Triages AppSec findings from `vuln-scan`. Verifies, dedupes, ranks. Emits `<target>/TRIAGE.md` plus the contract payload.

```bash
python3 scripts/finding-triage_tool.py --output json
python3 scripts/finding-triage_tool.py --input target.json --output json
python3 scripts/finding-triage_tool.py --output human
```

Full methodology in [`SKILL.md`](SKILL.md).
