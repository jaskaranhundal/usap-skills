# Polyglot sync scripts

USAP authors every skill once at the canonical path
`<domain>/<slug>/SKILL.md`. These scripts mirror that tree into the
directories each non-Claude agent runtime expects, so the **same source
of truth** powers Claude Code, OpenAI Codex CLI, Google Gemini CLI,
Cursor, Windsurf, and Aider.

## What gets generated

For each target platform we materialise a flat folder of relative
symlinks plus a JSON index:

| Target | Mirror directory      | Index                          | Used by            |
| ------ | --------------------- | ------------------------------ | ------------------ |
| Codex  | `.codex/skills/`      | `.codex/skills-index.json`     | OpenAI Codex CLI   |
| Gemini | `.gemini/skills/`     | `.gemini/skills-index.json`    | Google Gemini CLI  |
| Cursor | `.cursor/skills/`     | `.cursor/skills-index.json`    | Cursor agent rules |
| Windsurf | `.windsurf/skills/` | `.windsurf/skills-index.json`  | Windsurf Cascade   |
| Aider  | `.aider/skills/`      | `.aider/skills-index.json`     | Aider `/read`      |

Every `<target>/skills/<slug>.md` is a **relative symlink** pointing back
to `../../<domain>/<slug>/SKILL.md`. There is no copy — editing the
canonical file updates every platform mirror immediately, and `git`
tracks one byte (the symlink) per platform instead of 79 duplicated
files.

The companion `<target>/skills-index.json` carries
`{version, generated_at_utc, skills: [{slug, domain, name, description, path, target_path}]}`
so a runtime can enumerate skills without walking the tree.

## How to run

```bash
# Refresh every target.
python3 scripts/sync_all.py

# Only one platform.
python3 scripts/sync_codex_skills.py

# Drift gate (CI-friendly: exit 1 if anything would change).
python3 scripts/sync_all.py --check

# Hard rewrite (drops every existing *.md symlink before recreating).
python3 scripts/sync_all.py --clean
```

All scripts are **stdlib only** and reuse
`tools/validate_skill.parse_frontmatter` so the frontmatter rules stay
in one place. The shared walker lives in `scripts/_sync_lib.py`; each
per-platform script is a thin CLI wrapper around it.

## Why symlinks back to the canonical path

* One source of truth — Anthropic's claude-skills pattern.
* Zero drift: there is no per-platform copy to forget to update.
* Cheap CI: `--check` only verifies symlink targets and the index, so
  the gate runs in milliseconds.
* Platform-agnostic markdown: every consumer reads the exact same
  bytes Claude Code reads, including frontmatter.
