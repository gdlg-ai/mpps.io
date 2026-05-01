## ADDED Requirements

### Requirement: Auto-derive agent identity from Stripe metadata
The system SHALL generate a unique mpps-agent-id by applying Argon2 hash to the Stripe customer_id or SPT fingerprint on first contact. The same Stripe identity SHALL always map to the same mpps-agent-id.

#### Scenario: First-time agent receives assigned ID
- **WHEN** an agent calls /v1/notarize for the first time (no agent_id in request)
- **THEN** the response includes an assigned_agent_id derived from their Stripe payment metadata

#### Scenario: Returning agent recognized
- **WHEN** an agent with a previously assigned mpps-agent-id makes a new attestation
- **THEN** the system uses the existing mpps-agent-id in the receipt

### Requirement: Agent identity is privacy-preserving
The system SHALL NOT store the original Stripe customer_id. Only the one-way Argon2 hash (mpps-agent-id) is retained.

#### Scenario: Database breach does not expose Stripe accounts
- **WHEN** the attestation database is compromised
- **THEN** no Stripe account information can be reverse-engineered from stored mpps-agent-ids
