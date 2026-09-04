#!/usr/bin/env python3
"""Generate the Signal-Architecture USAP README banner.

Output: docs/assets/usap-banner.svg

Replaces the legacy LinkedIn key art PNG (usap-keyart.png). The banner is
a wide hero composition built from the design-system tokens:

  - Left half: wordmark + tagline + the three forcing stats (81/13/12)
  - Right half: central USAP hub orbited by 6 representative peripheral
    hexes (4 corners + top + bottom), with connective links from each
    back to the hub
  - Underlay: circuit-grid texture (--texture-grid) + radial hub spotlight
    (--grad-hub), both pulled from tokens/effects.css
  - SMIL animation: wordmark fades in, peripherals appear one at a time
    clockwise, the hub pulses ambiently, the tagline reveals last

The stats and agent labels embedded in the banner are the same values
the README quotes elsewhere — change them in NODES / STATS below and
re-run the script to regenerate.

Stdlib only.
"""
from __future__ import annotations
import argparse
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

# Canvas — wide hero ratio.
W = 1280
H = 440

# Signal Architecture palette (pulled verbatim from design-system tokens).
VOID = "#05080d"
SURFACE_1 = "#0d1117"
SURFACE_2 = "#11161f"
SURFACE_3 = "#161b22"
LINE_2 = "#2a323d"
CYAN_900 = "#06222b"
CYAN_700 = "#0e4a5c"
CYAN_400 = "#29d3f0"
CYAN_300 = "#5ee6ff"
INK_50 = "#f4f8fb"
INK_100 = "#e6edf3"
INK_200 = "#c9d1d9"
INK_300 = "#8b949e"
VIOLET_400 = "#d2a8ff"
ORANGE_400 = "#ffa657"
GREEN_400 = "#7ee787"
BLUE_400 = "#79c0ff"

# Right-side hex constellation.
HUB_CX = 970
HUB_CY = 220
HUB_W = 170
NODE_W = 96
RING_R = 165

# 6 peripheral nodes (clockwise from 12 o'clock). Pick the ones that
# represent the breadth of the cs-* fleet without trying to squeeze all
# 12 in — the full architecture diagram (usap-architecture.svg) covers
# that already.
NODES = [
    ("ALERT TRIAGE",       "cs-security-analyst",       "security",   ( 0, -1)),
    ("APPSEC",             "cs-appsec-engineer",        "appsec",     ( 0.866, -0.5)),
    ("EXEC BRIEF",         "cs-ciso-advisor",           "executive",  ( 0.866,  0.5)),
    ("INCIDENT",           "cs-incident-responder",     "security",   ( 0,  1)),
    ("DEVSECOPS",          "cs-devsecops-engineer",     "devsecops",  (-0.866,  0.5)),
    ("THREAT HUNT",        "cs-threat-intel-lead",      "security",   (-0.866, -0.5)),
]

DOMAIN_COLORS = {
    "security":   CYAN_400,
    "appsec":     VIOLET_400,
    "devsecops":  ORANGE_400,
    "executive":  BLUE_400,
    "governance": GREEN_400,
}

STATS = [
    ("81",  "Skills"),
    ("13",  "cs-* agents"),
    ("12",  "Domains"),
]


def hex_pts(cx, cy, w):
    """Pointy-top hexagon — matches the design-system HexNode proportions."""
    h = w * 1.1
    return [
        (cx,        cy - h / 2),
        (cx + w / 2, cy - h / 4),
        (cx + w / 2, cy + h / 4),
        (cx,        cy + h / 2),
        (cx - w / 2, cy + h / 4),
        (cx - w / 2, cy - h / 4),
    ]


def pts_attr(pts):
    return " ".join(f"{x:.1f},{y:.1f}" for x, y in pts)


