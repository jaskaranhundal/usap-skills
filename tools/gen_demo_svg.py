#!/usr/bin/env python3
"""Generate an animated SVG of the cs-appsec-engineer -> vuln-scan -> finding-triage demo.

Output renders directly in GitHub README via <img src="docs/assets/usap-alex-demo.svg">.
Self-contained SVG (no external CSS/JS, no fonts beyond the SVG-safe stack).

Every byte of the JSON payload shown is byte-identical to
appsec-devsecops/vuln-scan/expected_outputs/sample_output.json.

Stdlib only.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import List, Tuple

REPO_ROOT = Path(__file__).resolve().parent.parent

WIDTH = 920
HEIGHT = 980
LINE_HEIGHT = 16
LEFT_PAD = 14
TOP_PAD = 38
CHAR_WIDTH = 7.5
PER_LINE_DELAY = 0.16

BG = "#0d1117"
HEADER_BG = "#161b22"
HEADER_FG = "#c9d1d9"
PROMPT = "#7ee787"
USER = "#79c0ff"
AGENT = "#d2a8ff"
KEY = "#79c0ff"
STRING = "#a5d6ff"
NUMBER = "#ffa657"
PUNCT = "#c9d1d9"
COMMENT = "#8b949e"
BODY = "#e6edf3"


def esc(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


def segments(line: str) -> List[Tuple[str, str]]:
    if line.startswith("[") and "]" in line:
        end = line.index("]")
        color = line[1:end]
        rest = line[end + 1:]
        return [(color, rest)]

    stripped = line.lstrip()
    indent = line[: len(line) - len(stripped)]
    if not (stripped.startswith("{") or stripped.startswith('"') or stripped.startswith("}")
            or stripped.startswith("[") or stripped.startswith("]") or stripped.startswith(",")):
        return [(BODY, line)]

    out: List[Tuple[str, str]] = []
    if indent:
        out.append((BODY, indent))
    i = 0
    s = stripped
    key_seen = False
    while i < len(s):
        c = s[i]
        if c == '"':
            j = i + 1
            while j < len(s):
                if s[j] == '"' and s[j - 1] != "\\":
                    break
                j += 1
            literal = s[i:j + 1]
            k = j + 1
            while k < len(s) and s[k] in " \t":
                k += 1
            if k < len(s) and s[k] == ":" and not key_seen:
                out.append((KEY, literal))
                key_seen = True
            else:
                out.append((STRING, literal))
            i = j + 1
        elif c.isdigit() or (c == "-" and i + 1 < len(s) and s[i + 1].isdigit()):
            j = i + 1
            while j < len(s) and s[j] in "0123456789.eE+-":
                j += 1
            out.append((NUMBER, s[i:j]))
            i = j
        elif s[i:i + 5] == "false":
            out.append((NUMBER, "false")); i += 5
        elif s[i:i + 4] == "true":
            out.append((NUMBER, "true")); i += 4
        elif s[i:i + 4] == "null":
            out.append((NUMBER, "null")); i += 4
        elif c == ":":
            out.append((PUNCT, ":"))
            i += 1
        elif c in "{}[],":
            out.append((PUNCT, c))
            i += 1
            if c == ",":
                key_seen = False
        else:
            out.append((BODY, c))
            i += 1
    return out


def build_lines() -> List[str]:
    sample_path = REPO_ROOT / "appsec-devsecops/vuln-scan/expected_outputs/sample_output.json"
    payload = json.loads(sample_path.read_text())
    pretty = json.dumps(payload, indent=2).splitlines()

    out: List[str] = []
    out.append("[#8b949e]# USAP demo: cs-appsec-engineer -> vuln-scan -> finding-triage")
    out.append("[#8b949e]# JSON below is byte-identical to expected_outputs/sample_output.json")
    out.append("")
    out.append("[#7ee787]you  [#e6edf3]Scan examples/SimpleStoreAPI and route any high findings to triage.")
    out.append("")
    out.append("[#d2a8ff]cs-appsec-engineer  [#e6edf3]Running vuln-scan against threat model TM-001..TM-005.")
    out.append("")
    out.append("[#7ee787]$ python3 appsec-devsecops/vuln-scan/scripts/vuln-scan_tool.py \\")
    out.append("[#7ee787]    --input examples/SimpleStoreAPI/scan-context.json --output json")
    out.append("")
    out.extend(pretty)
    out.append("")
    out.append("[#d2a8ff]cs-appsec-engineer  [#e6edf3]severity=high  next_agents=[finding-triage]  handing off.")
    return out


def render(lines: List[str]) -> str:
    parts: List[str] = []
    parts.append(
        '<svg xmlns="http://www.w3.org/2000/svg" width="' + str(WIDTH) + '" height="' + str(HEIGHT) + '" '
        'viewBox="0 0 ' + str(WIDTH) + ' ' + str(HEIGHT) + '" '
        'font-family="ui-monospace, SFMono-Regular, Menlo, Monaco, \'Cascadia Mono\', \'Roboto Mono\', '
        'Consolas, \'Courier New\', monospace" font-size="13">'
    )
    parts.append('<rect x="0" y="0" width="' + str(WIDTH) + '" height="' + str(HEIGHT) + '" rx="8" ry="8" fill="' + BG + '"/>')
    parts.append('<rect x="0" y="0" width="' + str(WIDTH) + '" height="28" fill="' + HEADER_BG + '"/>')
    parts.append('<circle cx="16" cy="14" r="6" fill="#ff5f57"/>')
    parts.append('<circle cx="34" cy="14" r="6" fill="#febc2e"/>')
    parts.append('<circle cx="52" cy="14" r="6" fill="#28c840"/>')
    parts.append(
        '<text x="' + str(WIDTH // 2) + '" y="18" fill="' + HEADER_FG + '" font-size="12" '
        'text-anchor="middle">usap-alex demo - cs-appsec-engineer</text>'
    )

    for idx, raw_line in enumerate(lines):
        y = TOP_PAD + idx * LINE_HEIGHT
        if y > HEIGHT - 10:
            break
        begin = idx * PER_LINE_DELAY
        x = LEFT_PAD
        spans = segments(raw_line) if raw_line else [(BODY, "")]
        parts.append('<g opacity="0">')
        for color, text in spans:
            if not text:
                continue
            parts.append(
                '<text x="' + ("%.1f" % x) + '" y="' + str(y) + '" fill="' + color + '" '
                'xml:space="preserve">' + esc(text) + '</text>'
            )
            x += len(text) * CHAR_WIDTH
        parts.append(
            '<animate attributeName="opacity" from="0" to="1" begin="' + ("%.2f" % begin) + 's" '
            'dur="0.18s" fill="freeze"/></g>'
        )

    parts.append('</svg>')
    return "\n".join(parts)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--output", default=str(REPO_ROOT / "docs/assets/usap-alex-demo.svg"))
    args = ap.parse_args()
    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    lines = build_lines()
    svg = render(lines)
    out_path.write_text(svg)
    size_kb = out_path.stat().st_size / 1024
    print("wrote", out_path, "(", "%.1f" % size_kb, "KB,", len(lines), "lines)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
