# Red Team Domain — CLAUDE.md

---

## AUTHORIZATION REQUIRED

No skill in this domain may be invoked without explicit written authorization from the asset owner. Authorization must be verified before any engagement planning, execution, or tooling begins. The `red-team-planner` skill performs authorization document validation as its first action. Any skill invocation that bypasses the authorization gate is a policy violation and must be halted immediately.

If you are uncertain whether authorization covers a specific system, scope boundary, or technique, **stop and confirm in writing** before proceeding.

---

## Purpose

The `red-team/` domain contains skills for planning, executing, and reporting on adversarial security testing operations. Skills span the full engagement lifecycle: from objectives definition and Rules of Engagement documentation through kill chain execution planning, safe exploitation, automated continuous testing, lateral movement path analysis, AI/ML adversarial testing, and original security research.

Subdomains covered:

- Engagement planning and authorization (objectives, scope, RoE, phase mapping)
- Red team operations and kill chain execution (OPSEC, C2 design, lateral movement, exfil staging)
- Safe exploitation (scoped, minimal-footprint exploitation with abort conditions)
- Continuous and automated penetration testing (BAS, automated attack simulation, finding prioritization)
- Attack path analysis (lateral movement path mapping, target asset reachability)
- AI/ML adversarial testing (prompt injection, jailbreaks, model inversion, training data extraction)
- Security research (CVE research, PoC development, responsible disclosure)

All skills in this domain are subject to the Authorization Gate defined below. Skills that produce mutating actions on target systems (exploitation, C2 deployment, lateral movement) require an approved RoE document with defined scope boundaries and abort procedures before any action is taken.

---

## Skills Catalog

| Skill | Slug | Primary Tool | Coverage |
|---|---|---|---|
| red-team-planner | `red-team/red-team-planner` | `red-team-planner_tool.py` | Engagement planning, objectives definition, scope boundary documentation, RoE validation, phase map generation |
| red-team-operations | `red-team/red-team-operations` | `red-team-operations_tool.py` | Kill chain execution planning, OPSEC design, C2 architecture, lateral movement playbooks, exfil staging |
| safe-exploitation | `red-team/safe-exploitation` | `safe-exploitation_tool.py` | Scoped exploitation within defined RoE, minimal footprint, mandatory abort conditions, post-exploitation scope enforcement |
| continuous-pentesting | `red-team/continuous-pentesting` | `continuous-pentesting_tool.py` | BAS (Breach and Attack Simulation) result interpretation, automated pentest finding prioritization, coverage gap identification |
| attack-path-analysis | `red-team/attack-path-analysis` | `attack-path-analysis_tool.py` | Lateral movement path mapping through network topology, target asset reachability analysis, choke point identification |
| ai-red-teaming | `red-team/ai-red-teaming` | `ai-red-teaming_tool.py` | Adversarial testing of AI/ML systems: prompt injection, jailbreaks, model inversion, training data extraction, alignment bypass |
| security-research | `red-team/security-research` | `security-research_tool.py` | CVE research, PoC development (scoped), vulnerability reproduction, responsible disclosure workflow |

All skill paths are relative from the repository root as `red-team/<slug>/`. For example, the red-team-planner skill lives at `red-team/red-team-planner/`.

---

## Python Tools Reference

