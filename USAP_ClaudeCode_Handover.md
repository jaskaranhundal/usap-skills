# USAP — Claude Code Handover

**Repo:** `jaskaranhundal/usap-skills`
**Goal:** turn USAP into a credible, visible portfolio centerpiece that lands a Cloud / AI Security Engineer role (Germany, €75–90k+).
**Current state (good):** 79 skills, 12 `cs-*` orchestrator agents; framework-mapped (MITRE ATT&CK, ATLAS, NIST CSF 2.0, OWASP Top 10, D3FEND, NIST AI RMF) at the metadata layer; 11-field typed output contract; L1–L4 autonomy with `human_approval_required` gates; agentskills.io conformant; multi-tool.
**Weak spots to fix:** no visuals; claims without shown proof; README leads with raw counts; competitor framing risks implying parity with funded SaaS.

---

## Operating principles (do not violate)
1. **Accuracy over hype.** Every README claim must be verifiable. Never invent stars, usage, or adoption numbers.
2. **Precise attribution.** State exactly what is "ported from Anthropic's defensive-AI reference harness" vs original. No overstatement.
3. **Quality over quantity.** Do NOT add new skills or agents. Polish and prove what exists.
4. **Show, don't tell.** Prefer diagrams, a demo, and sample outputs over prose claims.

---

## Tasks — one PR each, in priority order

### 1. Rewrite the README hook
- Replace the dense bold paragraph with ONE crisp sentence (≤25 words): what it is, who it's for, where it runs.
- Move the detailed feature list to a section below it.
- **Done when:** the first line is a single scannable sentence and the skill count is not in it.

### 2. Add an architecture diagram
- Add a Mermaid diagram near the top: the 12 `cs-*` agents grouped by domain, plus the skill → agent → 11-field-output flow.
- **Done when:** it renders on GitHub and sits above the fold.

### 3. Add a working demo
- Produce an asciinema cast or GIF of `/usap-alex` handling one realistic alert end-to-end, showing the structured 11-field output. Embed near the top.
- If recording isn't feasible in this environment, generate a faithful example transcript in a fenced code block, clearly labeled as sample output.
- **Done when:** a reader can see USAP produce real structured output without installing it.

### 4. Reframe positioning
- Lead the value prop with the real differentiator: open-source (Apache-2.0), owned / no lock-in, typed output contract, framework-mapped — NOT the skill count.
- Reframe the competitor-table header as "open-source skills library vs paid SaaS platforms" (a different category); remove any implication of parity with funded autonomous-SOC products.
- **Done when:** the first paragraph emphasizes openness + standards + contract, and the table is framed as a category contrast.

### 5. Show proof
- Add one complete, real 11-field output example for a sample finding.
- Add a snippet or screenshot of the auto-generated ATT&CK Navigator layer and the NIST CSF coverage doc.
- **Done when:** the documented contract and mappings are demonstrated, not just asserted.

### 6. Reconcile counts
- Make skill/agent counts identical across README body, badges, the About blurb, and the GitHub profile bio.
- **Done when:** counts agree everywhere (`grep -ri "skills" README.md` + badges).

### 7. Self-audit (it's a security tool)
- Run USAP's own security-audit / `skill-security` skill against its own scripts. Add or verify `SECURITY.md`. Ensure no secrets, safe defaults, SHA-pinned dependencies.
- **Done when:** a self-audit result is committed and `SECURITY.md` exists.

### 8. Repo maturity
- Add/refresh `CHANGELOG.md`, cut a semver-tagged release, ensure `CONTRIBUTING.md` + "good first issue" labels exist, keep the repo pinned.
- **Done when:** a tagged release exists with a CHANGELOG entry.

---

## Do NOT
- Add new skills or agents.
- Fabricate metrics, stars, or adoption.
- Claim parity with funded SaaS platforms.
- Weaken attribution or remove honest framing.

*Career plan and résumé live in a separate doc (`Jaskarn_CareerPlan_CloudSecurity_AI.md`) — out of scope for this repo work.*
