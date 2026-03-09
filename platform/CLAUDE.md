# Platform Operations Domain — CLAUDE.md

This file is the authoritative domain guide for the `platform/` directory. It governs how Claude and cs-* agents understand, navigate, and apply the skills in this domain.

---

## Purpose

The Platform Operations domain provides structured operational guidance for maintaining the availability, reliability, and correctness of production systems under incident and degraded conditions. The domain currently contains one skill — sre-runbook-advisor — which focuses on the intersection of site reliability engineering practice and security-aware incident response.

The sre-runbook-advisor skill exists to address a gap that exists in most organizations: SRE runbooks are written by engineers optimizing for availability, but they are executed during incidents when security considerations (evidence preservation, change authorization, blast radius containment) are often deprioritized under time pressure. This skill applies security review reasoning to runbook design, execution guidance, and post-incident validation.

Core coverage area:

- **SRE Runbook Guidance** — Reviewing runbooks for security completeness, advising on security-aware execution sequences during incidents, and producing post-incident runbook improvement recommendations that harden the runbook against future security lapses under operational pressure.

The primary orchestrating agent for this domain is cs-security-analyst when an active incident is in progress, and cs-ciso-advisor when the request is a program-level review of runbook security maturity across the fleet.

---

## Skills Catalog

| Skill | Slug | Primary Tool | Coverage |
|---|---|---|---|
| sre-runbook-advisor | `platform/sre-runbook-advisor` | `sre-runbook-advisor_tool.py` | Runbook security review, incident execution guidance, post-incident improvement |

The skill directory follows the USAP Agent Skills Standard v1 layout:

```
sre-runbook-advisor/
├── SKILL.md
├── README.md
├── scripts/
│   └── sre-runbook-advisor_tool.py
├── references/
├── assets/
└── expected_outputs/
```

---

## Python Tools Reference

| Tool | Path | Key Flags | Output |
|---|---|---|---|
| `sre-runbook-advisor_tool.py` | `sre-runbook-advisor/scripts/` | `--runbook`, `--mode review\|execute\|improve`, `--incident-type`, `--output json` | Security gap findings, execution sequence with security checkpoints, improvement recommendations |

```bash
python platform/sre-runbook-advisor/scripts/sre-runbook-advisor_tool.py --help
python platform/sre-runbook-advisor/scripts/sre-runbook-advisor_tool.py \
  --runbook path/to/runbook.md --mode review --output json
python platform/sre-runbook-advisor/scripts/sre-runbook-advisor_tool.py \
  --runbook path/to/runbook.md --mode execute --incident-type database-failover --output json
```

---

## Domain Best Practices

1. **Security review runbooks before incidents, not during them.** A runbook that reaches an on-call engineer for the first time during a SEV1 incident is a runbook that has not been security reviewed. All production runbooks should be reviewed by sre-runbook-advisor in `--mode review` on a quarterly basis and after any significant infrastructure change that the runbook covers. Security gaps found during a review are addressable calmly; the same gaps found during an active incident create compounding risk.

2. **Runbook execution during incidents must preserve the evidence chain.** When an incident involves a suspected security component — unauthorized access, unusual traffic patterns, unexpected configuration changes — runbook execution steps must include explicit evidence preservation checkpoints before any remediation action that would modify system state. Remediating a compromised system before evidence is collected destroys forensic value. The sre-runbook-advisor in `--mode execute` inserts security-aware checkpoints into the execution sequence, including evidence preservation steps before destructive remediation actions.

3. **Every change made during incident execution must be authorization-logged.** Emergency access and break-glass procedures create audit trail gaps that are difficult to reconstruct post-incident. Runbooks executed during incidents should include an explicit step to log all changes made, by whom, and at what time, even if the logging is manual. The sre-runbook-advisor produces a structured change log template as part of every execute-mode output.

---

## Workflow: Runbook Security Review

```
Input: Runbook document (Markdown, Confluence export, or structured YAML)

Step 1 — Review Mode (sre-runbook-advisor)
  python platform/sre-runbook-advisor/scripts/sre-runbook-advisor_tool.py \
    --runbook <path> --mode review --output json

  Evaluated dimensions:
  - Evidence preservation steps present before destructive actions
  - Authorization requirements documented for privileged operations
  - Change logging steps included
  - Rollback procedure present and security-aware
  - Blast radius estimate for each major step

Step 2 — Finding Classification
  Critical gap --> Runbook blocked from production use; immediate remediation required
  High gap     --> Runbook conditionally approved; remediation within 30 days
  Medium gap   --> Tracked improvement; addressed in next quarterly review cycle

Step 3 — Post-Incident Improvement (after execution)
  python platform/sre-runbook-advisor/scripts/sre-runbook-advisor_tool.py \
    --runbook <path> --mode improve --output json
  Produces: Updated runbook with security checkpoints, change log template, and
            a structured improvement record for governance tracking
```

---

## Related Domains

| Domain | Directory | Relationship |
|---|---|---|
| Response | `response/` | Active incident execution coordinates with response/incident-commander; runbook advisor provides the security-aware execution layer on top of SRE procedures |
| Governance | `governance/` | Runbook security maturity feeds the security program governance cycle; critical runbook gaps route to governance/findings-tracker |
