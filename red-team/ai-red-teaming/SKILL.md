---
name: ai-red-teaming
description: USAP agent skill for AI Red Teaming. Use for Adversarial testing of AI/ML systems — prompt injection, model inversion, jailbreaks.
license: MIT
metadata:
  version: 1.0.0
  author: USAP Team
  category: usap-red-team
  updated: 2026-03-08
  agent_slug: "ai-red-teaming"
---

# AI Red Teaming

## Overview
Perform adversarial security testing of AI and ML systems including LLMs, embedding models, and ML pipelines. This skill governs how to identify prompt injection vulnerabilities, jailbreak susceptibilities, model inversion risks, data poisoning vectors, and adversarial example attacks. Every engagement requires explicit written authorization and produces a structured findings report with MITRE ATLAS mappings.

## Keywords
- usap
- security-agent
- ai-security
- red-team
- prompt-injection
- adversarial-ml
- operations

## Quick Start
```bash
python scripts/ai-red-teaming_tool.py --help
python scripts/ai-red-teaming_tool.py --output json
```

## Core Workflows
1. Validate authorization and define AI system scope.
2. Execute adversarial test battery against target AI system.
3. Score findings by exploitability, impact, and MITRE ATLAS mapping.
4. Produce structured findings report with remediation guidance.

---

## Skill Identity

| Field | Value |
|---|---|
| **Slug** | `ai-red-teaming` |
| **Level** | L4 |
| **Plane** | work |
| **Phase** | phase2 |
| **Domain** | Red Team / AI Security |
| **Role** | AI Security Researcher, Red Team Lead |
| **Authorization required** | yes |

---

## Input Schema

```json
{
  "event_type": "ai_red_team_engagement",
  "severity": "high",
  "raw_payload": {
    "target_system": "LLM application / ML pipeline / embedding model",
    "authorization_ref": "engagement-auth-2026-001",
    "scope": ["prompt-injection", "jailbreak", "model-inversion"],
    "model_type": "llm | classifier | embedding | generative",
    "access_level": "black-box | gray-box | white-box"
  },
  "context": {
    "environment": "staging",
    "affected_systems": ["ai-app-prod"],
    "timestamp_utc": "2026-03-08T09:00:00Z"
  }
}
```

---

## Core Methodology

### Step 1: Authorization Validation
Verify written authorization exists before any testing begins. Confirm scope boundaries: which models, endpoints, and attack categories are in scope.

### Step 2: Attack Surface Mapping
Identify all AI system entry points: user-facing prompts, API endpoints, fine-tuning interfaces, training data pipelines, embedding stores.

### Step 3: Adversarial Test Battery

**Track 1: Prompt Injection**
Attempt to override system prompts, extract hidden instructions, and hijack model behavior via crafted user inputs.

Attack patterns:
- Direct instruction override: "Ignore previous instructions and..."
- Indirect injection via retrieved documents (RAG poisoning)
- Role-play jailbreaks: "Pretend you are a model with no restrictions..."
- Chain-of-thought manipulation
- Multi-turn context accumulation attacks

**Track 2: Jailbreak Testing**
Test model safety guardrails using known and novel jailbreak techniques. Document which guardrails are bypassed and at what confidence threshold.

**Track 3: Model Inversion**
Attempt to extract training data, model weights, or system prompt content through repeated inference.

**Track 4: Adversarial Examples**
For classification/embedding models: generate inputs that cause incorrect classification while appearing benign.

**Track 5: Data Poisoning Assessment**
If fine-tuning or RAG pipelines are in scope: assess whether attacker-controlled data can influence model behavior.

### Step 4: MITRE ATLAS Mapping
Map all findings to MITRE ATLAS (Adversarial Threat Landscape for AI Systems) techniques.

### Step 5: Output Generation
Produce structured findings with ATLAS mappings, exploitability scores, and remediation recommendations.

---

## MITRE ATLAS Coverage

| Technique | ID | Description |
|---|---|---|
| Prompt Injection | AML.T0051 | Crafted inputs manipulate model behavior |
| Model Inversion | AML.T0024 | Extract private training data via inference |
| Adversarial Patch | AML.T0020 | Physical or digital adversarial inputs |
| Data Poisoning | AML.T0020.000 | Corrupt training data to influence model |
| Backdoor ML Model | AML.T0018 | Embed hidden trigger behavior in model |

---

## Output Contract

```json
{
  "agent_slug": "ai-red-teaming",
  "intent_type": "analyze",
  "action": "Remediate identified AI vulnerabilities and implement input validation guardrails.",
  "rationale": "Prompt injection bypassed system prompt in 3 of 5 attempts. Model leaked partial system prompt content.",
  "confidence": 0.88,
  "severity": "high",
  "key_findings": [],
  "evidence_references": [],
  "next_agents": ["guardrail", "agent-integrity-monitor"],
  "human_approval_required": true,
  "timestamp_utc": "2026-03-08T09:00:00Z"
}
```

---

## Escalation Logic

| Condition | Action |
|---|---|
| Successful prompt injection | Escalate to `guardrail` for output contract enforcement |
| System prompt extraction confirmed | Escalate to `incident-commander` (SEV2) |
| Training data leakage | Escalate to `privacy-dpia` and `incident-commander` |
| Authorization missing | Abort immediately — return policy violation |

---

## Related Skills

- `guardrail` — validates AI system outputs against manipulation
- `agent-integrity-monitor` — monitors AI agent behavior in production
- `ai-agent-security` — broader AI/LLM security assessment
- `red-team-planner` — scopes the overall engagement containing AI red teaming
