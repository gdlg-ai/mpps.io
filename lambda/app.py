"""
mpps.io — Serverless Receipt API v0.5.0
Lambda + API Gateway + DynamoDB + KMS + S3
"""

import json
import os
import re
import uuid
import hashlib
import base64
import time
from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional

import boto3
import stripe
from mangum import Mangum
from fastapi import FastAPI, Request, Response, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, field_validator

# ── Config ──────────────────────────────────────────────

VERSION = "0.5.0"
AWS_REGION = os.getenv("AWS_REGION", "us-west-2")
KMS_KEY_ALIAS = "alias/mpps-notary-key"
S3_BUCKET = "mpps-vault-2026"
S3_PREFIX = "attestations"
RATE_TABLE = "mpps-rate-limits"
CHALLENGE_TABLE = "mpps-challenges"
FREE_LIMIT = 10
FREE_WINDOW = 3600
CERT_FREE_DAILY = 10
CERT_PRICE_CENTS = 1
MAX_HASH_LEN = 128
MAX_DESC_LEN = 500
MAX_PARTIES = 10
MAX_AMOUNT_LEN = 50
MAX_LABEL_LEN = 80
MAX_SUBJECT_LEN = 160
MAX_CONTEXT_ITEMS = 20
MAX_CONTEXT_VALUE_LEN = 200
HEX_RE = re.compile(r'^sha256:[0-9a-f]{8,128}$')
ACTION_RE = re.compile(r'^[A-Za-z0-9_.:-]{1,80}$')

stripe.api_key = os.getenv("STRIPE_SECRET_KEY", "")
stripe.api_version = "2026-03-04.preview"

# ── AWS Clients ─────────────────────────────────────────

kms = boto3.client("kms", region_name=AWS_REGION)
s3 = boto3.client("s3", region_name=AWS_REGION)
ddb = boto3.resource("dynamodb", region_name=AWS_REGION)
rate_table = ddb.Table(RATE_TABLE)
challenge_table = ddb.Table(CHALLENGE_TABLE)

# ── Helpers ─────────────────────────────────────────────

def _get_real_ip(request: Request) -> str:
    xff = request.headers.get("x-forwarded-for", "")
    if xff:
        return xff.split(",")[0].strip()
    xri = request.headers.get("x-real-ip", "")
    if xri:
        return xri.strip()
    return request.client.host if request.client else "unknown"

def _request_id() -> str:
    return f"req_{uuid.uuid4().hex[:12]}"

def _std_headers(rid: str, extra: dict = None) -> dict:
    h = {"X-Request-Id": rid, "X-Powered-By": f"mpps.io/{VERSION}"}
    if extra:
        h.update(extra)
    return h

def _json_response(data: dict, status: int, rid: str, extra_headers: dict = None) -> Response:
    headers = {**_std_headers(rid), "Content-Type": "application/json"}
    if extra_headers:
        headers.update(extra_headers)
    return Response(content=json.dumps(data), status_code=status, headers=headers)

def _error(code: str, msg: str, status: int, rid: str, extra_headers: dict = None) -> Response:
    return _json_response({"error": code, "message": msg, "request_id": rid}, status, rid, extra_headers)

# ── Rate Limiting (DynamoDB) ────────────────────────────

def _rate_check(ip: str) -> tuple[bool, int, int]:
    key = f"rate:{ip}"
    now = int(time.time())
    window_start = now - FREE_WINDOW
    try:
        resp = rate_table.get_item(Key={"pk": key})
        item = resp.get("Item")
        if item and int(item.get("window_start", 0)) > window_start:
            count = int(item.get("count", 0))
            reset = int(item["window_start"]) + FREE_WINDOW - now
            return count < FREE_LIMIT, max(FREE_LIMIT - count, 0), max(reset, 0)
    except Exception:
        pass
    return True, FREE_LIMIT, FREE_WINDOW

