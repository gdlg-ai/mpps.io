# mpps.io

Tamper-proof receipts for AI agent work.

> Hash the artifact or action manifest. Get an HSM-signed receipt. Verify it later.

## What is mpps.io?

mpps.io creates cryptographic receipts for AI agents, automation workflows, and generated artifacts. A receipt proves that a specific hash or bounded action manifest was submitted at a specific time, signed by AWS KMS HSM key material, and stored under 10-year immutable retention.

mpps.io does not inspect your files, judge output quality, or certify legal truth. It gives you a durable evidence anchor for questions like:

- What did this agent claim it delivered?
- Which artifact hash was attached to this workflow?
- What inputs or parent receipts were linked to the result?
- Has this receipt changed since it was created?

## Core Use Cases

1. **Agent task completion** - attach a receipt to a finished report, code change, dataset, image, video, or decision memo.
2. **CI/release provenance** - anchor release artifacts, build outputs, and deployment manifests.
3. **Delivery evidence** - prove the hash of what was sent or received after an API, data, or payment workflow.
4. **Skill/plugin publication** - publish a receipt for the exact package or manifest users should install.

## Create an Agent Action Receipt

Use `/v1/receipts` when you have structured context: action name, artifact hashes, input hashes, and workflow metadata.

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
    "context": {
      "repo": "gdlg-ai/example",
      "commit": "abc123",
      "workflow": "release"
    }
  }'
```

The service canonicalizes the manifest, computes a `manifest_hash`, signs it, stores it, and returns:

```json
{
  "uuid": "mpps_att_8e2f4a1b3c5d4e6f",
  "receipt_type": "agent_action",
  "manifest_hash": "sha256:...",
  "timestamp": "2026-05-01T15:00:00.000Z",
  "signature": "...",
  "verify_url": "https://api.mpps.io/v1/verify/mpps_att_8e2f4a1b3c5d4e6f"
}
```

## Raw Hash Receipt

Use `/v1/notarize` when all you need is a receipt for one hash.

```bash
curl -X POST https://api.mpps.io/v1/notarize \
  -H "Content-Type: application/json" \
  -d '{"content_hash": "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"}'
```

## Certified Metadata Receipt

Use `/v1/certify` for a richer receipt with description, parties, amount, transaction type, and optional parent receipt.

```bash
curl -X POST https://api.mpps.io/v1/certify \
  -H "Content-Type: application/json" \
  -d '{
    "content_hash": "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "description": "API data delivery confirmation",
    "transaction_type": "DELIVERY_PROOF"
  }'
```

## Verify

```bash
curl https://api.mpps.io/v1/verify/mpps_att_8e2f4a1b3c5d4e6f
```

Offline verification is supported with the public key from:

```bash
curl https://api.mpps.io/v1/public-key
```

## Trust Model

| Layer | Mechanism | What It Means |
|-------|-----------|---------------|
| Hash-only input | SHA-256 hashes and bounded metadata | Original files do not need to leave your system |
| Source fingerprint | `mpps_agent_` derived from request source | Useful correlation, not strong identity |
| Timestamp | App timestamp plus KMS response timestamp | Signed evidence is anchored to service and AWS infrastructure time |
| Signature | AWS KMS RSA-PSS SHA-256 | Receipts are independently verifiable |
| Storage | S3 Object Lock, Compliance Mode, 10-year retention | Stored receipts are designed to be immutable |
| Verification | API and offline verifier | Receipts remain useful outside the live service |

## What mpps.io Does Not Prove

- It does not prove the submitted content is true, safe, legal, or high quality.
- It does not prove strong user or agent identity.
- It does not inspect raw artifacts.
- It is not a legal notary or dispute-resolution service.

## Pricing

| Endpoint | Free Tier | Paid Path |
|----------|-----------|-----------|
| `/v1/receipts` | 10/hour per source | Not required in this release |
| `/v1/notarize` | 10/hour per source | Not required in this release |
| `/v1/certify` | 10/day per source | Optional $0.01 Stripe flow after quota |
| `/v1/verify` | Unlimited practical use | None |

Payment workflows are supported as a use case, but mpps.io no longer depends on any payment protocol or service registry for its product positioning.

## Documentation

- [Protocol Specification](PROTOCOL.md)
- [Architecture](ARCHITECTURE.md)
- [Security Model](SECURITY.md)
- [API Reference](docs/api.md)
- [Offline Verification Guide](docs/verify.md)

## License

[MIT](LICENSE)

## Disclaimer

mpps.io is an independent open-source project built by GlideLogic Corp. (OTCQB: GDLG). Not affiliated with, endorsed by, or officially connected to Stripe, Inc., OpenClaw, OpenAI, Anthropic, C2PA, or SLSA.
