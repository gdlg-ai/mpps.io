# mpps.io API Reference

Base URL: `https://api.mpps.io`

mpps.io creates HSM-signed receipts for agent actions, generated artifacts, workflow outputs, and raw content hashes.

## GET /

Returns service metadata and endpoint list.

## GET /v1/health

```bash
curl https://api.mpps.io/v1/health
```

Response:

```json
{
  "status": "ok",
  "service": "mpps.io",
  "version": "0.5.0",
  "runtime": "lambda",
  "timestamp": "2026-05-01T15:00:00+00:00"
}
```

## POST /v1/receipts

Create a structured receipt for an agent or automated workflow action.

Rate limit: 10/hour per source.

Request:

```bash
curl -X POST https://api.mpps.io/v1/receipts \
  -H "Content-Type: application/json" \
  -d '{
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
        "label": "source prompt",
        "sha256": "sha256:0123456789abcdef"
      }
    ],
    "context": {
      "repo": "gdlg-ai/example",
      "commit": "abc123",
      "workflow": "release"
    }
  }'
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
    "artifact_hashes": [
      {
        "label": "dist/app.tar.gz",
        "sha256": "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
      }
    ],
    "context": {
      "commit": "abc123",
      "repo": "gdlg-ai/example",
      "workflow": "release"
    }
  },
  "timestamp": "2026-05-01T15:00:00.000Z",
  "kms_timestamp": "Fri, 01 May 2026 15:00:00 GMT",
  "signature": "<base64>",
  "certified": true,
  "paid": false,
  "storage": {
    "provider": "aws-s3",
    "lock_mode": "COMPLIANCE",
    "retention_years": 10
  },
  "verify_url": "https://api.mpps.io/v1/verify/mpps_att_8e2f4a1b3c5d4e6f",
  "certificate_url": "https://mpps.io/cert/?uuid=mpps_att_8e2f4a1b3c5d4e6f",
  "request_id": "req_<12hex>"
}
```

Validation:

| Field | Required | Notes |
|-------|----------|-------|
| `action` | Yes | Letters, numbers, dots, underscores, colons, hyphens |
| `subject` | No | Human-readable artifact or workflow subject |
| `artifact_hashes` | Yes | 1-20 hash references |
| `input_hashes` | No | 0-20 hash references |
| `context` | No | Up to 20 string fields |
| `parent_uuid` | No | Existing `mpps_att_...` UUID |

## POST /v1/notarize

Create a raw hash receipt. Use this when structured metadata is unnecessary.

Rate limit: 10/hour per source.

```bash
curl -X POST https://api.mpps.io/v1/notarize \
  -H "Content-Type: application/json" \
  -d '{"content_hash":"sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"}'
```

## POST /v1/certify

Create a richer receipt for a raw hash with optional metadata and certificate page.

Free tier: 10/day per source. After quota, the endpoint may return a Stripe-backed `402 Payment Required` challenge.

```bash
curl -X POST https://api.mpps.io/v1/certify \
  -H "Content-Type: application/json" \
  -d '{
    "content_hash": "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "description": "delivery receipt",
    "transaction_type": "DELIVERY_PROOF",
    "parent_uuid": "mpps_att_a1b2c3d4e5f67890"
  }'
```

## GET /v1/verify/{uuid}

Retrieve and verify a stored receipt.

```bash
curl https://api.mpps.io/v1/verify/mpps_att_8e2f4a1b3c5d4e6f
```

Response includes `verified: true` when found.

## GET /v1/public-key

Returns the public key for offline verification.

```bash
curl https://api.mpps.io/v1/public-key
```

## Headers

| Header | Meaning |
|--------|---------|
| `X-Request-Id` | Request correlation ID |
| `X-Powered-By` | mpps.io version |
| `X-RateLimit-*` | Free quota state for hourly endpoints |
| `X-Certify-Free-*` | Free certify quota state |
| `Payment-Receipt` | Paid certify payment receipt, when applicable |

## Errors

| HTTP | Code | Meaning |
|------|------|---------|
| 400 | `invalid_uuid`, `invalid_credential` | Malformed UUID or payment credential |
| 402 | `payment_required`, `payment_incomplete` | Optional paid certify flow |
| 404 | `not_found` | Receipt not found |
| 422 | `validation_error` | Invalid request body |
| 429 | `rate_limited` | Free quota exhausted |
| 503 | `service_error` | KMS, S3, Stripe, or dependency failure |

## Privacy Notes

Submit hashes, not raw private content. The structured receipt endpoint stores bounded metadata, so do not include secrets, raw prompts, customer data, or private source text in labels or context.
