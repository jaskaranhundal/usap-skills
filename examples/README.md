# USAP in action — reproducible examples

Every output below is **real** and **reproducible**: run the command yourself and you get the same result. This is what separates USAP from a prompt library — the numbers are computed, the evidence is fetched, and the accuracy is measured against ground truth USAP didn't write.

No install needed for these — just `git clone` and Python 3.9+ (stdlib only, zero dependencies).

---

## 1. Connector-agnostic evidence — one agent, any environment

USAP agents declare *logical* capabilities (`mcp:siem:search`), and the registry resolves them to whatever the operator actually connected. The same `cs-security-analyst` works against Splunk, Elastic, or Sentinel with no edit — and degrades gracefully when a connector is absent.

```console
$ python3 tools/mcp_router.py --resolve mcp:siem:search
siem.search resolves to: mcp__splunk__search

$ python3 tools/mcp_router.py --resolve mcp:cloud:list_findings
cloud.list_findings resolves to: None      # no cloud connector — the agent marks that axis UNKNOWN, never assumes
```

Why it matters: USAP is portable to *your* stack instead of hard-wired to one vendor's tooling.

---

## 2. The evidence gate — no verdict without a resolvable source

Every verdict USAP emits must cite evidence that resolves to a real artifact. A prose source ("the SIEM showed it") is **rejected at the contract boundary**. This is what makes USAP's conclusions verifiable instead of merely plausible.

```console
$ # a verdict citing prose evidence
prose source           -> REJECTED: evidence gate: no resolvable evidence source found …

$ # a verdict citing a live MCP tool-call id
mcp: resolvable source -> ACCEPTED
```

The four accepted forms: `mcp:<logical>:<tool>:<call_id>` (live fetch), `https://` (canonical external), `s3://` (artifact store), `local://<repo-path>` (in-repo standard). See [`standards/output-contract.md`](../standards/output-contract.md#resolvable-evidence-gate).

---

## 3. Reproducible scoring — computed, never narrated

If a number can be computed from a canonical source, USAP computes it. If it can't, USAP says *qualitative* — it never fabricates.

```console
$ python3 shared/scripts/epss_scorer.py --cve CVE-2021-44228        # real EPSS from the FIRST feed
CVE-2021-44228: EPSS 0.99999  (percentile 100.00%)

$ python3 shared/scripts/cvss_scorer.py --vector "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:C/C:H/I:H/A:H"
Base Score : 10.0 — Critical

$ python3 shared/scripts/confidence_rubric.py --secondary 2         # confidence from a written rubric
confidence: 0.84
rationale : 2 agreeing source(s) (best tier=secondary, w=0.70); corroboration lift => confidence 0.84.
```

The output contract **rejects** any payload whose claimed `cvss_score` disagrees with the vector it cites. See [`standards/confidence-rubric.md`](../standards/confidence-rubric.md).

---

## 4. Independent evaluation — graded on cases USAP didn't write

USAP's self-grading commands compare its output to its own answer key (circular). The held-out corpus fixes that: 12 hand-labeled cases from public incidents (Log4Shell, xz backdoor, Capital One, Okta, MOVEit, Midnight Blizzard) plus 5 benign false-positive traps that make precision and FPR honest.

```console
$ python3 tests/holdout_runner.py --responder synthetic \
      --predictions tests/holdout/example_predictions.json
USAP held-out evaluation — 12 cases, 12 graded
  confusion    TP=6 FP=1 FN=1 TN=4
  precision    0.8571
  recall       0.8571
  F1           0.8571
  FPR          0.2
  MTTD (min)   17.5
```

*(The run above scores a synthetic prediction batch that exercises the metrics engine. A live `--responder llm` run drives the personas against the corpus to produce USAP's real per-release score — see [`tests/holdout/README.md`](../tests/holdout/README.md).)*

---

## 5. The full 11-field output contract

Every skill emits the same typed JSON. Here is the real output of the `vuln-scan` skill (confidence computed from the rubric, evidence citing the fetching MCP call):

```console
$ python3 tools/output_contract.py appsec-devsecops/vuln-scan/expected_outputs/sample_output.json
PASS appsec-devsecops/vuln-scan/expected_outputs/sample_output.json
```

```jsonc
{
  "agent_slug": "vuln-scan",
  "intent_type": "detect",
  "action": "Hand off to finding-triage — 4 mapped findings, 1 unmapped, top severity high.",
  "confidence": 0.84,                                    // computed via confidence-rubric.md
  "severity": "high",
  "key_findings": ["VF-001 hardcoded-credential at src/config.py:14 — mapped to TM-001 …", "…"],
  "evidence_references": [
    {"source": "mcp:code:get_pr_diff:call_a1b2c3", "ref": "src/config.py:14", "quote": "PASSWORD = \"changeme-prod\""}
  ],                                                     // resolvable source — passes the evidence gate
  "next_agents": ["finding-triage"],
  "human_approval_required": false,
  "timestamp_utc": "2026-06-20T10:30:00Z"
  // + optional: mitre_ttps, cvss_score, epss_score, affected_assets, …
}
```

Full schema: [`standards/output-contract.md`](../standards/output-contract.md).

---

## Reproduce everything

```bash
git clone https://github.com/jaskaranhundal/usap-skills && cd usap-skills
python3 tools/mcp_router.py --resolve mcp:siem:search
python3 shared/scripts/epss_scorer.py --cve CVE-2021-44228
python3 tests/holdout_runner.py --responder synthetic --predictions tests/holdout/example_predictions.json
python3 tools/mcp_server_test.py        # 32-assertion end-to-end smoke test
```

That is USAP: agents reason, humans approve, MCP executes — and every claim is traceable, every number reproducible, every accuracy measured.
