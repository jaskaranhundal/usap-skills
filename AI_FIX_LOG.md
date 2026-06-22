Fixed issue: docs: add a 'Compare USAP to a one-off prompt library' explainer page
AI Notes: I need to create a new markdown file and modify two existing markdown files.

**Files to change:**

1.  `docs/explainers/usap-vs-prompt-libraries.md` (new file)
2.  `docs/index.md`
3.  `README.md`

```diff
--- a/docs/index.md
+++ b/docs/index.md
@@ -10,6 +10,10 @@
   - [What are Skills?](skills.md)
   - [Reference: Skill Schema](schema.md)
   - [How to Build a Skill](build-a-skill.md)
+- ### Explainers
+  - [USAP vs. One-Off Prompt Libraries](explainers/usap-vs-prompt-libraries.md)
+
+
 - ### Guides
   - [Installation](guides/install.md)
   - [Quickstart: "Hello World" Skill](guides/hello-world.md)
--- a/README.md
+++ b/README.md
@@ -21,6 +21,11 @@
 
 - **Type-safe Contracts:** USAP skills define explicit input/output schemas, ensuring reliable, predictable interactions.
 
+### What makes it different?
+
+A common question is, "Isn't this just prompts in a folder?" While USAP uses prompts, it adds a layer of structured contracts and routing capabilities that significantly differentiates it. For a deeper dive, see our explainer: [USAP vs. One-Off Prompt Libraries](docs/explainers/usap-vs-prompt-libraries.md).
+
+
 ## Getting Started
 
 ### Installation
--- /dev/null
+++ b/docs/explainers/usap-vs-prompt-libraries.md
@@ -0,0 +1,65 @@
+# USAP vs. One-Off Prompt Libraries
+
+One of the most common questions from new visitors to USAP is, "Isn't this just prompts in a folder?" It's a fair question, and on the surface, there's a resemblance. Both approaches involve collecting instructions for Language Models (LLMs). However, USAP's "skills" offer a fundamentally different paradigm that moves beyond simple prompt storage to enable robust, composable, and production-ready AI applications.
+
+Let's break down the differences.
+
+## What is a One-Off Prompt Library?
+
+A "one-off prompt library" is, at its core, a collection of text files, typically Markdown or plain text, each containing a carefully crafted prompt. These prompts might include system instructions, few-shot examples, and specific user query structures.
+
+**Why are they useful?**
+
+*   **Organization:** They help developers keep their prompts organized and reusable, preventing "prompt sprawl" within their codebase.
+*   **Version Control:** Storing prompts in Git allows for tracking changes, collaboration, and rollbacks.
+*   **Consistency:** They ensure that the same LLM instructions are used across different parts of an application or by different team members.
+
+**Example:** Imagine a folder with `summarize_article.txt`, `extract_entities.txt`, and `translate_to_spanish.txt`. Each file contains a prompt designed for a specific task. To use them, your application reads the file content and sends it to an LLM. This is a perfectly valid and useful pattern for many scenarios.
+
+## What SKILL.md Adds: Structured Contracts and Intelligence
+
+While USAP skills *do* contain prompts, they embed them within a rich, machine-readable `SKILL.md` contract. This contract adds several critical layers of intelligence and robustness:
+
+1.  **Typed Frontmatter:** Each `SKILL.md` begins with a YAML frontmatter defining structured metadata like `intent_type`, `input_schema`, `output_schema`, `persona`, and `version`. This isn't just documentation; it's data that an LLM-runner can parse and act upon.
+2.  **Decision Tables (Optional but powerful):** Skills can include decision tables that define routing logic *before* an LLM is even called. This allows for conditional execution or parameter adjustment based on inputs, all without relying on the LLM itself for the decision.
+3.  **Persona & Intent Classification:** The `persona` and `intent_type` fields in the frontmatter provide explicit guidance for the skill's role and purpose. An orchestrator can use `intent_type` to route incoming requests to the most appropriate skill, even *before* an LLM analyzes the user's input.
+4.  **CI-Validated Output Contract:** The `output_schema` isn't merely descriptive; it's enforced. USAP includes a CI step that validates the LLM's output against this schema, ensuring that downstream systems receive data in the expected format. This eliminates common LLM "hallucination" issues related to output structure.
+
+## Why This Matters at Runtime: Beyond Simple Prompting
+
+The structured nature of `SKILL.md` transforms a collection of prompts into a library of *intelligent agents*.
+
+*   **Efficient Routing:** An LLM-runner can inspect a skill's `intent_type` and `next_agents` (another field in the frontmatter) to make routing decisions *without* having to query an LLM. This saves tokens, reduces latency, and increases reliability. For example, if a user asks, "Scan this code for vulnerabilities," an orchestrator can immediately identify a `vuln-scan` skill by its `intent_type` without asking an LLM "Which skill should I use?"
+*   **Automated Validation:** Because inputs and outputs are schema-driven, USAP can automatically validate data, perform type conversions, and ensure data integrity throughout a multi-skill workflow.
+*   **Composability:** Skills become reusable building blocks that can be chained together programmatically, much like functions in a traditional codebase. The `next_agents` field explicitly declares potential follow-up skills, making complex workflows discoverable and manageable.
+*   **Predictable Behavior:** The explicit contracts lead to more predictable and testable AI behavior, moving LLM interactions closer to traditional software development principles.
+
+## A Concrete Diff: `appsec-devsecops/vuln-scan/`
+
+Let's consider the `appsec-devsecops/vuln-scan/` skill from the USAP library as an example.
+
+**Scenario 1: As a One-Off Prompt**
+
+You might have a file `vuln_scan_prompt.md`:
+
+```markdown
+# System Prompt
+You are an expert Application Security engineer.
+
+# User Prompt
+Review the following code snippet for security vulnerabilities:
+
+```python
+# User provided code here
+```
+
+Identify potential OWASP Top 10 vulnerabilities. Respond with a JSON object listing severity, description, and suggested fix for each.
+```
+
+Your application would read this, insert the user's code, and send it to the LLM. You'd then need custom code to parse the JSON response and handle any errors if the LLM didn't return valid JSON. There's no inherent way to know *what kind* of response to expect beyond manual inspection.
+
+**Scenario 2: As a USAP Skill (`appsec-devsecops/vuln-scan/`)**
+
+The `SKILL.md` for this skill would include:
+
+*   **`intent_type: vulnerability_scan`**: An orchestrator immediately knows this skill's purpose.
+*   **`input_schema`**: Specifies that the skill expects a `code_snippet` of type string.
+*   **`output_schema`**: Defines the exact JSON structure for identified vulnerabilities (e.g., an array of objects, each with `severity`, `description`, `recommendation`). This schema is validated by USAP's CI, ensuring the LLM *must* conform.
+*   **`persona: AppSec Engineer`**: Explicitly sets the LLM's role.
+*   **`prompt`**: Contains the actual prompt instructions, similar to the one-off example, but now *contained within* a structured contract.
+
+At runtime, an orchestrator could receive a request, see `intent_type: vulnerability_scan`, and route directly to this skill. The `input_schema` would validate the incoming code. After the LLM processes the request, the `output_schema` would automatically validate the LLM's JSON response, ensuring downstream systems receive reliable, structured data. This robustness transforms a simple prompt into a dependable, composable software component.
+
+## Conclusion
+
+While one-off prompt libraries are a valuable tool for organizing LLM instructions, USAP skills elevate this concept by introducing structured contracts, explicit metadata, and runtime validation. This shift transforms inert prompts into intelligent, testable, and composable agents, paving the way for more reliable and scalable AI applications.
```