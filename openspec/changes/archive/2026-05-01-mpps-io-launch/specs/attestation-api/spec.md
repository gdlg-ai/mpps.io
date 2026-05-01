## ADDED Requirements

### Requirement: Notarize endpoint accepts hash and returns signed receipt
The API SHALL expose POST /v1/notarize that accepts a content_hash (SHA-256) and mpp_intent (Stripe payment intent ID), and returns a UUID, timestamp, and HSM signature.

#### Scenario: Successful attestation
- **WHEN** an agent sends a valid content_hash and mpp_intent to POST /v1/notarize
- **THEN** the system returns a JSON receipt containing uuid, timestamp, content_hash, agent_id, and signature

#### Scenario: Missing content_hash
- **WHEN** an agent sends a request without content_hash
- **THEN** the system returns HTTP 400 with error "content_hash is required"

### Requirement: Attestation receipt is immutably stored
The system SHALL write every signed receipt to AWS S3 with Object Lock (Compliance Mode, 10-year retention).

#### Scenario: Receipt persisted to S3
- **WHEN** a notarization completes successfully
- **THEN** the receipt JSON is stored in S3 with Object Lock enabled and cannot be deleted or modified for 10 years

### Requirement: Receipt signature uses HSM
The system SHALL sign all receipts using AWS KMS with an asymmetric key (RSA-PSS SHA-256) stored in a FIPS 140-2 Level 3 hardware security module.

#### Scenario: Signature is verifiable with public key
- **WHEN** a receipt is returned to an agent
- **THEN** the signature can be verified offline using the mpps.io public key and standard OpenSSL tools

### Requirement: Rate limiting enforced
The system SHALL allow 10 free attestations per hour per agent. Beyond that, each attestation costs $0.01 via Stripe MPP.

#### Scenario: Free tier within limit
- **WHEN** an agent has made fewer than 10 attestations in the current hour
- **THEN** the attestation is processed without payment

#### Scenario: Paid tier triggered
- **WHEN** an agent exceeds 10 attestations in the current hour and provides a valid mpp_intent
- **THEN** the attestation is processed and $0.01 is charged
