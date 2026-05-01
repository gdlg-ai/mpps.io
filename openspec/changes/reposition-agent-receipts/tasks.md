## 1. OpenSpec Traceability

- [x] 1.1 Make OpenSpec artifacts visible to git for this repo.
- [x] 1.2 Capture the strategic pivot, design, and requirements in this change.
- [x] 1.3 Validate the OpenSpec change strictly.

## 2. API

- [x] 2.1 Add `POST /v1/receipts` for structured agent action receipts.
- [x] 2.2 Add manifest validation and canonical manifest hashing.
- [x] 2.3 Update root service metadata and `llms.txt`.
- [x] 2.4 Preserve existing `/v1/notarize`, `/v1/certify`, `/v1/verify`, and `/v1/public-key` behavior.

## 3. Documentation

- [x] 3.1 Rewrite README around agent action receipts.
- [x] 3.2 Update `PROTOCOL.md`, `ARCHITECTURE.md`, `SECURITY.md`, `docs/api.md`, and `docs/verify.md`.
- [x] 3.3 Remove `mpp.dev/services` and primary MPP positioning from docs.
- [x] 3.4 Keep payment workflows as a secondary use case with accurate limitations.

## 4. Website

- [x] 4.1 Rewrite the homepage around "tamper-proof receipts for AI agent work."
- [x] 4.2 Update pricing, integration, and trust sections to avoid overclaiming identity.
- [x] 4.3 Update terms/privacy/skills/certificate/verify pages where language conflicts with the new positioning.

## 5. Skill and SDK

- [x] 5.1 Update `skills/mpps-attestation/SKILL.md` for agent action receipts.
- [x] 5.2 Add a Python SDK helper for structured receipts.
- [x] 5.3 Sync the local `.agents/skills/mpps-attestation/SKILL.md` runtime copy.

## 6. Validation

- [x] 6.1 Run local syntax checks for Python files.
- [x] 6.2 Smoke-test the website files for broken old MPP strings.
- [x] 6.3 Record any live API deployment gap separately if local code changes are not deployed.

## 7. Deployment

- [x] 7.1 Deploy the static website to `mpps.io`.
- [x] 7.2 Deploy Lambda function `mpps-api` with `/v1/receipts`.
- [x] 7.3 Publish `mpps-attestation` 1.4.0 to ClawHub.
- [x] 7.4 Smoke-test live website, API health, receipt creation, receipt verification, and ClawHub metadata.
