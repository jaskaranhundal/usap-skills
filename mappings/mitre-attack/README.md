# MITRE ATT&CK coverage

Auto-generated from `metadata.frameworks.mitre_attack` arrays across every active-domain `SKILL.md`. Do not edit by hand.

## Files

| File | Source | Use |
|---|---|---|
| `attack-navigator-layer.json` | Navigator v4.5 layer | Load in <https://mitre-attack.github.io/attack-navigator/> to see per-technique skill counts. |
| `ATTACK_COVERAGE.md` | Per-tactic kill-chain rollup | Read directly on GitHub. Reconnaissance through Impact, each tactic with an ASCII bar (covered / MITRE v16 total) and a table of T-IDs with covering skills. |
| `coverage-summary.md` | Per-technique markdown table | Read directly on GitHub. Shows which skills cover each technique and how many techniques each domain cites. |

## Regenerate

```bash
python3 tools/framework_extractor.py --emit navigator   # only the JSON
python3 tools/framework_extractor.py --emit coverage    # only the .md
python3 tools/framework_extractor.py --emit all         # both, plus NIST CSF
python3 tools/framework_extractor.py --check            # fail on drift (used in CI)
```

## How to view the Navigator layer

1. Open <https://mitre-attack.github.io/attack-navigator/>.
2. Choose `Open Existing Layer` -> `Upload from local`.
3. Select `mappings/mitre-attack/attack-navigator-layer.json` from your local checkout.
4. The heat map renders with each technique scored by the number of USAP skills that reference it (red = single skill, green = many skills).

To share a live URL instead, host the JSON anywhere reachable and pass the raw URL via the Navigator's `Load Layer from URL` option.

## Adding ATT&CK coverage to a skill

Edit the skill's `SKILL.md` frontmatter and add the optional `metadata.frameworks` block:

```yaml
metadata:
  frameworks:
    mitre_attack: [T1078, T1059.001, T1083]
```

Cap is **8 IDs per framework per skill**. Pattern is `T\d{4}(\.\d{3})?`. The validator (`python3 tools/validate_skill.py --all`) rejects malformed IDs.

The extractor also scavenges T-IDs from each SKILL.md body, so techniques you reference in prose count even before you backfill the frontmatter array.

After editing, regenerate the artifacts with `python3 tools/framework_extractor.py --emit all` and commit the regenerated files alongside your skill change.