| Tool | Path | Purpose | Key Args |
|---|---|---|---|
| `red-team-planner_tool.py` | `red-team/red-team-planner/scripts/red-team-planner_tool.py` | Engagement phase planning, RoE document generation, scope boundary definition, authorization validation | `--objective`, `--scope-file`, `--duration-days`, `--output` |
| `red-team-operations_tool.py` | `red-team/red-team-operations/scripts/red-team-operations_tool.py` | Kill chain phase planning, C2 architecture selection, OPSEC profile generation, lateral movement playbook selection | `--phase`, `--opsec-level`, `--c2-type`, `--output` |
| `safe-exploitation_tool.py` | `red-team/safe-exploitation/scripts/safe-exploitation_tool.py` | Scoped exploitation execution planning, abort condition definition, post-exploitation scope enforcement, footprint minimization | `--target`, `--scope-file`, `--abort-conditions`, `--output` |
| `continuous-pentesting_tool.py` | `red-team/continuous-pentesting/scripts/continuous-pentesting_tool.py` | BAS result ingestion and prioritization, automated pentest coverage gap analysis, finding deduplication | `--bas-results`, `--framework`, `--priority-threshold`, `--output` |
| `attack-path-analysis_tool.py` | `red-team/attack-path-analysis/scripts/attack-path-analysis_tool.py` | Lateral movement path enumeration, reachability analysis from a starting node to a target asset, choke point identification | `--source-node`, `--target-asset`, `--topology-file`, `--output` |
| `ai-red-teaming_tool.py` | `red-team/ai-red-teaming/scripts/ai-red-teaming_tool.py` | AI/ML adversarial test case generation, prompt injection and jailbreak catalog execution, output risk classification | `--model-endpoint`, `--test-type`, `--attack-catalog`, `--output` |
| `security-research_tool.py` | `red-team/security-research/scripts/security-research_tool.py` | CVE research workflow, PoC scope validation, vulnerability reproduction environment setup, disclosure timeline generation | `--cve-id`, `--target-version`, `--disclosure-deadline`, `--output` |

All tools accept `--help` for full usage and `--output json` for machine-readable output.

```bash
# Quick invocation pattern for any tool in this domain
python red-team/<slug>/scripts/<slug>_tool.py --help
python red-team/<slug>/scripts/<slug>_tool.py --output json
```

---

## Authorization Gate

The following checklist must be satisfied before any red team skill is invoked. The `red-team-planner` skill validates these items as part of its opening workflow. Do not bypass this gate.

**Mandatory Pre-Engagement Authorization Checklist:**

- [ ] Signed Rules of Engagement (RoE) document on file, signed by the asset owner and the engagement lead
- [ ] Defined scope boundaries documented: IP ranges, domains, system names, and cloud accounts in scope
- [ ] Explicit out-of-scope declarations documented: systems, networks, and actions that are prohibited
- [ ] Emergency contact list: client technical contact, client executive sponsor, engagement lead, abort escalation path
- [ ] Abort procedures defined: conditions that trigger immediate halt, how abort is signaled, who is notified
- [ ] Data handling agreement for discovered vulnerabilities: how findings are stored, who has access, retention period
- [ ] Legal authorization letter from the asset owner or their designated representative
- [ ] Notification of affected system owners if engagement is not fully covert (purple team or overt assessment)
- [ ] Engagement start and end dates/times confirmed in writing

**For AI red teaming specifically:**
- [ ] Written authorization from the AI system owner, separate from general system authorization
- [ ] Confirmation that the model endpoint is a non-production instance or that production testing is explicitly authorized
- [ ] Data handling agreement covering model outputs, extracted embeddings, and any training data artifacts discovered

**For security research and PoC development specifically:**
- [ ] Confirmation that the research target is a system the researcher owns, a purpose-built lab environment, or an authorized bug bounty target
- [ ] Disclosure timeline agreed with the vendor prior to PoC development
- [ ] PoC scope reviewed and approved: no weaponization beyond minimum necessary to demonstrate impact

---

## Engagement Lifecycle

This six-phase lifecycle connects all skills in the domain. Each phase has a defined entry condition, responsible skill, and exit artifact that gates the next phase.

### Phase 1: Authorization and Planning

**Entry condition:** Engagement request received with initial scope description.

**Responsible skill:** `red-team-planner`

**Actions:** Validate all Authorization Gate checklist items. Define engagement objectives using the threat model (what adversary are we emulating?). Document scope boundaries. Generate phase map with timeline. Define success criteria for each phase.

**Exit artifact:** Signed RoE document, engagement phase map, threat actor profile, success criteria register.

---

### Phase 2: Reconnaissance

**Entry condition:** Phase 1 exit artifacts approved.

**Responsible skill:** `red-team-operations` (planning), `attack-path-analysis` (topology mapping)

**Actions:** Define reconnaissance activities permitted within scope (passive OSINT vs. active scanning). Map known network topology. Identify initial access targets. Generate a reconnaissance playbook aligned to the emulated threat actor's known TTPs.

