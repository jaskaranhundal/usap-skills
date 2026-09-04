# container-image-scan

**Level:** L3 (SOC Analyst, read-only) | **Category:** DevSecOps | **Intent:** `detect`

Classifies container-image vulnerability scan findings from Trivy, Grype, or Snyk into a `block-deploy` / `fix-by-sla-window` / `track` / `accept` decision. Separates a CVE in a base-image OS package from a CVE in an application dependency from an unexpected image layer with no matching build step — each has a different owner, remediation path, and urgency. An unexpected/implanted layer is always treated as a possible supply-chain compromise (MITRE T1525) regardless of whether it carries a CVE.

---

## When to trigger

- A Trivy, Grype, or Snyk scan completes against a newly built or newly pulled container image
- A CI/CD pipeline image-scan gate needs a block/fix/track/accept decision before deploy
- A scheduled registry-wide rescan surfaces new CVEs in already-deployed images
- A build's layer history or SBOM doesn't match its recorded Dockerfile/CI steps

---

## Key outputs

| Field | Type | Description |
|---|---|---|
| `action` | string | The recommended decision — `block-deploy`, `fix-by-sla-window`, `track`, or `accept` — plus the specific remediation |
| `severity` | string | Highest individual finding severity across the scanned image |
| `key_findings` | array | Per-finding CVE/package/layer, its component classification, and its recommended action |
| `mitre_ttps` | array | `T1525` when an unexpected layer is found; `T1190` when a vulnerable component backs an internet-facing service |
| `next_agents` | array | `incident-commander` when an implant is confirmed; `cloud-workload-protection` when the image is already running |

---

## Intent classification

```
any finding.component_type == unexpected_layer
  -> severity >= high, mitre_ttps += T1525, next_agents += incident-commander

finding.severity == critical OR CISA-KEV-listed -> block-deploy
finding.severity == high                        -> fix-by-sla-window (7d internet-facing / 14d internal)
finding.severity == medium                       -> track (30d)
finding.severity == low                          -> accept (90d or next base-image refresh)
```

`intent_type` is always `detect`; `human_approval_required` is always `false` — this skill classifies and recommends, it does not hold pipeline gate authority and does not quarantine images itself.

---

## Works with

**Upstream:** `iac-security` (Dockerfile / Kubernetes manifest that produced the image), `devsecops-pipeline` (CI/CD build trigger)

**Downstream:**
- `cloud-workload-protection` — image is already running as a workload; hand off for runtime behavior
- `incident-commander` — an unexpected/implanted layer is confirmed; requires a human isolation/quarantine decision
- `findings-tracker` — `fix-by-sla-window` and `track` findings enter lifecycle management

---

## Standalone use

```bash
cat container-image-scan/SKILL.md
# Paste into any LLM as system prompt, then send a scan event:

{
  "event_type": "container_image_scan",
  "severity": "critical",
  "raw_payload": {
    "image": "registry.example.com/acme/payments-api@sha256:8f3e1c2b9a4d...",
    "scanner": "trivy",
    "internet_facing": true,
    "findings": [
      {"id": "CVE-2024-3094", "package": "liblzma5", "component_type": "base_image_os_package", "severity": "critical"},
      {"id": "CVE-2021-44228", "package": "log4j-core", "component_type": "application_dependency", "severity": "critical"},
      {"id": null, "package": "unexpected-layer", "component_type": "unexpected_layer", "severity": "critical"}
    ]
  }
}
```

Or run the bundled tool directly:

```bash
python container-image-scan/scripts/container-image-scan_tool.py --output json
python container-image-scan/scripts/container-image-scan_tool.py --image registry.example.com/acme/api:latest --scanner grype --output table
```

---

## Runtime Contract

- ../../agents/container-image-scan.yaml
