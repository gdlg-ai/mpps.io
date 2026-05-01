## ADDED Requirements

### Requirement: Agent Action Receipt Endpoint

mpps.io SHALL provide a first-class endpoint for creating structured receipts for agent or automated workflow actions.

#### Scenario: Create receipt from artifact hashes

- **GIVEN** a client submits an action name and at least one artifact hash
- **WHEN** the client calls `POST /v1/receipts`
- **THEN** the service returns an HSM-signed receipt with a UUID, timestamp, manifest hash, verification URL, and `receipt_type` of `agent_action`

#### Scenario: Reject raw artifact content

- **GIVEN** a client attempts to submit raw content instead of hashes and bounded metadata
- **WHEN** the request is validated
- **THEN** the service rejects the request or ignores unsupported raw-content fields rather than storing artifact bytes

### Requirement: Manifest Hashing

mpps.io SHALL canonicalize receipt manifests and compute a SHA-256 manifest hash server-side before signing.

#### Scenario: Stable manifest hash

- **GIVEN** two semantically identical manifests with keys in different orders
- **WHEN** each is submitted to `POST /v1/receipts`
- **THEN** the computed manifest hash is identical

### Requirement: Weak Source Fingerprint Language

mpps.io SHALL describe IP-derived `agent_id` values as weak source fingerprints, not strong authenticated identities.

#### Scenario: Public docs explain identity limitation

- **GIVEN** a user reads the README, protocol, architecture, or security docs
- **WHEN** the docs mention `agent_id`
- **THEN** they explain that it is derived from network source information and should not be treated as strong identity

### Requirement: Payment Demotion

mpps.io SHALL treat payment workflows as a secondary use case rather than the product's primary positioning.

#### Scenario: Homepage primary message

- **GIVEN** a user opens the homepage
- **WHEN** they read the hero and first problem sections
- **THEN** the message is about tamper-proof receipts for AI agent work, not payment-service discovery

### Requirement: Backward Compatibility

mpps.io SHALL preserve existing attestation endpoints while adding the receipt endpoint.

#### Scenario: Existing notarize clients continue working

- **GIVEN** an existing client uses `POST /v1/notarize` with a valid SHA-256 content hash
- **WHEN** the request is processed
- **THEN** the service returns the same receipt shape as before or a backward-compatible superset
