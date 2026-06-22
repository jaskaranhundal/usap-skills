---
name: Feature request
about: A change to an existing skill or cs-* agent, a tooling improvement, or a doc / process change. Use the new_skill template if you're proposing a whole new SKILL.md.
title: "feat: "
labels: enhancement
assignees: ''
---

## What you want

One paragraph. The shape of the change, not the implementation.

## Why this is worth doing

What's wrong with the status quo? What does the change unlock? Be concrete — "would help" doesn't pass, "lets cs-incident-responder cite the live IOC at containment-decision time" does.

## What "done" looks like

A bullet list of acceptance criteria that a reviewer can check. Example:

- [ ] `<domain>/<slug>/SKILL.md` has a new decision table for X.
- [ ] `<domain>/<slug>/scripts/<slug>_tool.py` accepts a new `--mode=Y` flag.
- [ ] CI still passes.
- [ ] A test fixture under `expected_outputs/` exercises the new path.

## Scope notes

- Does this require a change to `standards/output-contract.md`?
- Does this change the L1–L4 level of any skill?
- Does it introduce a new dependency? (USAP is stdlib-only — non-stdlib deps are case-by-case and need explicit discussion.)

## Alternatives considered

If you considered other shapes and rejected them, say which and why. This shortens the review.