def hex_node(cx, cy, w, label, sub, color, hub=False, delay=0.0):
    inner_w = w - (3 if hub else 2.5)
    outer = pts_attr(hex_pts(cx, cy, w))
    inner = pts_attr(hex_pts(cx, cy, inner_w))
    fill = "url(#hub-fill)" if hub else SURFACE_1
    glow = "url(#hub-glow)" if hub else "url(#node-glow)"
    out = [f'<g opacity="0">']
    out.append(f'<polygon points="{outer}" fill="{color}" filter="{glow}"/>')
    out.append(f'<polygon points="{inner}" fill="{fill}"/>')
    if hub:
        out.append(
            f'<text x="{cx}" y="{cy + 14}" fill="{INK_50}" '
            f'font-family="\'Space Grotesk\', sans-serif" font-weight="700" '
            f'font-size="46" text-anchor="middle" letter-spacing="-0.02em">'
            f'USA<tspan fill="{CYAN_400}">P</tspan></text>'
        )
    else:
        out.append(
            f'<text x="{cx}" y="{cy - 2}" fill="{CYAN_300}" '
            f'font-family="\'IBM Plex Mono\', monospace" font-weight="600" '
            f'font-size="9.5" letter-spacing="0.1em" text-anchor="middle">{label}</text>'
        )
        out.append(
            f'<text x="{cx}" y="{cy + 12}" fill="{INK_300}" '
            f'font-family="\'IBM Plex Mono\', monospace" font-size="7.5" '
            f'letter-spacing="0.04em" text-anchor="middle">{sub}</text>'
        )
    out.append(
        f'<animate attributeName="opacity" from="0" to="1" '
        f'begin="{delay:.2f}s" dur="0.35s" fill="freeze"/>'
    )
    out.append('</g>')
    return "\n".join(out)


