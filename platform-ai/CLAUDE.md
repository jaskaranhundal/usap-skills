# Platform & AI Security Domain — CLAUDE.md

This file is the authoritative domain guide for the `platform-ai/` directory. It governs how Claude and cs-* agents understand, navigate, and apply the skills in this domain.

---

## Purpose

The Platform & AI Security domain governs security of the USAP platform itself and any AI systems operating within or adjacent to the enterprise security program. Skills in this domain address two interconnected concerns: the integrity and safe operation of AI agents (orchestration control, tool execution gating, output guardrails, behavioral monitoring) and the security assessment of AI/ML systems as first-class assets in the organization's risk landscape.

This domain is unique in that several of its skills — orchestrator, tool-execution-broker, and guardrail — are structural components of the USAP runtime. They are not called reactively in response to an incident; they execute on every agent invocation as part of the platform trust architecture. The remaining skills (agent-integrity-monitor, ai-agent-security, ai-ethics-governance, third-party-vendor-risk) are invoked analytically to assess AI systems, governance programs, and vendor relationships.

Core coverage areas:

- **Agent Orchestration** — Routing events across skills, managing cascade logic, sequencing multi-agent workflows with approval gates
- **Tool Execution Authorization** — Brokering all mutating tool calls from agents through scope validation, approval gating, and execution logging
- **Output Safety Guardrails** — Enforcing USAP output contracts, classifying agent intent, and blocking non-compliant outputs before delivery to operators
- **Agent Integrity Monitoring** — Continuous behavioral monitoring of AI agents to detect prompt injection, instruction override, and output manipulation
- **LLM and AI System Security** — Assessing AI/LLM deployments against OWASP LLM Top 10 and NIST AI RMF; validating trust boundaries and input/output sanitization
- **AI Ethics and Governance** — Reviewing AI system deployments for bias, fairness, transparency, and regulatory compliance including EU AI Act
- **Third-Party Vendor Risk** — Assessing AI/ML vendors and data processors for security posture, data handling practices, and regulatory compliance

No cs-* agent exclusively owns this domain. Platform-level skills (orchestrator, tool-execution-broker, guardrail) are invoked by the USAP runtime itself. Analytical skills are invoked by the most contextually appropriate cs-* agent for the task at hand, typically cs-security-analyst or cs-ciso-advisor.

---

## Skills Catalog

| Skill | Slug | Primary Tool | Coverage |
|---|---|---|---|
| orchestrator | `platform-ai/orchestrator` | `orchestrator_tool.py` | Multi-agent orchestration, event routing, cascade logic |
| tool-execution-broker | `platform-ai/tool-execution-broker` | `tool-execution-broker_tool.py` | Tool execution authorization, scope validation, approval gating |
| guardrail | `platform-ai/guardrail` | `guardrail_tool.py` | Input/output safety guardrails, intent classification, contract enforcement |
| agent-integrity-monitor | `platform-ai/agent-integrity-monitor` | `agent-integrity-monitor_tool.py` | Agent behavior monitoring, prompt injection detection, manipulation detection |
| ai-agent-security | `platform-ai/ai-agent-security` | `ai-agent-security_tool.py` | LLM security assessment, prompt injection, trust boundary validation |
| ai-ethics-governance | `platform-ai/ai-ethics-governance` | `ai-ethics-governance_tool.py` | AI governance review, bias assessment, EU AI Act, NIST AI RMF |
| third-party-vendor-risk | `platform-ai/third-party-vendor-risk` | `third-party-vendor-risk_tool.py` | Vendor risk assessment, data processor review, contractual control validation |

Each skill directory follows the USAP Agent Skills Standard v1 layout:

```
<skill-slug>/
├── SKILL.md
├── README.md
├── scripts/
│   └── <skill-slug>_tool.py
├── references/
├── assets/
└── expected_outputs/
```

---

## Python Tools Reference

