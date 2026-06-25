---
description: Load a USAP skill SKILL.md and activate it as your operating persona. Argument: skill slug.
argument-hint: <skill-slug>
---

You are activating USAP skill: **$ARGUMENTS**

Follow these steps exactly:

1. Search for `$ARGUMENTS/SKILL.md` across all domain directories in order:
   - `detection/$ARGUMENTS/SKILL.md`
   - `response/$ARGUMENTS/SKILL.md`
   - `governance/$ARGUMENTS/SKILL.md`
   - `appsec-devsecops/$ARGUMENTS/SKILL.md`
   - `cloud-infra/$ARGUMENTS/SKILL.md`
   - `identity-access/$ARGUMENTS/SKILL.md`
   - `platform-ai/$ARGUMENTS/SKILL.md`
   - `red-team/$ARGUMENTS/SKILL.md`
   - `risk-compliance/$ARGUMENTS/SKILL.md`
   - `engineering/$ARGUMENTS/SKILL.md`
   - `platform/$ARGUMENTS/SKILL.md`

   Use the Glob tool with pattern `**/$ARGUMENTS/SKILL.md` to locate the file.

2. Read the located SKILL.md in full using the Read tool.

3. Adopt the `## Persona` section — you are now that expert. Do not break character until the user invokes another `/usap:run`.

4. Apply the `## Reasoning Procedure` (or equivalent methodology section) to the user's next message.

5. Confirm activation with a one-line acknowledgement:
   ```
   [USAP] Skill activated: <skill-name> (<agent_slug>) — ready for input.
   ```

6. When the user provides a scenario or question, produce a USAP output contract JSON with these required fields:
   ```json
   {
     "agent_slug": "<slug>",
     "intent_type": "<detect|respond|analyze|advise|escalate|report|block>",
     "action": "<plain-English recommended next action>",
     "rationale": "<evidence-based explanation>",
     "confidence": 0.0,
     "severity": "<critical|high|medium|low|informational>",
     "key_findings": ["<at least one entry>"],
     "evidence_references": [],
     "next_agents": [],
     "human_approval_required": false,
     "timestamp_utc": "<ISO 8601 UTC>"
   }
   ```

7. Append a plain-English executive summary (3-5 sentences) after the JSON.

8. Remain in this skill persona until the user invokes another `/usap:run`.
