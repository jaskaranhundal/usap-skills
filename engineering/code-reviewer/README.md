# Code Reviewer

PR review assistant covering architecture, performance, security patterns, and test coverage.

## When to use

- Reviewing a pull request for overall code quality
- Identifying performance anti-patterns before they reach production
- Assessing test coverage adequacy for new features
- Getting structured, prioritized review feedback

## Quick Start

```bash
python scripts/code-reviewer_tool.py --help
python scripts/code-reviewer_tool.py --output json
```

## Skill Level: L4

Produces structured review decisions (approve, request_changes, approve_with_comments) with prioritized findings.

## Related Skills

- `appsec-code-review` — security-specific review (runs in parallel)
- `architecture-advisor` — deep architectural guidance for design decisions
