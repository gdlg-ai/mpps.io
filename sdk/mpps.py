"""
mpps - Python SDK for mpps.io receipt service.

Usage:
    import mpps

    receipt = mpps.create_receipt(
        action="release.publish",
        artifact_hashes=[
            {"label": "dist/app.tar.gz", "sha256": "sha256:e3b0c44298fc..."}
        ],
        context={"repo": "gdlg-ai/example", "commit": "abc123"},
    )
    print(receipt.manifest_hash)

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
    """Receipt returned by the receipts/notarize/certify endpoints."""

    uuid: str
    agent_id: str
    content_hash: str
    timestamp: str
    signature: str
    certified: bool = False
    paid: bool = False
    storage: Dict[str, object] = field(default_factory=dict)
    verify_url: str = ""
    request_id: str = ""
    certificate_url: str = ""
    metadata: Dict[str, object] = field(default_factory=dict)
    receipt_type: str = ""
    manifest_hash: str = ""
    manifest: Dict[str, object] = field(default_factory=dict)


@dataclass
class VerifyResult:
    """Verification result returned by the verify endpoint."""

    verified: bool
    uuid: str
    content_hash: str
    timestamp: str
    agent_id: str
    certified: bool = False
    receipt_type: str = ""
    manifest_hash: str = ""
    manifest: Dict[str, object] = field(default_factory=dict)


def hash_content(data: bytes) -> str:
    """Return a ``sha256:...`` formatted hash of *data*.

    >>> mpps.hash_content(b"hello")
    'sha256:2cf24dba5fb0a30e26e83b2ac5b9e29e1b161e5c1fa7425e73043362938b9824'
    """
    digest = hashlib.sha256(data).hexdigest()
    return f"sha256:{digest}"


def _receipt_from_body(body: Dict[str, object]) -> Receipt:
    metadata = body.get("metadata", {})
    if not isinstance(metadata, dict):
        metadata = {}
    manifest = body.get("manifest") or metadata.get("manifest") or {}
    if not isinstance(manifest, dict):
        manifest = {}
    return Receipt(
        uuid=body["uuid"],
        agent_id=body["agent_id"],
        content_hash=body["content_hash"],
        timestamp=body["timestamp"],
        signature=body["signature"],
        certified=body.get("certified", False),
        paid=body.get("paid", False),
        storage=body.get("storage", {}),
        verify_url=body.get("verify_url", ""),
        request_id=body.get("request_id", ""),
        certificate_url=body.get("certificate_url", ""),
        metadata=metadata,
        receipt_type=body.get("receipt_type", metadata.get("receipt_type", "")),
        manifest_hash=body.get("manifest_hash", metadata.get("manifest_hash", "")),
        manifest=manifest,
    )


def create_receipt(
    action: str,
    artifact_hashes: List[Dict[str, str]],
    subject: Optional[str] = None,
    input_hashes: Optional[List[Dict[str, str]]] = None,
    context: Optional[Dict[str, str]] = None,
    parent_uuid: Optional[str] = None,
    api_url: Optional[str] = None,
) -> Receipt:
    """Create a structured agent action receipt.

    Use this when the receipt should describe what an agent or workflow did,
    which artifacts it produced, and which inputs or parent receipts it used.

    Args:
        action: Stable action name such as ``release.publish``.
        artifact_hashes: One or more ``{"label": "...", "sha256": "sha256:..."}`` refs.
        subject: Optional human-readable artifact or workflow subject.
        input_hashes: Optional input hash refs.
        context: Optional small string metadata map.
        parent_uuid: Optional previous ``mpps_att_...`` receipt UUID.
        api_url: Override the default API base URL.

    Returns:
        A :class:`Receipt` with ``receipt_type``, ``manifest_hash``, and ``manifest``.

    Raises:
        MPPSError: On network or API errors.
    """
    base = api_url or MPPS_API_URL
    payload: Dict[str, object] = {
        "action": action,
        "artifact_hashes": artifact_hashes,
    }
    if subject is not None:
        payload["subject"] = subject
    if input_hashes is not None:
        payload["input_hashes"] = input_hashes
    if context is not None:
        payload["context"] = context
    if parent_uuid is not None:
        payload["parent_uuid"] = parent_uuid

    try:
        resp = requests.post(
            f"{base}/receipts",
            json=payload,
            timeout=30,
        )
        resp.raise_for_status()
    except requests.RequestException as exc:
        raise MPPSError(f"Receipt request failed: {exc}") from exc

    return _receipt_from_body(resp.json())


def notarize(
    content_hash: str,
    api_url: Optional[str] = None,
) -> Receipt:
    """Submit a content hash for a raw cryptographic receipt.

    No authentication required. The notarize endpoint is free (10/hour).

    Args:
        content_hash: Hash to attest, in ``sha256:...`` format.
        api_url: Override the default API base URL.

    Returns:
        A :class:`Receipt` with the receipt details.

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

    return _receipt_from_body(resp.json())


def verify(
    uuid: str,
    api_url: Optional[str] = None,
) -> VerifyResult:
    """Verify an existing receipt by UUID.

    Args:
        uuid: The receipt UUID to verify (e.g. ``mpps_att_8e2f4a1b3c5d4e6f``).
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
    metadata = body.get("metadata", {})
    if not isinstance(metadata, dict):
        metadata = {}
    manifest = body.get("manifest") or metadata.get("manifest", {})
    return VerifyResult(
        verified=body["verified"],
        uuid=body["uuid"],
        content_hash=body["content_hash"],
        timestamp=body["timestamp"],
        agent_id=body["agent_id"],
        certified=body.get("certified", False),
        receipt_type=body.get("receipt_type", metadata.get("receipt_type", "")),
        manifest_hash=body.get("manifest_hash", metadata.get("manifest_hash", "")),
        manifest=manifest if isinstance(manifest, dict) else {},
    )
