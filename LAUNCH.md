# Launch Playbook

This file is **local launch ammunition**: pre-written posts, PR templates, and target lists you can copy-paste when announcing or cross-posting USAP. Nothing here is automated; nothing claims metrics that aren't real. Edit before sending.

## Why this exists

The README converts visitors; LAUNCH.md feeds them visitors. The product is good. The distribution is the bottleneck.

## Principles (read these first)

1. **Don't fabricate metrics.** Don't say "10k downloads" or "used by Fortune 500" unless it's true. The repo's strength is the artifact, not the hype.
2. **Lead with the artifact.** Every post should link a real file in the repo — a `SKILL.md`, a `sample_output.json`, the architecture SVG, or the demo SVG. Show, don't tell.
3. **Be specific about who it's for.** "SOC engineers", "AppSec leads on Claude Code", "MSSPs writing CVSS-tagged deliverables." Generic security ICPs convert worse than a sharp persona.
4. **Engage in the comments.** The post is the beachhead. Replies decide whether it stays on the front page. Be in the thread for the first 4 hours.

## Where to post (priority order)

| Channel | Why first | Format |
|---|---|---|
| **Show HN** | Highest-quality engineering audience; long reach if it sticks. Best on Tue–Thu morning Pacific. | "Show HN: USAP — open-source AI cybersecurity skills, 11-field output contract, runs in any LLM" |
| **Hacker News (top)** | Same audience, no "Show HN" tag — use when you have a story angle (a release, an essay, a benchmark). | Linked to a blog post or `CHANGELOG.md` entry. |
| **r/netsec** | Security practitioners. Strict moderation — read the rules before posting. | Self-post; link to a specific skill, not the repo root. |
| **r/cybersecurity** | Broader audience, more permissive. | Same as r/netsec. |
| **r/programming** | Cross-post the technical angle: the typed contract + the validator gate. | Title leads with the engineering, not the security. |
| **lobste.rs** | Smaller but high-signal. Need an invite. | Same as Show HN. |
| **Twitter / X** | Use the thread template below. | Threads (5–8 tweets), not single posts. |
| **LinkedIn** | The actual audience of CISOs, MSSPs, hiring managers. | The long-form post in `LAUNCH-LINKEDIN.md` below. |
| **r/ClaudeAI, r/LocalLLaMA, r/OpenAI** | LLM-first audience, less security context. | Frame as "skills that run in any LLM, here's the contract." |
| **Discord — Anthropic, Claude Code, MCP communities** | Builders, not consumers. | Pin a "first-skill" tutorial. |

## Awesome-list submission targets

Each entry below is a real list to PR. Each one is one-line in their README. Don't bulk-PR all at once — file 2 per week so the contribution looks organic, not spammy.

| Repo | List entry to submit | Section |
|---|---|---|
| `sindresorhus/awesome` | `[usap-skills](https://github.com/jaskaranhundal/usap-skills) — Open-source AI cybersecurity skills with a typed 11-field output contract.` | Probably "Security" |
| `paragonie/awesome-appsec` | `[USAP](https://github.com/jaskaranhundal/usap-skills) — 79 AI security skills + 12 cs-* orchestrator agents` | "Online Resources" |
| `sbilly/awesome-security` | Same as above | "Defense" |
| `hslatman/awesome-threat-intelligence` | Frame as MITRE-mapped threat skills | "Tools" |
| `pe3zx/my-infosec-awesome` | Generic security tooling | "Tools and Resources" |
| `infosecn1nja/awesome-bugbounty-tools` | If you frame the red-team skills strongly | "Tools and Resources" |
| `JonnyBanana/Awesome-AI-Security` | Direct fit — AI + security | Main |
| `JohnHammond/awesome-claude-code` (if exists) | Frame as "Claude-Code-compatible agentskills.io conformant" | Main |
| `mcp-sec/awesome-mcp` | MCP angle | Main |

PR template for each:

```
Hi — adding USAP, an open-source AI cybersecurity skills library.

Why I think it fits this list: <one sentence specific to this list's theme>.

What it is: 79 SKILL.md packages + 12 cs-* orchestrator agents, Apache 2.0, with a typed 11-field JSON output contract validated in CI. Maps every skill to MITRE ATT&CK and NIST CSF 2.0. Runs in any LLM (Claude, ChatGPT, Gemini, Ollama, AnythingLLM).

Happy to adjust the description or section placement.
```

## Show HN draft

**Title:** `Show HN: USAP — 79 cybersecurity skills with a typed 11-field output contract, MIT-stack`

**Body:**

