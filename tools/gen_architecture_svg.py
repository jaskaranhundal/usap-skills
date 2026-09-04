#!/usr/bin/env python3
"""Generate a Signal-Architecture-styled hex constellation diagram.

Output: docs/assets/usap-architecture.svg

The diagram shows:
- A central USAP hub (large cyan-bordered hexagon with glow + circuit substrate)
- 12 peripheral hexes — one per cs-* orchestrator agent — arranged in a single
  ring at 30° spacing
- Connective lines from each peripheral to the hub
- Domain colour-coding on the peripheral border (security / appsec / devsecops /
  executive / governance)
- An "11-FIELD JSON OUTPUT CONTRACT" caption capsule at the bottom right
- SMIL animation: peripherals fade in sequentially clockwise; the hub pulses

Colors and tokens are pulled verbatim from docs/design-system/tokens/colors.css.
Stdlib only.
"""
from __future__ import annotations
import argparse
import math
from pathlib import Path
from typing import List, Tuple

REPO_ROOT = Path(__file__).resolve().parent.parent

# Canvas
W = 1200
H = 800
CX = W // 2
CY = 380

# Signal Architecture palette (token values from docs/design-system/tokens/colors.css)
VOID = "#05080d"
BG = "#0a0e16"
SURFACE_1 = "#0d1117"
SURFACE_2 = "#11161f"
SURFACE_3 = "#161b22"
LINE_1 = "#1f2630"
CYAN_900 = "#06222b"
CYAN_700 = "#0e4a5c"
CYAN_500 = "#1a8aa3"
CYAN_400 = "#29d3f0"
CYAN_300 = "#5ee6ff"
INK_100 = "#e6edf3"
INK_200 = "#c9d1d9"
INK_300 = "#8b949e"
VIOLET_400 = "#d2a8ff"
ORANGE_400 = "#ffa657"
GREEN_400 = "#7ee787"
BLUE_400 = "#79c0ff"

# Domain → border colour. Security stays cyan (the brand primary); the others
# get the same accent colours the design tokens already use for those concepts.
DOMAIN_COLORS = {
    "security":   CYAN_400,
    "appsec":     VIOLET_400,
    "devsecops":  ORANGE_400,
    "executive":  BLUE_400,
    "governance": GREEN_400,
}

# All 12 cs-* agents in the order they sit around the ring (clockwise from 12).
# (label, slug, domain). label = HUD short title; slug = agent dir name.
NODES = [
    ("ALERT TRIAGE",      "cs-security-analyst",        "security"),
    ("THREAT HUNT",       "cs-threat-intel-lead",       "security"),
    ("BLUE TEAM",         "cs-blue-team-analyst",       "security"),
    ("PURPLE TEAM",       "cs-purple-team-lead",        "security"),
    ("RED TEAM",          "cs-red-teamer",              "security"),
    ("CLOUD INVESTIGATE", "cs-cloud-investigator",      "security"),
    ("SUPPLY CHAIN",      "cs-supply-chain-defender",   "security"),
    ("IR COMMAND",        "cs-incident-responder",      "security"),
    ("APPSEC",            "cs-appsec-engineer",         "appsec"),
    ("DEVSECOPS",         "cs-devsecops-engineer",      "devsecops"),
    ("EXECUTIVE BRIEF",   "cs-ciso-advisor",            "executive"),
    ("PROGRAM OPS",       "cs-security-program-manager", "governance"),
]

# Hex geometry
HUB_SIZE = 220   # width of the central hub
NODE_SIZE = 140  # width of each peripheral hex
RING_R = 260     # radius of the peripheral ring (centre-to-centre)

def hex_points(cx, cy, w):
    """Pointy-top hexagon points — same proportions as HexNode.jsx clip-path."""
    h = w * 1.1
    return [
        (cx,        cy - h / 2),               # 50% 0%
        (cx + w / 2, cy - h / 4),              # 100% 25%
        (cx + w / 2, cy + h / 4),              # 100% 75%
        (cx,        cy + h / 2),               # 50% 100%
        (cx - w / 2, cy + h / 4),              # 0% 75%
        (cx - w / 2, cy - h / 4),              # 0% 25%
    ]


def pts_attr(points):
    return " ".join(f"{x:.1f},{y:.1f}" for x, y in points)