def _rate_hit(ip: str):
    key = f"rate:{ip}"
    now = int(time.time())
    try:
        resp = rate_table.get_item(Key={"pk": key})
        item = resp.get("Item")
        if item and int(item.get("window_start", 0)) > now - FREE_WINDOW:
            rate_table.update_item(
                Key={"pk": key},
                UpdateExpression="SET #c = #c + :one, #ttl = :ttl",
                ExpressionAttributeNames={"#c": "count", "#ttl": "ttl"},
                ExpressionAttributeValues={":one": 1, ":ttl": now + FREE_WINDOW},
            )
        else:
            rate_table.put_item(Item={"pk": key, "count": 1, "window_start": now, "ttl": now + FREE_WINDOW})
    except Exception:
        pass

def _cert_free_check(ip: str) -> tuple[bool, int]:
    key = f"cert:{ip}:{datetime.now(timezone.utc).strftime('%Y-%m-%d')}"
    try:
        resp = rate_table.get_item(Key={"pk": key})
        item = resp.get("Item")
        count = int(item["count"]) if item else 0
        return count < CERT_FREE_DAILY, max(CERT_FREE_DAILY - count, 0)
    except Exception:
        return True, CERT_FREE_DAILY

def _cert_free_hit(ip: str):
    key = f"cert:{ip}:{datetime.now(timezone.utc).strftime('%Y-%m-%d')}"
    now = int(time.time())
    try:
        rate_table.update_item(
            Key={"pk": key},
            UpdateExpression="SET #c = if_not_exists(#c, :zero) + :one, #ttl = :ttl",
            ExpressionAttributeNames={"#c": "count", "#ttl": "ttl"},
            ExpressionAttributeValues={":zero": 0, ":one": 1, ":ttl": now + 86400},
        )
    except Exception:
        pass

# ── Challenge Store (DynamoDB with TTL) ─────────────────

def _store_challenge(cid: str, data: dict):
    data["challenge_id"] = cid
    data["ttl"] = int(time.time()) + 600
    challenge_table.put_item(Item=data)

def _get_challenge(cid: str) -> dict | None:
    try:
        resp = challenge_table.get_item(Key={"challenge_id": cid})
        item = resp.get("Item")
        if item and int(item.get("ttl", 0)) > time.time():
            return item
    except Exception:
        pass
    return None

def _delete_challenge(cid: str):
    try:
        challenge_table.delete_item(Key={"challenge_id": cid})
    except Exception:
        pass

# ── Input Validation ────────────────────────────────────

class NotarizeRequest(BaseModel):
    content_hash: str = Field(..., max_length=MAX_HASH_LEN)

    @field_validator("content_hash")
    @classmethod
    def validate_hash(cls, v):
        if not HEX_RE.match(v):
            raise ValueError("must be format 'sha256:<hex>' with 8-128 hex characters")
        return v

class CertifyRequest(BaseModel):
    content_hash: str = Field(..., max_length=MAX_HASH_LEN)
    description: Optional[str] = Field(None, max_length=MAX_DESC_LEN)
    parties: Optional[list[str]] = Field(None, max_length=MAX_PARTIES)
    amount: Optional[str] = Field(None, max_length=MAX_AMOUNT_LEN)
    transaction_type: Optional[str] = Field(None, max_length=50)
    parent_uuid: Optional[str] = Field(None, max_length=40)

    @field_validator("content_hash")
    @classmethod
    def validate_hash(cls, v):
        if not HEX_RE.match(v):
            raise ValueError("must be format 'sha256:<hex>' with 8-128 hex characters")
        return v

    @field_validator("parent_uuid")
    @classmethod
    def validate_parent(cls, v):
        if v and not v.startswith("mpps_att_"):
            raise ValueError("must start with 'mpps_att_'")
        return v

class HashRef(BaseModel):
    label: Optional[str] = Field(None, max_length=MAX_LABEL_LEN)
    sha256: str = Field(..., max_length=MAX_HASH_LEN)

    @field_validator("sha256")
    @classmethod
    def validate_hash(cls, v):
        if not HEX_RE.match(v):
            raise ValueError("must be format 'sha256:<hex>' with 8-128 hex characters")
        return v

