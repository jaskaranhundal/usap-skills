# NIST CSF 2.0 alignment

Auto-generated from `metadata.frameworks.nist_csf` arrays across every active-domain `SKILL.md`. Do not edit by hand.

## File

`csf-alignment.md` — per-subcategory skill counts plus per-function citation totals across the six NIST CSF 2.0 functions:

- **GV** Govern
- **ID** Identify
- **PR** Protect
- **DE** Detect
- **RS** Respond
- **RC** Recover

## Regenerate

```bash
python3 tools/framework_extractor.py --emit coverage   # writes this file + the ATT&CK summary
python3 tools/framework_extractor.py --emit all
python3 tools/framework_extractor.py --check           # fail on drift (used in CI)
```

## Adding CSF coverage to a skill

Edit the skill's `SKILL.md` frontmatter and add the optional `metadata.frameworks` block:

```yaml
metadata:
  frameworks:
    nist_csf: [DE.CM-01, DE.AE-02, ID.RA-05]
```

Cap is **8 IDs per framework per skill**. Pattern is `[A-Z]{2}\.[A-Z]{2}-\d{2}`. The validator rejects malformed IDs.

After editing, regenerate the artifacts with `python3 tools/framework_extractor.py --emit all` and commit alongside your skill change.
