# Security Model

## Scope

mpps.io provides cryptographic receipts for hashes and bounded action manifests. It is designed to make tampering evident and verification independent. It is not designed to inspect content, authenticate every agent, judge correctness, or provide legal notarization.

## What We Defend Against

| Threat | Mitigation |
|--------|------------|
| Receipt tampering | HSM-signed evidence and offline verification |
| Stored-record modification | S3 Object Lock in Compliance Mode |
| Application clock manipulation | App timestamp plus KMS response timestamp |
| Private key extraction | AWS KMS HSM-backed, non-exportable key material |
| Service shutdown | Receipts and public key support offline verification |
| Raw data exposure through the service | Clients submit hashes and bounded metadata, not artifact bytes |

## Known Limitations

### Source Fingerprints Are Not Strong Identity

Current `agent_id` values are derived from request source information using:

```text
SHA-256(source_ip)[:8]
```

This is a weak source fingerprint. It can help correlate submissions from the same network source, but it is not authentication.

Limitations:

- agents behind shared NATs or proxies can share a fingerprint
- dynamic IPs can change the fingerprint for the same agent
- an attacker from the same network source may appear under the same fingerprint
- the fingerprint does not prove organization, user, wallet, account, or workload identity

The signed hash and timestamp remain valid even when identity is weak. Users should treat `agent_id` as correlation metadata only.

### Hashes Prove Submission, Not Truth

A receipt proves that a hash or manifest hash was submitted and signed at a time. It does not prove:

- the underlying artifact exists forever
- the artifact is accurate or safe
- the artifact was delivered to a particular recipient
- the submitting party had rights to the content
- the metadata is truthful

### Metadata Can Leak Information

`/v1/receipts` and `/v1/certify` accept bounded metadata. Do not include secrets, private prompts, customer data, or raw source content in metadata. Hash sensitive content locally and include only labels and hashes.

## What We Store

- SHA-256 content hashes or manifest hashes
- bounded action manifests for `/v1/receipts`
- optional certification metadata
- weak source fingerprints
- timestamps
- RSA-PSS signatures
- payment intent IDs for paid certify flows
- storage metadata

## What We Do Not Store

- raw artifact bytes
- full agent traces
- raw prompts unless a client puts them into metadata against guidance
- private keys
- payment credentials
- strong account identity in this release

## Admin Cannot

| Action | Enforcement |
|--------|-------------|
| Extract the HSM private key | AWS KMS key material is non-exportable |
| Forge old receipts without detection | signatures verify against public key and signed payload |
| Modify immutable objects during retention | S3 Object Lock Compliance Mode |
| Inspect raw artifacts through mpps.io | raw artifacts are not submitted |

## If mpps.io Is Compromised

- Existing receipts should remain verifiable if the public key and receipt JSON are available.
- Stored immutable objects should remain protected by the bucket retention policy.
- Attackers could disrupt new receipt creation or create misleading new receipts while they control the service.
- A key rotation and incident notice would be required for new trust after compromise.

## If mpps.io Shuts Down

- Receipts can still be verified offline with the receipt JSON and public key.
- The open-source verifier can be forked or hosted independently.
- Users should keep copies of important receipt JSON alongside their artifacts.

## Responsible Disclosure

Report security vulnerabilities to: **contact@mpps.io**

Until a dedicated security address exists, use contact@mpps.io with subject line "Security Disclosure".

## Disclaimer

mpps.io provides cryptographic evidence, not legal certification, warranty, content validation, or dispute adjudication.
