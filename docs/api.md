# API Reference

**Base URL**: `https://api.mpps.io`
**Version**: 0.4.0
**Runtime**: AWS Lambda

All requests and responses use JSON. Include `Content-Type: application/json` for POST requests.

All responses include:
- `X-Request-Id` — unique request identifier
- `X-Powered-By` — `mpps.io/0.4.0`

---

## POST /v1/notarize

Create a free attestation. Rate limit: 10/hour per IP.

### Request Body

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `content_hash` | string | Yes | SHA-256 hash, format `sha256:<hex>` (8-128 hex characters). |

### Example Request

```bash
curl -X POST https://api.mpps.io/v1/notarize \
  -H "Content-Type: application/json" \
  -d '{"content_hash": "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"}'
```

### Response 200 — Attestation Created

```json
{
  "uuid": "mpps_att_8e2f4a1b3c5d4e6f",
  "agent_id": "mpps_agent_7f8a9b0c",
  "content_hash": "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
  "timestamp": "2026-03-20T05:13:01.000Z",
  "signature": "MGYCMQDh7kR3L9x4bVkv...",
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

**Response headers:**

| Header | Description |
|--------|-------------|
| `X-RateLimit-Limit` | Maximum requests per window (10) |
| `X-RateLimit-Remaining` | Requests remaining in current window |
| `X-RateLimit-Reset` | Seconds until window resets |

### Response 429 — Rate Limited

```json
{
  "error": "rate_limited",
  "message": "Free tier: 10/hour. Use /v1/certify for more.",
  "request_id": "req_a1b2c3d4e5f6"
}
```

Includes `Retry-After` header (seconds).

---

## POST /v1/certify

Create a certified attestation with optional metadata. 10 free/day per IP, then $0.01 via Stripe.

### Request Body

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `content_hash` | string | Yes | SHA-256 hash, format `sha256:<hex>`. |
| `description` | string | No | Transaction description (max 500 chars). |
| `parties` | string[] | No | List of parties involved (max 10). |
| `amount` | string | No | Transaction amount (max 50 chars). |
| `transaction_type` | string | No | Type label (max 50 chars). |
| `parent_uuid` | string | No | Parent attestation UUID (must start with `mpps_att_`). |

### Example Request

```bash
curl -X POST https://api.mpps.io/v1/certify \
  -H "Content-Type: application/json" \
  -d '{
    "content_hash": "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "description": "Order delivery confirmation",
    "transaction_type": "DELIVERY_PROOF"
  }'
```

### Response 200 — Certified (Free Quota)

```json
{
  "uuid": "mpps_att_c4d5e6f7a8b90123",
  "agent_id": "mpps_agent_7f8a9b0c",
  "content_hash": "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
  "timestamp": "2026-03-20T05:14:00.000Z",
  "signature": "MGYCMQDh7kR3L9x4bVkv...",
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
    "transaction_type": "DELIVERY_PROOF"
  },
  "request_id": "req_b2c3d4e5f6a7"
}
```

**Response headers (free quota):**

| Header | Description |
|--------|-------------|
| `X-Certify-Free-Remaining` | Free certifications remaining today |
| `X-Certify-Free-Limit` | Daily free limit (10) |

### Response 402 — Payment Required

Returned when daily free quota is exhausted and no payment credential is provided.

```json
{
  "type": "payment_required",
  "challenge_id": "a1b2c3d4e5f6a7b8c9d0e1f2",
  "amount": "0.01",
  "currency": "usd",
  "description": "mpps.io certified attestation",
  "payment_intent_id": "pi_3abc123def456",
  "client_secret": "pi_3abc123def456_secret_xyz",
  "methods": ["card", "crypto"],
  "service": "mpps.io",
  "request_id": "req_c3d4e5f6a7b8"
}
```

**Response headers:**

| Header | Description |
|--------|-------------|
| `WWW-Authenticate` | Payment challenge details |

**To complete payment:** Confirm the PaymentIntent using the `client_secret`, then retry the certify request with:

```
Authorization: Payment <credential>
```

Where `<credential>` is either the `challenge_id` or a base64-encoded JSON containing `{"challenge_id": "..."}`.

### Response 200 — Certified (Paid)

Same as free response, plus a `Payment-Receipt` header containing a base64-encoded payment receipt.

---

## GET /v1/verify/{uuid}

Retrieve and verify an existing attestation.

### Path Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `uuid` | string | The attestation UUID (format: `mpps_att_` + 16 hex chars). |

### Example Request

```bash
curl https://api.mpps.io/v1/verify/mpps_att_8e2f4a1b3c5d4e6f
```

### Response 200 — Attestation Found

```json
{
  "uuid": "mpps_att_8e2f4a1b3c5d4e6f",
  "agent_id": "mpps_agent_7f8a9b0c",
  "content_hash": "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
  "timestamp": "2026-03-20T05:13:01.000Z",
  "signature": "MGYCMQDh7kR3L9x4bVkv...",
  "certified": false,
  "verified": true,
  "storage": {
    "provider": "aws-s3",
    "lock_mode": "COMPLIANCE",
    "retention_years": 10
  },
  "verify_url": "https://api.mpps.io/v1/verify/mpps_att_8e2f4a1b3c5d4e6f",
  "request_id": "req_d4e5f6a7b8c9"
}
```

For certified attestations, the response also includes `metadata` and `certificate_url`.

### Response 404 — Not Found

```json
{
  "error": "not_found",
  "message": "Attestation mpps_att_8e2f4a1b3c5d4e6f not found",
  "request_id": "req_d4e5f6a7b8c9"
}
```

### Response 400 — Invalid UUID

```json
{
  "error": "invalid_uuid",
  "message": "UUID must start with 'mpps_att_'",
  "request_id": "req_d4e5f6a7b8c9"
}
```

---

## GET /v1/public-key

Retrieve the public key for offline signature verification. Returns JSON (not a PEM file).

### Example Request

```bash
curl https://api.mpps.io/v1/public-key
```

### Response 200

```json
{
  "algorithm": "RSASSA_PSS_SHA_256",
  "key_spec": "RSA_2048",
  "public_key_base64": "MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8A...",
  "format": "DER",
  "usage": "Verify attestation signatures offline.",
  "request_id": "req_e5f6a7b8c9d0"
}
```

The `public_key_base64` field contains the base64-encoded DER public key. To use with OpenSSL, decode and convert to PEM format (see [Offline Verification Guide](verify.md)).

---

## GET /v1/health

Service health check.

### Example Request

```bash
curl https://api.mpps.io/v1/health
```

### Response 200

```json
{
  "status": "ok",
  "service": "mpps.io",
  "version": "0.4.0",
  "runtime": "lambda",
  "timestamp": "2026-03-20T05:13:01.000000+00:00"
}
```

---

## Error Format

All errors follow a consistent format:

```json
{
  "error": "<error_key>",
  "message": "<human-readable description>",
  "request_id": "req_..."
}
```

| Status | Error Key | Description |
|--------|-----------|-------------|
| 400 | `validation_error` / `invalid_uuid` | Malformed input |
| 402 | `payment_required` | Certify free quota exhausted |
| 429 | `rate_limited` | Notarize free tier exhausted (includes `Retry-After` header) |
| 503 | `service_error` | KMS or S3 failure (safe to retry) |
