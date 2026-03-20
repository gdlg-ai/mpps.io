# mpps-verifier

Offline verification tool for mpps.io attestation receipts.

Validates cryptographic signatures without any network calls. Your attestation remains verifiable even if mpps.io is offline.

## Requirements

- Python 3.8+
- `cryptography` library

## Install

```bash
pip install cryptography
```

## Usage

```bash
python verifier.py receipt.json --pubkey mpps-public.pem
```

## Example output

**Valid attestation:**

```
Attestation: mpps_att_8e2f4a1b3c5d4e6f
Agent:        mpps_agent_7f8a9b0c
Content hash: sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855
Timestamp:    2026-03-20T05:13:01.000Z
Signature:    VALID
```

**Invalid signature:**

```
INVALID — signature does not match
```

**Malformed input:**

```
ERROR — Missing required field: signature
```

## Note

No network access required. Your attestation remains valid even if mpps.io is offline.
