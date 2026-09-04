#!/usr/bin/env python3
"""Repo-local entry point for the USAP persona gate.

The implementation lives in plugins/usap/hooks/usap_gate.py because the hooks
must ship inside the plugin. This shim keeps a tools/ command for operators
and CI working from a checkout:

    python3 tools/usap_router.py classify "harden the runner against direct push"
    python3 tools/usap_router.py check-skill secrets-exposure
    python3 tools/usap_router.py record --session-id <id> --persona usap-devsecops \
        --pass DR --residual-risk medium --summary "hooks design reviewed"
"""
from __future__ import annotations

import runpy
import sys
from pathlib import Path

GATE = Path(__file__).resolve().parent.parent / "plugins" / "usap" / "hooks" / "usap_gate.py"

if __name__ == "__main__":
    sys.argv[0] = str(GATE)
    runpy.run_path(str(GATE), run_name="__main__")
