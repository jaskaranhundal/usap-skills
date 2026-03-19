#!/usr/bin/env python3
"""USAP Gemini Chat — runs Alex (cs-security-analyst) as a Gemini system prompt."""

import argparse
import os
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

KIT_MAP = {
    "lite":  REPO_ROOT / "dist" / "USAP_LITE.md",
    "pro":   REPO_ROOT / "dist" / "USAP_PRO.md",
    "full":  REPO_ROOT / "dist" / "USAP_BUNDLE.md",
}

DEFAULT_MODEL = "gemini-2.0-flash"


def load_system_prompt(kit: str, custom_path: str | None) -> str:
    if custom_path:
        path = Path(custom_path)
    else:
        path = KIT_MAP[kit]
    if not path.exists():
        print(f"Error: kit file not found: {path}", file=sys.stderr)
        print("Run: python3 shared/scripts/bundle_usap.py bundle --mode lite", file=sys.stderr)
        sys.exit(1)
    return path.read_text(encoding="utf-8")


def run_chat(api_key: str, system_prompt: str, model_name: str) -> None:
    try:
        import google.generativeai as genai
    except ImportError:
        print("Error: google-generativeai not installed.", file=sys.stderr)
        print("Run: pip install google-generativeai", file=sys.stderr)
        sys.exit(1)

    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(
        model_name=model_name,
        system_instruction=system_prompt,
    )
    chat = model.start_chat()

    print(f"USAP Alex — Gemini ({model_name})")
    print("Type your message. Ctrl+C or 'exit' to quit.\n")

    while True:
        try:
            user_input = input("You: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nExiting.")
            break
        if not user_input or user_input.lower() in ("exit", "quit"):
            break
        response = chat.send_message(user_input)
        print(f"\nAlex: {response.text}\n")


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="gemini_chat.py",
        description="Start an interactive USAP session with Alex on Google Gemini.",
    )
    parser.add_argument(
        "--kit", choices=["lite", "pro", "full"], default="lite",
        help="USAP kit to load as system prompt (default: lite)",
    )
    parser.add_argument(
        "--system-prompt", metavar="PATH",
        help="Override: load system prompt from a custom file path",
    )
    parser.add_argument(
        "--model", default=DEFAULT_MODEL, metavar="MODEL",
        help=f"Gemini model ID (default: {DEFAULT_MODEL})",
    )
    parser.add_argument(
        "--api-key", metavar="KEY",
        help="Gemini API key (default: reads GEMINI_API_KEY env var)",
    )
    args = parser.parse_args()

    api_key = args.api_key or os.environ.get("GEMINI_API_KEY", "")
    if not api_key:
        print("Error: Gemini API key required.", file=sys.stderr)
        print("Set GEMINI_API_KEY env var or pass --api-key KEY", file=sys.stderr)
        sys.exit(1)

    system_prompt = load_system_prompt(args.kit, args.system_prompt)
    run_chat(api_key, system_prompt, args.model)


if __name__ == "__main__":
    main()
