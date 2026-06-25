---
description: Run the full 4-agent USAP orchestration chain (cs-security-analyst → cs-incident-responder → cs-ciso-advisor → cs-security-program-manager) against the Perfect Storm scenario. Shows inter-agent handoffs and per-agent mock comparison.
---

You are running the full USAP 4-agent orchestration chain against the Perfect Storm scenario.

Read `tests/scenarios/nation-state-apt-crisis.json` now — you will use it throughout.
Read `tests/mocks/orchestration-chain-mock.json` now — you will compare against it at the end.

Operate each agent in sequence. Each agent reads its own file, adopts its persona, applies its workflow, and produces output that the next agent consumes. Show a clear separator between each agent's section.

---

## Agent 1 of 4 — cs-security-analyst (AT Workflow)

Read `agents/security/cs-security-analyst.md` in full.

Adopt the **Alex persona** (Tier 2 SOC, 12y). Apply the AT (Alert Triage) workflow to the Perfect Storm scenario.

Produce abbreviated output focused on the handoff payload:
- Top-5 alert priority signals (ranked, DDoS noise suppressed)
- Kill chain stage mapping (6 stages, all 8 vectors assigned)
- Two threat actor entries (nation-state APT + ransomware gang, clearly differentiated)
- SEV-1 declaration
- Routing decision: `next_agents: ["cs-incident-responder", "cs-ciso-advisor"]` with justification
- Prerequisite checks: all 7 UNKNOWN fields as PREREQUISITE_UNVERIFIED
- Sequenced containment plan (ransomware → APT → insider → supply chain)
- Regulatory flags (GDPR 72h + SEC 4-day)
- `human_approval_required: true`

Show the **handoff payload** passed to Agent 2 (the fields cs-incident-responder will consume).

---

## Agent 2 of 4 — cs-incident-responder (CO Workflow)

Read `agents/security/cs-incident-responder.md` in full.

Adopt the **Jordan persona** (IR Lead, 14y). Consume the Agent 1 handoff payload as your incident input.

Apply the CO (Active Containment) workflow. Produce:
- Formal SEV-1 incident declaration with incident ID and timestamp
- SLA clock: detection-to-containment target, eradication target, recovery target
- Containment action intents in correct sequence (ransomware first — all as intent blocks, no CLI)
- Evidence preservation order: collect C2 artifacts from DC-002 BEFORE evicting APT implants
- Forensic collection plan for compromised hosts (intent blocks only)
- Inherited prerequisite checks — propagate all 7 UNKNOWN fields, do not resolve by assumption
- Rollback plan for each isolation action

Show the **handoff payload** passed to Agent 3 (the fields cs-ciso-advisor will consume).

---

## Agent 3 of 4 — cs-ciso-advisor (BR Workflow)

Read `agents/executive/cs-ciso-advisor.md` in full.

Adopt the **Morgan persona** (CISO Advisor, 16y). Consume the Agent 2 handoff payload.

Apply the BR (Board Report) workflow. Produce:
- Board-level brief (non-technical, ≤1 page equivalent): what happened, business impact, what we're doing
- Regulatory notification decisions:
  - GDPR 72h: YES — required. Deadline 2026-03-14T08:00:00Z. DPA notification draft.
  - SEC 4-day: PROBABLE — materiality assessment required. Deadline 2026-03-15T08:00:00Z.
  - HIPAA: UNKNOWN — pending confirmation of PHI in exfiltrated data
- Business impact assessment: financial, reputational, operational
- Communication plan: internal (all-hands), customer, regulator
- Law enforcement referral recommendation (nation-state APT)
- Insurance claim trigger assessment
- All regulatory notification actions have `human_approval_required: true`

Show the **handoff payload** passed to Agent 4.

---

## Agent 4 of 4 — cs-security-program-manager (SC Workflow)

Read `agents/governance/cs-security-program-manager.md` in full.

Adopt the **Jordan persona** (Security Program Manager, 14y program lead). Consume the Agent 3 handoff payload.

Apply the SC (Proactive Scan) workflow. Produce:
- Post-incident proactive scan schedule — identify all program gaps exposed by the Perfect Storm
- Facilitated review session plan (FR) — cross-team lessons learned agenda
- 8 program-level findings (one per vector) mapped to security program gaps:
  1. EDR coverage gap (85% → 100% required)
  2. SIEM batch polling (5-min gap → real-time migration)
  3. IMDSv2 not enforced across AWS fleet
  4. TLS inspection status unknown — credential harvest visibility gap
  5. Supply chain policy gap — GitHub Actions OIDC token scope unrestricted
  6. No insider threat behavioral baseline — S3 exfil not pre-alerted
  7. FortiOS patch management — no compensating control for CVSS 9.8 zero-day
  8. DDoS did not trigger SIEM noise suppression — alert fatigue realized
- Security debt entries for each gap (with SLA breach risk)
- Roadmap update recommendations
- Does NOT self-trigger reactive workflows without 2+ confirmed signals from SC scan

---

## Handoff Chain Summary Table

After all 4 agents complete, output this table:

```
Orchestration Handoff Chain — Perfect Storm
============================================

| Step | Agent                        | Workflow | Consumed From       | Produced For          | next_agents Named |
|------|------------------------------|----------|---------------------|-----------------------|-------------------|
| 1    | cs-security-analyst          | AT       | Scenario JSON       | cs-incident-responder | cs-incident-responder, cs-ciso-advisor |
| 2    | cs-incident-responder        | CO       | Analyst AT output   | cs-ciso-advisor       | cs-ciso-advisor |
| 3    | cs-ciso-advisor              | BR       | Responder CO output | cs-security-program-manager | cs-security-program-manager |
| 4    | cs-security-program-manager  | SC       | CISO BR output      | (terminal)            | [] |
```

---

## Per-Agent Mock Comparison

Compare each agent's output against `tests/mocks/orchestration-chain-mock.json`.

For each agent, show:
- Items from `must_contain` that are PRESENT in the agent's output (PASS)
- Items from `must_contain` that are MISSING (FAIL)
- Items from `must_not_contain` that appeared (VIOLATION)

```
Agent Score Summary
===================
Agent 1 — cs-security-analyst:   <n>/<total must_contain> PASS | <violations> VIOLATIONS
Agent 2 — cs-incident-responder: <n>/<total must_contain> PASS | <violations> VIOLATIONS
Agent 3 — cs-ciso-advisor:       <n>/<total must_contain> PASS | <violations> VIOLATIONS
Agent 4 — cs-security-program-manager: <n>/<total must_contain> PASS | <violations> VIOLATIONS

Overall chain score: <n>/4 agents fully correct
```

Conclude with a one-paragraph assessment: where the orchestration chain performed well, where it broke down, and what would improve the weakest link.
