# Platform & AI Security

Skills for securing the USAP platform itself, orchestrating multi-agent workflows, and assessing AI/LLM systems as enterprise security assets.

---

## Domain Overview

The `platform-ai/` domain is dual-purpose. Three skills — orchestrator, tool-execution-broker, and guardrail — are structural components of the USAP runtime that execute on every agent invocation to enforce trust boundaries, approval gates, and output contracts. Four skills — agent-integrity-monitor, ai-agent-security, ai-ethics-governance, and third-party-vendor-risk — are analytical skills invoked to assess AI systems, governance programs, and AI vendor relationships.

This is a platform-level domain. No single cs-* agent exclusively owns it. Platform structural skills are invoked by the USAP runtime. Analytical skills are invoked by whichever cs-* agent is most appropriate for the task context.

---

## Skills

| Skill | Description | Primary Use Case |
|---|---|---|
| orchestrator | Multi-agent workflow orchestration. Routes events across skills, manages cascade logic, and sequences approval gates. | Coordinating a multi-step security investigation across detection, response, and governance skills |
| tool-execution-broker | Mediates all tool execution requests from agents. Validates scope, enforces approval tiers, and maintains an append-only execution log. | Gating a mutating action (e.g., credential revocation) requested by an agent |
| guardrail | Enforces USAP output contracts and intent classification on all agent outputs before delivery to operators or downstream skills. | Blocking a non-compliant agent output; classifying agent intent before a mutating action is permitted |
| agent-integrity-monitor | Monitors AI agent behavior against established baselines. Detects prompt injection indicators, instruction override, and output manipulation. | Continuous session monitoring; responding to suspected agent compromise |
| ai-agent-security | Security assessment of AI/LLM deployments. Evaluates the full inference stack against OWASP LLM Top 10 and MITRE ATLAS. | Pre-production AI agent security review; annual LLM security assessment |
| ai-ethics-governance | AI ethics and governance review. Produces risk tier classifications aligned to EU AI Act and NIST AI RMF. Covers bias, fairness, transparency, and human oversight. | EU AI Act compliance review; new AI system deployment approval |
| third-party-vendor-risk | Vendor risk assessment for AI/ML providers and data processors. Evaluates security posture, data handling practices, and contractual control adequacy. | New AI vendor onboarding; annual vendor reassessment |

---

## Quick Commands

All tools accept `--help` and `--output json`. Run from the repository root.

**orchestrator**
```bash
python platform-ai/orchestrator/scripts/orchestrator_tool.py --help
python platform-ai/orchestrator/scripts/orchestrator_tool.py --event security-alert --cascade-policy standard --output json
```

**tool-execution-broker**
```bash
python platform-ai/tool-execution-broker/scripts/tool-execution-broker_tool.py --help
python platform-ai/tool-execution-broker/scripts/tool-execution-broker_tool.py --tool credential-revoke --scope incident-response --requester cs-security-analyst --output json
```

**guardrail**
```bash
python platform-ai/guardrail/scripts/guardrail_tool.py --help
python platform-ai/guardrail/scripts/guardrail_tool.py --output-contract standard-v1 --intent-class advisory --output json
```

**agent-integrity-monitor**
```bash
python platform-ai/agent-integrity-monitor/scripts/agent-integrity-monitor_tool.py --help
python platform-ai/agent-integrity-monitor/scripts/agent-integrity-monitor_tool.py --agent-id cs-security-analyst --lookback 24 --output json
```

**ai-agent-security**
```bash
python platform-ai/ai-agent-security/scripts/ai-agent-security_tool.py --help
python platform-ai/ai-agent-security/scripts/ai-agent-security_tool.py --target my-llm-agent --assessment-type full --output json
```

**ai-ethics-governance**
```bash
python platform-ai/ai-ethics-governance/scripts/ai-ethics-governance_tool.py --help
python platform-ai/ai-ethics-governance/scripts/ai-ethics-governance_tool.py --system my-llm-agent --framework eu-ai-act --output json
```

**third-party-vendor-risk**
```bash
python platform-ai/third-party-vendor-risk/scripts/third-party-vendor-risk_tool.py --help
python platform-ai/third-party-vendor-risk/scripts/third-party-vendor-risk_tool.py --vendor openai --data-class pii --output json
```

---

## Directory Structure

```
platform-ai/
├── CLAUDE.md                              # Authoritative domain guide
├── README.md                              # This file
├── orchestrator/
│   ├── SKILL.md
│   ├── README.md
│   └── scripts/orchestrator_tool.py
├── tool-execution-broker/
│   ├── SKILL.md
│   ├── README.md
│   └── scripts/tool-execution-broker_tool.py
├── guardrail/
│   ├── SKILL.md
│   ├── README.md
│   └── scripts/guardrail_tool.py
├── agent-integrity-monitor/
│   ├── SKILL.md
│   ├── README.md
│   └── scripts/agent-integrity-monitor_tool.py
├── ai-agent-security/
│   ├── SKILL.md
│   ├── README.md
│   └── scripts/ai-agent-security_tool.py
├── ai-ethics-governance/
│   ├── SKILL.md
│   ├── README.md
│   └── scripts/ai-ethics-governance_tool.py
└── third-party-vendor-risk/
    ├── SKILL.md
    ├── README.md
    └── scripts/third-party-vendor-risk_tool.py
```

---

## Approval Gate Reference

| Action Type | Approval Required | Gate Skill |
|---|---|---|
| Read-only analysis | None (auto-authorized) | tool-execution-broker |
| Low-impact mutating (e.g., create ticket) | Soft approval (5-minute acknowledgment) | tool-execution-broker |
| High-impact mutating (e.g., revoke credential, block IP) | Explicit human sign-off | tool-execution-broker |
| Output with mutating intent classified by guardrail | Human approval before delivery | guardrail |
| Scope expansion attempt by agent | Rejected and logged; integrity alert raised | tool-execution-broker + agent-integrity-monitor |

---

## Related Domains

- [governance/](../governance/) — AI ethics governance outputs feed the security program governance cycle; EU AI Act high-risk findings become tracked compliance items
- [detection/](../detection/) — Agent integrity violations and prompt injection events feed behavioral analytics and detection engineering

## Full Domain Guide

For complete methodology, approval gate architecture, AI security risk matrix, OWASP LLM Top 10 coverage, deployment workflows, and best practices, see [CLAUDE.md](./CLAUDE.md).