```
USAP is an open-source library of cybersecurity skills you can paste into any LLM (Claude, ChatGPT, Gemini, Ollama, AnythingLLM) and get auditable security workflows out the other end. It's 79 SKILL.md system prompts + 12 cs-* orchestrator agents, Apache 2.0.

The piece I'm proud of is the typed 11-field output contract every skill emits — agent_slug, intent_type, action, rationale, confidence, severity, key_findings, evidence_references, next_agents, human_approval_required, timestamp_utc. CI runs a validator against every committed sample on every push, so the contract is checked, not just documented. The standards live at standards/output-contract.md.

A second piece I like: every skill carries machine-readable metadata.frameworks.{mitre_attack,nist_csf,owasp_top10,d3fend,mitre_atlas,nist_ai_rmf} arrays in its YAML frontmatter, and a stdlib generator (tools/framework_extractor.py) emits a live MITRE ATT&CK Navigator layer and a NIST CSF 2.0 coverage doc from those. CI fails on drift between source and generated docs — so the framework mappings can't quietly rot.

The cs-* agents (cs-security-analyst, cs-incident-responder, cs-red-teamer, cs-appsec-engineer, cs-ciso-advisor, …) compose the skills into workflows. There's an interactive 3-screen UI kit at docs/design-system/ui_kits/platform/index.html that renders the cs-appsec-engineer → vuln-scan → finding-triage flow, and the JSON the demo shows is byte-identical to the committed sample.

Not a SaaS. No vendor cloud. Designed for SOC + AppSec teams that already own LLM access.

Repo: https://github.com/jaskaranhundal/usap-skills
Demo (animated SVG of the flow): https://github.com/jaskaranhundal/usap-skills/blob/main/docs/assets/usap-alex-demo.svg
Output contract spec: https://github.com/jaskaranhundal/usap-skills/blob/main/standards/output-contract.md
```

Replies-to-expect notes (have answers ready):
- *Is this just prompts in a folder?* No — every skill ships with a Python `*_tool.py` stub + a `sample_output.json` + validator gates. Skills are the prompt; tools are the executable harness around them.
- *Why not LangChain / autogen / etc?* USAP is the substrate those frameworks compose, not a competitor. The skills can be invoked from any agent runtime that can paste a system prompt.
- *Where are the real-world results?* Honest answer: this is the substrate, not yet adoption. The repo's strength is the contract and the framework mapping discipline. Adoption is the next phase.
- *What's the v1.0 vs v1.1 differentiator?* See CHANGELOG.md.

## r/netsec / r/cybersecurity self-post

**Title:** `Open-source 79-skill cybersecurity library with a typed 11-field output contract — runs in any LLM`

**Body:**

```
Sharing USAP, an open-source skills library I've been building. Targeted at SOC and AppSec teams who already use Claude / ChatGPT / Gemini / Ollama and want a vetted skill corpus instead of one-off prompts.

What's in it (today):
- 79 SKILL.md packages across 12 domains: detection, response, appsec-devsecops, cloud-infra, identity-access, pentest, red-team, risk-compliance, etc.
- 12 cs-* orchestrator agents (cs-security-analyst, cs-incident-responder, cs-red-teamer, cs-appsec-engineer, cs-ciso-advisor, cs-threat-intel-lead, …) that compose the skills into workflows.
- Every skill emits an 11-field JSON output contract validated against tools/output_contract.py in CI on every push.
- metadata.frameworks.{mitre_attack,nist_csf,owasp_top10,d3fend,mitre_atlas,nist_ai_rmf} arrays auto-generate a MITRE ATT&CK Navigator layer and a NIST CSF 2.0 coverage doc. CI fails on drift.
- L1–L4 autonomy levels with explicit human_approval_required gates on mutating actions.
- Apache 2.0.

Demo SVG (animated, faithful render of cs-appsec-engineer → vuln-scan → finding-triage): docs/assets/usap-alex-demo.svg
Architecture diagram: docs/assets/usap-architecture.svg
Repo: github.com/jaskaranhundal/usap-skills

Not a SaaS, not a product launch — just the skills library. Feedback welcome, especially on skill-level decisions (correctness, omissions, framing).
```

## Twitter / X thread

