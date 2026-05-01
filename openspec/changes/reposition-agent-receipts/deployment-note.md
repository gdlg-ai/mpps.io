# Deployment Note

Date: 2026-05-01

This change updates API code, docs, website copy, the skill, and the SDK for the agent action receipt positioning.

Deployment status: deployed on 2026-05-01.

- Static website deployed to `16.145.171.169:/var/www/mpps.io`.
- Lambda function `mpps-api` deployed with `lambda/app.py` version `0.5.0`.
- ClawHub skill `mpps-attestation` published as version `1.4.0`.
- Smoke receipt created: `mpps_att_c16a98a6a49541ce`.

Verification commands:

```bash
curl https://api.mpps.io/v1/health
curl -X POST https://api.mpps.io/v1/receipts \
  -H "Content-Type: application/json" \
  -d '{"action":"agent.task.complete","artifact_hashes":[{"label":"example","sha256":"sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"}]}'
curl https://api.mpps.io/v1/verify/mpps_att_c16a98a6a49541ce
```
