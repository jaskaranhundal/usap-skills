#!/usr/bin/env python3
"""Generate the USAP social-preview / open-graph card.

Output: docs/assets/usap-social.svg

Dimensions match GitHub's social-preview spec (1280x640). Built from the
Signal Architecture token palette. Designed to convey three things to a
cold visitor scrolling Twitter / LinkedIn / HN:

  1. What it is (wordmark + tagline)
  2. The shape of the artifact (stats row + framework chips)
  3. Visual brand recognition (hub-and-node hex motif, signal cyan glow)

Stdlib only. Deterministic; re-run after stat changes.
"""
from __future__ import annotations
import argparse
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

# Canvas
W = 1280
H = 640

# Palette (design-system tokens)
VOID = "#05080d"
SURFACE_1 = "#0d1117"
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

HUB_CX = 960
HUB_CY = 340
HUB_W = 230
NODE_W = 110
RING_R = 220

NODES = [
    ("ALERT TRIAGE",  "cs-security-analyst",       "security",   ( 0, -1)),
    ("APPSEC",        "cs-appsec-engineer",        "appsec",     ( 0.866, -0.5)),
    ("EXEC BRIEF",    "cs-ciso-advisor",           "executive",  ( 0.866,  0.5)),
    ("INCIDENT",      "cs-incident-responder",     "security",   ( 0,  1)),
    ("DEVSECOPS",     "cs-devsecops-engineer",     "devsecops",  (-0.866,  0.5)),
    ("THREAT HUNT",   "cs-threat-intel-lead",      "security",   (-0.866, -0.5)),
]
DOMAIN_COLORS = {
    "security": CYAN_400, "appsec": VIOLET_400,
    "devsecops": ORANGE_400, "executive": BLUE_400, "governance": GREEN_400,
}


def hex_pts(cx, cy, w):
    h = w * 1.1
    return [
        (cx, cy - h / 2),
        (cx + w / 2, cy - h / 4),
        (cx + w / 2, cy + h / 4),
        (cx, cy + h / 2),
        (cx - w / 2, cy + h / 4),
        (cx - w / 2, cy - h / 4),
    ]


def pts_attr(pts):
    return " ".join(f"{x:.1f},{y:.1f}" for x, y in pts)


def hex_node(cx, cy, w, label, sub, color, hub=False):
    inner_w = w - (3 if hub else 2.5)
    outer = pts_attr(hex_pts(cx, cy, w))
    inner = pts_attr(hex_pts(cx, cy, inner_w))
    fill = "url(#hub-fill)" if hub else SURFACE_1
    glow = "url(#hub-glow)" if hub else "url(#node-glow)"
    out = []
    out.append(f'<polygon points="{outer}" fill="{color}" filter="{glow}"/>')
    out.append(f'<polygon points="{inner}" fill="{fill}"/>')
    if hub:
        out.append(
            f'<text x="{cx}" y="{cy + 22}" fill="{INK_50}" '
            f'font-family="\'Space Grotesk\', sans-serif" font-weight="700" '
            f'font-size="70" text-anchor="middle" letter-spacing="-0.02em">'
            f'USA<tspan fill="{CYAN_400}">P</tspan></text>'
        )
    else:
        out.append(
            f'<text x="{cx}" y="{cy - 2}" fill="{CYAN_300}" '
            f'font-family="\'IBM Plex Mono\', monospace" font-weight="600" '
            f'font-size="11" letter-spacing="0.1em" text-anchor="middle">{label}</text>'
        )
        out.append(
            f'<text x="{cx}" y="{cy + 14}" fill="{INK_300}" '
            f'font-family="\'IBM Plex Mono\', monospace" font-size="8.5" '
            f'letter-spacing="0.04em" text-anchor="middle">{sub}</text>'
        )
    return "\n".join(out)


