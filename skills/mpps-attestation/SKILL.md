---
name: mpps-attestation
description: "Free attestation for agents. Hash your data, POST to api.mpps.io, get a signed receipt. 10 free/hour + 10 certified/day."
license: MIT
homepage: https://mpps.io/skills
metadata:
  author: gdlg-ai
  version: "1.3.0"
  source: https://github.com/gdlg-ai/mpps.io
compatibility: Requires curl or any HTTP client. Network access to api.mpps.io.
---

# mpps-attestation

Free attestation for agent actions via [mpps.io](https://mpps.io).
No API key. No SDK. No credentials. One HTTP call.

**Source**: https://github.com/gdlg-ai/mpps.io (MIT)
**Docs**: https://github.com/gdlg-ai/mpps.io/blob/main/docs/api.md

## When to use

- After receiving data from a service — attest what arrived
- After paying via MPP — attest what was delivered
- Before spending money — attest the decision chain
- After completing any task — attest the result

## Attest (bash)

```bash
HASH=$(echo -n "$DATA" | sha256sum | awk '{print "sha256:" $1}')
curl -s -X POST https://api.mpps.io/v1/notarize \
  -H "Content-Type: application/json" \
  -d "{\"content_hash\": \"$HASH\"}"
# Returns: uuid, timestamp, HSM signature, verify_url
# Free: 10/hour. No auth needed.
```

## Attest (python)

```python
import hashlib, requests
h = "sha256:" + hashlib.sha256(data).hexdigest()
r = requests.post("https://api.mpps.io/v1/notarize", json={"content_hash": h})
receipt = r.json()
# receipt["uuid"]       → "mpps_att_0c27bebca6dc4bd6"
# receipt["signature"]  → HSM-signed, independently verifiable
# receipt["verify_url"] → "https://api.mpps.io/v1/verify/mpps_att_..."
```

## Certify with metadata (10 free/day)

Add description, amount, and other context. Free, same as notarize but richer.

```bash
curl -s -X POST https://api.mpps.io/v1/certify \
  -H "Content-Type: application/json" \
  -d '{
    "content_hash": "sha256:...",
    "description": "API data delivery confirmation",
    "amount": "$50.00"
  }'
# Free: 10/day. Returns certificate_url for a human-readable page.
# For paid options beyond free tier, see https://mpps.io/#pricing
```

## Verify

```bash
curl https://api.mpps.io/v1/verify/mpps_att_0c27bebca6dc4bd6
# Returns: verified: true + full receipt
```

## Privacy

You send only a SHA-256 hash — mpps.io never sees your original data. Avoid hashing short secrets directly; use larger payloads or add a salt.

## Key facts

- Free: 10 attestations/hour, 10 certified/day
- No registration, no API key, no credentials
- HSM-signed (AWS KMS, FIPS 140-2 Level 3)
- Stored 10 years (AWS S3 Object Lock, Compliance Mode)
- Open source: https://github.com/gdlg-ai/mpps.io
- Security: https://github.com/gdlg-ai/mpps.io/blob/main/SECURITY.md
- Verification: https://github.com/gdlg-ai/mpps.io/blob/main/docs/verify.md
