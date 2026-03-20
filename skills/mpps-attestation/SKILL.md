---
name: mpps-attestation
description: "Free, no-auth attestation. Prove what your agent did — one HTTP call, HSM-signed, stored 10 years. Paid certs get numbered IDs."
license: MIT
homepage: https://mpps.io/skills
metadata:
  author: gdlg-ai
  version: "1.2.1"
  source: https://github.com/gdlg-ai/mpps.io
compatibility: Network access to api.mpps.io required. Works with any HTTP client (curl, requests, fetch).
---

# mpps-attestation

Create cryptographic attestations for agent actions via [mpps.io](https://mpps.io).
Free. No API key. No SDK. One HTTP call.

**Source code**: https://github.com/gdlg-ai/mpps.io (MIT license)
**API docs**: https://github.com/gdlg-ai/mpps.io/blob/main/docs/api.md
**Security model**: https://github.com/gdlg-ai/mpps.io/blob/main/SECURITY.md

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

## Advanced: Certified attestation (10 free/day, then $0.01)

⚠️ **Payment notice:** After 10 free certifications per day, `/v1/certify` returns HTTP 402 and may trigger a $0.01 charge if your agent has MPP payment credentials (Tempo wallet, Stripe). Only use `/v1/certify` if you understand and authorize potential charges. For free-only usage, use `/v1/notarize` above.

Adds metadata, human-readable certificate page, and QR code.

```bash
curl -s -X POST https://api.mpps.io/v1/certify \
  -H "Content-Type: application/json" \
  -d '{
    "content_hash": "sha256:...",
    "description": "API data purchase confirmation",
    "amount": "$50.00"
  }'
```

**How billing works:** First 10 certifications per day are free — the API returns your receipt directly. After that, the API returns HTTP 402 with a Stripe PaymentIntent ($0.01). If your agent has an MPP-compatible payment method, it may authorize the charge automatically. The agent operator is responsible for configuring spending limits.

Paid certificates additionally include:
- `certification_id`: globally unique numbered ID (format: `MPPS-YYYYMMDD-NNNNNN-CC`)
- `paid: true` flag
- Certificate page with "Paid Certificate" badge

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
| Certification ID | — | — | ✓ |
| Paid badge | — | — | ✓ |

## Security & trust

All claims are verifiable:
- **HSM signing**: AWS KMS key `alias/mpps-notary-key`, FIPS 140-2 Level 3. Public key at `GET https://api.mpps.io/v1/public-key`.
- **Immutable storage**: AWS S3 Object Lock, Compliance Mode, 10-year retention. Cannot be deleted by anyone including AWS root.
- **Open source**: Full Lambda code, SDK, and verifier at https://github.com/gdlg-ai/mpps.io
- **Architecture**: https://github.com/gdlg-ai/mpps.io/blob/main/ARCHITECTURE.md
- **Security model**: https://github.com/gdlg-ai/mpps.io/blob/main/SECURITY.md
- **Offline verification**: https://github.com/gdlg-ai/mpps.io/blob/main/docs/verify.md

## Privacy

You send only a SHA-256 hash — mpps.io never sees your original data. For small or predictable inputs, hashes can theoretically be brute-forced. Avoid hashing short secrets directly; hash larger payloads or use a salt.

## Key facts

- Free: 10 attestations/hour, 10 certified/day
- No registration, no API key, no SDK required
- Built by GlideLogic Corp. (OTCQB: GDLG)
- Website: https://mpps.io
