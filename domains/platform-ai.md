# Platform & AI Domain

Skills in this domain govern the USAP platform itself, agent orchestration, and AI system security.

## Skills

| Slug | Level | Description |
|---|---|---|
| `orchestrator` | L2 | Multi-agent workflow orchestration: routes events, sequences agents, manages cascade logic |
| `tool-execution-broker` | L4 | Mediates tool execution requests from agents: scope validation, approval gating, execution logging |
| `guardrail` | L3 | Enforces USAP output contracts and intent classification guardrails on agent outputs |
| `agent-integrity-monitor` | L3 | Monitors AI agent outputs for integrity violations, prompt injection, and manipulation |
| `ai-agent-security` | L3 | Security assessment of AI/LLM agents: input validation, output sanitization, trust boundaries |
| `ai-ethics-governance` | L2 | AI ethics review, bias assessment, and responsible AI governance for AI system deployments |
| `ai-red-teaming` | L4 | Adversarial testing of AI/ML systems: prompt injection, model inversion, jailbreaks |

## Platform Architecture

```
User Input
    ↓
orchestrator (routing + cascade logic)
    ↓
[skill execution]
    ↓
guardrail (output validation)
    ↓
tool-execution-broker (if mutating actions)
    ↓
agent-integrity-monitor (continuous monitoring)
    ↓
Output to Operator
```

## AI Security Considerations

The USAP platform is itself an AI system and must be secured against:

1. **Prompt Injection** — `agent-integrity-monitor` detects injected instructions in tool outputs.
2. **Output Manipulation** — `guardrail` validates all outputs against the output contract schema.
3. **Scope Creep** — `tool-execution-broker` enforces scope boundaries on all tool executions.
4. **Adversarial Inputs** — `ai-agent-security` validates inputs at system boundaries.

## AI Red Teaming

The `ai-red-teaming` skill enables systematic adversarial testing of the USAP platform and any AI systems within scope:
- Prompt injection via user inputs
- Jailbreak attempts via instruction override
- Model inversion to extract training data
- Adversarial example generation

**Authorization Required:** AI red teaming requires explicit written authorization.
