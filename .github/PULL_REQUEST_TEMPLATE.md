<!-- Thanks for sending a PR. The checklist below is the same one CI checks; you don't need to write a long description if it's obvious from the diff. -->

## What this PR does

One paragraph.

## Why

What problem does this fix or what capability does this add? Link the issue if one exists (`Closes #N`).

## Affected surfaces

Tick everything that changed:

- [ ] Skills (`<domain>/<slug>/`)
- [ ] cs-* agents (`agents/<group>/cs-*.md`)
- [ ] Standards docs (`standards/`)
- [ ] Tools (`tools/`, `shared/scripts/`)
- [ ] Mappings (`mappings/`) — note: these are generated; do not hand-edit anything but the README.md files
- [ ] Docs site (`docs/`, `mkdocs.yml`)
- [ ] Design system (`docs/design-system/`)
- [ ] CI workflows (`.github/workflows/`)
- [ ] README / top-level docs

## Pre-merge checks (the CI gates run these; verify locally too)

- [ ] `python3 tools/validate_skill.py --all` — exits 0
- [ ] `python3 tools/validate_invocation_control.py --all --strict` — exits 0
- [ ] `python3 tools/regen_samples.py --check` — exits 0
- [ ] `python3 tools/framework_extractor.py --check` — exits 0
- [ ] `find <active-domain>/*/expected_outputs/sample_output.json -exec python3 tools/output_contract.py {} \;` — all pass
- [ ] If you added a new skill, the package is complete (`SKILL.md`, `README.md`, `references/workflow.md`, `assets/templates/output-template.json`, `expected_outputs/sample_output.json`, `scripts/<slug>_tool.py`)
- [ ] No new non-stdlib Python dependency (or if there is one, called out in the description with rationale)

## Anything reviewers should look at first

If the PR is large, point at the load-bearing file. "Start with `<path>:<line>`" is usually the right shape.
