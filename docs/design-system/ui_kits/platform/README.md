# UI Kit — USAP Platform

A high-fidelity realization of USAP as a product surface. USAP ships as an
open-source **CLI + skills library** (no GUI in the source repo), so this kit
faithfully renders the brand's established **"Signal Architecture"** key art and
its **documented agent-console demo** (`cs-appsec-engineer` → `vuln-scan` →
`finding-triage`, byte-identical to the repo's `sample_output.json`). Nothing
here is invented UX — it visualizes flows the README already documents.

## Screens

| File | Screen | Notes |
|---|---|---|
| `Landing.jsx` | Marketing hero | Hub-and-node hex constellation (from the LinkedIn key art), headline, 79/12/12 stats, CTAs. |
| `Console.jsx` | Agent console | The documented demo: a prompt runs `vuln-scan`, an agent replies, the 11-field JSON payload renders, confidence + handoff chip appear. |
| `Findings.jsx` | Findings dashboard | The five `SimpleStoreAPI` findings as a triage table with CVSS severity chips, threat-model mapping, and filter rail. |

`index.html` wires them into an interactive click-through: **Landing → Launch
console → Run → Open findings → back**.

## Composition

Every screen is built from the design-system primitives via
`window.USAPDesignSystem_e8597b` — `HexNode`, `AgentChip`, `Button`, `Card`,
`Tag`, `Input`, `SeverityBadge`, `ConfidenceMeter`, `CodeBlock`. No primitive is
re-implemented here.

> The compiled `_ds_bundle.js` is generated at the project root; these files load
> it via `../../_ds_bundle.js`.
