---
title: USAP Design System
description: Signal Architecture — the visual language and React component library for USAP. Deep-space field, electric-cyan signal, hexagonal agent nodes, clinical monospace telemetry.
---

# USAP Design System

**Signal Architecture** — the visual language and React component library
for the Unified Security Agent Platform. Deep-space field, electric-cyan
signal, hexagonal agent nodes, clinical monospace telemetry.

[Open the live platform UI kit →](design-system/ui_kits/platform/index.html){ .md-button .md-button--primary }
[Read the design system README →](design-system/README.md){ .md-button }

## What this gives you

| | |
|---|---|
| **10 React components** | `Button`, `Card`, `Tag`, `Input`, `Switch`, `SeverityBadge`, `ConfidenceMeter`, `CodeBlock`, `HexNode`, `AgentChip` |
| **160+ CSS tokens** | Colors (signal cyan + CVSS severity + surfaces), typography, spacing, radii, effects |
| **3-screen UI kit** | Landing → Agent Console → Findings — assembled entirely from the primitives, demoing the `cs-appsec-engineer → vuln-scan → finding-triage` flow |
| **14 specimen cards** | Brand, color, motion, type, spacing — open any one directly from `design-system/guidelines/` |

## Watchable demo: the platform UI kit

The kit lives at [`design-system/ui_kits/platform/index.html`](design-system/ui_kits/platform/index.html). Open it in any browser — no build step. React + Babel-in-browser are loaded from a CDN; everything else is local.

The three screens click through:

1. **Landing** — hub-and-node hex constellation with `cs-security-analyst`, `cs-incident-responder`, `cs-program-manager`, `cs-ciso-advisor` orbiting USAP at the center. The hero stat line shows `79 skills · 12 agents · 12 domains`.
2. **Agent Console** — a faithful, interactive render of the documented demo. You type a prompt, hit Run, the agent narrates, and the typed 11-field JSON payload renders in a terminal panel. The payload is **byte-identical** to [`appsec-devsecops/vuln-scan/expected_outputs/sample_output.json`](https://github.com/jaskaranhundal/usap-skills/blob/main/appsec-devsecops/vuln-scan/expected_outputs/sample_output.json).
3. **Findings** — the same 5 `SimpleStoreAPI` findings rendered as a CVSS-aligned triage table with a filter rail and threat-model mapping.

## Aesthetic at a glance

| | |
|---|---|
| **Mode** | Dark only — no light theme in the brand |
| **Accent** | Electric cyan `#29d3f0`, used as glow / emission, never as a large fill |
| **Motif** | The hexagon (agent node / hub) |
| **Type** | Space Grotesk display · IBM Plex Sans body · IBM Plex Mono telemetry |
| **Motion** | Precise, no overshoot — "signals don't bounce" |
| **Philosophy** | Mission-control meets a security-cleared terminal |

## Source of truth

This design system is the in-repo materialization of the [USAP Design System project on claude.ai/design](https://claude.ai/design/p/e8597b2f-ab1e-46b9-8bcd-e39cd3ef2f18). The project is the canonical authoring surface; the files under [`docs/design-system/`](https://github.com/jaskaranhundal/usap-skills/tree/main/docs/design-system) are a faithful import. Re-sync by re-running `DesignSync` against that project.

The compiled `_ds_bundle.js` and `_ds_manifest.json` are generated artifacts — never edit them by hand.

## Why it exists

USAP ships as a CLI + skills library. There is no GUI in the source repo. This design system gives the project a coherent visual language for everything outside the terminal — the docs site you're reading, screenshots in talks and articles, the LinkedIn key art, and any future product surface. Every screen in the kit is a faithful application of the **documented agent demo and the brand's hub-and-node key art** — nothing invented, everything traceable back to a file in the repo.
