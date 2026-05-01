# Reposition mpps.io Around Agent Action Receipts

## Why

The previous positioning centered on "proof of delivery for the Machine Payments Protocol" and a `tempoxyz/mpp` / `mpp.dev/services` distribution path. That path is now explicitly canceled. Keeping MPP as the headline creates a false strategic dependency and makes the project look like a solution waiting for another ecosystem to validate it.

The durable product insight is narrower and stronger: AI agents, automation workflows, and generated artifacts increasingly need receipts that prove *what was produced, when, and under which workflow context* without exposing the underlying content. Existing observability systems track traces, and supply-chain standards track build provenance; mpps.io can provide a small external cryptographic anchor for the final artifact or action.

## What Changes

- Reposition the public product from MPP-centric delivery proof to tamper-proof receipts for AI agent work.
- Add a first-class `/v1/receipts` API for structured agent action receipts while preserving `/v1/notarize`, `/v1/certify`, and `/v1/verify`.
- Treat IP-derived `agent_id` as a weak source fingerprint, not strong identity.
- Update homepage, README, API docs, protocol docs, skill docs, and `llms.txt` to match the new positioning.
- Keep payment workflows as a secondary use case only, not a primary route or protocol dependency.
- Make OpenSpec artifacts trackable in git so future strategy changes remain visible.

## Out of Scope

- No new payment provider or paid-dashboard work.
- No legal-notary positioning.
- No `tempoxyz/mpp` or `mpp.dev/services` work.
- No claim that mpps.io replaces tracing, C2PA, SLSA, or MCP.
- No authenticated team identity system in this change; source identity remains weak until a future release.

## Evidence From Explore

- OpenAI Agents SDK tracing documents a real need to collect agent run events, spans, tool calls, and custom events for debugging and production monitoring.
- MCP documents tools, resources, and prompts as standard primitives for AI integrations; mpps.io can attest outputs from those workflows without becoming an MCP replacement.
- SLSA attestation describes provenance for software artifacts, including how an artifact was produced.
- C2PA documents content provenance and explicitly avoids judging whether provenance is "good" or "bad"; this matches mpps.io's "prove facts, don't judge" stance.

## Impact

- Users should understand mpps.io in 10 seconds as "tamper-proof receipts for AI agent work."
- Agents and CI systems get a structured receipt endpoint instead of needing to invent metadata conventions around raw hash notarization.
- Existing API consumers remain compatible.
- Marketing claims are reduced to what the current implementation can defend.
- Superseded active changes (`mpp-dev-service-listing`, `mpps-io-launch`, and `skill-publishing`) are archived so future OpenSpec handoff starts from this repositioning change.
