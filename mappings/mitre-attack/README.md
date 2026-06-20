# MITRE ATT&CK coverage

Auto-generated from `metadata.frameworks.mitre_attack` arrays across every active-domain `SKILL.md`. Do not edit by hand.

## Files

| File | Source | Use |
|---|---|---|
| `attack-navigator-layer.json` | Navigator v4.5 layer | Load in <https://mitre-attack.github.io/attack-navigator/> to see per-technique skill counts. |
| `coverage-summary.md` | Per-technique markdown table | Read directly on GitHub. Shows which skills cover each technique and how many techniques each domain cites. |

## Regenerate

```bash
python3 tools/framework_extractor.py --emit navigator   # only the JSON
python3 tools/framework_extractor.py --emit coverage    # only the .md
python3 tools/framework_extractor.py --emit all         # both, plus NIST CSF
python3 tools/framework_extractor.py --check            # fail on drift (used in CI)
```

## Adding ATT&CK coverage to a skill

Edit the skill's `SKILL.md` frontmatter and add the optional `metadata.frameworks` block:

```yaml
metadata:
  frameworks:
    mitre_attack: [T1078, T1059.001, T1083]
```

Cap is **8 IDs per framework per skill**. Pattern is `T\d{4}(\.\d{3})?`. The validator (`python3 tools/validate_skill.py --all`) rejects malformed IDs.

After editing, regenerate the artifacts with `python3 tools/framework_extractor.py --emit all` and commit the regenerated files alongside your skill change.
