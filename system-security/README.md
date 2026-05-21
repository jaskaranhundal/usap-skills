# System Security Domain

Skills in the System Security domain assess and harden operating system and host configurations against CIS Benchmarks, DISA STIGs, and NSA hardening guides. They parse scanner output, classify configuration gaps by severity and MITRE ATT&CK technique, and produce prioritized remediation — without executing changes.

---

## Skills Index

| Skill | Description | Key Use Case |
|---|---|---|
| os-hardening | Assesses Linux/Windows/macOS configurations against CIS, STIG, and NSA baselines; classifies failed controls and produces prioritized remediation. | Golden-image hardening review, CIS drift assessment, audit evidence |

---

## Agent Links

The primary orchestrator for this domain is the [cs-blue-team-analyst](../agents/security/cs-blue-team-analyst.md) agent, which incorporates host-hardening findings into blue-team detection and response workflows.

---

## Quick Commands

Run any skill tool directly from the repository root. All tools accept `--help` and `--output json`.

**os-hardening**
```bash
python system-security/os-hardening/scripts/os-hardening_tool.py --help
python system-security/os-hardening/scripts/os-hardening_tool.py --output json
```

---

## Full Domain Guide

For complete methodology, MITRE ATT&CK coverage, Python tools reference, and domain best practices, see [CLAUDE.md](./CLAUDE.md).
