# USAP Orchestration Protocol

How `cs-*` agents hand work to each other, what travels in a handoff, where a chain must stop for a human, and how the same rules apply when no human is in the loop. This file is normative. The `usap:orchestrate` command, the MCP router and the scheduled runner implement it; if they disagree with this file, this file wins and the implementation is the bug.

Tracks [issue #144](https://github.com/jaskaranhundal/usap-skills/issues/144).

---

## 1. Three rules

1. **The payload is the handoff.** An agent hands work to another agent by emitting the 11-field output contract with the receiving agents named in `next_agents`. Nothing else is a handoff. Prose such as "passing this to the CISO" is not a handoff; a payload with `next_agents: ["cs-ciso-advisor"]` is.
2. **A mutating payload ends the chain at a hold.** Any payload with `human_approval_required: true` terminates the chain. The router returns `approval_required`; nothing is dispatched; the next agent does not run until a human records the approval. There is no autonomous path around this, in any runtime.
3. **The receiving agent inherits, never re-derives.** Fields marked UNKNOWN or `PREREQUISITE_UNVERIFIED` by the sending agent are carried forward unchanged. The receiving agent may resolve them only with new evidence it fetched itself, cited in `evidence_references`.

---

## 2. The handoff envelope

The envelope is the [11-field output contract](standards/output-contract.md). Four fields carry the orchestration semantics:

| Field | Orchestration meaning |
|---|---|
| `next_agents` | Ordered list of `cs-*` agent slugs (or skill slugs, for skill chains) that should run next. Empty means terminal. |
| `human_approval_required` | `true` stops the chain. The router surfaces an approval prompt; the audit log records `approval_required`. |
| `evidence_references` | Every verdict the next agent will build on must be traceable to a resolvable `source` here. A receiving agent may not cite the sending agent's prose as evidence; it cites the same underlying artifact. |
| `intent_type` | `escalate` names the next agent explicitly; `block` means the chain stopped for a policy reason (for example, a routed skill is not installed) and the payload says why. |

Optional fields agents already use in handoffs and which receivers must preserve when present: `prerequisite_checks`, `mitre_ttps`, `affected_assets`, `remediation_steps`, `mutating_category`, `approver_roles`.

**Announcing a handoff.** When a chain runs inside one session, the sending agent prints the payload, then one line:

```
Handoff → cs-<slug> (<workflow code>). Consumes: <fields>. Open: <UNKNOWN fields carried forward>.
```

That line is for the human reading along. The payload is what the next agent consumes.

---

## 3. The four USAP chains

Each chain names the trigger, the sequence, the pass codes from the agents' command menus, and the hold.

### 3.1 Design review

Trigger: a control, guard, gate, credential handling or protection is about to be designed or written.

| Step | Agent | Workflow | Produces |
|---|---|---|---|
| 1 | `cs-devsecops-engineer` | DR (Document Security Review) | Classified document type, deterministic signals, design findings |
| 2 | skill `threat-model` | invoked by step 1 when the document describes trust boundaries | STRIDE table per boundary |
| 3 | skill `security-requirements-review` | invoked by step 1 | Requirement gaps with document locations |
| 4 | `cs-devsecops-engineer` | DR, close-out | Residual-risk rating (`low` / `medium` / `high`) and the conditions attached to it |

Hold: the residual-risk rating is the output. The control is written only after a human reads the rating. The rating travels with the pull request that implements the control. A control with no recorded rating is treated as unreviewed.

### 3.2 Finding to ticket

Trigger: a scanner, an audit collector or a skill has produced a finding that should become a work item a colleague will see.

| Step | Agent or skill | Workflow | Produces |
|---|---|---|---|
| 1 | source skill (for example `vuln-scan`, `secrets-exposure`, `container-image-scan`) | its own procedure | Finding payload |
| 2 | skill `finding-triage` | — | Ranked, deduplicated finding with severity and confidence |
| 3 | skill `vulnerability-management` | — | Owner, SLA, remediation class |
| 4 | `cs-devsecops-engineer` | PR (pre-report pass) | Ticket text: what changes, the risk, the controls; no history, no hedging |
| 5 | connector `mcp:ticketing:create_issue` | — | Draft ticket |

Hold: step 5 is mutating and visible to a colleague. `human_approval_required: true` from step 4. The draft is created only after approval; the chain never assigns, transitions or mentions anyone.

### 3.3 Incident

Trigger: a confirmed or suspected active incident.

| Step | Agent or skill | Workflow | Produces |
|---|---|---|---|
| 1 | `cs-security-analyst` | AT (Alert Triage) | Ranked signals, kill-chain stage, severity declaration, `next_agents` |
| 2 | skill `incident-classification` | — | SEV level, regulatory clocks |
| 3 | `cs-incident-responder` | CO (Active Containment) | Containment intents in sequence, evidence-preservation order, rollback per action |
| 4 | skill `containment-advisor` | — | Isolation options with blast radius |
| 5 | `cs-ciso-advisor` | BR (Board Report) or RG (risk governance) | Notification decisions, residual-risk position |
| 6 | `cs-security-program-manager` | SC (Proactive Scan) | Program gaps, debt entries |

Holds: step 3 emits containment as intent blocks only, every one `human_approval_required: true`. Step 5 regulatory notifications are each a separate approval. Steps 1, 2, 4 and 6 are read-only and run without a hold.

### 3.4 Audit

Trigger: a scheduled or on-demand posture audit across an estate.

| Step | Agent or skill | Workflow | Produces |
|---|---|---|---|
| 1 | collectors (read-only) | — | Evidence bundle with resolvable sources |
| 2 | routed skills (`iac-security`, `cloud-security-posture`, `secrets-exposure`, `attack-surface-management`, `compliance-mapping`) | own procedures | Finding payloads |
| 3 | `cs-devsecops-engineer` | PA (post-assessment pass) | Consolidated findings, false-positive cuts, severity normalisation |
| 4 | `cs-security-program-manager` | debt tracker | Security debt entries with SLA |
| 5 | chain 3.2 per finding that needs a ticket | — | Draft tickets |

Hold: none until step 5, which inherits the finding-to-ticket hold. Steps 1 to 4 may run unattended.

---

## 4. Patterns

USAP uses four composition patterns. Name the pattern when you start a chain so the reader knows what to expect.

| Pattern | Shape | When |
|---|---|---|
| **Agent chain** | agent → agent → agent, each consuming the previous payload | Chains 3.1 to 3.4 |
| **Skill chain** | skill → skill → skill, no persona, one agent supervising | The inner steps of 3.2 and 3.4 |
| **Persona switch** | one operator session, one agent at a time, handoff announced between them | `usap:orchestrate`, interactive incident work |
| **Fan-out and consolidate** | one agent invokes several skills in parallel, then consolidates | PA passes, `cs-purple-team-lead` validation runs |

Fan-out consolidation is itself a payload: the consolidating agent cites the fanned-out payloads' evidence, not the payloads.

---

## 5. Routing rules the implementation must enforce

1. **Absent skill → `block`.** If a `next_agents` entry names a skill or agent that does not exist in the resolved tree (for example the installed plugin ships 33 of 80 skills), the router emits a `block` payload naming the missing slug and stops. It never silently falls through to a different skill. Tracked in [issue #141](https://github.com/jaskaranhundal/usap-skills/issues/141).
2. **Deterministic selection.** Ties break alphabetically. Two runs over the same payload route the same way. See [`docs/mcp-routing.md`](docs/mcp-routing.md).
3. **Audit every decision.** Route, approval, denial and dispatch each write one line to the hash-chained audit log (`tools/mcp_audit.py`). A chain with a gap in its audit trail is treated as failed.
4. **Read-only by default.** A connector capability is invoked autonomously only when it is declared `read_only` in the agent's `usap_mcp` block and the payload is not mutating. Everything else is gated.
5. **Budget is a routing input.** In scheduled runs, a chain step that would exceed the agent's daily budget is held, not skipped. The hold is a payload with `intent_type: block` and the reason.

---

## 6. Autonomous runs: the board is the state machine

When chains run without a human present (scheduled runner, headless sessions), agents do not talk to each other in prose. A handoff is performed by reassigning a work item on the board to the receiving agent; the receiving agent picks it up on its next run and reads the payload attached to the item. Consequences:

- Every step of every chain is a ticket transition with the payload attached. The ticket history is the audit trail a human reads.
- A hold is a ticket in the `awaiting-decision` state assigned to the human, carrying a decision card: what, evidence, residual risk, rollback, expiry.
- An approved decision releases the held step; a rejected one closes the ticket with the reason; an expired one is re-raised once, then closed.
- Session transcripts are the record of reasoning. A dashboard may render them. They are never the coordination channel.

This section describes the contract the private console implements. The public repository ships the payload format, the router rules and the audit log; the board itself is not part of this repository.

---

## 7. Overrides

The human decides. Any phase, persona, skill or routing choice may be overridden by the operator at any point, and the override is recorded as an `approval_granted` or `approval_denied` audit line with a reason. Overriding a hold to dispatch a mutating action is itself the approval; it is never implicit.

---

## See also

- [`standards/output-contract.md`](standards/output-contract.md) — the envelope
- [`docs/mcp-routing.md`](docs/mcp-routing.md) — router statuses and scoring
- [`docs/mcp-scheduled.md`](docs/mcp-scheduled.md) — the scheduled runner
- [`agents/CLAUDE.md`](agents/CLAUDE.md) — writing a `cs-*` agent, including the Command Menu codes used above
- [`plugins/usap/commands/orchestrate.md`](plugins/usap/commands/orchestrate.md) — a worked four-agent chain against the Perfect Storm scenario
