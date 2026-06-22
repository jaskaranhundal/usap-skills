<div align="center">

# USAP Design System

### `Signal Architecture` — the visual language of the Unified Security Agent Platform

Deep-space field · electric-cyan signal · hexagonal agent nodes · clinical monospace telemetry

</div>

---

## What this is

This is the brand and UI foundation for USAP. It gives designers and agents
everything needed to produce on-brand USAP interfaces, decks, and assets: a deep
near-black field, an electric-cyan signal accent, the hexagonal agent-node
motif, a CVSS-aligned severity scale, and a clinical monospace telemetry layer.

The design philosophy is **"Signal Architecture": the aesthetic of systems that
think** — deep-space telemetry, neural cartography, and cold-war cryptographic
schematics. The interface lives in the dark; cyan is light *emitted* by what is
alive or central.

Source of truth: the [USAP Design System project](https://claude.ai/design/p/e8597b2f-ab1e-46b9-8bcd-e39cd3ef2f18) on `claude.ai/design`. Sync changes by re-running `DesignSync` against that project.

## Quick start

Everything ships from one stylesheet. Link it, then build with the tokens.

```html
<link rel="stylesheet" href="styles.css" />
```

To use the **React components**, load the compiled bundle and read the
namespace off `window`:

```html
<link rel="stylesheet" href="styles.css" />
<script src="_ds_bundle.js"></script>
<script>
  const { Button, SeverityBadge, HexNode } = window.USAPDesignSystem_e8597b;
</script>
```

To see everything assembled — landing page, agent console, findings dashboard —
open [`ui_kits/platform/index.html`](ui_kits/platform/index.html) directly in a
browser (no build step required; React + Babel-in-browser are loaded via CDN).

## Layout

```
docs/design-system/
├── styles.css                 # the one file consumers link (@import only)
├── _ds_bundle.js              # compiled, namespaced React bundle
├── _ds_manifest.json          # component + token manifest
├── tokens/
│   ├── fonts.css              # @font-face / webfont imports
│   ├── colors.css             # surfaces, signal, neutrals, severity
│   ├── typography.css         # families, scale, tracking
│   ├── spacing.css            # 4px grid, radii, layout
│   └── effects.css            # shadows, glows, gradients, motion
├── components/
│   ├── core/                  # Button, Tag, Card
│   ├── inputs/                # Input, Switch
│   ├── security/              # SeverityBadge, ConfidenceMeter, CodeBlock
│   └── brand/                 # HexNode, AgentChip
└── ui_kits/
    └── platform/              # Landing → Console → Findings click-through
```

## Aesthetic at a glance

| | |
|---|---|
| **Mode** | Dark only (there is no light theme in the brand) |
| **Accent** | Electric cyan `#29d3f0`, used as glow/emission — never large fills |
| **Motif** | The hexagon (agent node / hub) |
| **Type** | Space Grotesk · IBM Plex Sans · IBM Plex Mono |
| **Motion** | Precise, no overshoot — "signals don't bounce" |

## Components

| Component | Group | What it is |
|---|---|---|
| `Button` | core | HUD action control — `primary` / `secondary` / `ghost` / `danger`, three sizes |
| `Tag` | core | Mono metadata capsule — `neutral` / `signal` / `agent` / `ok` |
| `Card` | core | The default dark panel surface, optional cyan accent rail + hover lift |
| `Input` | inputs | Terminal-style field with prompt glyph and cyan focus glow |
| `Switch` | inputs | Approval-gate toggle; on-state glows cyan |
| `SeverityBadge` | security | CVSS chip — solid for critical/high, outlined otherwise |
| `ConfidenceMeter` | security | Segmented 0–1 confidence bar (the contract's `confidence`) |
| `CodeBlock` | security | Terminal panel with traffic-light chrome + JSON highlighting |
| `HexNode` | brand | The signature hexagonal agent node (hub + peripheral) |
| `AgentChip` | brand | Identity token for a `cs-*` agent — violet dot + mono slug |

## Caveats

- **Fonts are substitutes.** Space Grotesk / IBM Plex Sans / IBM Plex Mono load remotely from Google Fonts via `tokens/fonts.css`.
- **No GUI exists in the upstream USAP source** — USAP is a CLI + skills library. Surfaces here are faithful applications of the key art and documented demo, not recreations of a shipped app.