class ReceiptRequest(BaseModel):
    action: str = Field(..., max_length=80)
    subject: Optional[str] = Field(None, max_length=MAX_SUBJECT_LEN)
    artifact_hashes: list[HashRef] = Field(..., min_length=1, max_length=20)
    input_hashes: Optional[list[HashRef]] = Field(None, max_length=20)
    context: Optional[dict[str, str]] = None
    parent_uuid: Optional[str] = Field(None, max_length=40)

    @field_validator("action")
    @classmethod
    def validate_action(cls, v):
        if not ACTION_RE.match(v):
            raise ValueError("use letters, numbers, dots, underscores, colons, or hyphens")
        return v

    @field_validator("context")
    @classmethod
    def validate_context(cls, v):
        if v is None:
            return v
        if len(v) > MAX_CONTEXT_ITEMS:
            raise ValueError(f"maximum {MAX_CONTEXT_ITEMS} context fields")
        for key, value in v.items():
            if not key or len(key) > MAX_LABEL_LEN:
                raise ValueError(f"context keys must be 1-{MAX_LABEL_LEN} characters")
            if not isinstance(value, str) or len(value) > MAX_CONTEXT_VALUE_LEN:
                raise ValueError(f"context values must be strings up to {MAX_CONTEXT_VALUE_LEN} characters")
        return v

    @field_validator("parent_uuid")
    @classmethod
    def validate_parent(cls, v):
        if v and not v.startswith("mpps_att_"):
            raise ValueError("must start with 'mpps_att_'")
        return v

def _hash_ref_public(ref: HashRef) -> dict:
    data = {"sha256": ref.sha256}
    if ref.label:
        data["label"] = ref.label
    return data

def _build_receipt_manifest(req: ReceiptRequest) -> tuple[dict, str]:
    manifest = {
        "schema": "mpps.agent_receipt.v1",
        "action": req.action,
        "artifact_hashes": [_hash_ref_public(ref) for ref in req.artifact_hashes],
    }
    if req.subject:
        manifest["subject"] = req.subject
    if req.input_hashes:
        manifest["input_hashes"] = [_hash_ref_public(ref) for ref in req.input_hashes]
    if req.context:
        manifest["context"] = {key: req.context[key] for key in sorted(req.context)}
    if req.parent_uuid:
        manifest["parent_uuid"] = req.parent_uuid

    canonical = json.dumps(manifest, sort_keys=True, separators=(",", ":")).encode("utf-8")
    manifest_hash = "sha256:" + hashlib.sha256(canonical).hexdigest()
    return manifest, manifest_hash

# ── Certification Counter ────────────────────────────────

def _next_cert_id() -> str:
    """Atomic increment → MPPS-YYYYMMDD-NNNNNN-CC format with CRC check."""
    try:
        date_str = datetime.now(timezone.utc).strftime("%Y%m%d")
        resp = rate_table.update_item(
            Key={"pk": "mpps:cert_counter"},
            UpdateExpression="SET #c = if_not_exists(#c, :zero) + :one",
            ExpressionAttributeNames={"#c": "count"},
            ExpressionAttributeValues={":zero": 0, ":one": 1},
            ReturnValues="UPDATED_NEW",
        )
        n = int(resp["Attributes"]["count"])
        body = f"MPPS-{date_str}-{n:06X}"
        check = hashlib.sha256(body.encode()).hexdigest()[:2].upper()
        return f"{body}-{check}"
    except Exception:
        return None

# ── Core: Sign & Store ──────────────────────────────────

