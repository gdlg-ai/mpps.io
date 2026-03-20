# mpps.io

Proof of delivery for the Machine Payments Protocol.

> Stripe MPP solved how agents pay. mpps.io solves how agents prove what happened.

## What is mpps.io?

mpps.io provides cryptographic attestation for agent-to-agent (A2A) transactions built on Stripe's Machine Payments Protocol. Every attestation records WHO submitted it (agent identity derived from IP address), WHAT was submitted (a SHA-256 hash — we never see your data), and WHEN it was submitted (a hardware-secured timestamp from atomic clock infrastructure). We don't validate content, we don't judge disputes — we provide mathematical proof that a specific hash existed at a specific time, signed by tamper-proof hardware.

## Three Principles

1. **Don't Look** — We receive only a SHA-256 hash. We never see, store, or transmit your original content.
2. **Don't Judge** — We are not arbitrators. We attest to facts (hash + time + identity), not interpretations.
3. **Don't Delete** — Every attestation is stored under S3 Object Lock (Compliance Mode) with 10-year retention. No one — not even us — can delete it.

## Quick Start

No SDK or API key required. Just send a hash:

```bash
curl -X POST https://api.mpps.io/v1/notarize \
  -H "Content-Type: application/json" \
  -d '{"content_hash": "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"}'
```

Or with Python:

```python
import requests

resp = requests.post("https://api.mpps.io/v1/notarize", json={
    "content_hash": "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
})
receipt = resp.json()

print(receipt["uuid"])       # mpps_att_8e2f4a1b3c5d4e6f
print(receipt["timestamp"])  # 2026-03-20T05:13:01.000Z
print(receipt["signature"])  # RSA-PSS signed by HSM
```

## Certify

For certified attestations with metadata (10 free/day, then $0.01 via Stripe):

```bash
curl -X POST https://api.mpps.io/v1/certify \
  -H "Content-Type: application/json" \
  -d '{
    "content_hash": "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "description": "Order delivery confirmation",
    "transaction_type": "DELIVERY_PROOF"
  }'
```

## Verify

```bash
curl https://api.mpps.io/v1/verify/mpps_att_8e2f4a1b3c5d4e6f
```

## How It Works

1. **Hash** — You compute a SHA-256 hash of your transaction data and send it to mpps.io.
2. **Sign** — The hash is signed by a hardware security module (HSM) and stored immutably.
3. **Receive** — You get back a signed receipt (UUID, timestamp, HSM signature) that proves your hash existed at that exact moment.

## Five-Layer Trust Chain

| Layer | Name | Mechanism |
|-------|------|-----------|
| 1 | **Identity Anchor** | SHA-256 derivation from agent IP address (Argon2id upgrade planned) |
| 2 | **Temporal Consensus** | AWS Time Sync Service (satellite atomic clock clusters, microsecond precision) |
| 3 | **Hardware Signing** | AWS KMS HSM (FIPS 140-2 Level 3), RSA-PSS SHA-256, private key never exportable |
| 4 | **Immutable Storage** | AWS S3 Object Lock, Compliance Mode, 10-year retention — cannot be deleted by anyone including AWS root |
| 5 | **Public Verification** | Open-source verifier, offline-capable — if mpps.io disappears, your evidence remains valid |

## Pricing

| Tier | Rate | Payment |
|------|------|---------|
| Free notarize | 10 / hour | None |
| Free certify | 10 / day | None |
| Paid certify | $0.01 / attestation | Stripe MPP |

Paid certificates include a globally unique `certification_id` (format: `MPPS-YYYYMMDD-NNNNNN-CC`) and a printable certificate page with QR verification.

## Documentation

- [Protocol Specification](PROTOCOL.md)
- [Architecture](ARCHITECTURE.md)
- [Security Model](SECURITY.md)
- [API Reference](docs/api.md)
- [Offline Verification Guide](docs/verify.md)

## License

[MIT](LICENSE)

## Disclaimer

mpps.io is an independent open-source project built by GlideLogic Corp. (OTCQB: GDLG). Not affiliated with, endorsed by, or officially connected to Stripe, Inc. or Tempo.
