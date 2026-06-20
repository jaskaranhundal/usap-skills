# owasp-top10-classifier

Maps a webapp finding description to OWASP Top 10 2025 categories with confidence. Output feeds `webapp-risk-triage` (re-routing) and `appsec-devsecops/sast-dast-coordinator` (deduplication).

```bash
python3 scripts/owasp-top10-classifier_tool.py --output json
python3 scripts/owasp-top10-classifier_tool.py --input finding.json --output json
python3 scripts/owasp-top10-classifier_tool.py --output human
```

Full taxonomy table + scoring rubric in [`SKILL.md`](SKILL.md).