def _sign_and_store(content_hash: str, agent_ip: str, metadata: dict = None, certified: bool = False, paid: bool = False) -> dict:
    att_uuid = f"mpps_att_{uuid.uuid4().hex[:16]}"
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"
    agent_id = f"mpps_agent_{hashlib.sha256(agent_ip.encode()).hexdigest()[:8]}"

    evidence = {"agent_id": agent_id, "content_hash": content_hash, "timestamp": ts}
    if metadata:
        evidence["metadata"] = metadata

    message = json.dumps(evidence, sort_keys=True).encode("utf-8")

    try:
        sig_response = kms.sign(
            KeyId=KMS_KEY_ALIAS, Message=message,
            MessageType="RAW", SigningAlgorithm="RSASSA_PSS_SHA_256",
        )
    except Exception as e:
        raise RuntimeError(f"KMS signing failed: {type(e).__name__}")

    # Use KMS response timestamp as authoritative AWS infrastructure time
    kms_time = sig_response.get("ResponseMetadata", {}).get("HTTPHeaders", {}).get("date", "")

    signature = base64.b64encode(sig_response["Signature"]).decode("utf-8")

    cert_id = _next_cert_id() if paid else None

    internal = {
        "uuid": att_uuid, "agent_id": agent_id, "content_hash": content_hash,
        "timestamp": ts, "kms_timestamp": kms_time,
        "signature": signature, "certified": certified, "paid": paid,
        "storage": {"provider": "aws-s3", "bucket": S3_BUCKET,
                    "lock_mode": "COMPLIANCE", "retention_years": 10},
    }
    if metadata:
        internal["metadata"] = metadata
    if cert_id:
        internal["certification_id"] = cert_id

    s3_key = f"{S3_PREFIX}/{ts[:10]}/{att_uuid}.json"
    try:
        s3.put_object(Bucket=S3_BUCKET, Key=s3_key,
                      Body=json.dumps(internal, indent=2), ContentType="application/json")
    except Exception as e:
        raise RuntimeError(f"S3 storage failed: {type(e).__name__}")

    public = {
        "uuid": att_uuid, "agent_id": agent_id, "content_hash": content_hash,
        "timestamp": ts, "kms_timestamp": kms_time,
        "signature": signature, "certified": certified, "paid": paid,
        "storage": {"provider": "aws-s3", "lock_mode": "COMPLIANCE", "retention_years": 10},
        "verify_url": f"https://api.mpps.io/v1/verify/{att_uuid}",
    }
    if metadata:
        public["metadata"] = metadata
    if cert_id:
        public["certification_id"] = cert_id
    if certified:
        public["certificate_url"] = f"https://mpps.io/cert/?uuid={att_uuid}"
    return public

# ── App ─────────────────────────────────────────────────

app = FastAPI(title="mpps.io", version=VERSION, docs_url=None, redoc_url=None)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# ── Root ────────────────────────────────────────────────

@app.get("/")
async def root():
    return {
        "service": "mpps.io",
        "description": "Tamper-proof receipts for AI agent work",
        "positioning": "HSM-signed action receipts for generated artifacts, workflow outputs, and delivery evidence",
        "version": VERSION,
        "endpoints": {
            "receipts": "POST /v1/receipts",
            "notarize": "POST /v1/notarize",
            "certify": "POST /v1/certify",
            "verify": "GET /v1/verify/{uuid}",
            "public_key": "GET /v1/public-key",
            "health": "GET /v1/health",
        },
        "docs": "https://mpps.io",
        "llms_txt": "https://api.mpps.io/llms.txt",
        "github": "https://github.com/gdlg-ai/mpps.io",
    }

# ── Global Exception Handler ────────────────────────────

from fastapi.exceptions import RequestValidationError

@app.exception_handler(RequestValidationError)
async def validation_handler(request: Request, exc: RequestValidationError):
    rid = _request_id()
    errors = [{"field": ".".join(str(l) for l in e["loc"]), "message": e["msg"]} for e in exc.errors()]
    return _error("validation_error", json.dumps(errors), 422, rid)

@app.exception_handler(Exception)
async def global_handler(request: Request, exc: Exception):
    rid = _request_id()
    return _error("internal_error", "An unexpected error occurred.", 500, rid)

# ── Health ──────────────────────────────────────────────

@app.get("/v1/health")
async def health():
    return {"status": "ok", "service": "mpps.io", "version": VERSION,
            "runtime": "lambda", "timestamp": datetime.now(timezone.utc).isoformat()}

# ── Agent Action Receipts ───────────────────────────────

