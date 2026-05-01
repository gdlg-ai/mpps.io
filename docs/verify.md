# Verification Guide

mpps.io receipts can be checked online through the API or offline with the public key. Structured agent action receipts add one more check: recompute the manifest hash and confirm it matches both `manifest_hash` and `content_hash`.

## Online Verification

```bash
curl https://api.mpps.io/v1/verify/mpps_att_8e2f4a1b3c5d4e6f
```

If the response contains `"verified": true`, the receipt exists in immutable storage and was returned by the verification endpoint.

For an agent action receipt, also inspect:

- `receipt_type`: should be `agent_action`
- `manifest_hash`: the canonical SHA-256 hash of the manifest
- `manifest`: the structured action, artifact hashes, input hashes, context, and optional parent receipt
- `content_hash`: should equal `manifest_hash`

## Offline Signature Verification

Offline verification proves the receipt signature matches the public key without contacting mpps.io after the key is fetched.

### 1. Save the receipt

```bash
curl https://api.mpps.io/v1/verify/mpps_att_8e2f4a1b3c5d4e6f > receipt.json
```

### 2. Fetch the public key

```bash
curl -s https://api.mpps.io/v1/public-key \
  | python3 -c '
import json, sys, base64
data = json.load(sys.stdin)
der = base64.b64decode(data["public_key_base64"])
b64 = base64.b64encode(der).decode()
print("-----BEGIN PUBLIC KEY-----")
for i in range(0, len(b64), 64):
    print(b64[i:i+64])
print("-----END PUBLIC KEY-----")
' > mpps-public.pem
```

Cross-check the key from more than one source when evidence quality matters. The repository verifier and published docs should use the same public key material.

### 3. Rebuild the signed message

The signature covers canonical JSON with sorted keys. A basic notarize receipt signs:

```json
{"agent_id":"...","content_hash":"sha256:...","timestamp":"..."}
```

A certified or structured receipt includes `metadata` in that signed message:

```bash
python3 - <<'PY' > message.bin
import json

r = json.load(open("receipt.json"))
evidence = {
    "agent_id": r["agent_id"],
    "content_hash": r["content_hash"],
    "timestamp": r["timestamp"],
}
if r.get("metadata"):
    evidence["metadata"] = r["metadata"]
print(json.dumps(evidence, sort_keys=True), end="")
PY
```

### 4. Decode the signature

```bash
python3 - <<'PY' > signature.bin
import base64, json, sys

r = json.load(open("receipt.json"))
sys.stdout.buffer.write(base64.b64decode(r["signature"]))
PY
```

### 5. Verify with OpenSSL

```bash
openssl dgst -sha256 \
  -verify mpps-public.pem \
  -sigopt rsa_padding_mode:pss \
  -sigopt rsa_pss_saltlen:-1 \
  -signature signature.bin \
  message.bin
```

Expected output:

```text
Verified OK
```

## Structured Receipt Manifest Check

For `/v1/receipts`, the signed `content_hash` is the canonical hash of the action manifest. Recompute it:

```bash
python3 - <<'PY'
import hashlib, json

r = json.load(open("receipt.json"))
manifest = r.get("manifest") or r.get("metadata", {}).get("manifest")
if not manifest:
    raise SystemExit("receipt has no manifest")

canonical = json.dumps(manifest, sort_keys=True, separators=(",", ":")).encode()
manifest_hash = "sha256:" + hashlib.sha256(canonical).hexdigest()

print("computed: ", manifest_hash)
print("reported: ", r.get("manifest_hash") or r.get("metadata", {}).get("manifest_hash"))
print("signed:   ", r["content_hash"])

if manifest_hash != r["content_hash"]:
    raise SystemExit("manifest hash does not match signed content_hash")
PY
```

This proves the action manifest returned by the API is the same manifest hash that was signed. It still does not prove the original artifact contents unless you separately hash those artifacts and compare them to the manifest's `artifact_hashes`.

## Python Verifier

The repository includes a standalone verifier:

```bash
pip install cryptography
python verifier/verifier.py receipt.json --pubkey mpps-public.pem
```

## Trust Model

- The signature proves mpps.io signed the receipt evidence.
- The manifest hash proves a structured action manifest was anchored without storing raw artifacts.
- `agent_id` is a weak source fingerprint, not authenticated identity.
- Verification does not prove content quality, authorship, legality, or delivery truth.
- If mpps.io is offline, stored receipts can still be checked with the public key and verifier.
