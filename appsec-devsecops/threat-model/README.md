# threat-model

Builds a STRIDE+DREAD threat model from a target spec. Entry point of USAP's AppSec chain (`threat-model` → `vuln-scan` → `finding-triage` → `patch-candidate`).

```bash
python3 scripts/threat-model_tool.py --output json
python3 scripts/threat-model_tool.py --input target.json --output json
python3 scripts/threat-model_tool.py --output human
```

Output conforms to USAP's 11-field contract. Full methodology in [`SKILL.md`](SKILL.md).
