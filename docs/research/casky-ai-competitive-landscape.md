# Casky.AI Competitive Landscape

A market analysis of Casky.AI and the agentic-AI security operations category, framed against the Unified Security Agent Platform (USAP) open-source skills model.

---

## 1. Executive Summary

- **Casky.AI** is a Claude-native "AI Security Investigation Platform" that converts real security artifacts (logs, configs, alerts) into CVSS-scored, MITRE-mapped findings via 754 open-source Markdown "skills." It is priced as a prosumer product ($49/month) with a gated enterprise track and a free playground, and explicitly competes with training/CTF incumbents (HackTheBox, TryHackMe, SANS) rather than SIEM/SOAR vendors.
- **The top five competitors** in the broader agentic-AI security space are **Simbian** (multi-agent SOC + pentest suite, $10M seed), **7AI** (50+ swarming SOC agents, $130M Series A — largest in cyber history), **Prophet Security** (agentic AI SOC platform, $41M total, 1M+ autonomous investigations), **Dropzone AI** (capacity-priced AI Tier-1 analyst, $57M total, 300+ deployments, Gartner-recognized), and **Andesite** (FedRAMP High "Bionic SOC" with ex-CIA leadership, $38.5M seed).
- **The category is bifurcating.** One half is enterprise-priced agentic SOC platforms targeting CISOs, MDRs, and federal buyers (Simbian, 7AI, Prophet, Dropzone, Andesite). The other half — where Casky sits — is a prosumer/practitioner play around investigation deliverables and career on-ramps that is sold direct to individual analysts and consultants.
- **USAP occupies a third position** that none of the six players occupy cleanly: a model-agnostic, fully open-source (Apache 2.0) skills + orchestrator-agent corpus that runs in any LLM (Claude, ChatGPT, Gemini, Ollama, AnythingLLM) with no SaaS layer and no vendor lock-in. The closest analog is the Casky-adjacent `mukul975/Anthropic-Cybersecurity-Skills` repo, but USAP ships orchestrator agents (the `cs-*` chain) and a typed output contract on top.
- **USAP's best fit** is the segment that wants Casky's open-skills posture without Casky's Claude-only runtime, $49/month wall, or waitlist — specifically SOC engineers, internal CISOs, devsecops teams, and red-teamers who already own LLM access and want a portable corpus they can drop into Claude Code, AnythingLLM, or their own agent framework.

---

## 2. Casky.AI Profile

### 2.1 Product and category

Casky positions itself as an **"AI Security Investigation Platform"** powered by Claude Sonnet 4.6, with the tagline *"Run real investigations. Ship professional findings."* The hero promise is artifact-to-deliverable: paste real logs, configs, or incident data, and Claude's extended-thinking reasoning produces CVSS-scored, MITRE-mapped findings ready for a client or CISO **in three minutes** ([casky.ai](https://casky.ai/)).

The core product surface is a **Skills Lab** that runs investigations against a catalog of **754 Claude Cybersecurity Skills** (structured Markdown task definitions) spanning 12 domains: Cloud Security (AWS/Azure/GCP), Web/API, Malware Analysis, Forensics & IR, Network Security, Identity & Access, Red Teaming, DevSecOps, Threat Intelligence, SOC Operations, Container Security, and OSINT/Recon. Three operating modes are advertised — **Simulation** (guided demo targets), **Evidence** (real artifacts producing structured findings), and **Actual** (enterprise infrastructure integration) — suggesting one product surface that scales from learning to production use.

### 2.2 Target market and personas

Casky's ICP is explicitly **bifurcated**:

