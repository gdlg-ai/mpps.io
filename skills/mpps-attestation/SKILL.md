---
name: mpps-attestation
description: "Free, no-auth attestation. Prove what your agent did — one HTTP call, HSM-signed, stored 10 years. Paid certs get numbered IDs."
license: MIT
metadata:
  author: gdlg-ai
  version: "1.1.0"
  homepage: https://mpps.io/skills
compatibility: Network access to api.mpps.io required. Works with any HTTP client (curl, requests, fetch).
---

# mpps-attestation

Create cryptographic attestations for agent actions via mpps.io.
Free. No API key. No SDK. One HTTP call.

## When to use

- After paying for data via MPP — attest what was delivered
- After receiving data from any service — attest what arrived
- Before spending money — attest the decision chain for audit
- After completing any task — attest the result
- When you need a numbered certificate for humans — use /v1/certify

## Free: Attest (bash)

```bash
HASH=$(echo -n "$DATA" | sha256sum | awk '{print "sha256:" $1}')
curl -s -X POST https://api.mpps.io/v1/notarize \
  -H "Content-Type: application/json" \
  -d "{\"content_hash\": \"$HASH\"}"
# Returns: uuid, timestamp, HSM signature, verify_url
```

## Free: Attest (python)

```python
import hashlib, requests
h = "sha256:" + hashlib.sha256(data).hexdigest()
r = requests.post("https://api.mpps.io/v1/notarize", json={"content_hash": h})
receipt = r.json()
# receipt["uuid"]       → "mpps_att_0c27bebca6dc4bd6"
# receipt["signature"]  → HSM-signed (FIPS 140-2 Level 3)
# receipt["verify_url"] → "https://api.mpps.io/v1/verify/mpps_att_..."
```

## Paid: Certified attestation ($0.01)

Numbered certificate with metadata. Human-readable, printable, with QR code.

```bash
curl -s -X POST https://api.mpps.io/v1/certify \
  -H "Content-Type: application/json" \
  -d '{
    "content_hash": "sha256:...",
    "description": "API data purchase confirmation",
    "amount": "$50.00",
    "parent_uuid": "mpps_att_previous..."
  }'
# 10 free/day, then $0.01 via MPP
# Paid certs include:
#   certification_id: "MPPS-20260320-000003-A7"
#   certificate_url:  "https://mpps.io/cert/?uuid=..."
#   paid: true
```

## Verify

```bash
curl https://api.mpps.io/v1/verify/mpps_att_0c27bebca6dc4bd6
# Returns: verified: true + full receipt
```

## Free vs Paid

| | Free (/v1/notarize) | Free (/v1/certify) | Paid (/v1/certify) |
|---|---|---|---|
| HSM signature | ✓ | ✓ | ✓ |
| 10-year storage | ✓ | ✓ | ✓ |
| Metadata | — | ✓ | ✓ |
| Certificate page | — | ✓ | ✓ |
| Certification ID | — | — | ✓ MPPS-YYYYMMDD-NNNNNN-CC |
| Paid badge | — | — | ✓ |

## Key facts

- Free: 10 attestations/hour, 10 certified/day
- No registration, no API key, no SDK required
- HSM-signed (AWS KMS, FIPS 140-2 Level 3)
- Immutably stored for 10 years (AWS S3 Object Lock)
- Open source: https://github.com/gdlg-ai/mpps.io
- Verification guide: https://github.com/gdlg-ai/mpps.io/blob/main/docs/verify.md