**Exit artifact:** Target profile document, network topology map, initial access candidate list, reconnaissance playbook.

---

### Phase 3: Initial Access and Exploitation

**Entry condition:** Phase 2 exit artifacts reviewed and exploitation scope confirmed in writing.

**Responsible skill:** `safe-exploitation`

**Actions:** Execute scoped exploitation attempts against in-scope targets using minimal footprint techniques. Validate each action against abort conditions before execution. Document all actions with timestamps. Halt and escalate immediately if an abort condition is triggered.

**Exit artifact:** Exploitation attempt log, confirmed initial access record (or null result), abort condition status report.

---

### Phase 4: Lateral Movement and Objective Pursuit

**Entry condition:** Confirmed initial access from Phase 3. Lateral movement explicitly authorized in RoE.

**Responsible skill:** `red-team-operations`, `attack-path-analysis`

**Actions:** Map lateral movement paths from initial access point to target assets. Select minimum-necessary lateral movement techniques. Execute within scope constraints. Document each step. Identify choke points and defensive gaps.

**Exit artifact:** Lateral movement path record, choke point analysis, target asset reachability verdict, access chain documentation.

---

### Phase 5: Continuous and Automated Coverage

**Entry condition:** Manual engagement phases complete or running in parallel with ongoing BAS program.

**Responsible skill:** `continuous-pentesting`

**Actions:** Ingest BAS tool results. Prioritize findings by exploitability and impact. Identify coverage gaps between automated and manual testing. Validate that critical paths from Phase 4 are represented in the BAS test catalog.

**Exit artifact:** BAS coverage gap report, finding priority matrix, recommended BAS catalog updates.

---

### Phase 6: Reporting and Remediation Handoff

**Entry condition:** All authorized phases complete.

**Responsible skill:** `red-team-planner` (report structure), all skills (finding contribution)

**Actions:** Aggregate all phase artifacts. Map findings to ATT&CK techniques. Generate executive summary with risk-ordered findings. Produce technical finding reports with reproduction steps, impact assessment, and remediation recommendations. Schedule remediation validation re-test window.

**Exit artifact:** Executive summary, technical findings report, ATT&CK Navigator coverage map for the engagement, remediation validation schedule.

---

## Kill Chain Phase Coverage Matrix

| Kill Chain Phase | Primary Skills | Key Outputs |
|---|---|---|
| Reconnaissance | red-team-operations, attack-path-analysis | Target profile, initial access candidates, topology map |
| Weaponization | red-team-planner, security-research | Threat actor TTP alignment, PoC scope validation |
| Delivery | safe-exploitation, red-team-operations | Scoped delivery method selection, abort conditions |
| Exploitation | safe-exploitation | Exploitation attempt log, confirmed access record |
| Installation | red-team-operations, safe-exploitation | C2 implant design (scoped), persistence documentation |
| Command and Control | red-team-operations | C2 architecture plan, OPSEC profile, beacon interval |
| Actions on Objectives | attack-path-analysis, safe-exploitation | Lateral movement record, target asset reachability, objective verdict |

AI system attack phases (for `ai-red-teaming`):

| AI Attack Phase | Skill | Key Outputs |
|---|---|---|
| Prompt injection | ai-red-teaming | Injection success rate, affected output categories |
| Jailbreak | ai-red-teaming | Jailbreak technique catalog results, bypass rate |
| Model inversion | ai-red-teaming | Data reconstruction risk score, PII extraction risk |
| Training data extraction | ai-red-teaming | Memorization indicators, verbatim reproduction rate |
| Alignment bypass | ai-red-teaming | Safety filter bypass catalog, risk classification |

---

## Domain Best Practices

1. **Authorization is not optional and cannot be assumed from context.** A verbal agreement, a previous engagement authorization, or an inferred permission is not authorization. The engagement does not begin until a signed RoE document with explicit scope boundaries is in hand. If the authorization document is ambiguous about whether a specific system is in scope, treat it as out of scope and request a written clarification before proceeding.