| Tool | Path | Key Flags | Output |
|---|---|---|---|
| `orchestrator_tool.py` | `orchestrator/scripts/` | `--event`, `--cascade-policy`, `--output json` | Routing decision, skill sequence, approval gate requirements |
| `tool-execution-broker_tool.py` | `tool-execution-broker/scripts/` | `--tool`, `--scope`, `--requester`, `--output json` | Authorization decision, scope validation result, execution log |
| `guardrail_tool.py` | `guardrail/scripts/` | `--input`, `--output-contract`, `--intent-class`, `--output json` | Guardrail verdict (pass/block), intent classification, contract diff |
| `agent-integrity-monitor_tool.py` | `agent-integrity-monitor/scripts/` | `--agent-id`, `--lookback`, `--output json` | Integrity violation report, injection indicators, anomaly score |
| `ai-agent-security_tool.py` | `ai-agent-security/scripts/` | `--target`, `--assessment-type`, `--output json` | OWASP LLM findings, trust boundary violations, risk rating |
| `ai-ethics-governance_tool.py` | `ai-ethics-governance/scripts/` | `--system`, `--framework eu-ai-act\|nist-ai-rmf`, `--output json` | Governance gap analysis, risk tier classification, remediation roadmap |
| `third-party-vendor-risk_tool.py` | `third-party-vendor-risk/scripts/` | `--vendor`, `--data-class`, `--output json` | Vendor risk score, control gap list, contractual remediation items |

All tools accept `--help` for full usage and `--output json` for machine-readable output compatible with downstream aggregation.

---

## Approval Gate Architecture

The tool-execution-broker and guardrail skills work together to form a two-layer trust boundary around every agent action that produces observable change in external systems.

### Layer 1: Guardrail (Output Contract Enforcement)

The guardrail skill evaluates agent outputs before they are delivered to an operator or passed to another skill. It operates on two axes:

1. **Intent Classification** — The output is classified against a pre-defined intent taxonomy (informational, advisory, remediation-instructing, mutating, data-exfiltrating). Outputs classified as mutating or data-exfiltrating trigger mandatory human approval before delivery.

2. **Contract Validation** — The output is compared against the output contract schema for the originating skill. Fields outside the schema, unexpected data types, or schema version mismatches cause the guardrail to block and log the output.

### Layer 2: Tool Execution Broker (Action Authorization)

When an agent requests execution of a tool that produces real-world side effects (writing to a SIEM, modifying a firewall rule, revoking a credential), the tool-execution-broker intercepts the request before execution and evaluates:

1. **Scope Validation** — Does the requested tool call fall within the authorized scope for the current task? Scope is defined per-task at invocation time and cannot be expanded by an agent at runtime.

2. **Approval Gate** — Based on the tool's risk tier (read-only, low-impact mutating, high-impact mutating), the broker either auto-authorizes, queues for soft approval (acknowledgment within 5 minutes), or requires explicit human sign-off before execution.

3. **Execution Logging** — Every authorized and rejected tool call is logged with the agent identity, requested scope, authorization decision, and a hash of the tool call parameters. Logs are append-only and cannot be modified by agents.

### Interaction Model

```
Agent Output
      |
      v
guardrail           (contract validation + intent classification)
      |
      +-- [informational / advisory]  --> deliver to operator
      |
      +-- [mutating intent detected]  --> queue for human approval
                                          if approved --> tool-execution-broker
                                                              |
                                                              v
                                                         scope validation
                                                              |
                                                         approval gate
                                                              |
                                                         execution + log
```

Neither skill can be bypassed by an agent. Both are enforced at the USAP runtime layer, outside the agent's execution context.

---

## AI Security Risk Matrix

| Risk Category | OWASP LLM Top 10 | Detection Skill | Mitigation |
|---|---|---|---|
| Prompt Injection | LLM01 | agent-integrity-monitor | Structured output contracts; input sanitization in ai-agent-security |
| Insecure Output Handling | LLM02 | guardrail | Output contract enforcement; schema validation on all agent responses |
| Training Data Poisoning | LLM03 | ai-agent-security | Data provenance review; training dataset access controls |
| Model Denial of Service | LLM04 | agent-integrity-monitor | Rate limiting; resource quota enforcement per agent session |
| Supply Chain Vulnerabilities | LLM05 | third-party-vendor-risk | Vendor assessment; model card validation; SBOM for ML dependencies |
| Sensitive Information Disclosure | LLM06 | guardrail, agent-integrity-monitor | Output redaction rules; PII classification in guardrail contract |
| Insecure Plugin Design | LLM07 | tool-execution-broker | Scope validation; tool registry with declared capability surface |
| Excessive Agency | LLM08 | tool-execution-broker, orchestrator | Scope constraints; mandatory approval gates for mutating actions |
| Overreliance | LLM09 | ai-ethics-governance | Human-in-the-loop gates; confidence thresholds on agent recommendations |
| Model Theft | LLM10 | ai-agent-security, third-party-vendor-risk | Access controls on model endpoints; vendor contractual protections |