@app.post("/v1/receipts")
async def create_receipt(req: ReceiptRequest, request: Request):
    rid = _request_id()
    ip = _get_real_ip(request)

    allowed, remaining, reset = _rate_check(ip)
    if not allowed:
        return _error("rate_limited", f"Free tier: {FREE_LIMIT}/hour.", 429, rid,
                       {"Retry-After": str(reset), "X-RateLimit-Limit": str(FREE_LIMIT),
                        "X-RateLimit-Remaining": "0", "X-RateLimit-Reset": str(reset)})

    manifest, manifest_hash = _build_receipt_manifest(req)
    metadata = {
        "receipt_type": "agent_action",
        "manifest_hash": manifest_hash,
        "manifest": manifest,
    }

    _rate_hit(ip)
    try:
        receipt = _sign_and_store(manifest_hash, ip, metadata=metadata, certified=True)
    except RuntimeError as e:
        return _error("service_error", str(e), 503, rid)

    receipt["request_id"] = rid
    receipt["receipt_type"] = "agent_action"
    receipt["manifest_hash"] = manifest_hash
    receipt["manifest"] = manifest
    return _json_response(receipt, 200, rid, {
        "X-RateLimit-Limit": str(FREE_LIMIT),
        "X-RateLimit-Remaining": str(max(remaining - 1, 0)),
        "X-RateLimit-Reset": str(reset),
    })

# ── Notarize (free) ─────────────────────────────────────

@app.post("/v1/notarize")
async def notarize(req: NotarizeRequest, request: Request):
    rid = _request_id()
    ip = _get_real_ip(request)

    allowed, remaining, reset = _rate_check(ip)
    if not allowed:
        return _error("rate_limited", f"Free tier: {FREE_LIMIT}/hour. Use /v1/certify for more.", 429, rid,
                       {"Retry-After": str(reset), "X-RateLimit-Limit": str(FREE_LIMIT),
                        "X-RateLimit-Remaining": "0", "X-RateLimit-Reset": str(reset)})

    _rate_hit(ip)
    try:
        receipt = _sign_and_store(req.content_hash, ip)
    except RuntimeError as e:
        return _error("service_error", str(e), 503, rid)

    receipt["request_id"] = rid
    return _json_response(receipt, 200, rid, {
        "X-RateLimit-Limit": str(FREE_LIMIT),
        "X-RateLimit-Remaining": str(max(remaining - 1, 0)),
        "X-RateLimit-Reset": str(reset),
    })

# ── Certify (free daily + paid) ─────────────────────────

@app.post("/v1/certify")
async def certify(req: CertifyRequest, request: Request):
    rid = _request_id()
    ip = _get_real_ip(request)
    auth = request.headers.get("authorization", "")
    free_avail, free_remaining = _cert_free_check(ip)

    metadata = {k: v for k, v in {
        "description": req.description, "parties": req.parties,
        "amount": req.amount, "transaction_type": req.transaction_type,
        "parent_uuid": req.parent_uuid,
    }.items() if v is not None}

    # Free daily quota
    if free_avail and not auth.lower().startswith("payment "):
        _cert_free_hit(ip)
        try:
            receipt = _sign_and_store(req.content_hash, ip, metadata=metadata or None, certified=True)
        except RuntimeError as e:
            return _error("service_error", str(e), 503, rid)
        receipt["request_id"] = rid
        return _json_response(receipt, 200, rid, {
            "X-Certify-Free-Remaining": str(free_remaining - 1),
            "X-Certify-Free-Limit": str(CERT_FREE_DAILY),
        })

    # 402 challenge
    if not auth.lower().startswith("payment "):
        try:
            pi = stripe.PaymentIntent.create(
                amount=CERT_PRICE_CENTS, currency="usd",
                payment_method_types=["card", "crypto"],
                metadata={"service": "mpps.io", "type": "certify"},
            )
        except Exception:
            return _error("payment_setup_failed", "Could not create payment intent.", 503, rid)

        cid = uuid.uuid4().hex[:24]
        _store_challenge(cid, {
            "payment_intent_id": pi.id, "client_secret": pi.client_secret,
            "content_hash": req.content_hash, "metadata": metadata,
        })
        return _json_response({
            "type": "payment_required", "challenge_id": cid,
            "amount": "0.01", "currency": "usd",
            "description": "mpps.io certified receipt",
            "payment_intent_id": pi.id, "client_secret": pi.client_secret,
            "methods": ["card", "crypto"], "service": "mpps.io", "request_id": rid,
        }, 402, rid, {
            "WWW-Authenticate": f'Payment realm="mpps.io" challenge_id="{cid}" amount="0.01" currency="usd"',
        })

    # Verify payment
    credential = auth[len("payment "):].strip()
    try:
        cred_data = json.loads(base64.b64decode(credential))
        cid = cred_data.get("challenge_id", credential)
    except Exception:
        cid = credential

    challenge_data = _get_challenge(cid)
    if not challenge_data:
        return _error("invalid_credential", "Invalid or expired payment credential.", 400, rid)

    pi_id = challenge_data["payment_intent_id"]
    try:
        pi = stripe.PaymentIntent.retrieve(pi_id)
    except Exception:
        return _error("payment_verification_failed", "Could not verify payment.", 503, rid)

    if pi.status not in ("succeeded", "requires_capture"):
        return _json_response({
            "error": "payment_incomplete", "status": pi.status,
            "message": f"Payment status: '{pi.status}'. Complete payment, then retry.",
            "client_secret": pi.client_secret, "request_id": rid,
        }, 402, rid)

    ch_metadata = challenge_data.get("metadata", {})
    if isinstance(ch_metadata, str):
        ch_metadata = json.loads(ch_metadata)
    ch_metadata["payment_intent_id"] = pi_id
    ch_metadata["payment_amount"] = "0.01"
    ch_metadata["payment_currency"] = "usd"

    try:
        receipt = _sign_and_store(challenge_data["content_hash"], ip, metadata=ch_metadata, certified=True, paid=True)
    except RuntimeError as e:
        return _error("service_error", str(e), 503, rid)

    receipt["request_id"] = rid
    _delete_challenge(cid)

    payment_receipt = base64.b64encode(json.dumps({
        "challengeId": cid, "method": "stripe", "reference": pi_id,
        "settlement": {"amount": "1", "currency": "usd"},
        "status": "success", "timestamp": receipt["timestamp"],
    }).encode()).decode()

    return _json_response(receipt, 200, rid, {"Payment-Receipt": payment_receipt})

