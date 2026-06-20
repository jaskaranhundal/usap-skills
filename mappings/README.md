# Framework coverage mappings

This tree is **fully auto-generated** from `metadata.frameworks.*` arrays in every active-domain `SKILL.md`. The source of truth lives in the skill frontmatter; the artifacts under each subdirectory are derived.

Do not hand-edit anything in `mappings/` except this README and the per-subdirectory `README.md` files. CI regenerates the artifacts on every PR and fails the build if a committed file drifts from the source-of-truth frontmatter (see `.github/workflows/validate-skills.yml`).

## Layout

| Path | Purpose |
|---|---|
| `mitre-attack/attack-navigator-layer.json` | MITRE ATT&CK Navigator v4.5 layer. Load directly into <https://mitre-attack.github.io/attack-navigator/>. |
| `mitre-attack/coverage-summary.md` | Per-technique skill counts plus per-domain technique tallies. |
| `nist-csf/csf-alignment.md` | Per-subcategory skill counts plus per-function citation totals. |

## Regenerating

```bash
python3 tools/framework_extractor.py --emit all       # write every artifact
python3 tools/framework_extractor.py --emit navigator # ATT&CK Navigator only
python3 tools/framework_extractor.py --emit coverage  # the two coverage .md files
python3 tools/framework_extractor.py --check          # CI drift gate
```

The extractor is stdlib-only Python. No dependency install. Run from the repo root.

## Adding a new framework

1. Update the `metadata.frameworks` section of `standards/frontmatter-spec.md` with the new key and its ID pattern.
2. Add the same key to `FRAMEWORK_PATTERNS` in `tools/validate_skill.py`.
3. Add an emitter under `tools/framework_extractor.py` and a new sub-directory under `mappings/` for the generated artifact(s).
4. Run `python3 tools/framework_extractor.py --emit all`, commit, and push.
