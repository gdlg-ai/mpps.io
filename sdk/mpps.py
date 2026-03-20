"""
mpps - Python SDK for mpps.io attestation service.

Usage:
    import mpps

    receipt = mpps.notarize(
        content_hash="sha256:e3b0c44298fc..."
    )
    print(receipt.uuid)       # mpps_att_8e2f4a1b3c5d4e6f
    print(receipt.timestamp)  # 2026-03-20T05:13:01.000Z

    result = mpps.verify(receipt.uuid)
    print(result.verified)    # True
"""

from __future__ import annotations

import hashlib
import os
from dataclasses import dataclass, field
from typing import Dict, List, Optional

import requests

MPPS_API_URL = "https://api.mpps.io/v1"


class MPPSError(Exception):
    """Base exception for mpps SDK errors."""


@dataclass
class Receipt:
    """Attestation receipt returned by the notarize/certify endpoints."""

    uuid: str
    agent_id: str
    content_hash: str
    timestamp: str
    signature: str
    certified: bool = False
    storage: Dict[str, object] = field(default_factory=dict)
    verify_url: str = ""
    request_id: str = ""
    certificate_url: str = ""
    metadata: Dict[str, object] = field(default_factory=dict)


@dataclass
class VerifyResult:
    """Verification result returned by the verify endpoint."""

    verified: bool
    uuid: str
    content_hash: str
    timestamp: str
    agent_id: str
    certified: bool = False


def hash_content(data: bytes) -> str:
    """Return a ``sha256:...`` formatted hash of *data*.

    >>> mpps.hash_content(b"hello")
    'sha256:2cf24dba5fb0a30e26e83b2ac5b9e29e1b161e5c1fa7425e73043362938b9824'
    """
    digest = hashlib.sha256(data).hexdigest()
    return f"sha256:{digest}"


def notarize(
    content_hash: str,
    api_url: Optional[str] = None,
) -> Receipt:
    """Submit a content hash for cryptographic attestation.

    No authentication required. The notarize endpoint is free (10/hour).

    Args:
        content_hash: Hash to attest, in ``sha256:...`` format.
        api_url: Override the default API base URL.

    Returns:
        A :class:`Receipt` with the attestation details.

    Raises:
        MPPSError: On network or API errors.
    """
    base = api_url or MPPS_API_URL
    payload = {"content_hash": content_hash}

    try:
        resp = requests.post(
            f"{base}/notarize",
            json=payload,
            timeout=30,
        )
        resp.raise_for_status()
    except requests.RequestException as exc:
        raise MPPSError(f"Notarize request failed: {exc}") from exc

    body = resp.json()
    return Receipt(
        uuid=body["uuid"],
        agent_id=body["agent_id"],
        content_hash=body["content_hash"],
        timestamp=body["timestamp"],
        signature=body["signature"],
        certified=body.get("certified", False),
        storage=body.get("storage", {}),
        verify_url=body.get("verify_url", ""),
        request_id=body.get("request_id", ""),
    )


def verify(
    uuid: str,
    api_url: Optional[str] = None,
) -> VerifyResult:
    """Verify an existing attestation by UUID.

    Args:
        uuid: The attestation UUID to verify (e.g. ``mpps_att_8e2f4a1b3c5d4e6f``).
        api_url: Override the default API base URL.

    Returns:
        A :class:`VerifyResult` indicating validity.

    Raises:
        MPPSError: On network or API errors.
    """
    base = api_url or MPPS_API_URL

    try:
        resp = requests.get(f"{base}/verify/{uuid}", timeout=30)
        resp.raise_for_status()
    except requests.RequestException as exc:
        raise MPPSError(f"Verify request failed: {exc}") from exc

    body = resp.json()
    return VerifyResult(
        verified=body["verified"],
        uuid=body["uuid"],
        content_hash=body["content_hash"],
        timestamp=body["timestamp"],
        agent_id=body["agent_id"],
        certified=body.get("certified", False),
    )
