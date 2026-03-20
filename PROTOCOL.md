# Machine Attestation Protocol (MAP) — Specification v0.4.0

## Overview

The Machine Attestation Protocol (MAP) defines how agents request and receive cryptographic attestations for MPP transactions through mpps.io. MAP provides a standard interface for creating tamper-proof records that bind agent identity, content hashes, and hardware-secured timestamps into a single verifiable receipt.

## Terminology

| Term | Definition |
|------|-----------|
| **Attestation** | A cryptographically signed record proving a specific hash was submitted by a specific agent at a specific time. |
| **Receipt** | The JSON response returned after a successful attestation, containing all fields needed for independent verification. |
| **Content Hash** | A SHA-256 digest of the original data. mpps.io never receives the original data — only this hash. |
| **Agent ID** | A deterministic, one-way identifier derived from the agent's IP address via SHA-256. |
| **UUID** | A globally unique identifier for the attestation, format: `mpps_att_` + 16 hex characters. |
| **Certified Attestation** | An attestation with additional metadata and a certificate URL, created via `/v1/certify`. |

## Endpoints

### POST /v1/notarize (Free)

Create a basic attestation. Rate limit: 10/hour per IP.

**Request:**

```json
{
  "content_hash": "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `content_hash` | string | Yes | SHA-256 hash, format `sha256:<hex>` where hex is 8-128 characters. |

No authentication required. No other fields accepted.

### POST /v1/certify (Free daily + Paid)

Create a certified attestation with optional metadata. 10 free/day per IP, then $0.01 via Stripe.

**Request:**

```json
{
  "content_hash": "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
  "description": "Order delivery confirmation",
  "parties": ["agent_buyer_001", "agent_seller_002"],
  "amount": "49.99 USD",
  "transaction_type": "DELIVERY_PROOF",
  "parent_uuid": "mpps_att_a1b2c3d4e5f67890"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `content_hash` | string | Yes | SHA-256 hash, format `sha256:<hex>`. |
| `description` | string | No | Description of the transaction (max 500 chars). |
| `parties` | string[] | No | List of parties involved (max 10). |
| `amount` | string | No | Transaction amount (max 50 chars). |
| `transaction_type` | string | No | Type label (max 50 chars). |
| `parent_uuid` | string | No | UUID of a parent attestation (must start with `mpps_att_`). |

**Payment flow:** When daily free quota is exhausted and no payment credential is provided, the API returns `402` with a Stripe PaymentIntent. The agent completes payment and retries with `Authorization: Payment <credential>`.

## Response Format

**200 OK — Notarize:**

```json
{
  "uuid": "mpps_att_8e2f4a1b3c5d4e6f",
  "agent_id": "mpps_agent_7f8a9b0c",
  "content_hash": "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
  "timestamp": "2026-03-20T05:13:01.000Z",
  "signature": "MGYCMQDh7kR3L9x...",
  "certified": false,
  "storage": {
    "provider": "aws-s3",
    "lock_mode": "COMPLIANCE",
    "retention_years": 10
  },
  "verify_url": "https://api.mpps.io/v1/verify/mpps_att_8e2f4a1b3c5d4e6f",
  "request_id": "req_a1b2c3d4e5f6"
}
```

**200 OK — Certify (additional fields):**

```json
{
  "uuid": "mpps_att_c4d5e6f7a8b90123",
  "agent_id": "mpps_agent_7f8a9b0c",
  "content_hash": "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
  "timestamp": "2026-03-20T05:13:01.000Z",
  "signature": "MGYCMQDh7kR3L9x...",
  "certified": true,
  "storage": {
    "provider": "aws-s3",
    "lock_mode": "COMPLIANCE",
    "retention_years": 10
  },
  "verify_url": "https://api.mpps.io/v1/verify/mpps_att_c4d5e6f7a8b90123",
  "certificate_url": "https://mpps.io/cert/mpps_att_c4d5e6f7a8b90123",
  "metadata": {
    "description": "Order delivery confirmation",
    "parties": ["agent_buyer_001", "agent_seller_002"],
    "amount": "49.99 USD",
    "transaction_type": "DELIVERY_PROOF"
  },
  "request_id": "req_a1b2c3d4e5f6"
}
```

## UUID Format

All attestation UUIDs follow the format:

```
mpps_att_ + 16 hex characters
```

Example: `mpps_att_8e2f4a1b3c5d4e6f`

The prefix enables identification and routing. The 16 hex characters are derived from a UUID v4, guaranteeing global uniqueness.

## Agent ID Derivation

Agent IDs are currently derived from the requesting IP address using SHA-256:

```
agent_id = "mpps_agent_" + SHA-256(ip_address)[:8]
```

Example: IP `203.0.113.42` → `mpps_agent_7f8a9b0c`

**Properties:**
- Deterministic — same IP always produces the same agent ID
- One-way — the IP address cannot be recovered from the agent ID
- Lightweight — no additional credentials required

**Planned upgrade:** Future versions will migrate to Argon2id derivation from Stripe credentials, providing stronger identity binding that is independent of network topology. The current SHA-256(IP) approach is a known limitation — agents behind shared NATs or proxies will share an identity.

## Signature Scheme

All attestations are signed using RSA-PSS:

| Parameter | Value |
|-----------|-------|
| Algorithm | RSASSA_PSS_SHA_256 |
| Hash | SHA-256 |
| Key size | 2048-bit |
| Key storage | AWS KMS HSM (FIPS 140-2 Level 3) |

The signed message is the canonical JSON representation of:

```json
{"agent_id":"...","content_hash":"...","timestamp":"..."}
```

For certified attestations with metadata:

```json
{"agent_id":"...","content_hash":"...","metadata":{...},"timestamp":"..."}
```

Fields are sorted alphabetically. No whitespace. UTF-8 encoding.

The signature is returned as raw base64 (no prefix).

## Verification

Attestations can be verified offline using the mpps.io public key:

1. Reconstruct the canonical signed message from the receipt fields, sorted alphabetically, no whitespace.
2. Decode the `signature` field from base64.
3. Verify the RSA-PSS signature against the reconstructed message using the mpps.io public key.

If verification succeeds, the attestation is authentic and unmodified. No network access to mpps.io is required.

The public key is available at `GET https://api.mpps.io/v1/public-key` (returns JSON with `public_key_base64` in DER format).

## Rate Limits

| Endpoint | Free Tier | Paid |
|----------|-----------|------|
| `/v1/notarize` | 10 / hour per IP | N/A |
| `/v1/certify` | 10 / day per IP | $0.01 via Stripe |
| `/v1/verify` | Unlimited | N/A |
| `/v1/public-key` | Unlimited | N/A |

When the notarize free tier is exhausted, the API returns `429 Too Many Requests` with a `Retry-After` header.

When the certify free tier is exhausted, the API returns `402 Payment Required` with a Stripe PaymentIntent for $0.01.

## Error Codes

| Code | Error Key | Description |
|------|-----------|-------------|
| `400` | `validation_error` | Missing or malformed `content_hash`, invalid format. |
| `402` | `payment_required` | Certify free tier exhausted. Response includes Stripe PaymentIntent. |
| `429` | `rate_limited` | Notarize free tier exhausted. Includes `Retry-After` header. |
| `503` | `service_error` | KMS or S3 failure. The attestation was not created. Safe to retry. |

All errors return:

```json
{
  "error": "<error_key>",
  "message": "<human-readable description>",
  "request_id": "req_..."
}
```
