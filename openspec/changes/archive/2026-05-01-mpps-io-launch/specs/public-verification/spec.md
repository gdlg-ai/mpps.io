## ADDED Requirements

### Requirement: Web verification page
The website SHALL serve /verify/{uuid} that displays attestation details: UUID, timestamp, content_hash, agent_id, signature status, and storage retention info.

#### Scenario: Valid UUID lookup
- **WHEN** a user navigates to /verify/mpps_att_8e2f...
- **THEN** the page displays the attestation record with "VERIFIED" status and all metadata

#### Scenario: Unknown UUID
- **WHEN** a user navigates to /verify/invalid-uuid
- **THEN** the page displays "Attestation not found"

### Requirement: Offline CLI verification
The verifier CLI SHALL validate an attestation receipt JSON against the mpps.io public key without any network calls.

#### Scenario: Valid receipt verified offline
- **WHEN** a user runs `mpps verify receipt.json --pubkey mpps-public.pem`
- **THEN** the tool outputs "Attestation valid" with timestamp and hash details

#### Scenario: Tampered receipt detected
- **WHEN** a user runs verify on a receipt with a modified content_hash
- **THEN** the tool outputs "INVALID — signature does not match"

### Requirement: Downloadable receipt
The /verify/{uuid} page SHALL offer a "Download Receipt (JSON)" button that provides the full signed receipt for offline storage.

#### Scenario: Download receipt JSON
- **WHEN** a user clicks "Download Receipt" on a valid /verify page
- **THEN** a JSON file containing uuid, timestamp, content_hash, agent_id, signature, and public key reference is downloaded