def render() -> str:
    p = []
    p.append(
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" '
        f'width="100%" font-family="\'IBM Plex Sans\', system-ui, sans-serif">'
    )

    # defs
    p.append('<defs>')
    p.append(
        f'<filter id="hub-glow" x="-50%" y="-50%" width="200%" height="200%">'
        f'<feGaussianBlur in="SourceGraphic" stdDeviation="5"/>'
        f'<feMerge><feMergeNode/><feMergeNode in="SourceGraphic"/></feMerge>'
        f'</filter>'
    )
    p.append(
        f'<filter id="node-glow" x="-50%" y="-50%" width="200%" height="200%">'
        f'<feGaussianBlur in="SourceGraphic" stdDeviation="1.6"/>'
        f'<feMerge><feMergeNode/><feMergeNode in="SourceGraphic"/></feMerge>'
        f'</filter>'
    )
    p.append(
        f'<radialGradient id="hub-fill" cx="50%" cy="45%" r="65%">'
        f'<stop offset="0%" stop-color="{CYAN_900}"/>'
        f'<stop offset="100%" stop-color="{VOID}"/>'
        f'</radialGradient>'
    )
    p.append(
        f'<radialGradient id="hub-spot" cx="{HUB_CX}" cy="{HUB_CY}" r="280" '
        f'gradientUnits="userSpaceOnUse">'
        f'<stop offset="0%" stop-color="rgba(41,211,240,0.18)"/>'
        f'<stop offset="100%" stop-color="rgba(41,211,240,0)"/>'
        f'</radialGradient>'
    )
    p.append(
        f'<pattern id="grid" x="0" y="0" width="28" height="28" patternUnits="userSpaceOnUse">'
        f'<path d="M 28 0 L 0 0 0 28" fill="none" stroke="rgba(41,211,240,0.045)" stroke-width="1"/>'
        f'</pattern>'
    )
    p.append(
        f'<linearGradient id="link" x1="0" y1="0" x2="1" y2="0">'
        f'<stop offset="0%" stop-color="rgba(41,211,240,0.06)"/>'
        f'<stop offset="50%" stop-color="rgba(41,211,240,0.45)"/>'
        f'<stop offset="100%" stop-color="rgba(41,211,240,0.06)"/>'
        f'</linearGradient>'
    )
    # Subtle vignette protecting the left edge so the wordmark stays legible
    p.append(
        f'<linearGradient id="left-shade" x1="0" y1="0" x2="1" y2="0">'
        f'<stop offset="0%" stop-color="rgba(5,8,13,0.95)"/>'
        f'<stop offset="60%" stop-color="rgba(5,8,13,0.4)"/>'
        f'<stop offset="100%" stop-color="rgba(5,8,13,0)"/>'
        f'</linearGradient>'
    )
    p.append('</defs>')

    # background layers
    p.append(f'<rect x="0" y="0" width="{W}" height="{H}" fill="{VOID}"/>')
    p.append(f'<rect x="0" y="0" width="{W}" height="{H}" fill="url(#grid)"/>')
    p.append(f'<rect x="0" y="0" width="{W}" height="{H}" fill="url(#hub-spot)"/>')
    p.append(f'<rect x="0" y="0" width="{int(W * 0.6)}" height="{H}" fill="url(#left-shade)"/>')

    # ─── Left half: brand block ────────────────────────────────────────
    LEFT_X = 60

    # Eyebrow / kicker
    p.append(
        f'<g opacity="0">'
        f'<text x="{LEFT_X}" y="78" fill="{CYAN_400}" '
        f'font-family="\'IBM Plex Mono\', monospace" font-size="11" '
        f'letter-spacing="0.22em">UNIFIED SECURITY AGENT PLATFORM</text>'
        f'<animate attributeName="opacity" from="0" to="1" begin="0.1s" dur="0.4s" fill="freeze"/>'
        f'</g>'
    )

    # Wordmark
    p.append(
        f'<g opacity="0">'
        f'<text x="{LEFT_X}" y="170" fill="{INK_50}" '
        f'font-family="\'Space Grotesk\', sans-serif" font-weight="700" '
        f'font-size="98" letter-spacing="-0.025em">'
        f'USA<tspan fill="{CYAN_400}">P</tspan></text>'
        f'<animate attributeName="opacity" from="0" to="1" begin="0.0s" dur="0.5s" fill="freeze"/>'
        f'</g>'
    )

    # Tagline (the design system's documented slogan)
    p.append(
        f'<g opacity="0">'
        f'<text x="{LEFT_X}" y="215" fill="{INK_100}" '
        f'font-family="\'Space Grotesk\', sans-serif" font-weight="500" '
        f'font-size="26" letter-spacing="-0.01em">'
        f'Agents reason · Humans approve · MCP executes</text>'
        f'<animate attributeName="opacity" from="0" to="1" begin="0.4s" dur="0.5s" fill="freeze"/>'
        f'</g>'
    )

    # Subhead
    p.append(
        f'<g opacity="0">'
        f'<text x="{LEFT_X}" y="252" fill="{INK_300}" '
        f'font-family="\'IBM Plex Sans\', sans-serif" font-size="15" '
        f'letter-spacing="0.01em">'
        f'Open-source AI cybersecurity skills · runs in any LLM · Apache 2.0</text>'
        f'<animate attributeName="opacity" from="0" to="1" begin="0.6s" dur="0.5s" fill="freeze"/>'
        f'</g>'
    )

    # Stats row
    for i, (n, lbl) in enumerate(STATS):
        sx = LEFT_X + i * 150
        p.append(f'<g opacity="0">')
        p.append(
            f'<text x="{sx}" y="335" fill="{INK_50}" '
            f'font-family="\'Space Grotesk\', sans-serif" font-weight="600" '
            f'font-size="40" letter-spacing="-0.01em">{n}</text>'
        )
        p.append(
            f'<text x="{sx}" y="360" fill="{INK_300}" '
            f'font-family="\'IBM Plex Mono\', monospace" font-size="10" '
            f'letter-spacing="0.14em">{lbl.upper()}</text>'
        )
        p.append(
            f'<animate attributeName="opacity" from="0" to="1" '
            f'begin="{0.8 + i * 0.12:.2f}s" dur="0.4s" fill="freeze"/>'
        )
        p.append('</g>')

    # Framework chip row
    p.append(
        f'<g opacity="0">'
        f'<rect x="{LEFT_X}" y="378" width="170" height="22" rx="11" '
        f'fill="{CYAN_900}" stroke="{CYAN_700}"/>'
        f'<text x="{LEFT_X + 10}" y="393" fill="{CYAN_300}" '
        f'font-family="\'IBM Plex Mono\', monospace" font-size="10" '
        f'letter-spacing="0.12em">MITRE ATT&amp;CK</text>'
        f'<rect x="{LEFT_X + 180}" y="378" width="150" height="22" rx="11" '
        f'fill="{CYAN_900}" stroke="{CYAN_700}"/>'
        f'<text x="{LEFT_X + 190}" y="393" fill="{CYAN_300}" '
        f'font-family="\'IBM Plex Mono\', monospace" font-size="10" '
        f'letter-spacing="0.12em">NIST CSF 2.0</text>'
        f'<rect x="{LEFT_X + 340}" y="378" width="190" height="22" rx="11" '
        f'fill="{CYAN_900}" stroke="{CYAN_700}"/>'
        f'<text x="{LEFT_X + 350}" y="393" fill="{CYAN_300}" '
        f'font-family="\'IBM Plex Mono\', monospace" font-size="10" '
        f'letter-spacing="0.12em">11-FIELD JSON OUTPUT</text>'
        f'<animate attributeName="opacity" from="0" to="1" begin="1.3s" dur="0.4s" fill="freeze"/>'
        f'</g>'
    )

    # ─── Right half: hex constellation ─────────────────────────────────
    # Connective links first so nodes sit on top
    for i, (label, slug, domain, (dx, dy)) in enumerate(NODES):
        nx = HUB_CX + RING_R * dx
        ny = HUB_CY + RING_R * dy
        p.append(
            f'<line x1="{HUB_CX}" y1="{HUB_CY}" x2="{nx:.1f}" y2="{ny:.1f}" '
            f'stroke="url(#link)" stroke-width="1.5" stroke-dasharray="4 5" opacity="0">'
            f'<animate attributeName="opacity" from="0" to="1" '
            f'begin="{0.5 + i * 0.07:.2f}s" dur="0.3s" fill="freeze"/>'
            f'</line>'
        )

    # Peripheral nodes
    for i, (label, slug, domain, (dx, dy)) in enumerate(NODES):
        nx = HUB_CX + RING_R * dx
        ny = HUB_CY + RING_R * dy
        p.append(hex_node(nx, ny, NODE_W, label, slug, DOMAIN_COLORS[domain],
                          hub=False, delay=0.7 + i * 0.08))

    # Central hub LAST so it overlaps clean
    p.append(hex_node(HUB_CX, HUB_CY, HUB_W, "USAP", "", CYAN_400, hub=True, delay=0.2))

    # Hub ambient pulse
    pr = HUB_W / 2 + 12
    p.append(
        f'<circle cx="{HUB_CX}" cy="{HUB_CY}" r="{pr:.0f}" fill="none" '
        f'stroke="{CYAN_400}" stroke-width="1" opacity="0">'
        f'<animate attributeName="opacity" values="0;0.5;0" dur="2.4s" begin="2.0s" repeatCount="indefinite"/>'
        f'<animate attributeName="r" values="{pr:.0f};{pr + 22:.0f};{pr:.0f}" dur="2.4s" begin="2.0s" repeatCount="indefinite"/>'
        f'</circle>'
    )

    p.append('</svg>')
    return "\n".join(p)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--output", default=str(REPO_ROOT / "docs/assets/usap-banner.svg"))
    args = ap.parse_args()
    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(render())
    print(f"wrote {out} ({out.stat().st_size} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
