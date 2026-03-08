# usap-skills

56 standalone LLM skill packages for the [USAP (Unified Security Agent Platform)](https://github.com/jaskaranhundal/usap).

Each `SKILL.md` is a complete LLM system prompt. Paste it into AnythingLLM, Ollama, ChatGPT, Claude, or any LLM interface and use it without installing USAP. The USAP platform uses these packages as its agent skill library via git submodule.

---

## Which agent for which problem?

### Active incident in progress

| Situation | Start here | Then cascade to |
|---|---|---|
| Any new security event | `incident-classification` | Routes to the right specialist |
| Confirmed active incident, need command | `incident-commander` | `forensics`, `containment-advisor` |
| Need to contain an active threat | `containment-advisor` | MCP execution layer |
| Ransomware or destructive attack | `incident-commander` → `containment-advisor` | `forensics`, `compliance-mapping` |
| Forensic timeline and chain of custody | `forensics` | `threat-intelligence`, `compliance-mapping` |

### Credentials and identity

| Situation | Agent |
|---|---|
| Secret/API key found in code or logs | `secrets-exposure` |
| IAM anomaly, privilege escalation, root usage | `identity-access-risk` |
| Unusual user behavior, insider threat indicators | `behavioral-analytics` |
| Cryptographic key management risk | `cryptography-key-management` |

### Threats and hunting

| Situation | Agent |
|---|---|
| Hypothesis-driven threat hunt | `threat-hunting` |
| IOC enrichment and actor attribution | `threat-intelligence` |
| Anomaly or behavioral deviation | `behavioral-analytics` |
| Active network intrusion or lateral movement | `threat-hunting` → `incident-classification` |

### Vulnerabilities and patching

| Situation | Agent |
|---|---|
| CVE triage and prioritization | `vulnerability-management` |
| Zero-day, no patch available | `zero-day-response` |
| Code scanning (SAST/DAST) results | `sast-dast-coordinator` |
| IaC misconfiguration | `iac-security` |
| Cloud posture and drift | `cloud-security-posture` |
| Dependency and SBOM analysis | `supply-chain-risk` |

### Cloud and infrastructure

| Situation | Agent |
|---|---|
| AWS/Azure/GCP misconfiguration scan | `cloud-security-posture` |
| Public attack surface mapping | `attack-surface-management` |
| Network exposure and open ports | `network-exposure` |
| Endpoint and OS security | `endpoint-os-security` |
| OT/ICS/IoT device security | `ot-iot-device-security` |
| Build pipeline integrity | `build-integrity` |

### Detection and engineering

| Situation | Agent |
|---|---|
| Write a detection rule for a new TTP | `detection-engineering` |
| Assess telemetry data quality | `telemetry-signal-quality` |
| Continuous automated pentesting results | `continuous-pentesting` |
| AI/LLM agent integrity and prompt injection | `agent-integrity-monitor` |

### Architecture and design

| Situation | Agent |
|---|---|
| Threat model a new system or feature | `risk-threat-modeling` |
| Security architecture review | `security-architecture` |
| AI system ethics and governance | `ai-ethics-governance` |
| AI agent security assessment | `ai-agent-security` |

### Compliance and governance

| Situation | Agent |
|---|---|
| Map findings to compliance frameworks | `compliance-mapping` |
| Track regulatory horizon changes | `regulatory-horizon` |
| Internal audit and SOC 2 evidence | `internal-audit-assurance` |
| Privacy DPIA for a new feature | `privacy-dpia` |
| Security policy and control assessment | `security-policy-control` |
| Cyber insurance risk inputs | `cyber-insurance` |
| Quantum cryptography readiness | `quantum-security-readiness` |

### Supply chain and third parties

| Situation | Agent |
|---|---|
| Dependency and package risk | `supply-chain-risk` |
| Supply chain attack simulation | `supply-chain-simulation` |
| Vendor and third-party risk assessment | `third-party-vendor-risk` |

### Red team and adversary simulation

| Situation | Agent |
|---|---|
| Red team campaign planning | `red-team-planner` |
| Red team execution and Kill Chain | `red-team-operations` |
| Safe, scoped exploitation | `safe-exploitation` |
| Attack path analysis | `attack-path-analysis` |
| Security research and vulnerability discovery | `security-research` |

### Operations and reporting

| Situation | Agent |
|---|---|
| Track and triage security findings | `findings-tracker` |
| Security metrics and KPI reporting | `metrics-reporting` |
| Knowledge base and lessons learned | `knowledge-management` |
| Security awareness and training | `security-awareness` |
| Orchestrate a multi-agent workflow | `orchestrator` |

---

## All 56 agents

| Slug | Level | Category | Description |
|---|---|---|---|
| `agent-integrity-monitor` | L3 | Detection | Monitors AI agent outputs for integrity violations, prompt injection, and manipulation |
| `ai-agent-security` | L3 | Detection | Security assessment of AI/LLM agents: input validation, output sanitization, trust boundaries |
| `ai-ethics-governance` | L2 | Governance | AI ethics review, bias assessment, and responsible AI governance for AI system deployments |
| `attack-path-analysis` | L3 | Analysis | Maps attacker lateral movement paths through network topology to reach target assets |
| `attack-surface-management` | L3 | Analysis | Discovers and inventories public-facing attack surface: domains, IPs, ports, web assets |
| `behavioral-analytics` | L3 | Detection | UEBA: entity risk scoring, insider threat pattern detection, account takeover identification |
| `build-integrity` | L3 | Detection | Verifies software build pipeline integrity: artifact signing, provenance, reproducibility |
| `cloud-security-posture` | L4 | Cloud | CSPM: AWS/Azure/GCP posture evaluation against CIS Benchmarks, drift detection, compliance mapping |
| `compliance-mapping` | L2 | Compliance | Maps security findings to regulatory frameworks: GDPR, PCI DSS, HIPAA, SOC 2, ISO 27001 |
| `containment-advisor` | L3 | Response | Recommends containment strategies across 10 threat types; assesses blast radius and production impact |
| `continuous-pentesting` | L3 | Testing | Interprets and prioritizes automated continuous penetration testing results |
| `cryptography-key-management` | L3 | Identity | Assesses cryptographic key lifecycle risk: weak algorithms, key rotation gaps, HSM gaps |
| `cyber-insurance` | L2 | Governance | Evaluates cyber insurance coverage adequacy against incident scenarios and risk profile |
| `data-security-classification` | L3 | Data | Classifies data assets by sensitivity, maps to regulatory requirements, recommends controls |
| `detection-engineering` | L3 | Detection | Designs and validates SIEM/EDR detection rules in Sigma, KQL, SPL, YARA with MITRE mapping |
| `devsecops-pipeline` | L3 | DevSecOps | Security gate assessment for CI/CD pipelines: secrets scanning, SAST, DAST, SCA integration |
| `endpoint-os-security` | L4 | Endpoint | Endpoint and OS security assessment: patch status, EDR coverage, hardening baselines |
| `enterprise-risk-assessment` | L2 | Risk | Board-level enterprise risk assessment: risk aggregation, heat maps, risk appetite alignment |
| `findings-tracker` | L3 | Operations | Tracks, triages, deduplicates, and ages security findings across the vulnerability lifecycle |
| `forensics` | L3 | Response | Legally defensible digital forensics: DFRWS six-phase framework, chain-of-custody, dwell time |
| `guardrail` | L3 | Governance | Enforces USAP output contracts and intent classification guardrails on agent outputs |
| `iac-security` | L3 | DevSecOps | Infrastructure-as-Code security analysis: Terraform, CloudFormation, Kubernetes manifests |
| `identity-access-risk` | L4 | Identity | IAM anomaly detection, privilege escalation analysis, CloudTrail pattern matching (5 patterns) |
| `incident-classification` | L3 | Response | Universal first-triage: classifies events into 14 types, assigns severity, identifies false positives |
| `incident-commander` | L2 | Response | Active incident command (ICS model): SEV1-4 declaration, response tracks, regulatory deadlines |
| `insider-physical-risk` | L3 | Detection | Insider threat and physical security risk assessment combining behavioral and physical indicators |
| `internal-audit-assurance` | L2 | Compliance | Internal audit evidence collection: SOC 2, ISO 27001, SOX IT general controls |
| `knowledge-management` | L2 | Operations | Security knowledge base management: lessons learned, runbook quality, knowledge gap identification |
| `metrics-reporting` | L2 | Reporting | Security KPI and metrics reporting: MTTR, MTTD, patch coverage, SLA compliance |
| `network-exposure` | L3 | Network | Network exposure assessment: open ports, firewall rule analysis, internet-facing service inventory |
| `orchestrator` | L2 | Orchestration | Multi-agent workflow orchestration: routes events, sequences agents, manages cascade logic |
| `ot-iot-device-security` | L4 | OT/IoT | OT/ICS/IoT device security: protocol analysis, firmware assessment, network segmentation gaps |
| `privacy-dpia` | L2 | Compliance | Data Protection Impact Assessment for GDPR-applicable features and processing activities |
| `quantum-security-readiness` | L2 | Risk | Post-quantum cryptography readiness: identifies vulnerable algorithms, migration planning |
| `red-team-operations` | L3 | Red Team | Kill Chain execution planning: OPSEC, C2 design, lateral movement, exfil staging (requires authorization) |
| `red-team-planner` | L3 | Red Team | Red team campaign planning: objectives, scope, RoE, phase map, authorization validation |
| `regulatory-horizon` | L2 | Compliance | Tracks emerging regulatory requirements and their security control implications |
| `risk-threat-modeling` | L1 | Risk | STRIDE/PASTA/LINDDUN threat modeling: DFDs, risk scoring (Likelihood × Impact), MITRE mapping |
| `safe-exploitation` | L3 | Testing | Scoped, safe exploitation execution with minimal footprint and mandatory abort conditions |
| `sast-dast-coordinator` | L3 | DevSecOps | Coordinates and interprets SAST, DAST, and SCA scan results; deduplicates findings |
| `secrets-exposure` | L4 | Detection | Credential exposure analysis: 15 secret types, entropy scoring, blast radius, attacker timeline |
| `secure-sdlc` | L3 | DevSecOps | Secure software development lifecycle: security requirements, design review, code review guidance |
| `security-architecture` | L2 | Architecture | Security architecture review: zero trust assessment, control coverage gaps, architecture risk |
| `security-awareness` | L2 | Training | Security awareness program assessment: phishing simulation results, training effectiveness |
| `security-policy-control` | L2 | Governance | Security policy adequacy review: gap analysis against frameworks, control effectiveness |
| `security-research` | L3 | Research | Vulnerability research and responsible disclosure guidance |
| `supply-chain-risk` | L3 | Risk | SBOM analysis, malicious package detection (5 categories), SLSA build integrity assessment |
| `supply-chain-simulation` | L3 | Risk | Simulates supply chain attack scenarios to test detection and response capabilities |
| `telemetry-signal-quality` | L3 | Detection | Assesses telemetry data quality, dedup confidence, normalization errors, data source health |
| `third-party-vendor-risk` | L2 | Risk | Third-party and vendor risk assessment: security questionnaires, contract risk, SLA gaps |
| `threat-hunting` | L3 | Detection | Hypothesis-driven, IOC-driven, and anomaly-driven threat hunting with 4 built-in playbooks |
| `threat-intelligence` | L3 | Intelligence | Threat intelligence enrichment: IOC analysis, actor attribution, TTP mapping |
| `tool-execution-broker` | L4 | Operations | Mediates tool execution requests from agents: scope validation, approval gating, execution logging |
| `vulnerability-management` | L3 | Vulnerability | Full vulnerability lifecycle: CVSS v3.1 + EPSS scoring, SLA-based prioritization, remediation tracking |
| `zero-day-response` | L3 | Response | Zero-day compensating controls: exposure scoring, 5 control options, vendor timeline tracking |
| `zero-day-response-governance` | L2 | Governance | Board/executive coordination for zero-day events: communication matrix, regulatory deadlines |

---

## Standalone use (no USAP required)

Paste any `SKILL.md` into your LLM as the system prompt, then send a security event as the user message.

```bash
# View a SKILL.md
cat secrets-exposure/SKILL.md

# Minimal user message structure
{
  "event_type": "secret_exposure",
  "severity": "critical",
  "raw_payload": {
    "file_path": "config/prod.env",
    "matched_pattern": "aws_access_key",
    "branch": "main"
  }
}
```

The LLM returns a structured JSON recommendation with `action`, `rationale`, `intent_type`, `confidence`, `key_findings`, `evidence_references`, and `timestamp_utc`.

---

## Use with USAP

This repo is the default `skills/` submodule in the USAP platform.

```bash
# Clone USAP with all public skills
git clone --recurse-submodules https://github.com/jaskaranhundal/usap.git

# To add private bug bounty skills alongside:
git submodule add https://github.com/jaskaranhundal/usap-bugbounty skills-bb
echo "USAP_SKILLS_PATHS=./skills,./skills-bb" >> .env
python3 -m usap.cli validate-agents   # 63 agents valid
```

---

## Skill package structure

```
<slug>/
  SKILL.md                              # LLM system prompt + YAML frontmatter
  README.md                             # This file — what the agent does
  references/
    workflow.md                         # Step-by-step analyst workflow
    *.md                                # Domain-specific reference documents
  assets/
    templates/
      output-template.json              # Output schema template
  expected_outputs/
    sample_output.json                  # Representative output example
  scripts/
    <slug>_tool.py                      # CLI tool
    pre_analysis.py                     # Optional: deterministic pre-analysis
```

---

## Shared utilities

`shared/scripts/` contains tools used across multiple skill packages:

| Script | Description |
|---|---|
| `cvss_scorer.py` | CVSS v3.1 base score calculator — no dependencies |
| `bb_scope_enforcer.py` | Bug bounty scope enforcement — validates targets against scope file |

See [`shared/README.md`](shared/README.md) for usage.

---

## Contributing

To add a new agent, open a PR against this repo. See [CONTRIBUTING.md](CONTRIBUTING.md) for the full authoring guide including frontmatter requirements, SKILL.md body structure, and quality bar.

---

## License

Apache 2.0 — see [LICENSE](LICENSE).
