## ADDED Requirements

### Requirement: Python SDK with notarize function
The SDK SHALL provide a `mpps.notarize(content_hash, mpp_token)` function that calls the API and returns a receipt object with uuid, timestamp, and signature fields.

#### Scenario: SDK notarize call
- **WHEN** a developer calls `mpps.notarize(content_hash="sha256:...", mpp_token="st_mpp_...")`
- **THEN** a receipt object is returned with .uuid, .timestamp, .signature, and .agent_id attributes

### Requirement: Python SDK with verify function
The SDK SHALL provide a `mpps.verify(uuid)` function that queries the API and returns the attestation status.

#### Scenario: SDK verify call
- **WHEN** a developer calls `mpps.verify("mpps_att_8e2f...")`
- **THEN** a verification result is returned with .valid (boolean), .timestamp, and .content_hash

### Requirement: CLI verifier tool
The verifier SHALL be a standalone Python script that takes a receipt JSON file and a public key PEM file, and outputs whether the attestation signature is valid.

#### Scenario: CLI verify valid receipt
- **WHEN** a user runs `python verifier.py receipt.json --pubkey mpps-public.pem`
- **THEN** stdout shows "✓ Attestation valid" with timestamp and hash

#### Scenario: CLI verify invalid receipt
- **WHEN** a user runs verify on a tampered receipt
- **THEN** stdout shows "✗ INVALID — signature does not match" and exits with code 1

### Requirement: GitHub repo documentation set
The repository SHALL include: README.md (project overview + quick start), PROTOCOL.md (MAP protocol specification), ARCHITECTURE.md (five-layer trust chain), SECURITY.md (security model + threat analysis + disclaimers), docs/api.md (API reference), docs/verify.md (offline verification guide).

#### Scenario: Developer finds documentation
- **WHEN** a developer visits github.com/gdlg-ai/mpps.io
- **THEN** the README provides a clear overview, quick start code, and links to all documentation files
