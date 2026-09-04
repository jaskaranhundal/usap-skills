#!/usr/bin/env python3
"""Run every implemented tool against its recorded fixture and validate the payload.

tests/fixtures/manifest.json lists {tool, input, expect_exit}. For each entry
this runner executes the tool with --input <fixture> --output json, checks the
exit code, and validates the emitted payload with tools/output_contract.py
(full evidence gate). A green run means the tool produced a real, resolvable
verdict from a real input; it is the proof that a skill is implemented rather
than a declared stub.

    python3 tests/run_fixtures.py            # all entries
    python3 tests/run_fixtures.py --only secrets-exposure

Exit 1 on any failure. Stdlib only.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
MANIFEST = REPO / "tests" / "fixtures" / "manifest.json"
CONTRACT = REPO / "tools" / "output_contract.py"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", help="substring filter on the tool path")
    args = ap.parse_args()

    entries = json.loads(MANIFEST.read_text(encoding="utf-8"))["fixtures"]
    if args.only:
        entries = [e for e in entries if args.only in e["tool"]]
    failures = 0
    for e in entries:
        tool, inp, want = REPO / e["tool"], REPO / e["input"], int(e["expect_exit"])
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as fh:
            out_path = Path(fh.name)
        r = subprocess.run([sys.executable, str(tool), "--input", str(inp), "--output", "json"],
                           capture_output=True, text=True, timeout=120)
        out_path.write_text(r.stdout, encoding="utf-8")
        label = e["tool"]
        if r.returncode != want:
            print(f"  FAIL {label}: exit {r.returncode}, expected {want}\n{r.stderr[-400:]}")
            failures += 1
            continue
        try:
            payload = json.loads(r.stdout)
        except json.JSONDecodeError as exc:
            print(f"  FAIL {label}: stdout is not JSON ({exc})")
            failures += 1
            continue
        if payload.get("status") == "not_implemented":
            print(f"  FAIL {label}: still a declared stub")
            failures += 1
            continue
        c = subprocess.run([sys.executable, str(CONTRACT), str(out_path)], capture_output=True, text=True)
        if c.returncode != 0:
            print(f"  FAIL {label}: output contract\n{c.stdout[-600:]}{c.stderr[-200:]}")
            failures += 1
            continue
        print(f"  PASS {label}: exit {r.returncode}, severity {payload.get('severity')}, confidence {payload.get('confidence')}")
    print(f"fixtures={len(entries)} failures={failures}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
