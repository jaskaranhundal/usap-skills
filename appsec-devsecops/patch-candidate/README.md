# patch-candidate

**L4 mutating-action skill.** Generates candidate patches for confirmed AppSec findings. Never auto-applies — human approval required on every output. Reads `<target>/TRIAGE.md`, emits per-finding `.patch` files and `<target>/PATCH-CANDIDATES.md`.

```bash
python3 scripts/patch-candidate_tool.py --output json
python3 scripts/patch-candidate_tool.py --input target.json --output json
python3 scripts/patch-candidate_tool.py --output human
```

`disable-model-invocation: true` — only humans can invoke this skill via Claude Code's slash command. Full methodology in [`SKILL.md`](SKILL.md).