# ── Verify ──────────────────────────────────────────────

@app.get("/v1/verify/{att_uuid}")
async def verify(att_uuid: str):
    rid = _request_id()
    if not att_uuid.startswith("mpps_att_") or len(att_uuid) > 40:
        return _error("invalid_uuid", "UUID must start with 'mpps_att_'", 400, rid)

    # Direct S3 lookup by scanning today and recent dates
    for days_ago in range(0, 365):
        d = datetime.now(timezone.utc)
        from datetime import timedelta
        date_str = (d - timedelta(days=days_ago)).strftime("%Y-%m-%d")
        s3_key = f"{S3_PREFIX}/{date_str}/{att_uuid}.json"
        try:
            result = s3.get_object(Bucket=S3_BUCKET, Key=s3_key)
            internal = json.loads(result["Body"].read())
            public = {
                "uuid": internal["uuid"], "agent_id": internal["agent_id"],
                "content_hash": internal["content_hash"], "timestamp": internal["timestamp"],
                "kms_timestamp": internal.get("kms_timestamp", ""),
                "signature": internal["signature"], "certified": internal.get("certified", False),
                "paid": internal.get("paid", False), "verified": True,
                "storage": {"provider": "aws-s3", "lock_mode": "COMPLIANCE", "retention_years": 10},
                "verify_url": f"https://api.mpps.io/v1/verify/{att_uuid}", "request_id": rid,
            }
            if internal.get("metadata"):
                public["metadata"] = internal["metadata"]
                meta = internal["metadata"]
                if isinstance(meta, dict):
                    if meta.get("receipt_type"):
                        public["receipt_type"] = meta["receipt_type"]
                    if meta.get("manifest_hash"):
                        public["manifest_hash"] = meta["manifest_hash"]
                    if meta.get("manifest"):
                        public["manifest"] = meta["manifest"]
            if internal.get("certification_id"):
                public["certification_id"] = internal["certification_id"]
            if internal.get("certified"):
                public["certificate_url"] = f"https://mpps.io/cert/?uuid={att_uuid}"
            return _json_response(public, 200, rid)
        except s3.exceptions.NoSuchKey:
            continue
        except Exception:
            continue

    return _error("not_found", f"Receipt {att_uuid} not found", 404, rid)