def hex_node(cx, cy, w, label, sub, color, hub=False, delay=0.0):
    """Render one hex node with an animated fade-in."""
    inner_w = w - (4 if hub else 3)
    inner_h = inner_w * 1.1
    outer_pts = pts_attr(hex_points(cx, cy, w))
    inner_pts = pts_attr(hex_points(cx, cy, inner_w))
    glow_filter = "url(#hub-glow)" if hub else "url(#node-glow)"
    label_color = INK_100 if hub else CYAN_300
    sub_color = INK_300

    parts = []
    parts.append(f'<g opacity="0">')
    # outer border polygon
    parts.append(f'<polygon points="{outer_pts}" fill="{color}" filter="{glow_filter}"/>')
    # inner face polygon
    inner_fill = "url(#hub-fill)" if hub else SURFACE_1
    parts.append(f'<polygon points="{inner_pts}" fill="{inner_fill}"/>')
    if hub:
        # large wordmark inside hub
        parts.append(
            f'<text x="{cx}" y="{cy + 18}" fill="{INK_100}" '
            f'font-family="\'Space Grotesk\', sans-serif" font-weight="700" '
            f'font-size="62" text-anchor="middle" letter-spacing="-0.02em">'
            f'USA<tspan fill="{CYAN_400}">P</tspan></text>'
        )
        parts.append(
            f'<text x="{cx}" y="{cy + 50}" fill="{INK_300}" '
            f'font-family="\'IBM Plex Mono\', monospace" font-size="11" '
            f'letter-spacing="0.18em" text-anchor="middle">UNIFIED SECURITY AGENT PLATFORM</text>'
        )
    else:
        parts.append(
            f'<text x="{cx}" y="{cy - 4}" fill="{label_color}" '
            f'font-family="\'IBM Plex Mono\', monospace" font-weight="600" '
            f'font-size="12" letter-spacing="0.12em" text-anchor="middle">{label}</text>'
        )
        parts.append(
            f'<text x="{cx}" y="{cy + 14}" fill="{sub_color}" '
            f'font-family="\'IBM Plex Mono\', monospace" font-size="9.5" '
            f'letter-spacing="0.04em" text-anchor="middle">{sub}</text>'
        )
    parts.append(
        f'<animate attributeName="opacity" from="0" to="1" '
        f'begin="{delay:.2f}s" dur="0.35s" fill="freeze"/>'
    )
    parts.append('</g>')
    return "\n".join(parts)


