---
name: Propose a new skill
about: You've shipped a security workflow at work and want it to become a USAP skill. Use this — it's strictly scoped.
title: "skill: "
labels: new-skill, enhancement
assignees: ''
---

## The workflow you've shipped

One paragraph. What does an analyst / engineer actually do today, end-to-end, that you'd like to encode as a USAP skill? Be specific about inputs (a Splunk search? an EDR event? a Terraform plan?) and outputs (a CVSS-tagged finding? a Jira ticket draft? a containment recommendation?).

## Where it fits

| | |
|---|---|
| Proposed slug (kebab-case, ≤4 words) | `<slug>` |
| Domain | one of: `appsec-devsecops`, `cloud-infra`, `detection`, `governance`, `identity-access`, `pentest`, `platform-ai`, `red-team`, `response`, `risk-compliance`, `system-security`, `webapp-security` |
| Intent type | one of: `detect`, `respond`, `analyze`, `advise`, `escalate`, `report`, `block` |
| Autonomy level | L1 (advisory) / L2 (CISO-grade) / L3 (SOC read-only) / L4 (mutating, gated) |
| Mutates anything? | yes / no — if yes, list the mutating action (e.g. "recommends key rotation") |

## Persona this skill represents

Who does this work today? Job title, years of experience, primary environment. (Drives the SKILL.md "Persona" section.)

## Decision tables

What are the 1–3 explicit decision tables the skill needs? E.g. "Severity by exposure level", "Action by detection age", "Routing by classification." A skill without at least one decision table is a prompt, not a skill — please don't propose those.

## MITRE / framework mappings

Which ATT&CK technique IDs apply? NIST CSF 2.0 subcategories? OWASP Top 10 categories? List what you'd put in `metadata.frameworks.*`.

## What "done" looks like

The skill is mergeable when it ships:

- [ ] `<domain>/<slug>/SKILL.md` with full frontmatter, Persona, Overview, ≥1 decision table, intent-classification rule.
- [ ] `<domain>/<slug>/scripts/<slug>_tool.py` emitting a contract-compliant 11-field payload.
- [ ] `<domain>/<slug>/expected_outputs/sample_output.json` that passes `tools/output_contract.py`.
- [ ] `<domain>/<slug>/references/workflow.md` with the procedure.
- [ ] `<domain>/<slug>/assets/templates/output-template.json` + `<domain>/<slug>/README.md`.
- [ ] `metadata.frameworks.*` arrays populated.

## Anything else

Sample inputs, sample outputs, references to public sources (NIST docs, MITRE pages, etc.) that the skill body should cite.