2. **Operate with the minimum footprint necessary to demonstrate impact.** Red team operations are not exercises in thoroughness of access — they are exercises in demonstrating that a defined adversary could achieve a defined objective. Do not persist on systems, escalate privileges, or exfiltrate data beyond what is necessary to prove the finding. Every unnecessary action increases the probability of causing unintended harm and complicates the deconfliction process.

3. **Document every action with a timestamp before executing it.** A red team log that is reconstructed from memory after the engagement is not a defensible record. Log each action, the tool used, the target system, the timestamp, and the outcome in real time. If an abort condition is triggered, the log is evidence. If a production system is accidentally impacted, the log is the deconfliction record.

4. **Abort conditions are not suggestions — they are hard stops.** Before each exploitation phase, abort conditions must be explicitly defined and agreed upon: what triggers an immediate halt, how the halt is signaled to the client, and who is notified. When an abort condition is triggered, stop all activity immediately, notify the client emergency contact, and wait for written confirmation before resuming any activity.

5. **Never conduct AI red teaming against production model endpoints without explicit written authorization.** AI/ML models in production serve real users. Adversarial inputs can cause real service disruption, expose other users' data through model memory, or permanently affect model behavior through persistent context mechanisms. The authorization for AI red teaming must explicitly name the model endpoint, the production vs. staging classification, and the test types permitted.

6. **Security research PoCs must stop at minimum reproducibility.** A PoC that demonstrates a vulnerability is in scope. A PoC that is weaponized into a reliable exploit for distribution is not. The `security-research` skill enforces a scope gate before PoC development proceeds. If a CVE research finding has potential for significant real-world harm, coordinate with the vendor on disclosure timeline before any PoC work begins, regardless of whether a bug bounty program is in scope.

7. **Deconflict with the client's defensive team before and after each major phase.** A fully covert engagement that is detected by the client's SOC and escalated as a real incident is a test failure — not a success. Agree on a deconfliction protocol in the RoE: how the client contacts the engagement team, what information is shared, and how a real incident is distinguished from engagement activity. Purple team and overt engagement models should use real-time deconfliction throughout.

8. **Map all findings to ATT&CK techniques before the final report.** Findings that are not mapped to ATT&CK provide limited value for defensive improvement. The ATT&CK mapping in the final report enables the detection engineering team to directly identify coverage gaps and the threat intelligence team to correlate engagement activity with known actor profiles. Every finding must include at minimum one ATT&CK technique ID and one detection recommendation.

---

## Workflow: Full Red Team Engagement

```
red-team-planner  →  red-team-operations  →  safe-exploitation  →  attack-path-analysis
                                                                            |
                                          continuous-pentesting  ←──────────┘
                                                   |
                                          security-research  (if CVE or novel technique)
                                                   |
                                          red-team-planner  (report phase)
```

For AI system targets, `ai-red-teaming` runs in parallel with `safe-exploitation` and `attack-path-analysis` against the AI/ML component scope defined in the RoE.

---

## MITRE ATT&CK Technique Coverage

| Technique | ID | Covering Skills |
|---|---|---|
| Active Scanning | T1595 | red-team-operations, attack-path-analysis |
| Gather Victim Network Information | T1590 | red-team-operations, attack-path-analysis |
| Exploit Public-Facing Application | T1190 | safe-exploitation |
| Valid Accounts | T1078 | safe-exploitation, red-team-operations |
| Spearphishing Attachment | T1566.001 | red-team-operations |
| Command and Scripting Interpreter | T1059 | red-team-operations, safe-exploitation |
| Remote Services | T1021 | red-team-operations, attack-path-analysis, safe-exploitation |
| Lateral Tool Transfer | T1570 | red-team-operations, attack-path-analysis |
| Pass the Hash / Pass the Ticket | T1550 | safe-exploitation, attack-path-analysis |
| Exfiltration Over C2 Channel | T1041 | red-team-operations |
| Ingress Tool Transfer | T1105 | red-team-operations |
| Application Layer Protocol — C2 | T1071 | red-team-operations |
| Masquerading | T1036 | red-team-operations (OPSEC profile) |
| Indicator Removal | T1070 | red-team-operations (OPSEC profile) |
| Exploit for Privilege Escalation | T1068 | safe-exploitation |
| Scheduled Task — Persistence | T1053 | red-team-operations |
| Account Manipulation | T1098 | safe-exploitation, red-team-operations |

