# SRE Runbook Advisor Workflow

## Runbook Generation

1. Identify the service and failure mode from alert context
2. Calculate SLO burn rate: `burn_rate = error_rate / (1 - slo_target)`
3. Map common root causes for this failure mode
4. Generate diagnosis steps with specific commands and metrics
5. Define resolution paths for each root cause
6. Set escalation criteria

## SLO Analysis

1. Receive alert context: error rate, SLO target, time window
2. Calculate burn rate
3. Determine alert tier based on burn rate threshold
4. Estimate time to error budget exhaustion: `eta = (1 - slo_target) / error_rate`
5. Recommend escalation level

## Postmortem Facilitation (Blameless)

1. Collect incident timeline from all stakeholders
2. Identify contributing factors — focus on systems, not people
3. Facilitate 5-Why root cause analysis
4. Define action items with owners and due dates
5. Produce blameless postmortem document
6. Route to knowledge-management for storage

## On-Call Handoff Checklist

- [ ] Current incident state summarized
- [ ] All active actions listed with owners
- [ ] Unresolved hypotheses documented
- [ ] Next check-in time defined
- [ ] Stakeholder communication status noted