```
1/ Quietly shipped: USAP — 79 open-source cybersecurity skills + 12 cs-* orchestrator agents.

Every skill emits a typed 11-field JSON contract.

Runs in any LLM.

🧵 (1/7)

🔗 github.com/jaskaranhundal/usap-skills

2/ The shape every skill must produce:

agent_slug · intent_type · action · rationale · confidence · severity · key_findings · evidence_references · next_agents · human_approval_required · timestamp_utc

CI fails on every push if a sample drops a required field.

3/ The 12 cs-* orchestrator agents compose skills into workflows:

cs-security-analyst (SOC)
cs-incident-responder
cs-red-teamer
cs-appsec-engineer
cs-ciso-advisor
cs-threat-intel-lead
cs-purple-team-lead
…

Each is a system prompt; each routes to skills.

4/ Framework mappings aren't decoration — they're machine-readable.

Every skill carries metadata.frameworks.{mitre_attack, nist_csf, owasp_top10, …} in YAML frontmatter.

A stdlib extractor generates a live MITRE ATT&CK Navigator layer.

CI fails on drift between source and generated docs.

5/ The autonomy model is L1–L4.

Mutating actions (key rotation, isolation, account disablement) carry an explicit `human_approval_required: true` in the output payload.

You can build agent stacks against this without trusting model judgment alone.

6/ Watchable demo (animated SVG, renders inline on GitHub):

github.com/jaskaranhundal/usap-skills/blob/main/docs/assets/usap-alex-demo.svg

The JSON shown in the demo is byte-identical to the committed sample_output.json. Nothing invented.

7/ Apache 2.0. No SaaS layer. Not a competitor to LangChain / autogen — it's the substrate they compose.

Stars + feedback welcome.

github.com/jaskaranhundal/usap-skills

If you build security tooling, please rip apart the output contract and tell me what's missing.
```

## LinkedIn post (long-form)

**Hook:** A typed output contract is the difference between "AI helped me write a security report" and "AI ran an audit my CISO will sign."

**Body:**

```
Open-sourced today: USAP — a library of cybersecurity skills that runs in any LLM, emits a typed 11-field JSON output contract on every call, and ships 12 cs-* orchestrator agents that compose those skills into auditable workflows.

Why a contract matters more than a prompt:

A prompt is creative. A contract is auditable. USAP skills emit eleven required fields on every output — agent_slug, intent_type, action, rationale, confidence, severity, key_findings, evidence_references, next_agents, human_approval_required, timestamp_utc. CI runs the validator against every committed sample on every push, so the contract is checked, not just claimed.

A second piece I'm proud of: every skill carries machine-readable metadata.frameworks.{mitre_attack, nist_csf, owasp_top10, d3fend, atlas, nist_ai_rmf} arrays in its frontmatter. A stdlib extractor generates a live MITRE ATT&CK Navigator layer and a NIST CSF 2.0 coverage doc directly from those — and CI fails the build on any drift between the source mappings and the generated docs. Coverage docs can't quietly rot.

The 12 cs-* orchestrator agents — cs-security-analyst, cs-incident-responder, cs-red-teamer, cs-appsec-engineer, cs-ciso-advisor, cs-threat-intel-lead, and seven more — chain skills into workflows the way a senior analyst would. The autonomy model is L1–L4; mutating actions like key rotation or host isolation are gated behind an explicit human_approval_required flag in the output payload, so anything destructive still requires an operator click.

Apache 2.0. Runs in Claude, ChatGPT, Gemini, Ollama, AnythingLLM. Not a SaaS — the skills are MD + Python, no vendor cloud, no per-seat pricing, no telemetry leaving your environment.

If you build security tooling, please rip apart the contract and tell me what's missing. The repo is github.com/jaskaranhundal/usap-skills.

#cybersecurity #appsec #soc #aiagents #opensource
```

## Comment-thread responses (have these ready)

> "How is this different from `<X>`?"

USAP is the substrate, not the runner. LangChain / autogen / CrewAI build the loop; USAP is the corpus the loop reads. The contract is the load-bearing piece — skills emit it on every call so the runner doesn't have to guess.

> "Is this another Claude-only thing?"

No. Every skill is plain markdown + a Python stdlib `_tool.py`. The reference runner uses any LLM. The Claude Code invocation-control extensions are optional (see `standards/frontmatter-spec.md` "Invocation Control"); the skills work without them.

> "Show me one skill in detail."

The cleanest one to read first is `appsec-devsecops/vuln-scan/`. Persona, Overview, decision tables with MITRE mappings, expected_outputs/sample_output.json (the same one the demo SVG renders), and a working `vuln-scan_tool.py`. ~5 minute read.

> "What's the catch?"

This is pre-1.0-rolling. Some skills still need their framework mappings backfilled (see `mappings/mitre-attack/coverage-summary.md` — 10 of 79 carry mappings today; ongoing). The honesty is in `SELF-AUDIT.md` — the validator gate is published, the gaps are published, fixes are tracked openly.