def render() -> str:
    parts: List[str] = []
    parts.append(
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" '
        f'width="100%" font-family="\'IBM Plex Sans\', system-ui, sans-serif">'
    )
    # Defs: filters + gradients + the circuit-grid pattern
    parts.append('<defs>')
    parts.append(
        f'<filter id="hub-glow" x="-50%" y="-50%" width="200%" height="200%">'
        f'<feGaussianBlur in="SourceGraphic" stdDeviation="6"/>'
        f'<feMerge><feMergeNode/><feMergeNode in="SourceGraphic"/></feMerge>'
        f'</filter>'
    )
    parts.append(
        f'<filter id="node-glow" x="-50%" y="-50%" width="200%" height="200%">'
        f'<feGaussianBlur in="SourceGraphic" stdDeviation="2"/>'
        f'<feMerge><feMergeNode/><feMergeNode in="SourceGraphic"/></feMerge>'
        f'</filter>'
    )
    # Radial fill for the hub face — cyan-900 → void (matches HexNode.jsx hub gradient)
    parts.append(
        f'<radialGradient id="hub-fill" cx="50%" cy="45%" r="65%">'
        f'<stop offset="0%" stop-color="{CYAN_900}"/>'
        f'<stop offset="100%" stop-color="{VOID}"/>'
        f'</radialGradient>'
    )
    # Hub-spotlight gradient on the background (--grad-hub token)
    parts.append(
        f'<radialGradient id="bg-spot" cx="50%" cy="50%" r="55%">'
        f'<stop offset="0%" stop-color="rgba(41,211,240,0.14)"/>'
        f'<stop offset="100%" stop-color="rgba(41,211,240,0)"/>'
        f'</radialGradient>'
    )
    # Circuit substrate pattern — faint cyan grid (--texture-grid token)
    parts.append(
        f'<pattern id="grid" x="0" y="0" width="32" height="32" patternUnits="userSpaceOnUse">'
        f'<path d="M 32 0 L 0 0 0 32" fill="none" stroke="rgba(41,211,240,0.045)" stroke-width="1"/>'
        f'</pattern>'
    )
    # Connective-line gradient (dimmer at the ends, brighter in the middle)
    parts.append(
        f'<linearGradient id="link" x1="0" y1="0" x2="1" y2="0">'
        f'<stop offset="0%" stop-color="rgba(41,211,240,0.05)"/>'
        f'<stop offset="50%" stop-color="rgba(41,211,240,0.4)"/>'
        f'<stop offset="100%" stop-color="rgba(41,211,240,0.05)"/>'
        f'</linearGradient>'
    )
    parts.append('</defs>')

    # Background layers
    parts.append(f'<rect x="0" y="0" width="{W}" height="{H}" fill="{VOID}"/>')
    parts.append(f'<rect x="0" y="0" width="{W}" height="{H}" fill="url(#grid)"/>')
    parts.append(f'<rect x="0" y="0" width="{W}" height="{H}" fill="url(#bg-spot)"/>')

    # Connective lines — drawn FIRST so the nodes sit on top
    line_anim_offset = 0.05
    for i, _ in enumerate(NODES):
        angle = (i / len(NODES)) * 2 * math.pi - math.pi / 2  # start at 12 o'clock
        nx = CX + RING_R * math.cos(angle)
        ny = CY + RING_R * math.sin(angle)
        parts.append(
            f'<line x1="{CX}" y1="{CY}" x2="{nx:.1f}" y2="{ny:.1f}" '
            f'stroke="url(#link)" stroke-width="1.5" stroke-dasharray="4 6" opacity="0">'
            f'<animate attributeName="opacity" from="0" to="1" begin="{line_anim_offset + i * 0.08:.2f}s" '
            f'dur="0.3s" fill="freeze"/>'
            f'</line>'
        )

    # Peripheral nodes
    base_node_delay = 0.6
    for i, (label, slug, domain) in enumerate(NODES):
        angle = (i / len(NODES)) * 2 * math.pi - math.pi / 2
        nx = CX + RING_R * math.cos(angle)
        ny = CY + RING_R * math.sin(angle)
        parts.append(hex_node(nx, ny, NODE_SIZE, label, slug, DOMAIN_COLORS[domain],
                              hub=False, delay=base_node_delay + i * 0.08))

    # Central hub LAST so it sits over the link starts cleanly
    parts.append(hex_node(CX, CY, HUB_SIZE, "USAP", "", CYAN_400, hub=True, delay=0.0))

    # Hub ambient pulse: a second hex outline that fades/scales on a loop
    pulse_r = HUB_SIZE / 2 + 12
    parts.append(
        f'<circle cx="{CX}" cy="{CY}" r="{pulse_r}" fill="none" stroke="{CYAN_400}" '
        f'stroke-width="1" opacity="0">'
        f'<animate attributeName="opacity" values="0;0.5;0" dur="2.4s" begin="2.2s" repeatCount="indefinite"/>'
        f'<animate attributeName="r" values="{pulse_r};{pulse_r + 28};{pulse_r}" dur="2.4s" begin="2.2s" repeatCount="indefinite"/>'
        f'</circle>'
    )

    # Output-contract capsule at the bottom
    cap_w, cap_h = 760, 56
    cap_x = CX - cap_w / 2
    cap_y = 730
    parts.append(
        f'<g opacity="0">'
        f'<rect x="{cap_x}" y="{cap_y}" width="{cap_w}" height="{cap_h}" rx="10" '
        f'fill="{SURFACE_1}" stroke="{CYAN_700}" stroke-width="1"/>'
        f'<text x="{CX}" y="{cap_y + 26}" text-anchor="middle" '
        f'font-family="\'IBM Plex Mono\', monospace" font-size="10.5" letter-spacing="0.18em" '
        f'fill="{CYAN_400}">11-FIELD JSON OUTPUT CONTRACT</text>'
        f'<text x="{CX}" y="{cap_y + 47}" text-anchor="middle" '
        f'font-family="\'IBM Plex Mono\', monospace" font-size="11" letter-spacing="0.04em" '
        f'fill="{INK_200}">agent_slug · intent_type · action · rationale · confidence · severity · '
        f'key_findings · evidence_references · next_agents · human_approval_required · timestamp_utc</text>'
        f'<animate attributeName="opacity" from="0" to="1" begin="1.7s" dur="0.5s" fill="freeze"/>'
        f'</g>'
    )

    # Top-left HUD caption
    parts.append(
        f'<g opacity="0">'
        f'<text x="40" y="50" font-family="\'IBM Plex Mono\', monospace" font-size="11" '
        f'letter-spacing="0.2em" fill="{CYAN_400}">USAP · ARCHITECTURE</text>'
        f'<text x="40" y="70" font-family="\'IBM Plex Mono\', monospace" font-size="10" '
        f'letter-spacing="0.08em" fill="{INK_300}">81 skills · 13 cs-* agents · 12 active domains</text>'
        f'<animate attributeName="opacity" from="0" to="1" begin="0.1s" dur="0.4s" fill="freeze"/>'
        f'</g>'
    )

    # Domain colour legend (top-right)
    legend_x = W - 220
    legend_y = 40
    parts.append('<g opacity="0">')
    legend_items = [
        ("security/",   CYAN_400),
        ("appsec/",     VIOLET_400),
        ("devsecops/",  ORANGE_400),
        ("executive/",  BLUE_400),
        ("governance/", GREEN_400),
    ]
    for li, (lbl, col) in enumerate(legend_items):
        ly = legend_y + li * 18
        parts.append(
            f'<rect x="{legend_x}" y="{ly}" width="14" height="14" fill="{col}" rx="2"/>'
            f'<text x="{legend_x + 22}" y="{ly + 11}" font-family="\'IBM Plex Mono\', monospace" '
            f'font-size="10.5" fill="{INK_200}" letter-spacing="0.06em">{lbl}</text>'
        )
    parts.append(
        f'<animate attributeName="opacity" from="0" to="1" begin="1.5s" dur="0.4s" fill="freeze"/>'
        f'</g>'
    )

    parts.append('</svg>')
    return "\n".join(parts)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--output", default=str(REPO_ROOT / "docs/assets/usap-architecture.svg"))
    args = ap.parse_args()
    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(render())
    print(f"wrote {out} ({out.stat().st_size} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
