# USAP vs. Prompt Libraries: Why a Skill is More Than a Prompt

When developers first encounter the Unified Security Agent Platform (USAP), they often ask a fundamental question: *"Isn't this just a folder of prompts?"* 

It is a fair question. At a glance, both prompt libraries and USAP store Markdown files containing instructions for Large Language Models (LLMs). However, while prompt libraries focus on packaging instructions for human use, USAP is designed to turn prompts into machine-readable software components. 

Here is a look at what prompt libraries do well, what a USAP skill adds, and why this distinction is critical for building autonomous agentic workflows.

## What a Prompt Library Actually Is

Prompt libraries solve a real and valuable problem. They are curated collections of system or user prompts designed to help developers and teams interact with LLMs more effectively. A well-maintained prompt library provides:

* **Reusable Prompts:** No need to reinvent the wheel for common tasks like code generation, translation, or security analysis.
* **Team Knowledge Sharing:** Teams can pool their best-performing prompts in one repository.
* **Better Consistency:** Standardized templates reduce variability in LLM outputs.
* **Easier Onboarding:** New team members can quickly reference proven prompts rather than writing them from scratch.
* **Faster Experimentation:** Teams can test different prompt versions to see which works best for their use case.

Prompt libraries are excellent tools for humans who need inspiration or templates to copy and paste into a chat interface.

## What `SKILL.md` Adds

A USAP skill (defined in a `SKILL.md` file) goes beyond a simple prompt template. It is a strictly structured software contract. A USAP skill encapsulates instructions alongside machine-readable metadata and validation rules:

* **Typed YAML Frontmatter:** Defines metadata such as version, author, allowed and disallowed tools, file paths, and framework mappings (like MITRE ATT&CK or OWASP Top 10).
* **Persona and Intent Classification:** Defines the agent's identity and maps user actions to specific intent types (e.g., `detect`, `remediate`, `report`).
* **Decision Tables:** Embeds logical guidelines for the agent to weigh risks and determine scores (e.g., proximity to threats).
* **Workflow Metadata & Cascading:** Outlines the agent's limits and lists `next_agents` that should be invoked downstream.
* **Typed JSON Output Contract:** Restricts the model's output to a standardized 11-field JSON contract (containing fields like `agent_slug`, `intent_type`, `severity`, `confidence`, and `human_approval_required`).
* **CI Validation:** Validates both schemas and sample outputs in continuous integration on every single commit, ensuring no syntax or contract drifts occur.

In short, a USAP skill is a strict contract, ensuring that the model behaves like a reliable software module.

## Why This Matters at Runtime

This machine-readable structure is what enables true multi-agent orchestration. Because the runtime runner knows the structure of the skill beforehand, it can programmatically control the execution flow:

1. **Dynamic Routing:** The runner can inspect the `intent_type` to determine what action was taken (e.g., a read-only detection vs. a mutating containment action).
2. **Orchestrator Cascades:** The runner reads the `next_agents` array to automatically chain agents. If `vuln-scan` finishes, the runner immediately knows to pass the output to `finding-triage` without having to prompt a model to make that routing decision.
3. **Human-in-the-Loop Gating:** If the output contract's `human_approval_required` field is `true`, the runner can halt execution and prompt for approval before executing any destructive tool.
4. **Predictable Integration:** The output is always a validated, typed 11-field JSON object. Downstream software components can consume the output programmatically without parsing unpredictable natural language.

---

## Concrete Comparison: Vulnerability Scanning

To see the difference in practice, consider how a vulnerability scanning task is handled in both paradigms.

### The Prompt Library Approach

In a prompt library, you might find a prompt located at `appsec-devsecops/vuln-scan/` containing:

> "Scan this application for vulnerabilities and tell me what you find."

While this prompt can yield interesting insights, it has several limitations at scale:
* **Free-form output:** The model might return a bulleted list, a code block, or a conversational explanation.
* **No guaranteed fields:** You cannot guarantee that the model will include severity levels, file paths, or confidence scores in a consistent format.
* **No routing metadata:** The runner does not know which agent should analyze these findings next.
* **No contract validation:** If the model hallucinates or changes its output format, the downstream integration breaks.
* **Natural language parsing:** Any system consuming this output must use complex regular expressions or another LLM call to extract the findings.

### The USAP Skill Approach

In USAP, the `vuln-scan` skill provides:
* **Structured Metadata:** Classified under `intent_type: detect` and maps to MITRE ATT&CK technique `T1190`.
* **Cascading Rules:** Explicitly lists `next_agents: ["finding-triage"]`.
* **Confidence & Severity:** Standardized scores computed based on proximity to DREAD threats.
* **Structured Evidence:** Citations referencing specific code lines and matching evidence quotes.
* **Typed JSON Contract:** Emits an 11-field JSON payload that is validated in CI to ensure fields like `human_approval_required` and `timestamp_utc` are present.

Because of this contract, another agent or tool in the pipeline can immediately consume the output JSON and continue the DevSecOps workflow without human intervention.

## Closing Summary

Prompt libraries package instructions for humans and models. USAP skills package instructions plus machine-readable contracts that enable orchestration. By moving from templates to contracts, USAP transforms LLMs from conversational assistants into reliable, interconnected security agents.
