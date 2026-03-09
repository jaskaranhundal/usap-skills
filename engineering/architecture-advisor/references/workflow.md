# Architecture Advisor Workflow

## Phase 1: Context Gathering

1. Understand the problem being solved
2. Identify constraints: team size, timeline, existing technology stack
3. Clarify non-functional requirements: latency targets, throughput, availability SLA
4. Identify stakeholders and their concerns

## Phase 2: Options Development

1. Generate at least 3 viable design options
2. For each option: describe approach, key components, and implementation path
3. Identify trade-offs for each option across all 8 dimensions

## Phase 3: Trade-Off Analysis

1. Score each option across 8 dimensions (1-5 scale)
2. Weight dimensions by stakeholder priorities
3. Identify the dominant option (best weighted score)
4. Document any hard constraints that eliminate options

## Phase 4: ADR Generation

1. Draft ADR in MADR format
2. Include Context, Decision, Options Considered, and Consequences
3. Set status to "Proposed" for human review and adoption

## Phase 5: Communication

1. Produce executive summary: what is changing and why
2. Identify risks and mitigation strategies
3. Define success criteria for the architectural change

## Trade-Off Scoring Guide (1-5)

| Score | Meaning |
|---|---|
| 5 | Excellent — strong advantage |
| 4 | Good — clear benefit |
| 3 | Neutral — neither advantage nor disadvantage |
| 2 | Poor — notable drawback |
| 1 | Bad — serious concern |
