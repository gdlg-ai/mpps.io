# mpps.io Receipt Protocol - Specification v0.5.0

This protocol defines how clients create and verify tamper-proof receipts through mpps.io. It is intentionally small: clients submit hashes and bounded metadata; mpps.io returns HSM-signed receipts that can be verified online or offline.

## Terms

| Term | Definition |
|------|------------|
| Receipt | A signed JSON record proving a hash or manifest hash was submitted at a specific time. |
| Agent action receipt | A receipt created from a structured manifest describing an agent or workflow action. |
| Manifest | Bounded metadata containing action, artifact hashes, input hashes, workflow context, and optional parent receipt. |
| Manifest hash | SHA-256 hash of the canonical JSON manifest. |
| Content hash | A SHA-256 digest supplied by the client. mpps.io does not receive the original artifact. |
| Source fingerprint | `mpps_agent_` value derived from request source information. This is not strong authentication. |
| UUID | Receipt identifier, format `mpps_att_` + 16 hex characters. |

## Endpoints

### POST /v1/receipts

Create a structured receipt for agent work, generated artifacts, release outputs, or workflow delivery evidence.

Rate limit: 10/hour per source.

Request:

```json
{
  "action": "release.publish",
  "subject": "dist/app.tar.gz",
  "artifact_hashes": [
    {
      "label": "dist/app.tar.gz",
      "sha256": "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
    }
  ],
  "input_hashes": [
    {
      "label": "prompt",
      "sha256": "sha256:0123456789abcdef"
    }
  ],
  "context": {
    "repo": "gdlg-ai/example",
    "commit": "abc123",
    "workflow": "release"
  },
  "parent_uuid": "mpps_att_a1b2c3d4e5f67890"
}
```

Rules:

- `action` must use letters, numbers, dots, underscores, colons, or hyphens.
- `artifact_hashes` is required and must include at least one SHA-256 hash.
- `input_hashes` is optional.
- `context` is optional, string-only, and bounded.
- Raw artifact bytes are not accepted.

The server canonicalizes the manifest with sorted JSON keys and compact separators, then computes:

```text
manifest_hash = "sha256:" + SHA256(canonical_manifest_json)
```

Response:

```json
{
  "uuid": "mpps_att_8e2f4a1b3c5d4e6f",
  "agent_id": "mpps_agent_7f8a9b0c",
  "content_hash": "sha256:<manifest_hash_hex>",
  "receipt_type": "agent_action",
  "manifest_hash": "sha256:<manifest_hash_hex>",
  "manifest": {
    "schema": "mpps.agent_receipt.v1",
    "action": "release.publish",
    "subject": "dist/app.tar.gz",
    "artifact_hashes": [{"label": "dist/app.tar.gz", "sha256": "sha256:..."}],
    "context": {"commit": "abc123", "repo": "gdlg-ai/example", "workflow": "release"}
  },
  "timestamp": "2026-05-01T15:00:00.000Z",
  "kms_timestamp": "Fri, 01 May 2026 15:00:00 GMT",
  "signature": "<base64>",
  "certified": true,
  "paid": false,
  "storage": {"provider": "aws-s3", "lock_mode": "COMPLIANCE", "retention_years": 10},
  "verify_url": "https://api.mpps.io/v1/verify/mpps_att_8e2f4a1b3c5d4e6f",
  "certificate_url": "https://mpps.io/cert/?uuid=mpps_att_8e2f4a1b3c5d4e6f",
  "request_id": "req_<12hex>"
}
```

### POST /v1/notarize

Create a raw hash receipt.

Rate limit: 10/hour per source.

Request:

```json
{
  "content_hash": "sha256:<hex>"
}
```

Response:

```json
{
  "uuid": "mpps_att_8e2f4a1b3c5d4e6f",
  "agent_id": "mpps_agent_7f8a9b0c",
  "content_hash": "sha256:<hex>",
  "timestamp": "2026-05-01T15:00:00.000Z",
  "kms_timestamp": "Fri, 01 May 2026 15:00:00 GMT",
  "signature": "<base64>",
  "certified": false,
  "paid": false,
  "storage": {"provider": "aws-s3", "lock_mode": "COMPLIANCE", "retention_years": 10},
  "verify_url": "https://api.mpps.io/v1/verify/mpps_att_8e2f4a1b3c5d4e6f",
  "request_id": "req_<12hex>"
}
```

### POST /v1/certify

Create a richer receipt for a raw content hash with optional metadata.

Free tier: 10/day per source. After quota, the service may return a Stripe-backed `402 Payment Required` challenge for optional paid certificates.

Request:

```json
{
  "content_hash": "sha256:<hex>",
  "description": "API data delivery confirmation",
  "parties": ["buyer-agent", "vendor-agent"],
  "amount": "$50.00",
  "transaction_type": "DELIVERY_PROOF",
  "parent_uuid": "mpps_att_a1b2c3d4e5f67890"
}
```

### GET /v1/verify/{uuid}

Retrieve a receipt by UUID. The response includes `verified: true` when a stored receipt is found and reconstructed successfully.

### GET /v1/public-key

Returns the RSA public key in DER/base64 form for offline verification.

## Signature Payload

All receipt types sign canonical JSON with sorted keys:

```json
{
  "agent_id": "mpps_agent_7f8a9b0c",
  "content_hash": "sha256:<hex>",
  "metadata": {...},
  "timestamp": "2026-05-01T15:00:00.000Z"
}
```

`metadata` is omitted for raw `/v1/notarize` receipts. For `/v1/receipts`, `content_hash` is the manifest hash and metadata contains `receipt_type`, `manifest_hash`, and the manifest itself.

Algorithm: RSA-PSS with SHA-256 (`RSASSA_PSS_SHA_256`).

## Identity Model

Current `agent_id` values are source fingerprints:

```text
agent_id = "mpps_agent_" + SHA-256(source_ip)[:8]
```

This is useful for correlating repeated submissions from the same network source, but it is not strong agent identity. Shared NATs, proxies, and dynamic IPs can merge or split identities. Future releases may add credential-backed identity, but this version does not claim authentication.

## Verification

Verification requires:

1. Receipt JSON.
2. mpps.io public key from `/v1/public-key`.
3. Reconstructed signed message using `agent_id`, `content_hash`, `timestamp`, and optional `metadata`.
4. RSA-PSS SHA-256 verification.

No call to mpps.io is required after the public key and receipt are available.

## Error Codes

| HTTP | Code | Meaning |
|------|------|---------|
| 400 | `invalid_uuid` / `invalid_credential` | Malformed UUID or payment credential |
| 402 | `payment_required` | Optional paid certify quota path |
| 404 | `not_found` | Receipt not found |
| 422 | `validation_error` | Request body failed validation |
| 429 | `rate_limited` | Free tier exhausted |
| 503 | `service_error` | KMS, S3, Stripe, or dependency error |

## Non-Goals

mpps.io does not prove that an artifact is correct, legal, safe, or high quality. It does not inspect raw content. It does not provide legal notarization or dispute resolution. It records and signs bounded facts.
