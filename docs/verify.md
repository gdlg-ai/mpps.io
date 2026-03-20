# Verification Guide

Two ways to verify any mpps.io attestation: **online** (one curl) or **offline** (with the public key).

## Online Verification

```bash
curl https://api.mpps.io/v1/verify/mpps_att_d530a57c095a4d66
```

If `"verified": true` is in the response, the attestation exists and is authentic. Done.

## Offline Verification

Verify without contacting mpps.io. You need: the receipt JSON + the public key.

### End-to-End Example

This uses the real Genesis Certificate (mpps_att_d530a57c095a4d66) as a worked example.

**Step 1: Save the receipt**

```bash
cat > receipt.json << 'EOF'
{
  "uuid": "mpps_att_d530a57c095a4d66",
  "agent_id": "mpps_agent_58ce44d9",
  "content_hash": "sha256:2b0a0357f4c629f357fcf97a8febe6b38be78cace22823ae15823d9e723ae3d0",
  "timestamp": "2026-03-20T06:52:12.982Z",
  "signature": "O0fL23h282wHOfQ/NE62HPpI/F4mNSG+327knmEPfDVpJ1EB6Gec/VYGWcgaExEqPzfRW6M96G4B2orPSTMl6h0bL54sxJN9HmdnnJ0Msahm4pZ2muk1FipOoXEugIXTZibh57f7dqbz2YxBlTZJElbMf4LX2QcrefC9ESTquG5VVrYlGDG4GN7PNVS7tae2yBeYBOCmlYVHdpgUrWCBK1fi+/TWfoMNWE9GxGiV5dFLBp5iVUYUm0STD2O111cd7ZTGE8uPPqJJ2U5IZukbxd8k6WhuZBlHntZLluTHkzifq62XSeizjij9kwmY3cBLNGUBHJctJKCA7nxnKBioEg=="
}
EOF
```

**Step 2: Get the public key**

```bash
# Fetch from API and convert to PEM
curl -s https://api.mpps.io/v1/public-key \
  | python3 -c "
import json, sys, base64
data = json.load(sys.stdin)
der = base64.b64decode(data['public_key_base64'])
pem = '-----BEGIN PUBLIC KEY-----\n'
b64 = base64.b64encode(der).decode()
pem += '\n'.join([b64[i:i+64] for i in range(0, len(b64), 64)])
pem += '\n-----END PUBLIC KEY-----\n'
print(pem, end='')
" > mpps-public.pem
```

**How to trust this key:** Compare with the key published on GitHub, or fetch from multiple networks at different times. The key fingerprint should always match.

**Step 3: Reconstruct the signed message**

The signature covers a canonical JSON of `agent_id`, `content_hash`, and `timestamp` — sorted alphabetically, no whitespace:

```bash
echo -n '{"agent_id":"mpps_agent_58ce44d9","content_hash":"sha256:2b0a0357f4c629f357fcf97a8febe6b38be78cace22823ae15823d9e723ae3d0","timestamp":"2026-03-20T06:52:12.982Z"}' > message.bin
```

**Step 4: Decode the signature**

```bash
echo -n 'O0fL23h282wHOfQ/NE62HPpI/F4mNSG+327knmEPfDVpJ1EB6Gec/VYGWcgaExEqPzfRW6M96G4B2orPSTMl6h0bL54sxJN9HmdnnJ0Msahm4pZ2muk1FipOoXEugIXTZibh57f7dqbz2YxBlTZJElbMf4LX2QcrefC9ESTquG5VVrYlGDG4GN7PNVS7tae2yBeYBOCmlYVHdpgUrWCBK1fi+/TWfoMNWE9GxGiV5dFLBp5iVUYUm0STD2O111cd7ZTGE8uPPqJJ2U5IZukbxd8k6WhuZBlHntZLluTHkzifq62XSeizjij9kwmY3cBLNGUBHJctJKCA7nxnKBioEg==' | base64 -d > signature.bin
```

**Step 5: Verify with OpenSSL**

```bash
openssl dgst -sha256 \
  -verify mpps-public.pem \
  -sigopt rsa_padding_mode:pss \
  -sigopt rsa_pss_saltlen:-1 \
  -signature signature.bin \
  message.bin
```

Output:
```
Verified OK
```

If you see `Verified OK`, the attestation is authentic and untampered. No network needed.

### All-in-One Script

Verify any receipt JSON in one command:

```bash
#!/bin/bash
# Usage: ./verify.sh receipt.json mpps-public.pem

RECEIPT="$1"
PUBKEY="$2"

# Extract fields and build canonical message
MSG=$(python3 -c "
import json, sys
r = json.load(open('$RECEIPT'))
ev = {'agent_id': r['agent_id'], 'content_hash': r['content_hash'], 'timestamp': r['timestamp']}
if 'metadata' in r and r.get('certified'):
    ev['metadata'] = r['metadata']
print(json.dumps(ev, sort_keys=True, separators=(',', ':')), end='')
")

# Extract and decode signature
SIG=$(python3 -c "
import json, base64, sys
r = json.load(open('$RECEIPT'))
sys.stdout.buffer.write(base64.b64decode(r['signature']))
")

# Verify
echo -n "$MSG" > /tmp/mpps_msg.bin
echo -n "$SIG" > /tmp/mpps_sig.bin
openssl dgst -sha256 -verify "$PUBKEY" \
  -sigopt rsa_padding_mode:pss \
  -sigopt rsa_pss_saltlen:-1 \
  -signature /tmp/mpps_sig.bin /tmp/mpps_msg.bin

rm -f /tmp/mpps_msg.bin /tmp/mpps_sig.bin
```

### Python Verifier

The repository includes a standalone Python verifier:

```bash
# Install dependency
pip install cryptography

# Verify
python verifier/verifier.py receipt.json --pubkey mpps-public.pem
```

Output:
```
✓ Attestation valid
  UUID:         mpps_att_d530a57c095a4d66
  Agent:        mpps_agent_58ce44d9
  Content hash: sha256:2b0a0357f4c629f357fcf97a8febe6b38be78cace22823ae15823d9e723ae3d0
  Timestamp:    2026-03-20T06:52:12.982Z
```

## How Verification Works (Any Language)

1. Parse the receipt JSON.
2. Build the canonical message: `{"agent_id":"...","content_hash":"...","timestamp":"..."}` — keys sorted alphabetically, no whitespace, UTF-8. Include `"metadata":{...}` if the attestation is certified.
3. Base64-decode the `signature` field (raw base64, no prefix).
4. RSA-PSS verify with SHA-256, salt length = `PSS.MAX_LENGTH`, using the mpps.io public key.

## Trust Model

- **Public key source**: `GET https://api.mpps.io/v1/public-key` returns JSON with `public_key_base64` (DER, base64-encoded).
- **Cross-check**: Fetch the key from multiple sources (API, GitHub, Wayback Machine) and compare. If they match, the key is authentic.
- **After verification**: No further contact with mpps.io is needed. The receipt + public key = self-contained proof.
- **If mpps.io is offline**: Your receipts remain valid forever. The math doesn't change.
