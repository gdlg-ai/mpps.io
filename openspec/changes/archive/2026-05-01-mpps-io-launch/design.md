## Context

mpps.io is a greenfield project. The server (16.145.171.169) is a clean Ubuntu box with Nginx, Docker, PostgreSQL, and Redis available. The GitHub repo (gdlg-ai/mpps.io) exists with only a LICENSE file. The domain mpps.io is registered, email contact@mpps.io is configured.

The project has two deliverables shipping simultaneously:
1. **Website** — static landing page + dynamic /verify endpoint
2. **GitHub repo** — documentation, SDK, and verifier as the open-source face

## Goals / Non-Goals

**Goals:**
- Ship a functional website at mpps.io with SSL
- Ship complete GitHub documentation (README, PROTOCOL, ARCHITECTURE, SECURITY)
- Ship a Python SDK skeleton that demonstrates the API contract
- Ship a CLI verifier that can validate attestation receipts offline
- Establish the /verify/{uuid} page as the public proof endpoint
- Independent /privacy and /terms pages with proper legal disclaimers

**Non-Goals:**
- Actual AWS KMS/S3 integration (Phase 2 — this launch is the public face)
- Live payment processing via Stripe MPP (Phase 2)
- Production attestation API backend (Phase 2)
- Mobile responsiveness beyond basic viewport meta
- User accounts or dashboards
- CI/CD pipeline

## Decisions

### 1. Website: Static HTML + minimal JS, served by Nginx
**Why:** No build step, no framework dependency, instant deploy via scp. A single `index.html` with inline CSS gives the industrial, protocol-grade aesthetic we want. The /verify/{uuid} page can be a static template that calls a future API.
**Alternative rejected:** Next.js/React — overkill for a landing page, adds deploy complexity.

### 2. GitHub docs as Markdown, not a docs site
**Why:** Developers read GitHub READMEs natively. No need for a separate docs hosting service. `/docs` on the website simply links to the GitHub repo.
**Alternative rejected:** GitBook/Docusaurus — unnecessary abstraction layer for launch.

### 3. Python SDK as a single-file module initially
**Why:** The SDK demonstrates the API contract. A single `mpps.py` with clear function signatures is more readable than a full package structure for launch.
**Alternative rejected:** Full pip-installable package — will do in Phase 2 when the API is live.

### 4. Verifier as a standalone Python script
**Why:** Demonstrates offline verification is possible. Takes a receipt JSON and public key, outputs verification result. No network calls needed.
**Alternative rejected:** Go binary — Python matches the SDK language and lowers the barrier.

### 5. Website structure
```
/var/www/mpps.io/
├── index.html          # Landing page
├── privacy.html        # Privacy policy
├── terms.html          # Terms of service
├── verify.html         # Verification page (template)
├── css/
│   └── style.css       # Shared styles
└── assets/
    └── (minimal)
```

### 6. Pricing display: Free tier + paid tier
- Free: 10 attestations per hour (no signup required)
- Paid: $0.01 per attestation via Stripe MPP
- Display on landing page. No payment integration at launch — just the stated pricing model.

### 7. Nginx config: mpps.io with Let's Encrypt SSL
```
server {
    listen 80;
    server_name mpps.io www.mpps.io;
    return 301 https://mpps.io$request_uri;
}

server {
    listen 443 ssl;
    server_name mpps.io;
    root /var/www/mpps.io;
    index index.html;

    # Let's Encrypt certs
    ssl_certificate /etc/letsencrypt/live/mpps.io/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/mpps.io/privkey.pem;

    location / {
        try_files $uri $uri.html $uri/ =404;
    }
}
```

## Risks / Trade-offs

- **[Stripe trademark]** → Mitigation: Footer explicitly states "Not affiliated with Stripe, Inc." Domain uses "mpp" descriptively (fair use).
- **[No live API at launch]** → Mitigation: SDK and docs define the contract. /verify page shows a demo receipt. GitHub stars and PR buzz drive initial interest before API goes live.
- **[Single server, no redundancy]** → Acceptable for launch. Static site has near-zero downtime risk. Production API (Phase 2) will need proper infra.
- **[HSM signing not configured]** → The architecture docs describe the target state. Launch ships the promise and the open-source verification logic; actual KMS integration follows.