AI/ML-specific coverage:

| Technique | Description | Covering Skill |
|---|---|---|
| Prompt Injection | Adversarial input that overrides model instructions | ai-red-teaming |
| Jailbreak | Technique to bypass model safety filters | ai-red-teaming |
| Model Inversion | Extracting training data from model outputs | ai-red-teaming |
| Membership Inference | Determining if a record was in training data | ai-red-teaming |
| Training Data Poisoning | Corrupting model behavior via training input manipulation | ai-red-teaming (research scope) |

---

## Related Domains

### detection/ (adversarial validation)

The red team domain and the detection domain have a direct adversarial validation relationship:

- `red-team-operations` and `safe-exploitation` findings identify detection gaps. These gaps are consumed by `detection/detection-engineering` to author new rules and coverage improvements.
- `detection/behavioral-analytics` is tested during the engagement to determine whether insider-threat-style activity from the red team is detected. UEBA evasion findings feed back to `detection/behavioral-analytics` for threshold calibration.
- The ATT&CK Navigator coverage map produced in the engagement final report is directly consumed by `detection/detection-engineering` for coverage gap prioritization.

Full domain reference: `detection/CLAUDE.md`

### appsec-devsecops/

- `security-research` findings (particularly web application vulnerabilities and supply chain findings) overlap with `appsec-devsecops/sast-dast-coordinator` scope. Deduplicate findings before reporting to avoid double-counting in the risk register.
- `safe-exploitation` and `red-team-operations` findings against application targets feed `appsec-devsecops/pipeline-security-scan` with validation evidence: confirmed exploitable vulnerabilities that SAST/DAST missed indicate scanner coverage gaps.
- `ai-red-teaming` findings against AI systems used in the development pipeline (code suggestion models, AI-assisted review) are shared with `appsec-devsecops/` for secure AI integration guidance.

Full domain reference: `appsec-devsecops/CLAUDE.md`

---

## Path Reference

All skill paths in this domain are relative from the repository root using the convention `red-team/<slug>/`. Sub-paths within each skill follow the standard USAP skill layout:

```
red-team/<slug>/
  README.md          -- skill overview and quick commands
  SKILL.md           -- full skill specification and methodology
  scripts/           -- executable Python tools
  references/        -- supporting documentation
  expected_outputs/  -- representative tool outputs for validation
  assets/            -- supporting data files
```

To invoke any tool directly from the repository root:

```bash
python red-team/<slug>/scripts/<tool>.py --help
```

Examples:

```bash
python red-team/red-team-planner/scripts/red-team-planner_tool.py \
  --scope-file ./scope.json --duration-days 14 --output json

python red-team/safe-exploitation/scripts/safe-exploitation_tool.py \
  --target 10.1.2.3 --scope-file ./scope.json --output json

python red-team/attack-path-analysis/scripts/attack-path-analysis_tool.py \
  --source-node 10.1.2.3 --target-asset db-prod-01 --topology-file ./topology.json --output json

python red-team/ai-red-teaming/scripts/ai-red-teaming_tool.py \
  --model-endpoint https://api.internal/v1/chat --test-type prompt-injection --output json
```

---

## Authoring Notes

When adding a new skill to this domain:

1. Place the skill directory under `red-team/<slug>/`.
2. Follow the domain Python tool naming convention: `<slug>_tool.py` in `scripts/`.
3. Update this CLAUDE.md Skills Catalog table and Kill Chain Phase Coverage Matrix.
4. Update the root `README.md` Domain Index table entry for `Red Team`.
5. Update `domains/red-team.md` with the new skill slug and level.
6. Confirm the Authorization Gate section covers the new skill's specific authorization requirements. If the skill has unique authorization needs, add a dedicated sub-section.
7. Ensure all MITRE ATT&CK technique mappings relevant to the new skill are added to the coverage section above.
8. Document the skill's relationship to the detection domain for adversarial validation purposes.
