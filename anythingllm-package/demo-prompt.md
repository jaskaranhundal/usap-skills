# USAP Demo Prompt — FortiGate Zero-Day
# Workspace: USAP Master Orchestrator
# Paste this entire block as a single message in the chat

---

Run AT and CA workflows against the following scenario.

Scenario:
- Organisation: global fintech, 4000 users
- Production shutdown: NOT allowed
- Vendor patch available: NO — 7 day wait
- Attacker is confirmed aware of the vulnerability

Vulnerability:
- Product: FortiGate FortiOS
- CVSS: 9.8 — network, zero-auth, scope changed, all impacts HIGH
- Exploited in wild: YES
- Exploit completes in 3 minutes
- IDS signature available: NO

Environment:
- 2x FortiGate firewalls (active-passive HA, internet-facing)
- 1x Kubernetes cluster (public Ingress exposed)
- 6x AWS VPCs (private subnets, 6 accounts)
- 1x GitHub Actions pipeline (OIDC enabled)
- 1x Okta SSO (4000 users, MFA enforced, SAML enabled)
- SIEM batch polling: 5-minute interval (NOT real-time)

Unknown fields — label all as PREREQUISITE_UNVERIFIED, do not assume values:
- tls_inspection_status
- aws_imds_version
- firewall_cpu_baseline
- siem_eps_capacity
- existing_compromise_status

Threat intel:
- Active scanning against this org confirmed
- Backdoor account creation observed in wild (T1136)
- Known TTPs: T1190, T1136, T1078, T1021, T1583

Tasks to complete:
1. Classify the alert — SEV-1 or SEV-2 with justification
2. Enumerate all attack paths from a compromised FortiGate (minimum 4 — include K8s pivot, AWS IMDS hop, Okta SAML abuse, GitHub OIDC theft, HA failover propagation)
3. Propose compensating controls — no patching, no production shutdown, no raw CLI commands, USAP intent blocks only
4. Classify each control as IMMEDIATE (0-24h) or DEFERRED (24h-7d) with rationale
5. Assess whether the firewall is already compromised — existing_compromise_status is UNKNOWN, do not assume clean
6. Produce a 7-day risk assessment showing daily residual risk as controls are applied
7. Flag regulatory obligations — PCI-DSS, GDPR, FCA

Rules:
- All 5 UNKNOWN fields must appear as PREREQUISITE_UNVERIFIED in your output
- No bash, FortiOS CLI, AWS CLI, or kubectl in compensating controls
- human_approval_required: true on every mutating control
- Confidence score required on the compromise assessment