# ── Public Key ──────────────────────────────────────────

@app.get("/v1/public-key")
async def public_key():
    rid = _request_id()
    try:
        response = kms.get_public_key(KeyId=KMS_KEY_ALIAS)
        pem = base64.b64encode(response["PublicKey"]).decode("utf-8")
    except Exception:
        return _error("service_error", "Could not retrieve public key.", 503, rid)
    return _json_response({
        "algorithm": "RSASSA_PSS_SHA_256", "key_spec": "RSA_2048",
        "public_key_base64": pem, "format": "DER",
        "usage": "Verify receipt signatures offline.", "request_id": rid,
    }, 200, rid)

# ── llms.txt ────────────────────────────────────────────

@app.get("/llms.txt")
async def llms_txt():
    return Response(content=f"""# mpps.io — Tamper-Proof Receipts for AI Agent Work
# Version: {VERSION}
# Base URL: https://api.mpps.io
# Purpose: HSM-signed receipts for agent actions, generated artifacts, workflow outputs, and delivery evidence
# Runtime: AWS Lambda (serverless)

## Services

### POST /v1/receipts
Free (10/hour per source). Create a structured agent action receipt. No auth required.
Input: {{"action": "build.release", "subject": "dist/app.tar.gz", "artifact_hashes": [{{"label": "dist/app.tar.gz", "sha256": "sha256:<hex>"}}], "input_hashes": [{{"label": "prompt", "sha256": "sha256:<hex>"}}], "context": {{"repo": "...", "commit": "..."}}, "parent_uuid": "mpps_att_..."}}
Output: HSM-signed receipt with receipt_type="agent_action", manifest_hash, manifest, timestamp, signature, storage, verify_url.

### POST /v1/notarize
Free (10/hour per source). Raw hash receipt. No auth required.
Input: {{"content_hash": "sha256:<hex>"}}
Output: {{"uuid": "mpps_att_<16hex>", "agent_id": "mpps_agent_<8hex>", "content_hash": "sha256:...", "timestamp": "ISO8601", "signature": "<base64>", "certified": false, "storage": {{"provider": "aws-s3", "lock_mode": "COMPLIANCE", "retention_years": 10}}, "verify_url": "https://api.mpps.io/v1/verify/<uuid>", "request_id": "req_<12hex>"}}

### POST /v1/certify
10 free/day per source, then optional $0.01 Stripe payment flow.
Input: {{"content_hash": "sha256:<hex>", "description": "...", "parties": [...], "amount": "...", "transaction_type": "...", "parent_uuid": "mpps_att_..."}}
Free response: same as notarize but certified: true + certificate_url.
Paid flow: POST without auth after quota → 402 with payment_intent_id + client_secret → pay via Stripe → POST with Authorization: Payment <credential> → certified receipt + Payment-Receipt header.

### GET /v1/verify/{{uuid}}
Free. Returns receipt with verified: true.

### GET /v1/public-key
Free. Returns JSON with public_key_base64 (DER format, base64 encoded) for offline signature verification.

### GET /v1/health
Service status. Returns version, runtime, timestamp.

## Pricing
- /v1/receipts: Free (10/hour)
- /v1/notarize: Free (10/hour)
- /v1/certify: 10 free/day, then optional $0.01 via Stripe
- /v1/verify: Free
- /v1/public-key: Free

## Trust Model
mpps.io proves that a hash or bounded receipt manifest was submitted at a specific time and signed by non-exportable HSM key material.
agent_id is a weak source fingerprint derived from network source information, not strong authenticated identity.
mpps.io does not validate content quality, legality, authorship, or delivery truth.

## About
Built by GlideLogic Corp. (OTCQB: GDLG). Not affiliated with Stripe, OpenAI, Anthropic, C2PA, or SLSA.
Website: https://mpps.io | GitHub: https://github.com/gdlg-ai/mpps.io | Contact: contact@mpps.io
""", media_type="text/plain")

# ── Lambda Handler ──────────────────────────────────────

handler = Mangum(app)
