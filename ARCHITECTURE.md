# Architecture - Agent Receipt Layer

## Overview

mpps.io is a small receipt pipeline for AI agents and automation workflows. Clients submit hashes or bounded action manifests. The service signs the evidence with AWS KMS, stores the receipt in immutable object storage, and returns a JSON receipt that can be verified later.

The architecture is intentionally not a full tracing system, not a content-provenance standard, and not a legal notary. It is a cryptographic anchor for important agent work.

## Request Flow

```text
Agent / CI / workflow
  |
  | POST /v1/receipts, /v1/notarize, or /v1/certify
  v
API Gateway
  |
  v
Lambda validation
  |
  | /v1/receipts only:
  | canonicalize manifest -> SHA-256 manifest_hash
  v
KMS Sign (RSA-PSS SHA-256)
  |
  v
S3 immutable storage
  |
  v
Receipt JSON + verify URL
```

## Receipt Types

### Agent Action Receipt

`POST /v1/receipts` records an action manifest:

- action name
- subject
- artifact hashes
- input hashes
- workflow context
- optional parent receipt

The original artifact is never uploaded. The signed `content_hash` is the server-computed manifest hash.

### Raw Hash Receipt

`POST /v1/notarize` records one client-provided content hash. This remains the lowest-friction endpoint.

### Certified Metadata Receipt

`POST /v1/certify` records a raw content hash with optional metadata and a certificate URL. This endpoint keeps the existing free daily quota and optional paid path.

## Trust Chain

| Layer | Mechanism | Claim |
|-------|-----------|-------|
| Input minimization | Hashes and bounded metadata | mpps.io does not need raw artifact data |
| Source fingerprint | SHA-256 of network source | weak correlation only, not authentication |
| Canonical manifest | sorted compact JSON for `/v1/receipts` | stable manifest hash for equivalent payloads |
| Timestamp | app timestamp plus KMS HTTP date | signed evidence has service and infrastructure time anchors |
| Hardware signing | AWS KMS HSM, RSA-PSS SHA-256 | private key is non-exportable |
| Immutable storage | S3 Object Lock, Compliance Mode | stored receipts are designed to be unmodifiable for 10 years |
| Public verification | API and offline verifier | receipts can be checked without trusting the live website |

## Identity Model

The current `agent_id` is a source fingerprint:

```text
mpps_agent_ + SHA-256(source_ip)[:8]
```

This is deliberately low-friction and useful for rough correlation. It is not proof of a specific human, organization, machine, wallet, account, or agent. Shared NATs and proxies can produce shared fingerprints; dynamic IPs can produce changing fingerprints.

Future work may add API keys, signed client keys, workload identity, or wallet-backed identity. Those are not part of this release.

## Storage Model

Each receipt is stored as a JSON object under:

```text
attestations/YYYY-MM-DD/mpps_att_<id>.json
```

The public receipt omits the bucket name but includes:

- UUID
- source fingerprint
- content or manifest hash
- timestamp and KMS timestamp
- signature
- certified/paid flags
- metadata, when present
- storage retention summary
- verify URL

## Verification Model

Verification reconstructs the signed message from receipt fields and verifies the RSA-PSS signature with the public key from `/v1/public-key`.

For `/v1/receipts`, callers may also recompute the manifest hash from the returned manifest to verify that `manifest_hash` and `content_hash` match the canonical manifest.

## Design Decisions

**Why not store full traces?** Full traces are useful for debugging, but they often contain sensitive prompts, tool outputs, and internal state. mpps.io stores a compact receipt anchor instead.

**Why not replace SLSA or C2PA?** Those standards solve domain-specific provenance problems. mpps.io can anchor a SLSA predicate, C2PA manifest, release hash, or simpler action manifest without pretending to replace those ecosystems.

**Why keep `/v1/notarize`?** A raw hash receipt is still useful and preserves existing clients.

**Why add `/v1/receipts`?** Without a structured endpoint, users invent inconsistent metadata around a hash. The receipt endpoint gives agents and CI systems a default shape for action evidence.

**Why not claim strong identity now?** The current service has no authentication requirement. Strong identity would require keys, wallets, accounts, or signed workload credentials, which belong in a separate change.