---

## Domain Best Practices

1. **Human approval gates are non-negotiable for mutating actions.** No agent in the USAP platform may execute a tool that modifies external state without an explicit human approval event recorded in the tool-execution-broker log. Auto-authorization is permitted only for read-only tool calls explicitly declared as `read_only: true` in the tool registry.

2. **Scope must be declared at invocation, not expanded at runtime.** When a task is initiated, its authorized tool scope is fixed. An agent that requests tools outside its declared scope during execution is flagged as a scope expansion violation by tool-execution-broker and the request is rejected with an integrity alert.

3. **Guardrail output contracts are versioned and immutable per release.** Output contract schemas are stored under version control and cannot be modified by agents at runtime. Schema upgrades require a formal review cycle and a version bump. The guardrail always evaluates against the contract version that was current when the task was invoked.

4. **Treat prompt injection as an always-on threat.** Every string that enters an agent from an external source — tool output, user input, API response, file content — is a potential injection vector. The agent-integrity-monitor continuously correlates agent behavior against its declared instruction set; deviations from expected behavior trigger an integrity alert regardless of where in the session they occur.

5. **AI system security assessments must cover the full inference stack.** An ai-agent-security assessment that evaluates only the model API is incomplete. The full stack — prompt construction, context injection, tool calling mechanism, output parsing, and downstream consumers — must be in scope. Trust boundaries exist at every transition point in this stack.

6. **Vendor AI risk is supply chain risk.** When an organization deploys a third-party AI model, that model's training data provenance, fine-tuning practices, update cadence, and API security posture are all inherited risks. The third-party-vendor-risk skill must be run before any new AI vendor goes to production and on a minimum annual reassessment cycle thereafter.

7. **EU AI Act risk tier classification gates deployment, not just documentation.** For any AI system deployed in a regulated context, the ai-ethics-governance skill must produce a formal risk tier classification (unacceptable, high, limited, minimal) before the system goes to production. High-risk systems require ongoing monitoring, transparency measures, and human oversight mechanisms that must be validated quarterly.

8. **Deviations from expected agent behavior are always significant.** An agent that begins producing outputs inconsistent with its declared purpose, that calls tools it has not historically used, or that generates unusually long or structurally atypical outputs should be treated as a potential integrity violation until proven otherwise. Agent behavioral baselines must be established during onboarding and refreshed after any model update.

---

## Workflow: Agent Deployment Security Review

This workflow must be completed before any new AI agent is deployed in a production USAP environment.

```
Step 1 — AI Agent Security Assessment (ai-agent-security)
  python ai-agent-security/scripts/ai-agent-security_tool.py \
    --target <agent-name> --assessment-type full --output json
  Gate: No Critical findings; all High findings have accepted remediation plan

Step 2 — Ethics and Governance Review (ai-ethics-governance)
  python ai-ethics-governance/scripts/ai-ethics-governance_tool.py \
    --system <agent-name> --framework eu-ai-act --output json
  Gate: Risk tier classified; if high-risk, human oversight mechanisms documented

Step 3 — Vendor Risk Assessment (if using third-party model) (third-party-vendor-risk)
  python third-party-vendor-risk/scripts/third-party-vendor-risk_tool.py \
    --vendor <vendor-name> --data-class <highest-data-class> --output json
  Gate: Vendor risk score <= accepted threshold; contractual controls confirmed

Step 4 — Tool Scope Declaration (tool-execution-broker)
  python tool-execution-broker/scripts/tool-execution-broker_tool.py \
    --tool <tool-list> --scope <declared-scope> --requester <agent-id> --output json
  Gate: All tools in scope declared; risk tier documented; approval gates configured

Step 5 — Output Contract Registration (guardrail)
  python guardrail/scripts/guardrail_tool.py \
    --output-contract <contract-schema> --intent-class <intent-taxonomy> --output json
  Gate: Output contract schema valid and version-controlled; intent classifications complete

Step 6 — Baseline Establishment (agent-integrity-monitor)
  python agent-integrity-monitor/scripts/agent-integrity-monitor_tool.py \
    --agent-id <agent-id> --lookback 0 --output json
  Gate: Behavioral baseline recorded; monitoring alerts configured

Decision: ALL PASS --> Agent approved for production deployment
          ANY FAIL --> Deployment blocked; findings returned to agent owner
```

---

## Workflow: Ongoing Agent Integrity Monitoring

This workflow runs continuously (recommended: hourly) for all production agents.

