---
name: Bug report
about: Something USAP did wrong — a validator misfire, a skill that returned a non-conformant payload, a tool script that errored, a doc that's stale.
title: "bug: "
labels: bug
assignees: ''
---

## What happened

A clear, one-paragraph description of the bug.

## What you expected to happen

A clear, one-paragraph description of the expected behaviour.

## How to reproduce it

```bash
# the exact commands you ran
```

If the bug involves an LLM response, include:
- Which LLM and version (Claude 4.7 Opus, GPT-5, etc.)
- The skill you ran (path to its `SKILL.md`)
- The input you fed it (paste verbatim or attach as a file)
- The output you got (paste verbatim)

## Where the bug lives

If you've already isolated it, link the file and line:
- `path/to/file.py:42`
- or the skill: `<domain>/<slug>/`

## USAP version / commit

```bash
git rev-parse HEAD
```

## Environment

- OS: <macOS 14.5 / Ubuntu 24.04 / Windows 11 / etc>
- Python: <python3 --version>
- USAP runner: <Claude Code / AnythingLLM / paste-into-LLM / your own>

## Anything else

Logs, screenshots, related issues.
