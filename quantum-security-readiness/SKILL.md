---
name: quantum-security-readiness
description: USAP agent skill for Quantum Security Readiness. Use for Track post-quantum migration readiness and crypto agility.
license: MIT
metadata:
  version: 1.0.0
  author: USAP Team
  category: usap-governance
  updated: 2026-02-28
  agent_slug: "quantum-security-readiness"
---

# Quantum Security Readiness

## Overview

This skill governs the organization's readiness for the post-quantum cryptographic transition.
It maintains a complete inventory of cryptographic assets, assesses their quantum vulnerability,
and drives a prioritized migration roadmap to NIST-standardized post-quantum cryptography (PQC)
algorithms. The agent operates read-only for inventory and assessment work. Actual cryptographic
migration — changing algorithms in running systems, updating certificate policies, or modifying
key management procedures — is classified as `mutating/policy_change` and requires human approval.

## Keywords

- usap
- security-agent
- mcp
- approval-gated
- evidence-chain
- governance

## Quick Start

```bash
python scripts/quantum-security-readiness_tool.py --help
python scripts/quantum-security-readiness_tool.py --output json
```

## Quantum Threat Model

### Why Cryptographically Relevant Quantum Computers Matter

Current widely deployed public-key cryptography relies on the computational hardness of integer
factorization (RSA) and the discrete logarithm problem (ECC, DH). A cryptographically relevant
quantum computer (CRQC) running Shor's algorithm breaks both problems in polynomial time,
rendering all RSA and ECC-based systems cryptographically worthless.

Current consensus threat timeline:
- 2026-2028: NIST PQC standards fully finalized and production-grade implementations available
- 2030-2035: Majority of security community estimates first CRQC with sufficient qubit quality
  and error correction to break RSA-2048
- Tail risk: nation-state adversaries may achieve CRQC earlier than public estimates

Symmetric cryptography (AES-256, SHA-3) survives with Grover's algorithm doubling required key
length — AES-256 remains secure; AES-128 degrades to 64-bit effective security.

### Harvest Now, Decrypt Later (HNDL)

HNDL is the present threat. Adversaries collect encrypted traffic today and store it for
decryption once a CRQC is available. This is not a future threat — it is happening now.

Data sensitivity window analysis:
- If data must remain confidential for > 10 years, migration to PQC is urgent regardless of
  CRQC timeline uncertainty
- Government classified data: migrate immediately
- Health records, financial data: migrate within 24 months
- Short-lived session data: migrate during normal infrastructure refresh cycles

## NIST PQC Standards

NIST completed PQC standardization with FIPS 203, 204, and 205 published in August 2024.

### Key Encapsulation Mechanism (KEM)

**CRYSTALS-Kyber (FIPS 203 — ML-KEM)**

Kyber is based on the Module Learning With Errors (MLWE) problem. It is the primary replacement
for RSA and ECDH key exchange.

Security parameter sets:
- ML-KEM-512: ~128 bits classical security (not recommended for new systems)
- ML-KEM-768: ~192 bits classical security (recommended general purpose)
- ML-KEM-1024: ~256 bits classical security (required for data > 10 year sensitivity)

Performance: Kyber key generation and encapsulation are faster than RSA-2048 key exchange in
most benchmark environments. Public key sizes are larger (1184 bytes for ML-KEM-768 vs 256 bytes
for P-256 public key) — protocol designers must account for this in handshake buffers and
certificate infrastructure.

### Digital Signatures

**CRYSTALS-Dilithium (FIPS 204 — ML-DSA)**

Dilithium is the primary replacement for RSA-PSS and ECDSA in code signing, TLS certificates,
and document signing. Based on Module Learning With Errors.

Security parameter sets:
- ML-DSA-44: ~128 bits security
- ML-DSA-65: ~192 bits security (recommended)
- ML-DSA-87: ~256 bits security

**SPHINCS+ (FIPS 205 — SLH-DSA)**

Hash-based signature scheme. Conservative fallback — security depends only on hash function
security, not on unproven lattice problem assumptions. Larger signatures and slower performance
than Dilithium. Recommended for firmware signing where signature generation is infrequent but
long-term trust is critical.

**FALCON (FIPS 206 — FN-DSA)**

NTRU lattice-based signatures. Compact signature sizes, useful for constrained environments.
Requires side-channel-resistant implementation.

## Cryptographic Inventory

This agent maintains and continuously updates a cryptographic bill of materials (CBOM) covering:

### Asset Categories