- **Practitioners producing client deliverables** — consultants, analysts, and security engineers who take real artifacts and need CVSS-scored, MITRE-mapped findings "you can hand to a client or CISO" ([casky.ai](https://casky.ai/)).
- **Juniors, students, and career switchers** — explicitly positioned for users who want to "walk out with a portfolio of real findings — not just a transcript." Career paths productize five end-roles: Cloud Security Engineer, Network Security Engineer, Web & App Security Engineer, SOC Analyst, and Penetration Tester (coming soon).

A **CISO/security-leader buyer persona** is implied (consumer of outputs, blog audience) but not the daily user. A **dedicated `/enterprise` route** exists but exposes no public content — the page returns header-only to fetches, consistent with a contact-sales motion for a still-thin enterprise SKU. **No customer logos, case studies, or named-account references** are visible on any fetched page.

### 2.3 Pricing and business model

Casky runs a **hybrid open-source + commercial SaaS** model:

- **Open-source layer**: the underlying skills library is published as `mukul975/Anthropic-Cybersecurity-Skills` on GitHub under Apache 2.0, cited at 16.8k stars / 2.0k forks. The repo is 99.6% Python with skills packaged as Markdown + YAML frontmatter and installable via `npx skills add` or git clone ([github.com/mukul975/Anthropic-Cybersecurity-Skills](https://github.com/mukul975/Anthropic-Cybersecurity-Skills)).
- **Commercial layer**: a **free Playground tier** (gated by an early-access waitlist, advertised as "Find your first real vulnerability — free") and a **flat $49/month paid plan** that includes async access to all 754 skills.
- **Enterprise tier** ("Casky Explainable Security") is gated — no pricing, SLA, feature matrix, or deployment model is public.
- **Future cohort-based education** is hinted via a Maven partnership marked "Coming soon."

The site reads as **pre-GA / waitlist-led** rather than a fully self-serve SaaS. No funding, headcount, or customer counts are disclosed publicly.

### 2.4 Positioning and competitive claims

The explicit competitive wedge is **"real evidence vs. simulation,"** framed directly against training/CTF incumbents on the homepage:

- HackTheBox: *"HTB teaches you to capture flags. Casky generates findings you hand to a client."*
- SANS: *"SANS costs $5K and takes a week. Casky costs $49/month and works on your actual logs."*
- TryHackMe: *"TryHackMe gives you a room. Casky takes your real evidence."*

Versus generic scanners, the differentiator is **consultant-grade structured output** (CVSS + asset + MITRE tags + remediation) rather than raw scores. Versus other AI products, the differentiator is **reasoning transparency** — users "watch Claude's extended thinking process" stream live. Framework-coverage authority is signalled via specific counts: 14 MITRE ATT&CK tactics, 291 techniques, NIST CSF 2.0 (6 functions), OWASP Top 10 2025 (10 categories).

Notably absent: **no named enterprise logos, no quantified customer outcomes** (vs. competitors' 7M investigations / 96% FP reductions), and **no SOC/SIEM/EDR connector list**.

### 2.5 Technology stack and integrations

Casky is an **applied layer on Anthropic**, not a foundation-model company:

- **Core engine**: Claude Sonnet 4.6 (with a "Claude Mythos Preview" tier referenced in the blog) and Anthropic's extended-thinking reasoning surfaced through a browser playground.
- **Knowledge layer**: the open-source skills repo, with framework taxonomies baked in at specific versions — MITRE ATT&CK v19.1, NIST CSF 2.0, MITRE ATLAS v5.4, D3FEND v1.3, NIST AI RMF 1.0 GenAI Profile, OWASP Top 10 2025.
- **Platform compatibility (claimed for the skills layer)**: Claude Code, GitHub Copilot, Cursor, Windsurf, Cline, Continue, OpenAI Codex CLI, Gemini CLI, LangChain, CrewAI, AutoGen, Semantic Kernel, and MCP-compatible systems — i.e., the **skills are model-agnostic even though the SaaS product is Claude-only**.
- **Companion products** referenced in the blog: **Hermes Agent** (persistent 24/7 AI scanner pitched as "no SOC required") and **ClawBots** (autonomous agents framed around accessibility), plus a tie-in to Anthropic's **Project Glasswing** zero-day coalition.

**Integration gap**: no public evidence of named SIEM/EDR/SOAR/ticketing connectors (Splunk, Sentinel, CrowdStrike, SentinelOne, Jira, ServiceNow). "Actual mode" enterprise infrastructure integration is named but unspecified. By comparison, Prophet, Dropzone, and 7AI publish 70–90+ named connector lists.

### 2.6 Open questions about Casky

1. What does the Enterprise SKU actually include? `/enterprise` is a stub.
2. Are "Actual mode" integrations real connectors (SIEM/EDR/cloud APIs) or just generic log ingestion?
3. Is the SaaS runtime open source, or only the skills definitions? The license boundary between `casky.ai` (the platform) and the GitHub repo is undocumented.
4. What is the company-to-repo relationship — is `mukul975` first-party, sponsored, or a community maintainer?
5. Is multi-model support shipped, or is the SaaS Claude-only despite the skills being model-agnostic?

---

## 3. Top 5 Competitors

### 3.1 Simbian — Multi-agent SOC + Pentest under one platform

**Positioning.** "Self-Improving SecOps." Four autonomous AI agents — AI SOC, AI Threat Hunt, AI Pentest, AI NetSecOps — anchored by a per-tenant **Context Lake**, a federated **Reasoning Engine**, and a **TrustedLLM** layer marketed as hardened against prompt injection and model poisoning ([simbian.ai](https://simbian.ai/)).

**Target buyer.** Mid-market and enterprise SOCs, with explicit and unusually strong messaging for **MSSPs/MDRs managing 200–300+ tenants**. MSSP framing positions Simbian as a margin lever, not a Tier-1 replacement.

**Key features.** Tier-1/Tier-2 alert triage with verdict + audit trail; parallel hunts across EDR/SIEM/identity/cloud (Microsoft Sentinel data lake support added Sep 2025); continuous and on-demand pentesting using their ARMM maturity model with up to five retests; firewall/network-policy automation; per-tenant context isolation for MSSPs; SaaS or on-prem deployment; "Cyber AI Gym" continuous retraining loop.

**Differentiators.** Only major rival that ships **both defensive (SOC/hunt/netsecops) and offensive (pentest)** in one platform. Per-tenant Context Lake for MSSP isolation is unique among rivals. Publishes its own **Cyber Defense Benchmark** scoring 14 frontier LLMs — uses third-party-evaluator positioning as a sales weapon.

**Pricing.** Enterprise sales-gated except for the **AI Pentest Agent at $4,000–$8,000 per pentest** (Standard vs. Premium, includes up to five retests). MSSP packaging is per-tenant subscription.

**Recent signals.** $10M seed (Apr 2024, Cota Capital / Icon Ventures), Wipro managed-service deal (Sep 2025), NuSummit AI-MDR launch (Jan 2026), SoftBank C&S Corp customer win (Dec 2025), claimed "industry-first Autonomous SecOps Platform" unveil at RSAC 2026.

**Citations.** [simbian.ai](https://simbian.ai/), [TechCrunch](https://techcrunch.com/2024/04/11/simbian-brings-ai-to-existing-security-tools/), [SecurityWeek](https://www.securityweek.com/simbian-emerges-from-stealth-with-10-million-to-build-autonomous-ai-based-security-platform/).

### 3.2 7AI — 50+ swarming agents, capitalized for the long game

**Positioning.** "Service-as-Software" agentic SOC platform that deploys a **swarm of 50+ purpose-built AI SOC agents** across Endpoint, Identity, Cloud, Email, and Network domains. Pitches "swarming agents that form conclusions" as the architectural contrast to single-LLM AI-SOC copilots and rule-based SOAR ([7ai.com](https://7ai.com/)).

**Target buyer.** Mid-market through large-enterprise SOCs suffering analyst burnout and Tier-1 staffing cost; **MSSPs/global service providers** as platform partners (DXC Technology global partnership). Disclosed verticals: insurance/insurtech (Duck Creek, Cole Scott & Kissane, Abacus), data security (BigID), IT services (DXC).

**Key features.** Autonomous investigation with written conclusions + evidence chain; unified Cases module; 95–99% false-positive elimination; conclusion-driven remediation with human-approval gates; Threat Hunt + Threat Intel Hunt (Jun 2026); customer-customizable **Skills** module (no-code drag-and-drop agent behaviors, also Jun 2026); board-ready Enterprise Insights dashboards.

**Differentiators.** **Founding pedigree**: Lior Div and Yonatan Striem-Amit previously co-founded Cybereason — strong CISO-buyer access. **Largest cyber Series A in history** ($130M, Dec 2025) at ~$700M valuation gives capital and signaling advantage. DXC global SOC-as-a-service channel embeds 7AI inside a top-5 IT services partner. Public ROI dashboard (7M+ investigations, 1M+ analyst hours saved, $59.9M productivity reclaimed) is unusually concrete vs. peer marketing.

**Pricing.** Not published. `/pricing` returns 404. Sales-led; "Service as Software" positioning implies outcome-based or subscription enterprise pricing.

**Recent signals.** $36M seed announced Feb 2025, $130M Series A Dec 2025 (Index Ventures, Blackstone Innovations), DXC partnership Aug 2025, AWS Security Hub Extended integration Feb 2026, 100+ employees by May 2026, Israel Barak (ex-Cybereason CISO) appointed CISO Mar 2026.

**Citations.** [7ai.com](https://7ai.com/), [BusinessWire Series A](https://www.businesswire.com/news/home/20251204907769/en/), [SC Media](https://www.scworld.com/news/cybersecurity-startup-7ai-raises-record-130m-to-scale-agentic-ai), [Crunchbase](https://www.crunchbase.com/organization/seven-ai).

### 3.3 Prophet Security — Lifecycle-complete agentic AI SOC

**Positioning.** Agentic AI SOC platform that autonomously **triages, investigates, and (with human-in-loop) responds** to security alerts across the customer's existing stack. Sells against MDR services and copilots — explicitly framing the buyer choice as *"build vs. MDR vs. agentic AI SOC."* ([prophetsecurity.ai](https://www.prophetsecurity.ai/)).

**Target buyer.** Mid-market to large enterprise in-house SOCs and security engineering teams. Named customers skew US tech (Instacart, Udemy, Redis, Zip, Clari, iCapital, Upwind), industrials (Cabinetworks, JB Poindexter, Penske), and healthcare. Buyer is typically CISO or SOC director.

**Key features.** AI SOC Analyst (multi-step investigation of *every* alert, all severities, with bi-directional SIEM sync), AI Threat Hunter (natural-language and continuous hunts, hunt template library), Detection Advisor (tuning recommendations), transparent reasoning trail (plan + queries + evidence + conclusion), per-tenant adaptation from analyst feedback, autonomous remediation with optional human gates.

**Differentiators.** End-to-end lifecycle in one product. **100% alert coverage** claim — investigates low/medium/info alerts that human SOCs drop. **Bi-directional SIEM/case-management integration** so verdicts flow back into existing workflow. Founder credibility (Kamal Shah ex-StackRox CEO, Vibhav Sreekanti ex-Red Hat) is used as a wedge against AI-first founders without SOC pedigree.

**Pricing.** Not published; `/pricing` returns 404. Demo-gated.

**Recent signals.** $11M seed Apr 2024, **$30M Series A Aug 2025** led by Accel (total ~$41M), Amex Ventures + Citi Ventures strategic round Feb 2026, ExtraHop NDR integration Jun 2026, SOC 2 Type 2. Company-wide claims: >1M autonomous investigations across customer base in ~6 months, 96% FP reduction, 10x faster response.

**Citations.** [prophetsecurity.ai](https://www.prophetsecurity.ai/), [VentureBeat](https://venturebeat.com/ai/ai-vs-ai-prophet-security-raises-30m-to-replace-human-analysts-with-autonomous-defenders), [Series A announcement](https://www.prophetsecurity.ai/blog/prophet-security-raises-30-million-series-a-led-by-accel).

### 3.4 Dropzone AI — Capacity-priced AI Tier-1 analyst

**Positioning.** Agentic AI SOC platform — a **"software-only Tier-1 analyst replacement"** that runs 24/7, ingests alerts from existing SIEM/EDR/cloud/identity/email, runs full Tier-1 investigations end-to-end, and can take bounded auto-containment actions (IP block, account disable) with human oversight on mutating steps ([dropzone.ai](https://www.dropzone.ai/)).

**Target buyer.** Enterprise SOCs (Fortune 500, mid-market, federal), MSSPs (multi-tenant plan), SIEM-modernization buyers. ICP framing: *"10x SOC capacity without hiring."*

**Key features.** Autonomous triage across phishing/endpoint/network/cloud/identity/insider classes; hypothesis-driven proactive hunting; auto-generated "hunt packs" from threat intel; agentless SaaS, ~1 hour deploy; "Glass Box" reasoning transparency; coachable in natural language (no playbook scripting); context memory; unlimited users; bundled threat intel feeds.

**Differentiators.** **Pure-software claim** ("no hidden human analysts") is a direct shot at managed-SOC and AI-assisted-MDR. **Investigation-capacity pricing** is unusual: $36K/yr for one AI analyst doing up to 4,000 investigations/year, unlimited users — predictable vs. SIEM GB-based and SOAR seat-based pricing. **Glass-box transparency** positioned against "black-box" peers. **Gartner Hype Cycle for Security Operations 2026** + Innovation Insight for AI SOC Agents recognition. **14 US patents**. Federal/IQT-backed.

**Pricing.** Most transparent in the cohort: published anchor of **~$36,000/year per AI analyst / 4,000 investigations / unlimited users**. Three tiers (Standard, Enterprise, MSSP) gated to sales. Volume discounts above 4,000 investigations.

**Recent signals.** $5.6M seed (2023), $16.85M Series A (Apr 2024, Theory Ventures), **$37M Series B Jul 2025** led by Theory Ventures (Madrona, Decibel, PSL, IQT) — total ~$57.4M. 300+ deployments worldwide. RSAC Innovation Sandbox Finalist 2024, Gartner Cool Vendor 2024, AI 100 (2025). Founder Edward Wu ex-ExtraHop detection lead.

**Citations.** [dropzone.ai](https://www.dropzone.ai/), [SiliconANGLE](https://siliconangle.com/2025/07/28/dropzone-ai-raises-37m-expand-ai-soc-analyst-development-integrations/), [GeekWire](https://www.geekwire.com/2025/seattle-startup-dropzone-raises-37m-to-supercharge-its-ai-soc-analyst-security-software/), [Pricing page](https://www.dropzone.ai/pricing).

### 3.5 Andesite — FedRAMP High "Bionic SOC" with national-security pedigree

**Positioning.** **"Human-AI collaboration"** — explicit anti-"replace the analyst" framing. Flagship is a **Workbench** that consolidates and triages alerts across SIEM/EDR/XDR/IdP, paired with configurable AI agents and playbooks. Sold as a no-data-migration overlay with single-tenant SaaS, **air-gapped**, and self-managed deployment options ([andesite.ai](https://andesite.ai/)).

**Target buyer.** **U.S. federal government and national-security buyers** (FedRAMP High Authorized, Department of War partnership via Second Front Systems), large financial institutions, and enterprise SOCs that need data residency, classification, or air-gap requirements. Personas: SOC analysts (including T1), threat hunters, security ops leaders.

**Key features.** Workbench consolidated queue; configurable agents and playbooks (phishing triage, alert management); natural-language investigation; **Evidentiary AI audit trails** tying every AI step to verified evidence; **Safe AI Architecture** (single-tenant SaaS or air-gapped, IDP + CAC/PIV identity, no customer data trains models); **model-agnostic LLM layer** (BYO enterprise LLM); continuous AI evaluation (correctness/relevancy/faithfulness); 50+ prebuilt integrations.

**Differentiators.** **FedRAMP High Authorization** (Mar 2026) is rare in the AI-SOC cohort. **Leadership pedigree from CIA/national-security community** (CEO Brian Carbaugh ex-CIA Special Activities; CSO Greg Rattray; CPO William MacMillan). **Model-agnostic BYO-LLM** distinguishes from Claude-locked or single-vendor peers. **Air-gapped deployment** rare among SaaS-only AI-SOC peers. Outcome-based pricing rather than per-seat or per-token. Early adopter of Anthropic's Mythos model via Project Glasswing (Apr 2026).

**Pricing.** Not published. Marketing states pricing is "based on outcomes, not on AI usage." Demo-gated with an ROI calculator.

**Recent signals.** $15.25M seed Apr 2024, $23M seed extension Feb 2025 (General Catalyst, Red Cell, In-Q-Tel) for ~$38.5M total. Second Front Systems / DoW partnership Feb 2026. **FedRAMP High** Mar 2026. Anthropic Mythos/Glasswing partner Apr 2026.

**Citations.** [andesite.ai](https://andesite.ai/), [Nextgov coverage](https://www.nextgov.com/cybersecurity/2025/02/ai-cybersecurity-firm-andesite-secures-added-23m-funding/402891/), [Anthropic Project Glasswing](https://www.anthropic.com/news/expanding-project-glasswing).

---

## 4. Comparison Matrix

| Vendor | Positioning | Target Buyer | Agentic vs. Copilot | Open Source vs. Closed | Pricing | Integration Model | Model Platform Support |
|---|---|---|---|---|---|---|---|
| **Casky.AI** | "AI Security Investigation Platform" — real artifacts to client-ready CVSS/MITRE findings | Consultants, juniors/students, career switchers; gated enterprise track | Agentic playground (streamed Claude reasoning) | Skills layer open (Apache 2.0); SaaS runtime closed | Free waitlist; $49/mo flat; enterprise contact-sales | Browser playground + manual evidence paste; no named SIEM/EDR connectors | Claude Sonnet 4.6 only (skills repo claims platform-agnostic for self-host) |
| **Simbian** | Self-Improving SecOps: multi-agent SOC + Pentest + NetSecOps + Hunt | Mid-market & enterprise SOCs; **MSSPs/MDRs** at 200–300+ tenants | Fully agentic, reasoning-based (playbook-less) | Closed | Enterprise sales-gated; Pentest $4K–$8K/engagement | 100+ claimed native integrations; SaaS or on-prem | Closed TrustedLLM layer (model details not disclosed) |
| **7AI** | Service-as-Software: swarm of 50+ specialized SOC agents | Mid-market/large enterprise SOCs; MSSPs via DXC channel | Agentic swarm forming conclusions | Closed | Not published (sales-led); outcome-positioned | 70+ named API connectors (CrowdStrike, Splunk, Sentinel, Okta, Wiz, etc.) | Closed; "architecturally grounded" but provider undisclosed |
| **Prophet Security** | Agentic AI SOC: triage + investigation + response + hunting + tuning | In-house SOCs (CISO/SOC director); mid-market to large enterprise | Fully agentic with transparent reasoning chain | Closed | Not published; demo-gated | 60+ named integrations across SIEM/EDR/identity/cloud/email/ticketing; bi-directional SIEM sync | Closed; model provider not disclosed |
| **Dropzone AI** | Software-only AI Tier-1 analyst replacement | Enterprise SOCs (F500, federal), MSSPs, SIEM-modernization buyers | Agentic, "Glass Box" reasoning, bounded auto-containment | Closed (14 US patents) | **Published: $36K/yr per AI analyst / 4,000 investigations** | 90+ named integrations; agentless SaaS, ~1 hr deploy | Closed; model provider not disclosed |
| **Andesite** | "Bionic SOC" — human-AI collaboration, anti-replacement | U.S. federal/DoW, financial institutions, regulated enterprise | Configurable agents under human oversight | Closed (BYO-LLM) | Not published; "outcomes, not AI usage" | 50+ prebuilt integrations; SaaS, single-tenant, or **air-gapped** | **Model-agnostic / BYO enterprise LLM**; early Claude Mythos / Glasswing partner |
| **USAP** | Open-source LLM skills + `cs-*` orchestrator agents for security operations | SOC engineers, internal CISOs, devsecops, red-teamers; consultancies; open-source-first orgs | Orchestrator-agent pattern over standalone skills; typed JSON contract | **Fully open source (Apache 2.0) — skills, agents, scripts, output contract** | Free (open source); no SaaS layer | No bundled connectors; runs inside the user's LLM/IDE/agent framework | **Model-agnostic** — Claude, ChatGPT, Gemini, Ollama, AnythingLLM, any MCP host |

---

## 5. Where USAP Fits

The agentic-AI-security market has organized itself into three distinct lanes, and USAP sits in a lane that none of the six profiled players occupy cleanly.

### 5.1 The three lanes today

- **Lane A — Enterprise agentic SOC platforms.** Simbian, 7AI, Prophet, Dropzone, and Andesite all sell a hosted multi-agent product to CISOs and SOC directors. They differentiate on connector breadth, deployment posture (SaaS vs. on-prem vs. FedRAMP High), and proof points (Gartner inclusion, named logos, FP reduction percentages). Pricing is enterprise sales-gated except for Dropzone's $36K/yr published anchor.
- **Lane B — Prosumer investigation platforms.** Casky is the clearest example: a $49/month SaaS sold to individual practitioners producing client deliverables, with a free Playground waitlist and a career-on-ramp wrapper. The wedge is *real evidence vs. training simulation*, aimed at HackTheBox/TryHackMe/SANS rather than at SIEM/SOAR.
- **Lane C — Open, portable skills + orchestrator corpus.** Casky's underlying `Anthropic-Cybersecurity-Skills` repo is in this lane, but Casky itself has chosen to capture value by hosting it as a SaaS. **USAP is purpose-built for Lane C and stays there**: the artifact is the skills + agents + output contract, with no hosted runtime.

### 5.2 Best-fit USAP buyer segments

1. **In-house SOC and detection engineering teams that already own LLM access.** They want a vetted skills corpus they can pipe into Claude Code, an AnythingLLM workspace, or a private Bedrock/Vertex deployment, without paying per investigation or per seat.
2. **DevSecOps and platform-security teams** embedding security skills into their existing developer workflows (CI/CD, code review, PR gates). The `appsec-devsecops` domain and the `cs-devsecops-engineer` agent are designed for this — Casky's playground UX is not.
3. **Internal red-team and pentest groups** that want a portable, open-source skills library for engagement planning and report generation, without the legal complexity of running a vendor's hosted pentest agent against their own assets. Simbian's Pentest Agent is $4K–$8K per engagement; USAP's `red-team` and `pentest` domains are zero marginal cost.
4. **Consultancies and MSSPs that need to embed security skills into their own delivery platform.** Apache 2.0 + no SaaS dependency means a consultancy can fork, white-label, and ship USAP-based agents inside its own MDR stack. Casky's licensing of the SaaS layer for hosted-competitor use is undocumented; Simbian/Prophet/7AI/Dropzone/Andesite are closed.
5. **Regulated / air-gapped buyers experimenting before committing to Andesite.** USAP runs in any private LLM (Ollama, on-prem Bedrock, private Azure OpenAI) — useful for proving out workflows before a FedRAMP High procurement cycle.

### 5.3 What differentiates USAP vs. each competitor

- **vs. Casky** — USAP is **not Claude-locked, not behind a waitlist, not $49/month, and not a SaaS**. It ships **orchestrator agents** (`cs-security-analyst` Alex, `cs-incident-responder`, `cs-ciso-advisor`, `cs-devsecops-engineer`, `cs-red-teamer`, `cs-blue-team-analyst`) on top of the skills, plus an enforced typed JSON **output contract** (`agent_slug`, `intent_type`, `severity`, `evidence_references`, `human_approval_required`, etc.). The Casky-adjacent open-source repo lacks the orchestrator and contract layers.
- **vs. Simbian** — USAP does not pretend to be a multi-agent SaaS platform with TrustedLLM and a Context Lake. It is the skills/agent corpus that lets a buyer build that posture inside their own stack. Simbian is for buyers who want it hosted; USAP is for buyers who do not.
- **vs. 7AI** — 7AI's swarm runs as an enterprise SaaS billed on outcomes; USAP runs in the buyer's LLM at no marginal cost. USAP is also model-agnostic where 7AI is a closed runtime.
- **vs. Prophet Security** — Prophet's defensible asset is its connector catalog and per-tenant adaptation loop. USAP does not compete there; instead, it complements existing SIEM/EDR by giving the in-house team a portable skills library that can run alongside Prophet without overlap.
- **vs. Dropzone AI** — Dropzone monetizes investigation *capacity* ($36K/yr for 4,000 investigations). USAP monetizes nothing — the skills and agents are free Apache 2.0 — so the comparison is *"buy Dropzone for 24/7 autonomous Tier-1 ops"* vs. *"adopt USAP to professionalize ad-hoc investigations inside your existing LLM stack."*
- **vs. Andesite** — Andesite is FedRAMP-High, BYO-LLM, and air-gap capable; USAP is the only one in this list that can be **dropped into an Andesite-style air-gapped LLM with zero vendor relationship**. For federal/regulated buyers, USAP is closer to "starter kit before Andesite procurement" than a direct competitor.

### 5.4 The structural USAP advantages

- **Open source (Apache 2.0)** — no waitlist, no $49/mo wall, no SSO upcharge.
- **Standalone-LLM portability** — each `SKILL.md` is a complete system prompt that runs in any LLM, with no platform install.
- **Orchestrator-agent layer** — the `cs-*` chain is the missing piece in the Casky-adjacent open-source repo: it composes skills into auditable workflows.
- **Typed output contract** — every skill emits a JSON payload with required fields including severity, evidence, and an explicit `human_approval_required` boolean. None of the six competitors publish their output schema.
- **Domain breadth without prosumer compromise** — 71 skills across 11 domains explicitly cover system-security, pentest, red-team, identity-access, and governance, not just SOC triage.

---

## 6. Recommended Positioning

### 6.1 Positioning statements (draft, three to five)

1. **"USAP is the open Apache-2.0 skills corpus and `cs-*` orchestrator agents that turn any LLM into a security operations team — no SaaS, no $49/month wall, no Claude lock-in."**
2. **"Casky's playground is closed and Claude-only. USAP is the same kind of skills layer, with orchestrator agents and a typed output contract, runnable inside Claude, ChatGPT, Gemini, or your own private LLM."**
3. **"71 skills, 11 domains, 7 `cs-*` agents — bring your own LLM. Drop into Claude Code, AnythingLLM, or your CI pipeline in minutes."**
4. **"For SOC engineers, devsecops teams, and red-teamers who already own LLM access and don't want to rent a security agent SaaS."**
5. **"The standardized output contract — every skill emits CVSS, MITRE, evidence references, and an explicit `human_approval_required` flag — makes USAP safe to embed in production agent stacks where competitor copilots remain black boxes."**

### 6.2 Top-three ICPs to prioritize

1. **In-house SOC and detection engineering teams (50–500-person security org).** They already buy Splunk/Sentinel + an EDR; they have Claude Enterprise or an internal LLM gateway; they want a vetted skills library to amplify analyst output without procuring another SaaS line item. Distribution: GitHub, security-engineering Slack/Discord communities, conference talks.
2. **DevSecOps and platform-security engineers at engineering-led orgs.** They already use Claude Code or similar; they want security skills embedded in their PR/CI workflow. Hook is the `appsec-devsecops` domain + `cs-devsecops-engineer` agent + the Claude Code plugin distribution. Distribution: dev-tools content channels, Claude Code plugin registry.
3. **Independent consultants, MSSPs, and security consultancies serving SMB clients.** Same pain Casky addresses (client-ready CVSS/MITRE findings), but the consultancies want to *embed* the skills in their own delivery stack and white-label, which the Casky SaaS does not enable. Distribution: MSSP forums, OSINT/security community channels, direct outreach.

---

## 7. Risks and Open Questions to Validate

1. **Casky vs. USAP overlap clarity.** Both reference Apache-2.0 cybersecurity skills repos with similar framework mappings (MITRE / NIST CSF 2.0 / OWASP). Validate whether USAP's 71-skill corpus is meaningfully differentiated in domain coverage or depth from the 754-skill Casky-adjacent repo, or whether the differentiation has to rest on the `cs-*` orchestrator + output contract layer.
2. **Claude-only vs. truly model-agnostic claim.** USAP claims to run in Claude, ChatGPT, Gemini, Ollama, AnythingLLM. Validate this on at least one non-Anthropic model end-to-end (output-contract conformance, evidence-reference quality, refusal rates) before making the claim load-bearing in marketing.
3. **Enterprise interest in open-source vs. hosted.** Andesite's FedRAMP-High and BYO-LLM motion suggests there is a buyer that wants model-agnostic + air-gap. Validate whether that buyer prefers a fully open Apache-2.0 corpus (USAP) or a paid BYO-LLM SaaS (Andesite) — the answer determines whether USAP needs a hosted commercial offering.
4. **Connector gap impact.** Prophet (60+), Dropzone (90+), 7AI (70+), Andesite (50+) all publish detailed connector lists. USAP ships no bundled connectors. Validate whether buyers in the target ICPs treat connectors as table stakes, or accept that USAP runs alongside their existing SIEM/EDR via the user's LLM.
5. **MSSP / consultancy licensing posture.** USAP is Apache 2.0, which permits hosted-competitor use. Decide explicitly whether MSSPs reselling USAP-derived agents is a desired channel (likely yes) or a risk (white-labeled forks fragmenting the project).
6. **`cs-*` orchestrator brand vs. Alex.** Currently, the universal entry is `cs-security-analyst` ("Alex"). Validate whether the public-facing brand should lead with **Alex** (memorable, persona-driven, like Casky's Hermes/ClawBots) or with the **`cs-*` taxonomy** (clearer to engineers but less memorable to CISO buyers).
7. **Distribution channels.** Validate which combination of GitHub readme polish, Claude Code plugin registry presence, AnythingLLM marketplace listing, and conference talks (BSides, fwd:cloudsec, RSAC) actually drives adoption for an open-source security project in 2026 — versus paid acquisition the SaaS competitors are leaning on.

---

## 8. Sources

### Casky.AI

- https://casky.ai/
- https://casky.ai/blog
- https://casky.ai/enterprise
- https://casky.ai/pricing
- https://casky.ai/about
- https://github.com/mukul975/Anthropic-Cybersecurity-Skills

### Simbian

- https://simbian.ai/
- https://simbian.ai/products/ai-soc-agent
- https://simbian.ai/products/ai-pentest-agent
- https://simbian.ai/solutions/mssp-mdr
- https://simbian.ai/about-us
- https://simbian.ai/press-releases
- https://techcrunch.com/2024/04/11/simbian-brings-ai-to-existing-security-tools/
- https://www.businesswire.com/news/home/20240411263264/en/Simbian-Emerges-from-Stealth-with-$10M-to-Build-Fully-Autonomous-Security-Platform-Powered-by-GenAI
- https://www.securityweek.com/simbian-emerges-from-stealth-with-10-million-to-build-autonomous-ai-based-security-platform/
- https://pitchbook.com/profiles/company/589708-81
- https://tracxn.com/d/companies/simbian/__LfNqPxQStpXSKaHZ5uVWbqfasfcf-Bl-xxMFXZfsxaY/funding-and-investors

### 7AI

- https://7ai.com/
- https://7ai.com/platform
- https://7ai.com/company
- https://7ai.com/news
- https://blog.7ai.com/
- https://blog.7ai.com/citing-the-agentic-security-inflection-point-7ai-raises-largest-cybersecurity-a-round-in-history-to-bring-ai-security-agents-to-enterprises
- https://www.businesswire.com/news/home/20251204907769/en/
- https://www.scworld.com/news/cybersecurity-startup-7ai-raises-record-130m-to-scale-agentic-ai
- https://www.crunchbase.com/organization/seven-ai
- https://pitchbook.com/profiles/company/600908-05
- https://tracxn.com/d/companies/7ai/__4RRSZCHOEtBO41GenAIO3DEaEbOVYbheaDLQtjLCO0g

### Prophet Security

- https://www.prophetsecurity.ai/
- https://www.prophetsecurity.ai/customers
- https://www.prophetsecurity.ai/integrations
- https://www.prophetsecurity.ai/blog
- https://www.prophetsecurity.ai/blog/prophet-security-raises-30-million-series-a-led-by-accel
- https://venturebeat.com/ai/ai-vs-ai-prophet-security-raises-30m-to-replace-human-analysts-with-autonomous-defenders
- https://www.builtinsf.com/articles/prophet-security-raises-30m-series-a-20250804
- https://finance.yahoo.com/news/prophet-security-raises-30m-series-130000806.html
- https://www.crunchbase.com/organization/prophet-security
- https://tracxn.com/d/companies/prophetsecurity/__kJs_oWGhcSlK1rmcWvyLCq8cSEVT3gEKFjNCQyhVS5c
- https://baincapitalventures.com/insight/prophet-security-is-using-ai-to-cut-mean-time-to-response-by-10x-for-security-operations-teams/
- https://www.accel.com/relationships/prophet-security

### Dropzone AI

- https://www.dropzone.ai/
- https://www.dropzone.ai/product
- https://www.dropzone.ai/pricing
- https://www.dropzone.ai/integrations
- https://www.dropzone.ai/company
- https://www.dropzone.ai/press-release/dropzone-ai-37m-series-b-funding-ai-soc-agents
- https://www.dropzone.ai/press-release/dropzone-ai-raises-16-85-million-series-a-to-equip-cyber-defenders-with-24-7-generative-ai-powered-autonomous-investigations
- https://siliconangle.com/2025/07/28/dropzone-ai-raises-37m-expand-ai-soc-analyst-development-integrations/
- https://www.geekwire.com/2025/seattle-startup-dropzone-raises-37m-to-supercharge-its-ai-soc-analyst-security-software/

### Andesite

- https://andesite.ai/
- https://andesite.ai/product/
- https://andesite.ai/integrations/
- https://andesite.ai/company/
- https://andesite.ai/blog/
- https://andesite.ai/roi-calculator/
- https://andesite.ai/andesite-ai-secures-15-25m-to-bolster-cybersecurity-with-advanced-ai-analytics/
- https://www.nextgov.com/cybersecurity/2025/02/ai-cybersecurity-firm-andesite-secures-added-23m-funding/402891/
- https://fintech.global/2025/02/11/cybersecurity-firm-andesite-secures-23m-to-launch-ai-powered-bionic-soc/
- https://techfundingnews.com/human-ai-collaboration-in-cyber-defence-teams-ex-cia-executives-andesite-snaps-23m-from-general-catalyst/
- https://www.crunchbase.com/organization/andesite-ai
- https://pitchbook.com/profiles/company/550896-76
- https://www.anthropic.com/news/expanding-project-glasswing

### USAP (this project)

- https://github.com/jaskaranhundal/usap-skills
- https://github.com/jaskaranhundal/usap
