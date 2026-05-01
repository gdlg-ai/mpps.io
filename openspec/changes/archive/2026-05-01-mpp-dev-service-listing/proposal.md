## Status

Canceled on 2026-05-01. Do not submit work to `tempoxyz/mpp` or pursue a `mpp.dev/services` listing unless strategy is explicitly changed again.

Historical cleanup: `tempoxyz/mpp#621` was opened briefly from `gdlg-ai:add-mpps-io-current`, then closed unmerged on 2026-05-01; both `gdlg-ai/mpp` branches (`add-mpps-io-current` and the old `add-mpps-io`) were deleted.

## Why

mpps.io is live, API working, website up, GitHub repo clean. The next strategic step is getting listed on mpp.dev/services — the official MPP service directory. This is the most native distribution channel: every agent using `tempo wallet` or `mppx` discovers services here.

mpps.io is the only service that serves the MPP ecosystem itself. Every other service uses MPP to get paid. mpps.io makes every MPP transaction more trustworthy.

## What Changes

- Fork tempoxyz/mpp repository
- Add mpps.io entry to `schemas/services.ts`
- Submit PR with service listing

## PR Details

### Title
```
Add mpps.io — attestation for agent commerce
```

### Description
```
mpps.io provides cryptographic attestation for MPP transactions.

MPP receipts prove money moved. mpps.io proves what was delivered.
It is the only service on this registry that serves the MPP
ecosystem itself — every other service uses MPP to get paid,
mpps.io makes every MPP transaction more trustworthy.

After any MPP payment, either party calls mpps.io to attest
what was exchanged, creating a complete evidence chain.

Details:
- Live API: https://api.mpps.io
- Free: 10 attestations/hour, 10 certified/day (no auth)
- Paid: $0.01/attestation via Stripe
- HSM-signed (AWS KMS, FIPS 140-2 Level 3)
- 10-year immutable storage (S3 Object Lock, Compliance Mode)
- Open source: https://github.com/gdlg-ai/mpps.io (MIT)
- llms.txt: https://api.mpps.io/llms.txt
- Website: https://mpps.io

Built by GlideLogic Corp. (OTCQB: GDLG).
```

### services.ts Entry
```typescript
// ── mpps.io ─────────────────────────────────────────────────────
{
  id: "mpps",
  name: "mpps.io",
  url: "https://api.mpps.io",
  serviceUrl: "https://api.mpps.io",
  description: "Cryptographic attestation for agent commerce. Proof of delivery for every MPP transaction.",
  categories: ["data"],
  integration: "third-party",
  tags: ["attestation", "proof", "trust", "notarize", "certificate", "audit", "receipt", "delivery"],
  status: "active",
  docs: {
    homepage: "https://mpps.io",
    llmsTxt: "https://api.mpps.io/llms.txt",
    apiReference: "https://github.com/gdlg-ai/mpps.io/blob/main/docs/api.md",
  },
  provider: { name: "GlideLogic Corp.", url: "https://glidelogic.ai" },
  realm: "api.mpps.io",
  intent: "charge",
  payment: STRIPE_PAYMENT,
  endpoints: [
    { route: "POST /v1/notarize", desc: "Free HSM-signed attestation (10/hour)" },
    { route: "POST /v1/certify", desc: "Certified attestation with metadata and certificate", amount: "1" },
    { route: "GET /v1/verify/:uuid", desc: "Verify any attestation" },
    { route: "GET /v1/public-key", desc: "Public key for offline verification" },
    { route: "GET /v1/health", desc: "Service health check" },
  ],
},
```

## Capabilities

### New Capabilities
- `mpp-service-listing`: PR to tempoxyz/mpp to list mpps.io on mpp.dev/services

### Modified Capabilities

## Impact

- External PR to tempoxyz/mpp (we don't control merge timeline)
- Once merged: mpps.io appears in mpp.dev/services, discoverable by all MPP agents
- Uses STRIPE_PAYMENT (same as Stripe Climate precedent)
- GitHub account gdlg-ai must fork tempoxyz/mpp