**TLS Endpoints**
- All external and internal HTTPS services
- Current cipher suite negotiated (recorded via active scanning)
- Certificate key type and size
- Certificate expiration and renewal pipeline

**Code Signing**
- Build pipeline signing keys and algorithms
- Container image signing (Cosign key type)
- Package signing (npm, PyPI, apt, RPM GPG keys)

**Data at Rest Encryption**
- Database encryption keys and algorithms
- Object storage encryption configuration
- Full disk encryption algorithms

**Authentication Infrastructure**
- SSH host and user keys (RSA-4096, ECDSA P-256, Ed25519)
- JWT signing algorithms (RS256, ES256, EdDSA)
- SAML signing certificates
- VPN IKE/IPSec algorithms and DH groups

**Secrets Management**
- HSM key types and quantum vulnerability
- Key derivation function configurations

### Vulnerability Classification

Each asset is assigned a migration urgency tier:

| Tier | Criteria | Target Migration Date |
|---|---|---|
| CRITICAL | Data sensitivity > 10 years AND RSA/ECC protected | Within 6 months |
| HIGH | Active key exchange (TLS) exposed to internet capture | Within 18 months |
| MEDIUM | Internal services using RSA/ECC | Within 36 months |
| LOW | Short-lived sessions, already-expired data | During normal refresh |

## Hybrid Classical + PQC Transition Approach

During the transition period, hybrid key exchange is the recommended approach. Hybrid schemes
combine a classical key exchange (X25519 ECDH) with a PQC KEM (ML-KEM-768) and derive the
session key from both shared secrets. This provides:

- Security if PQC algorithms prove weaker than expected
- Security if classical algorithms remain unbroken before CRQC
- Forward compatibility with post-CRQC environments

TLS 1.3 hybrid groups standardized in IETF RFC 9496:
- `X25519MLKEM768` (IANA code point 0x11ec)
- `SecP256r1MLKEM768`

This agent tracks hybrid KEM adoption across TLS endpoints as an intermediate milestone
before full PQC-only migration.

## Crypto Agility Assessment

Crypto agility is the architectural property that allows cryptographic algorithm replacement
without system redesign. This agent assesses:

- Algorithm hardcoding in source code (grep for "RSA", "SHA1", "MD5", key size constants)
- Certificate pinning implementations that prevent algorithm rotation
- HSM dependency on specific algorithm support
- Protocol versions that cannot negotiate new cipher suites (TLS 1.0/1.1 must be eliminated)

Crypto agility score: 0-100 composite based on percentage of systems with algorithm
abstraction layers, configurable key types, and tested rotation procedures.

## Intent and Action Classification

| Action Type | Classification | Approval Required |
|---|---|---|
| Scan TLS endpoints for algorithm inventory | read_only | No |
| Assess certificate quantum vulnerability | read_only | No |
| Generate CBOM report | read_only | No |
| Score crypto agility posture | read_only | No |
| Update migration priority tier for an asset | mutating/policy_change | Yes |
| Initiate certificate re-issuance with PQC algorithm | mutating/policy_change | Yes |
| Modify cipher suite policy on load balancer | mutating/policy_change | Yes |

## Core Workflows

1. Validate input context and required fields.
2. Apply deterministic and policy-aligned reasoning for agent quantum-security-readiness.
3. Emit structured recommendation payloads for orchestrator processing.
4. Enforce human approval gates for mutating actions.

## Evidence Chain Requirements

Every assessment finding must include:

- `asset_id`: unique identifier for the cryptographic asset
- `asset_type`: tls_endpoint | signing_key | data_at_rest | auth_infrastructure | secrets
- `algorithm`: current algorithm in use (e.g., RSA-2048, ECDH-P256)
- `quantum_vulnerable`: boolean
- `data_sensitivity_years`: estimated years data must remain confidential
- `hndl_exposure`: boolean — is this traffic capturable by passive adversary today
- `migration_tier`: CRITICAL | HIGH | MEDIUM | LOW
- `recommended_pqc_replacement`: target NIST algorithm with parameter set
- `hybrid_capable`: boolean — can system support hybrid classical+PQC today
- `assessment_date`: ISO 8601 UTC

## Script Reference

- `scripts/quantum-security-readiness_tool.py`: CLI helper with --help and JSON output.

## Validation Checklist

- [ ] SKILL.md frontmatter is valid
- [ ] Script runs with --help
- [ ] references/ has at least one guide
- [ ] expected_outputs/ contains representative output
- [ ] Runtime contract link points to ../../agents/quantum-security-readiness.yaml

## Runtime Contract

- ../../agents/quantum-security-readiness.yaml
