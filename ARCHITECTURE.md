# Architecture — Five-Layer Trust Chain

## Overview

mpps.io is built as a minimal, auditable pipeline. Each layer addresses a single trust requirement. No layer depends on mpps.io remaining operational — once an attestation is created, it is independently verifiable forever.

## Request Flow

```
Agent ──→ API Gateway ──→ Lambda (Python) ──→ KMS Sign ──→ S3 Store ──→ Return Receipt
  │            │               │                 │            │              │
  │            │               │                 │            │              └─ Receipt JSON
  │            │               │                 │            └─ Object Lock (10yr)
  │            │               │                 └─ RSA-PSS signature (HSM)
  │            │               └─ SHA-256(IP) agent ID + timestamp
  │            └─ Rate limiting (DynamoDB)
  └─ SHA-256 hash (original data never leaves the agent)
```

## Layer 1: Identity Anchor

**Purpose**: Bind attestations to a deterministic agent identity without requiring authentication.

**Current mechanism (v0.4.0)**:
- Input: Agent's IP address (extracted from `X-Forwarded-For` or `X-Real-IP` headers)
- Process: `SHA-256(ip_address)[:8]` → 8-character hex digest
- Output: `mpps_agent_` + hex-encoded hash

**Properties**:
- One-way derivation — IP address cannot be recovered from the agent ID
- Deterministic — same IP always produces the same ID
- No credentials required — zero-friction onboarding

**Known limitations**:
- Agents behind shared NATs or proxies will share an identity
- IP addresses can change, causing the same agent to produce different IDs
- Weaker identity binding than credential-based approaches

**Planned upgrade**: Future versions will migrate to Argon2id derivation from Stripe credentials, providing stronger identity binding that is independent of network topology and resistant to brute-force recovery.

## Layer 2: Temporal Consensus

**Purpose**: Establish a trustworthy timestamp independent of mpps.io's own clock.

**Mechanism**:
- Dual timestamps per attestation:
  - `timestamp`: Application-level UTC time (ISO 8601, millisecond resolution). Included in the signed evidence.
  - `kms_timestamp`: AWS KMS response header date from the signing operation. Infrastructure-level, cannot be manipulated by application code.
- Cross-verifiable: significant divergence between the two indicates tampering.

**Properties**:
- KMS timestamp sourced directly from AWS infrastructure — not controlled by mpps.io
- Auditable via AWS CloudTrail
- Resistant to software-level clock manipulation

## Layer 3: Hardware Signing

**Purpose**: Produce a signature that cannot be forged, even by mpps.io administrators.

**Mechanism**:
- Service: AWS KMS with HSM backing
- Certification: FIPS 140-2 Level 3
- Algorithm: RSASSA_PSS_SHA_256, 2048-bit key
- Signed payload: Canonical JSON of `{agent_id, content_hash, timestamp}` (plus `metadata` for certified attestations)

**Properties**:
- Private key generated inside the HSM — never exportable
- No human, including AWS or mpps.io administrators, can extract the private key
- All signing operations are logged in CloudTrail
- Public key is freely available for independent verification

## Layer 4: Immutable Storage

**Purpose**: Ensure attestations cannot be altered or deleted after creation.

**Mechanism**:
- Service: AWS S3 with Object Lock
- Mode: Compliance Mode
- Retention: 10 years from creation
- Pre-paid: Storage costs covered for the full retention period

**Properties**:
- Cannot be deleted by anyone during the retention period — not by mpps.io, not by AWS root account
- Cannot be overwritten or modified
- Compliance Mode cannot be shortened or disabled, even by the bucket owner
- Each attestation is stored as an individual, immutable object

## Layer 5: Public Verification

**Purpose**: Enable anyone to verify an attestation without trusting or contacting mpps.io.

**Mechanism**:
- Public key available via API: `GET https://api.mpps.io/v1/public-key` (returns JSON with base64-encoded DER key)
- Open-source verification tool in `verifier/`
- Verification requires only: the receipt JSON + the public key

**Properties**:
- Fully offline — no network access needed after obtaining the public key
- No mpps.io dependency — verification works even if mpps.io is permanently offline
- Open-source — verification logic is auditable by anyone
- Deterministic — same inputs always produce the same verification result

## Design Decisions

**Why serverless (Lambda)?** Minimal attack surface. No persistent servers to compromise. Each invocation is isolated.

**Why S3 Object Lock over a blockchain?** Object Lock provides the same immutability guarantee with lower cost, higher throughput, and no consensus overhead. The trust anchor is hardware (HSM + S3 Compliance Mode), not distributed consensus.

**Why SHA-256(IP) for identity (for now)?** Zero-friction onboarding — no credentials, no registration, no setup. The trade-off is weaker identity binding, which will be addressed with Argon2id derivation from Stripe credentials in a future release.

**Why RSA-PSS over ECDSA?** Broader toolchain support for offline verification. OpenSSL, every major language's standard library, and hardware tokens all support RSA-PSS verification natively.

---

*Trust the math, not the notary.*
