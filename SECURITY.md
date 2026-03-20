# Security Model

## Threat Model

### What We Defend Against

| Threat | Mitigation |
|--------|-----------|
| **Data tampering** | HSM-signed attestations + S3 Object Lock (Compliance Mode). Modification is physically impossible during the retention period. |
| **Timestamp manipulation** | Timestamps sourced from AWS Time Sync (atomic clock infrastructure), not from application servers. |
| **Administrator compromise** | HSM private keys are non-exportable (hardware-enforced). S3 Compliance Mode prevents deletion by any principal, including root. |
| **Service failure** | All attestations are independently verifiable offline. No ongoing dependency on mpps.io. |
| **Agent impersonation** | Agent IDs are derived via SHA-256 from the requesting IP address. See Known Limitations below. |

### Known Limitations

**IP-based identity (v0.4.0):** The current agent identity model derives agent IDs from IP addresses using `SHA-256(IP)[:8]`. This provides basic identity binding but has weaknesses:

- Agents behind shared NATs or proxies will share an identity
- IP addresses can change, causing the same agent to produce different IDs over time
- An attacker on the same network could produce attestations under the same agent ID

This is a known trade-off for zero-friction onboarding (no API keys, no registration). A future release will migrate to Argon2id derivation from Stripe credentials, which will provide cryptographically strong identity binding independent of network topology.

**Until then, agent IDs should be treated as a weak identity signal, not a strong authentication guarantee.** The integrity of the attestation itself (hash + timestamp + HSM signature) is unaffected by this limitation.

### What We Do NOT Defend Against

- **DDoS beyond standard AWS protection** — mpps.io uses AWS Shield Standard. Volumetric attacks beyond this threshold may cause temporary unavailability (but never data loss or corruption).
- **IP spoofing at the network level** — The current IP-based identity can be influenced by network-level attacks. This will be mitigated when credential-based identity is implemented.

## What We Store

- SHA-256 content hashes (never the original content)
- Derived agent IDs (SHA-256 of IP — not reversible to the original address)
- ISO 8601 timestamps from AWS Time Sync
- RSA-PSS signatures from AWS KMS HSM
- Stripe payment intent IDs (for paid certify billing reconciliation)
- Certification metadata (description, parties, amount, transaction_type) when provided

## What We Do NOT Store

- Original content, documents, or transaction data
- Personal identifying information (PII)
- Raw IP addresses beyond standard AWS logging
- Stripe customer credentials

## Admin Cannot

| Action | Enforcement |
|--------|-------------|
| Access HSM private keys | Hardware-enforced (FIPS 140-2 Level 3). Key material never leaves the HSM boundary. |
| Delete stored attestations | S3 Compliance Mode. No principal — including AWS root — can delete objects during the retention period. |
| Modify existing records | S3 Object Lock prevents overwrites. Each object is immutable once written. |
| View original content | Only SHA-256 hashes are received and stored. Original content never reaches mpps.io. |

## If mpps.io Is Compromised

- **Existing attestations cannot be altered.** S3 Compliance Mode is hardware-enforced and independent of application-level access.
- **Existing signatures can be verified offline.** The public key is published and archived. Verification requires no contact with mpps.io.
- **New attestations may be disrupted.** An attacker with API access could potentially create fraudulent attestations. However, these would be detectable — the compromised signing key can be revoked and a new key pair issued.
- **Historical records remain intact.** The immutability guarantee is provided by AWS infrastructure, not by mpps.io's application layer.

## If mpps.io Shuts Down

- **All receipts remain independently verifiable.** Verification requires only the receipt JSON and the public key — no network access.
- **The public key is published and archived.** Available via `GET https://api.mpps.io/v1/public-key` and archived via the Wayback Machine.
- **S3 retention continues for the full 10-year period.** Storage is pre-paid. AWS will maintain the objects regardless of mpps.io's operational status.
- **The verification tool is open-source.** Anyone can fork, host, or run it independently.

## Responsible Disclosure

Report security vulnerabilities to: **contact@mpps.io**

(A dedicated security@mpps.io address will be established. Until then, use contact@mpps.io with subject line "Security Disclosure".)

We commit to:
- Acknowledging receipt within 48 hours
- Providing an initial assessment within 7 days
- Not pursuing legal action against good-faith security researchers

## Disclaimer

mpps.io provides cryptographic attestation, not legal certification. Attestations prove a hash was submitted at a specific time. They do not validate the content behind the hash, guarantee transaction outcomes, or constitute legal evidence in any jurisdiction without additional verification.
