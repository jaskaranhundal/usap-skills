# Red Team Domain

Skills in this domain plan, execute, and report on adversarial security testing operations.

## Skills

| Slug | Level | Description |
|---|---|---|
| `red-team-operations` | L3 | Kill Chain execution planning: OPSEC, C2 design, lateral movement, exfil staging (requires authorization) |
| `red-team-planner` | L3 | Red team campaign planning: objectives, scope, RoE, phase map, authorization validation |
| `safe-exploitation` | L3 | Scoped, safe exploitation execution with minimal footprint and mandatory abort conditions |
| `continuous-pentesting` | L3 | Interprets and prioritizes automated continuous penetration testing results |
| `attack-path-analysis` | L3 | Maps attacker lateral movement paths through network topology to reach target assets |
| `ai-red-teaming` | L4 | Adversarial testing of AI/ML systems: prompt injection, model inversion, jailbreaks |

## Authorization Requirements

All red team skills require explicit written authorization before execution. The `red-team-planner` skill validates authorization documents as part of its workflow.

**Mandatory Pre-Engagement Checklist:**
- [ ] Signed Rules of Engagement (RoE) document
- [ ] Defined scope boundaries (IPs, domains, systems)
- [ ] Emergency contact and abort procedures
- [ ] Data handling agreement for discovered vulnerabilities
- [ ] Legal authorization letter from asset owner

## Kill Chain Phases Covered

1. Reconnaissance
2. Weaponization
3. Delivery
4. Exploitation
5. Installation
6. Command & Control
7. Actions on Objectives

## Orchestrator Agent

[cs-red-teamer](../agents/security/cs-red-teamer.md) — coordinates red team skills for full engagement lifecycle management.
