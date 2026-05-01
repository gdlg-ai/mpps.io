# Design: Agent Action Receipts

## Product Thesis

The project should not sell "generic notarization" or "MPP infrastructure." Both are too broad and easy to ignore. The useful wedge is a concrete action:

> When an agent or automated workflow produces something important, it creates a receipt.

The receipt is not the full trace, the full content, or a legal assertion. It is a compact, signed, timestamped, immutable anchor that links hashes of inputs/outputs to a workflow context.

## Positioning

Primary:

- "Tamper-proof receipts for AI agent work."
- "Hash the artifact or action manifest. Get an HSM-signed receipt. Verify it later."

Secondary use cases:

- Agent task completion receipts
- Generated report, code, dataset, or media artifact receipts
- CI/release provenance anchors
- Payment or API delivery evidence
- Skill/plugin publication hash receipts

De-emphasized:

- Machine Payments Protocol as the main market
- Tempo wallet integration
- `mpp.dev/services`
- dispute resolution
- strong agent identity

## API Shape

Keep existing:

- `POST /v1/notarize`: raw content hash receipt
- `POST /v1/certify`: richer metadata + optional paid path
- `GET /v1/verify/{uuid}`: retrieve receipt
- `GET /v1/public-key`: offline verification key

Add:

`POST /v1/receipts`

Input:

```json
{
  "action": "build.release",
  "subject": "dist/app.tar.gz",
  "artifact_hashes": [
    {"label": "dist/app.tar.gz", "sha256": "sha256:<hex>"}
  ],
  "input_hashes": [
    {"label": "prompt", "sha256": "sha256:<hex>"}
  ],
  "context": {
    "repo": "gdlg-ai/example",
    "commit": "abc123",
    "workflow": "release"
  },
  "parent_uuid": "mpps_att_..."
}
```

Server behavior:

1. Validate labels, action, hashes, context size, and parent UUID.
2. Canonicalize the manifest with sorted JSON keys.
3. Compute `manifest_hash = sha256:<hex>`.
4. Call the same HSM signing/storage path as other attestations.
5. Store only hashes and bounded metadata; do not accept raw artifact bytes.
6. Return a normal mpps receipt with `receipt_type: "agent_action"` and manifest metadata.

## Trust Model

Truthful:

- The receipt proves that a bounded manifest/hash was submitted at a specific time.
- The receipt proves the submitted manifest/hash has not been altered.
- The receipt can be verified online or offline.

Not claimed:

- The agent identity is strongly authenticated.
- The output is correct, high quality, lawful, or safe.
- The submitted hash corresponds to content that mpps.io inspected.
- The receipt is legal certification.

## Why Not Just Tracing?

Tracing systems are useful for operational debugging and monitoring. mpps.io should not compete there. The useful gap is a durable, public, content-minimal anchor that can be attached to artifacts, releases, customer deliveries, and audit records without exposing the trace payload.

## Why Not Full C2PA/SLSA?

C2PA and SLSA are heavier, domain-specific standards. mpps.io can coexist by anchoring hashes of C2PA manifests, SLSA provenance, or simpler ad hoc manifests. This change should avoid pretending to be a replacement standard.

## Rollout

1. Ship the new endpoint and docs while preserving existing endpoints.
2. Rewrite homepage and README around agent receipts.
3. Update skill instructions to teach receipt creation, not just raw notarization.
4. Later changes can add CLI/GitHub Action/MCP integrations if demand is observed.