```
agent-integrity-monitor     (behavioral deviation check against baseline)
          |
          +-- [no deviation]       --> log clean check; continue
          |
          +-- [minor deviation]    --> flag for review; notify security team
                                       schedule manual review within 24 hours
          |
          +-- [injection indicator detected]
                                   --> immediately suspend agent session
                                       invoke guardrail to block pending outputs
                                       trigger incident-commander escalation
                                       preserve session logs for forensics
          |
          +-- [scope expansion attempt]
                                   --> tool-execution-broker rejects and logs
                                       agent-integrity-monitor raises critical alert
                                       cs-security-analyst notified immediately
```

All integrity alerts are structured payloads consumable by the response domain. A confirmed prompt injection event or scope expansion attempt is treated as a security incident of at minimum SEV2 severity.

---

## OWASP LLM Top 10 Coverage

| OWASP LLM ID | Risk Name | Covering Skills | Coverage Type |
|---|---|---|---|
| LLM01 | Prompt Injection | agent-integrity-monitor, ai-agent-security | Detection + Prevention |
| LLM02 | Insecure Output Handling | guardrail | Prevention (output contract enforcement) |
| LLM03 | Training Data Poisoning | ai-agent-security, third-party-vendor-risk | Assessment |
| LLM04 | Model Denial of Service | agent-integrity-monitor, orchestrator | Detection + Rate Limiting |
| LLM05 | Supply Chain Vulnerabilities | third-party-vendor-risk, ai-agent-security | Assessment |
| LLM06 | Sensitive Information Disclosure | guardrail, agent-integrity-monitor | Prevention + Detection |
| LLM07 | Insecure Plugin Design | tool-execution-broker | Prevention (tool registry + scope) |
| LLM08 | Excessive Agency | tool-execution-broker, orchestrator | Prevention (approval gates) |
| LLM09 | Overreliance | ai-ethics-governance | Governance (human oversight gates) |
| LLM10 | Model Theft | ai-agent-security, third-party-vendor-risk | Assessment + Contractual |

---

## Platform Architecture

The USAP platform routes every user-initiated security task through the following trust chain:

```
User / Operator Input
        |
        v
orchestrator            (event classification, skill routing, cascade policy)
        |
        v
[skill execution]       (domain skill produces analysis or recommendation)
        |
        v
guardrail               (output contract validation, intent classification)
        |
        +-- [safe output]       --> deliver to operator or next skill
        |
        +-- [mutating intent]   --> human approval required
                                    |
                                    v
                            tool-execution-broker   (scope validation, gate, log)
                                    |
                                    v
                              [tool executes]
        |
        v
agent-integrity-monitor (continuous session behavioral monitoring)
```

---

## Related Domains

### governance/

The ai-ethics-governance skill produces regulatory compliance assessments (EU AI Act, NIST AI RMF) that feed into the governance domain's security program management workflows. EU AI Act high-risk classifications become tracked findings in `governance/findings-tracker`. AI governance metrics feed `governance/metrics-reporting` and `governance/ciso-brief-generator` for board-level AI risk reporting.

Full domain reference: `governance/CLAUDE.md`

### detection/

The agent-integrity-monitor produces behavioral anomaly data that integrates with `detection/behavioral-analytics` when agent compromise is suspected. Confirmed prompt injection events and scope expansion attempts are structured payloads that feed `detection/threat-intelligence` for actor attribution and `detection/detection-engineering` for new detection rule authoring covering AI-specific attack patterns.

Full domain reference: `detection/CLAUDE.md`

---

## Standards and Frameworks Referenced

| Standard | Application in this Domain |
|---|---|
| OWASP LLM Top 10 | Primary vulnerability taxonomy for ai-agent-security assessments |
| NIST AI Risk Management Framework (AI RMF) | Governance structure for ai-ethics-governance assessments |
| EU AI Act (2024) | Regulatory compliance framework; risk tier classification in ai-ethics-governance |
| NIST SP 800-218A | Secure AI/ML development practices; referenced in ai-agent-security |
| ISO/IEC 42001 | AI management system standard; aligns with ai-ethics-governance governance review |
| MITRE ATLAS | Adversarial ML threat matrix; TTP reference for agent-integrity-monitor and ai-agent-security |
| SOC 2 Type II | Vendor trust evidence framework referenced in third-party-vendor-risk |
| ISO 27001 / ISO 27701 | Vendor security and privacy management baseline for third-party-vendor-risk |
