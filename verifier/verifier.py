"""
mpps-verifier -- Offline attestation verification tool.

Verifies mpps.io attestation receipts without any network calls.
All you need is the receipt JSON and the mpps.io public key.

Usage:
    python verifier.py receipt.json --pubkey mpps-public.pem
"""

from __future__ import annotations

import argparse
import base64
import json
import sys
from pathlib import Path

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, utils


def load_receipt(path: str) -> dict:
    """Load and minimally validate a receipt JSON file."""
    data = json.loads(Path(path).read_text())
    for key in ("agent_id", "content_hash", "timestamp", "signature"):
        if key not in data:
            raise ValueError(f"Missing required field: {key}")
    return data


def reconstruct_message(receipt: dict) -> bytes:
    """Reconstruct the canonical signed message from receipt evidence fields."""
    evidence = {
        "agent_id": receipt["agent_id"],
        "content_hash": receipt["content_hash"],
        "timestamp": receipt["timestamp"],
    }
    return json.dumps(evidence, sort_keys=True, separators=(",", ":")).encode()


def verify_signature(message: bytes, signature_b64: str, pubkey_path: str) -> bool:
    """Verify an RSA-PSS SHA-256 signature against a PEM public key."""
    pem_data = Path(pubkey_path).read_bytes()
    public_key = serialization.load_pem_public_key(pem_data)
    signature = base64.b64decode(signature_b64)

    try:
        public_key.verify(  # type: ignore[union-attr]
            signature,
            message,
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH,
            ),
            hashes.SHA256(),
        )
        return True
    except Exception:
        return False


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Offline verification of mpps.io attestation receipts.",
    )
    parser.add_argument("receipt_file", help="Path to the receipt JSON file")
    parser.add_argument(
        "--pubkey",
        default="mpps-public.pem",
        help="Path to the mpps.io PEM public key (default: mpps-public.pem)",
    )
    args = parser.parse_args()

    try:
        receipt = load_receipt(args.receipt_file)
    except (json.JSONDecodeError, ValueError) as exc:
        print(f"\u2717 ERROR \u2014 {exc}", file=sys.stderr)
        sys.exit(2)
    except FileNotFoundError:
        print(f"\u2717 ERROR \u2014 file not found: {args.receipt_file}", file=sys.stderr)
        sys.exit(2)

    try:
        message = reconstruct_message(receipt)
        valid = verify_signature(message, receipt["signature"], args.pubkey)
    except FileNotFoundError:
        print(f"\u2717 ERROR \u2014 public key not found: {args.pubkey}", file=sys.stderr)
        sys.exit(2)
    except Exception as exc:
        print(f"\u2717 ERROR \u2014 {exc}", file=sys.stderr)
        sys.exit(2)

    if valid:
        print("\u2713 Attestation valid")
        print(f"  UUID:         {receipt.get('uuid', 'N/A')}")
        print(f"  Agent:        {receipt['agent_id']}")
        print(f"  Content hash: {receipt['content_hash']}")
        print(f"  Timestamp:    {receipt['timestamp']}")
    else:
        print("\u2717 INVALID \u2014 signature does not match")
        sys.exit(1)


if __name__ == "__main__":
    main()
