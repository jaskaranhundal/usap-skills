#!/usr/bin/env python3
"""USAP EPSS scorer — reproducible exploit-probability lookup.

EPSS (Exploit Prediction Scoring System) is published by FIRST.org. This tool
fetches the real EPSS probability + percentile for a CVE from the canonical
feed instead of letting a model narrate a number. If the feed is unreachable
or the CVE is unknown, it returns a *qualitative* result — it never fabricates
a score.

Design principles (from the USAP 7.5->9.5 thesis):
  * Every number reproducible: the score comes from api.first.org, not the LLM.
  * Never fabricate: unknown/unreachable -> epss=None + a note, exit 0.
  * Cache to survive rate limits + offline runs: ~/.usap/cache/epss/<cve>.json
    with a 24h TTL (EPSS is republished daily).

Stdlib only (urllib). No external dependencies.

Usage::

    python3 shared/scripts/epss_scorer.py --cve CVE-2021-44228
    python3 shared/scripts/epss_scorer.py --text "impacted by CVE-2021-44228 and CVE-2024-3094"
    echo '{"cves": ["CVE-2021-44228"]}' | python3 shared/scripts/epss_scorer.py --output json

Returns, per CVE::

    {"cve": "CVE-2021-44228", "epss": 0.97565, "percentile": 0.99998,
     "fetched_at_utc": "2026-07-03T09:10:00Z", "source": "https://api.first.org/data/v1/epss?cve=CVE-2021-44228"}

or, when the score cannot be resolved::

    {"cve": "CVE-2021-44228", "epss": null, "percentile": null,
     "qualitative": true, "note": "EPSS feed unreachable — score not computed"}
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

FEED = "https://api.first.org/data/v1/epss"
CVE_RE = re.compile(r"CVE-\d{4}-\d{4,7}", re.IGNORECASE)
CACHE_TTL_SECONDS = 24 * 60 * 60  # EPSS is republished daily


def _now_utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _cache_dir() -> Path:
    d = Path(os.environ.get("USAP_CACHE_DIR") or (Path.home() / ".usap" / "cache")) / "epss"
    d.mkdir(parents=True, exist_ok=True)
    return d


def extract_cves(text: str) -> list[str]:
    """Return de-duplicated, upper-cased CVE IDs found in arbitrary text."""
    seen: dict[str, None] = {}
    for m in CVE_RE.findall(text or ""):
        seen[m.upper()] = None
    return list(seen.keys())


def _read_cache(cve: str) -> dict | None:
    p = _cache_dir() / f"{cve}.json"
    if not p.is_file():
        return None
    try:
        age = datetime.now(timezone.utc).timestamp() - p.stat().st_mtime
        if age > CACHE_TTL_SECONDS:
            return None
        return json.loads(p.read_text())
    except Exception:
        return None


def _write_cache(cve: str, payload: dict) -> None:
    try:
        (_cache_dir() / f"{cve}.json").write_text(json.dumps(payload))
    except Exception:
        pass  # cache is best-effort; a write failure must never break scoring


def _qualitative(cve: str, note: str) -> dict:
    return {
        "cve": cve,
        "epss": None,
        "percentile": None,
        "qualitative": True,
        "note": note,
    }


def score_cve(cve: str, *, use_cache: bool = True, timeout: float = 10.0) -> dict:
    """Fetch the EPSS score for one CVE from the FIRST feed.

    Returns a dict with a numeric ``epss``/``percentile`` on success, or a
    qualitative dict (``epss: None``) when the feed is unreachable or the CVE
    is unknown. Never raises; never fabricates a number.
    """
    cve = (cve or "").strip().upper()
    if not CVE_RE.fullmatch(cve):
        return _qualitative(cve, "not a valid CVE identifier")

    if use_cache:
        cached = _read_cache(cve)
        if cached is not None:
            return cached

    url = f"{FEED}?cve={cve}"
    req = urllib.request.Request(url, headers={"User-Agent": "usap-epss-scorer/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = json.loads(resp.read().decode("utf-8", "replace"))
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, ValueError) as exc:
        return _qualitative(cve, f"EPSS feed unreachable — score not computed ({type(exc).__name__})")

    data = body.get("data") or []
    if not data:
        result = _qualitative(cve, "CVE not present in EPSS feed (too new, rejected, or reserved)")
        _write_cache(cve, result)
        return result

    row = data[0]
    try:
        result = {
            "cve": cve,
            "epss": float(row["epss"]),
            "percentile": float(row["percentile"]),
            "fetched_at_utc": _now_utc(),
            "source": url,
        }
    except (KeyError, ValueError, TypeError):
        return _qualitative(cve, "EPSS feed returned an unparseable row")
    _write_cache(cve, result)
    return result


def score_many(cves: list[str], *, use_cache: bool = True) -> list[dict]:
    return [score_cve(c, use_cache=use_cache) for c in cves]


def main() -> int:
    ap = argparse.ArgumentParser(description="Fetch reproducible EPSS scores from the FIRST feed.")
    g = ap.add_mutually_exclusive_group()
    g.add_argument("--cve", help="A single CVE id, e.g. CVE-2021-44228")
    g.add_argument("--text", help="Free text; all CVE ids in it are scored")
    g.add_argument("--vector", help="Alias for --text (extracts CVE ids from the string)")
    ap.add_argument("--no-cache", action="store_true", help="Bypass the local 24h cache")
    ap.add_argument("--output", choices=["json", "text"], default="text")
    args = ap.parse_args()

    if args.cve:
        cves = [args.cve]
    elif args.text or args.vector:
        cves = extract_cves(args.text or args.vector)
    elif not sys.stdin.isatty():
        try:
            payload = json.loads(sys.stdin.read() or "{}")
            cves = payload.get("cves") or extract_cves(json.dumps(payload))
        except json.JSONDecodeError:
            cves = []
    else:
        ap.error("provide --cve, --text, or JSON on stdin")

    if not cves:
        print("No CVE identifiers found.", file=sys.stderr)
        return 1

    results = score_many(cves, use_cache=not args.no_cache)
    if args.output == "json":
        print(json.dumps(results, indent=2))
        return 0

    for r in results:
        if r.get("epss") is None:
            print(f"{r['cve']}: qualitative — {r.get('note')}")
        else:
            pct = r["percentile"] * 100
            print(f"{r['cve']}: EPSS {r['epss']:.5f}  (percentile {pct:.2f}%)  [{r['source']}]")
    return 0


if __name__ == "__main__":
    sys.exit(main())
