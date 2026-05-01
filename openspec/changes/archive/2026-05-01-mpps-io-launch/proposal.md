## Status

Archived on 2026-05-01 as superseded by `reposition-agent-receipts`. Historical only; do not use this MPP-centric launch plan as current strategy.

## Why

Stripe MPP launched on 2026-03-18 and solved how machines pay each other. But there is no trust layer — no way for agents to prove what happened during a transaction. mpps.io fills this gap as the open-source trust infrastructure for MPP: cryptographic attestation, agent identity, and independently verifiable proof of submission.

## What Changes

- Create full GitHub repository content (README, PROTOCOL, ARCHITECTURE, SECURITY docs) under gdlg-ai/mpps.io
- Build and deploy mpps.io website: landing page, /verify/{uuid} page, /privacy, /terms, /status
- Create Python SDK skeleton (`mpps` package) for agent integration
- Create CLI verifier tool for offline attestation verification
- Deploy Nginx + SSL on server 16.145.171.169
- Set up API endpoint: POST /v1/notarize

## Capabilities

### New Capabilities
- `attestation-api`: Core notarization API — accepts content hash + MPP payment, returns signed UUID with HSM signature and immutable S3 storage
- `agent-identity`: Auto-derived agent identity from Stripe SPT/customer_id, mapped to mpps-agent-id via Argon2 hash
- `public-verification`: Web-based (/verify/{uuid}) and CLI-based offline verification of attestation receipts
- `website`: Landing page, privacy policy, terms of service, pricing display — all English, deployed on mpps.io
- `sdk-and-tools`: Python SDK (`mpps` package) and CLI verifier for developer integration

### Modified Capabilities

## Impact

- New web deployment on 16.145.171.169 (Nginx, SSL via Let's Encrypt)
- New GitHub repo content at gdlg-ai/mpps.io (public, MIT license)
- AWS dependencies: S3 (Object Lock), KMS (HSM signing) — to be configured
- Stripe MPP integration for payment verification
- DNS: mpps.io must point to server IP
- Email: contact@mpps.io for legal/support pages
