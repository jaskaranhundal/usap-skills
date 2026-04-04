#!/usr/bin/env python3
"""
usap_preview_server.py — Generates USAP_LITE.md and serves it as a
web preview on http://localhost:8080. Used by .claude/launch.json.
"""

import http.server
import socketserver
import sys
import threading
from pathlib import Path

# Resolve repo root (2 levels up from shared/scripts/)
REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "shared" / "scripts"))

from bundle_usap import cmd_bundle  # noqa: E402

import argparse

PORT = 8080

HTML_TEMPLATE = """\
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>USAP Lite — System Prompt Preview</title>
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
          background: #0f1117; color: #e2e8f0; min-height: 100vh; }}
  header {{ background: #1a1f2e; border-bottom: 1px solid #2d3748;
            padding: 16px 32px; display: flex; align-items: center; gap: 16px; }}
  header h1 {{ font-size: 18px; font-weight: 700; color: #63b3ed; }}
  header .badge {{ background: #2d3748; border-radius: 9999px;
                   padding: 4px 12px; font-size: 12px; color: #a0aec0; }}
  .copy-btn {{ margin-left: auto; background: #3182ce; color: white; border: none;
               border-radius: 6px; padding: 8px 20px; cursor: pointer;
               font-size: 14px; font-weight: 600; }}
  .copy-btn:hover {{ background: #2b6cb0; }}
  .copy-btn.copied {{ background: #38a169; }}
  .container {{ max-width: 960px; margin: 32px auto; padding: 0 24px; }}
  .meta {{ background: #1a1f2e; border: 1px solid #2d3748; border-radius: 8px;
           padding: 16px 20px; margin-bottom: 24px;
           display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; }}
  .meta-item {{ text-align: center; }}
  .meta-item .val {{ font-size: 28px; font-weight: 700; color: #63b3ed; }}
  .meta-item .lbl {{ font-size: 12px; color: #718096; margin-top: 2px; }}
  .instructions {{ background: #1a1f2e; border: 1px solid #2d3748; border-radius: 8px;
                   padding: 16px 20px; margin-bottom: 24px; }}
  .instructions h2 {{ font-size: 14px; font-weight: 600; color: #a0aec0;
                      text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 12px; }}
  .instructions ol {{ padding-left: 20px; color: #cbd5e0; font-size: 14px; line-height: 1.8; }}
  .instructions code {{ background: #2d3748; border-radius: 4px;
                        padding: 1px 6px; font-family: monospace; font-size: 13px; }}
  pre {{ background: #1a1f2e; border: 1px solid #2d3748; border-radius: 8px;
         padding: 24px; overflow-x: auto; font-family: "SF Mono", "Fira Code", monospace;
         font-size: 13px; line-height: 1.7; color: #e2e8f0; white-space: pre-wrap;
         word-break: break-word; }}
  footer {{ text-align: center; color: #4a5568; font-size: 12px;
            padding: 24px; margin-top: 16px; }}
</style>
</head>
<body>
<header>
  <h1>USAP — Lite System Prompt</h1>
  <span class="badge">kit: LITE</span>
  <span class="badge">model: any LLM</span>
  <button class="copy-btn" onclick="copyPrompt(this)">Copy Prompt</button>
</header>

<div class="container">
  <div class="meta">
    <div class="meta-item">
      <div class="val">{char_count}</div>
      <div class="lbl">Characters</div>
    </div>
    <div class="meta-item">
      <div class="val">{token_estimate}</div>
      <div class="lbl">Est. Tokens</div>
    </div>
    <div class="meta-item">
      <div class="val">{size_kb}</div>
      <div class="lbl">KB</div>
    </div>
  </div>

  <div class="instructions">
    <h2>How to use this prompt</h2>
    <ol>
      <li>Click <strong>Copy Prompt</strong> above</li>
      <li>Open <code>AnythingLLM</code> → New Workspace → paste as system prompt</li>
      <li>Or open <code>ChatGPT / Claude / Gemini</code> → paste as first message</li>
      <li>Ask Alex any security question — or send a scenario JSON to run AT/CA workflows</li>
    </ol>
  </div>

  <pre id="prompt-content">{content}</pre>
</div>

<footer>USAP — Unified Security Agent Platform &nbsp;|&nbsp; usap-skills &nbsp;|&nbsp; MIT License</footer>

<script>
function copyPrompt(btn) {{
  const text = document.getElementById('prompt-content').textContent;
  navigator.clipboard.writeText(text).then(() => {{
    btn.textContent = 'Copied!';
    btn.classList.add('copied');
    setTimeout(() => {{ btn.textContent = 'Copy Prompt'; btn.classList.remove('copied'); }}, 2000);
  }});
}}
</script>
</body>
</html>
"""


def build_bundle() -> str:
    """Generate USAP_LITE.md and return its content."""
    ns = argparse.Namespace(mode="lite", output=None)
    cmd_bundle(ns)
    lite_path = REPO_ROOT / "dist" / "USAP_LITE.md"
    return lite_path.read_text(encoding="utf-8")


class USAPHandler(http.server.BaseHTTPRequestHandler):
    content: str = ""

    def do_GET(self):
        if self.path in ("/", "/index.html"):
            body = HTML_TEMPLATE.format(
                content=self.content.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"),
                char_count=f"{len(self.content):,}",
                token_estimate=f"{len(self.content) // 4:,}",
                size_kb=f"{len(self.content.encode()) / 1024:.1f}",
            ).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        elif self.path == "/raw":
            body = self.content.encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, fmt, *args):
        pass  # suppress request logs


def main():
    print("Generating USAP_LITE bundle...", flush=True)
    try:
        content = build_bundle()
        print(f"Bundle ready — {len(content):,} chars ({len(content.encode()) / 1024:.1f} KB)", flush=True)
    except Exception as e:
        print(f"Bundle generation failed: {e}", file=sys.stderr, flush=True)
        content = f"# Bundle generation failed\n\nError: {e}\n"

    USAPHandler.content = content

    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("", PORT), USAPHandler) as httpd:
        print(f"USAP Preview Server running at http://localhost:{PORT}", flush=True)
        print(f"Raw prompt at http://localhost:{PORT}/raw", flush=True)
        httpd.serve_forever()


if __name__ == "__main__":
    main()
