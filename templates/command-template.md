# Command Template

Placeholder for slash-command templates. Use this file as a scaffold when adding new Claude Code slash commands to the USAP platform.

## Command Structure

```yaml
---
name: /<command-name>
description: <one-line description>
trigger: <when this command should be invoked>
---
```

## Command Body

```
<Full command prompt body here.>
<Include context, workflow steps, and expected output format.>
```

## Example Commands

### /usap-triage
Trigger a full triage workflow using `incident-classification` → appropriate specialist skill.

### /usap-hunt
Launch a threat hunting session using `threat-hunting` with a provided hypothesis.

### /usap-posture
Generate a security posture score using `security-posture-score` + `metrics-reporting`.

## Adding a New Command

1. Copy this template.
2. Fill in YAML frontmatter.
3. Write the command prompt body following SKILL.md conventions.
4. Register the command in the platform's command registry.
5. Test with a representative input payload.