def render() -> str:
    p = []
    p.append(
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" '
        f'width="{W}" height="{H}" '
        f'font-family="\'IBM Plex Sans\', system-ui, sans-serif">'
    )

    # defs
    p.append('<defs>')
    p.append(
        f'<filter id="hub-glow" x="-50%" y="-50%" width="200%" height="200%">'
        f'<feGaussianBlur in="SourceGraphic" stdDeviation="7"/>'
        f'<feMerge><feMergeNode/><feMergeNode in="SourceGraphic"/></feMerge></filter>'
    )
    p.append(
        f'<filter id="node-glow" x="-50%" y="-50%" width="200%" height="200%">'
        f'<feGaussianBlur in="SourceGraphic" stdDeviation="2"/>'
        f'<feMerge><feMergeNode/><feMergeNode in="SourceGraphic"/></feMerge></filter>'
    )
    p.append(
        f'<radialGradient id="hub-fill" cx="50%" cy="45%" r="65%">'
        f'<stop offset="0%" stop-color="{CYAN_900}"/>'
        f'<stop offset="100%" stop-color="{VOID}"/></radialGradient>'
    )
    p.append(
        f'<radialGradient id="bg-spot" cx="{HUB_CX}" cy="{HUB_CY}" r="380" '
        f'gradientUnits="userSpaceOnUse">'
        f'<stop offset="0%" stop-color="rgba(41,211,240,0.20)"/>'
        f'<stop offset="100%" stop-color="rgba(41,211,240,0)"/></radialGradient>'
    )
    p.append(
        f'<pattern id="grid" x="0" y="0" width="32" height="32" patternUnits="userSpaceOnUse">'
        f'<path d="M 32 0 L 0 0 0 32" fill="none" stroke="rgba(41,211,240,0.05)" stroke-width="1"/></pattern>'
    )
    p.append(
        f'<linearGradient id="link" x1="0" y1="0" x2="1" y2="0">'
        f'<stop offset="0%" stop-color="rgba(41,211,240,0.06)"/>'
        f'<stop offset="50%" stop-color="rgba(41,211,240,0.5)"/>'
        f'<stop offset="100%" stop-color="rgba(41,211,240,0.06)"/></linearGradient>'
    )
    p.append(
        f'<linearGradient id="left-shade" x1="0" y1="0" x2="1" y2="0">'
        f'<stop offset="0%" stop-color="rgba(5,8,13,0.95)"/>'
        f'<stop offset="55%" stop-color="rgba(5,8,13,0.4)"/>'
        f'<stop offset="100%" stop-color="rgba(5,8,13,0)"/></linearGradient>'
    )
    p.append('</defs>')

    # Background layers
    p.append(f'<rect x="0" y="0" width="{W}" height="{H}" fill="{VOID}"/>')
    p.append(f'<rect x="0" y="0" width="{W}" height="{H}" fill="url(#grid)"/>')
    p.append(f'<rect x="0" y="0" width="{W}" height="{H}" fill="url(#bg-spot)"/>')
    p.append(f'<rect x="0" y="0" width="{int(W * 0.6)}" height="{H}" fill="url(#left-shade)"/>')

    # Left text block
    LX = 80
    p.append(
        f'<text x="{LX}" y="115" fill="{CYAN_400}" font-family="\'IBM Plex Mono\', monospace" '
        f'font-size="13" letter-spacing="0.24em">UNIFIED SECURITY AGENT PLATFORM</text>'
    )
    p.append(
        f'<text x="{LX}" y="240" fill="{INK_50}" font-family="\'Space Grotesk\', sans-serif" '
        f'font-weight="700" font-size="138" letter-spacing="-0.025em">'
        f'USA<tspan fill="{CYAN_400}">P</tspan></text>'
    )
    p.append(
        f'<text x="{LX}" y="295" fill="{INK_100}" font-family="\'Space Grotesk\', sans-serif" '
        f'font-weight="500" font-size="30" letter-spacing="-0.01em">'
        f'Agents reason · Humans approve · MCP executes</text>'
    )
    p.append(
        f'<text x="{LX}" y="335" fill="{INK_300}" font-family="\'IBM Plex Sans\', sans-serif" '
        f'font-size="18" letter-spacing="0.01em">'
        f'Open-source AI cybersecurity skills · runs in any LLM · Apache 2.0</text>'
    )

    # Stat row
    stats = [("79", "Skills"), ("12", "cs-* agents"), ("12", "Domains"),
             ("11", "Field contract")]
    for i, (n, lbl) in enumerate(stats):
        sx = LX + i * 160
        p.append(
            f'<text x="{sx}" y="445" fill="{INK_50}" '
            f'font-family="\'Space Grotesk\', sans-serif" font-weight="600" '
            f'font-size="52" letter-spacing="-0.01em">{n}</text>'
        )
        p.append(
            f'<text x="{sx}" y="478" fill="{INK_300}" '
            f'font-family="\'IBM Plex Mono\', monospace" font-size="11" '
            f'letter-spacing="0.14em">{lbl.upper()}</text>'
        )

    # Framework chip row
    chips = [("MITRE ATT&CK", 200), ("NIST CSF 2.0", 180), ("OWASP TOP 10", 180),
             ("APACHE 2.0", 160)]
    cx = LX
    for label, cw in chips:
        p.append(
            f'<rect x="{cx}" y="510" width="{cw}" height="28" rx="14" '
            f'fill="{CYAN_900}" stroke="{CYAN_700}"/>'
            f'<text x="{cx + 14}" y="529" fill="{CYAN_300}" '
            f'font-family="\'IBM Plex Mono\', monospace" font-size="11" '
            f'letter-spacing="0.12em">{label}</text>'
        )
        cx += cw + 12

    # GitHub URL footer
    p.append(
        f'<text x="{LX}" y="595" fill="{INK_300}" '
        f'font-family="\'IBM Plex Mono\', monospace" font-size="14" letter-spacing="0.04em">'
        f'github.com/jaskaranhundal/usap-skills</text>'
    )

    # Right side: constellation
    # Connective links first
    for label, slug, domain, (dx, dy) in NODES:
        nx = HUB_CX + RING_R * dx
        ny = HUB_CY + RING_R * dy
        p.append(
            f'<line x1="{HUB_CX}" y1="{HUB_CY}" x2="{nx:.1f}" y2="{ny:.1f}" '
            f'stroke="url(#link)" stroke-width="1.5" stroke-dasharray="4 5"/>'
        )
    for label, slug, domain, (dx, dy) in NODES:
        nx = HUB_CX + RING_R * dx
        ny = HUB_CY + RING_R * dy
        p.append(hex_node(nx, ny, NODE_W, label, slug, DOMAIN_COLORS[domain]))
    # Hub last
    p.append(hex_node(HUB_CX, HUB_CY, HUB_W, "USAP", "", CYAN_400, hub=True))

    p.append('</svg>')
    return "\n".join(p)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--output", default=str(REPO_ROOT / "docs/assets/usap-social.svg"))
    args = ap.parse_args()
    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(render())
    print(f"wrote {out} ({out.stat().st_size} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
