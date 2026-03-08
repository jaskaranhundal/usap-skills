# usap-skills

Standalone skill packages for the [USAP (Unified Security Agent Platform)](https://github.com/jaskaranhundal/usap).

Each directory is a self-contained skill package. The `SKILL.md` file in each package is a complete LLM system prompt — you can paste it directly into AnythingLLM, Ollama, ChatGPT, or any other LLM interface and use it without installing USAP.

---

## Skill packages (56 agents)

| Slug | Level | Category |
|---|---|---|
| agent-integrity-monitor | L3 | detection |
| ai-agent-security | L3 | detection |
| ai-ethics-governance | L2 | governance |
| attack-path-analysis | L3 | analysis |
| attack-surface-management | L3 | analysis |
| behavioral-analytics | L3 | detection |
| build-integrity | L3 | detection |
| cloud-security-posture | L3 | compliance |
| compliance-mapping | L2 | compliance |
| containment-advisor | L3 | response |
| continuous-pentesting | L3 | testing |
| cryptography-key-management | L3 | identity |
| cyber-insurance | L2 | governance |
| data-security-classification | L3 | data |
| detection-engineering | L3 | detection |
| devsecops-pipeline | L3 | devsecops |
| endpoint-os-security | L4 | endpoint |
| enterprise-risk-assessment | L2 | risk |
| findings-tracker | L3 | operations |
| forensics | L3 | response |
| guardrail | L3 | governance |
| iac-security | L3 | devsecops |
| identity-access-risk | L3 | identity |
| incident-classification | L3 | response |
| incident-commander | L2 | response |
| insider-physical-risk | L3 | detection |
| internal-audit-assurance | L2 | compliance |
| knowledge-management | L2 | operations |
| metrics-reporting | L2 | reporting |
| network-exposure | L3 | network |
| orchestrator | L2 | orchestration |
| ot-iot-device-security | L4 | ot-iot |
| privacy-dpia | L2 | compliance |
| quantum-security-readiness | L2 | risk |
| red-team-operations | L3 | red-team |
| red-team-planner | L3 | red-team |
| regulatory-horizon | L2 | compliance |
| risk-threat-modeling | L2 | risk |
| safe-exploitation | L3 | testing |
| sast-dast-coordinator | L3 | devsecops |
| secrets-exposure | L3 | detection |
| secure-sdlc | L3 | devsecops |
| security-architecture | L2 | architecture |
| security-awareness | L2 | training |
| security-policy-control | L2 | governance |
| security-research | L3 | research |
| supply-chain-risk | L3 | risk |
| supply-chain-simulation | L3 | risk |
| telemetry-signal-quality | L3 | detection |
| third-party-vendor-risk | L2 | risk |
| threat-hunting | L3 | detection |
| threat-intelligence | L3 | intelligence |
| tool-execution-broker | L4 | operations |
| vulnerability-management | L3 | vulnerability |
| zero-day-response | L3 | response |
| zero-day-response-governance | L2 | governance |

---

## Standalone use (no USAP required)

Copy the contents of any `SKILL.md` into your LLM interface as the system prompt. Then send security event context as the user message.

```bash
# Example: use secrets-exposure agent in any LLM
cat secrets-exposure/SKILL.md
```

---

## Use with USAP

This repo is the default `skills/` submodule in the USAP platform repo.

```bash
# Clone USAP with skills
git clone --recurse-submodules https://github.com/jaskaranhundal/usap.git
```

To add private bug bounty skills alongside this library, clone
[usap-bugbounty](https://github.com/jaskaranhundal/usap-bugbounty) and set:

```
USAP_SKILLS_PATHS=./skills,./skills-bb
```

---

## Contributing

To add a new agent, open a PR against this repo. See
[CONTRIBUTING.md](https://github.com/jaskaranhundal/usap/blob/main/CONTRIBUTING.md)
in the platform repo for the full agent authoring guide.

Each skill package must include:

```
<slug>/
  SKILL.md                          # LLM system prompt + frontmatter
  README.md                         # Human-readable description
  references/workflow.md            # Analysis workflow
  assets/templates/output-template.json
  expected_outputs/sample_output.json
  scripts/<slug>_tool.py
```

---

## License

Apache 2.0
