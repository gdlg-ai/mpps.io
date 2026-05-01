## ADDED Requirements

### Requirement: Landing page with required sections
The landing page at mpps.io SHALL contain these sections in order: Hero (tagline + CTA), Problem (three pain points), How It Works (three-step diagram), Three Principles (don't look / don't judge / don't delete), Code Snippet (Python quick start), Security (five-layer trust chain summary), Pricing (free tier + paid tier), Footer (disclaimer + links).

#### Scenario: Developer visits mpps.io
- **WHEN** a developer navigates to mpps.io
- **THEN** they see a professional, industrial-aesthetic page with all required sections and can reach the GitHub repo within one click

### Requirement: Privacy policy page
The /privacy page SHALL describe: what data mpps.io collects (only SHA-256 hashes, Stripe payment metadata, timestamps), what it does NOT collect (original content, personal data beyond Stripe metadata), data retention (10-year immutable storage for attestations), and contact email (contact@mpps.io).

#### Scenario: User reads privacy policy
- **WHEN** a user navigates to /privacy
- **THEN** they see a complete, standalone privacy policy with contact@mpps.io as the contact

### Requirement: Terms of service page
The /terms page SHALL state: mpps.io provides cryptographic attestation only (not legal certification, not content validation, not financial guarantees), limitation of liability, service availability disclaimer, and MIT license reference for open-source components.

#### Scenario: User reads terms
- **WHEN** a user navigates to /terms
- **THEN** they see standalone terms of service with clear disclaimers about the nature of the attestation service

### Requirement: Footer disclaimer on all pages
Every page SHALL include a footer stating: "mpps.io is an independent open-source project built by GlideLogic Corp. (OTCQB: GDLG). Not affiliated with, endorsed by, or officially connected to Stripe, Inc. or Tempo."

#### Scenario: Stripe disclaimer visible
- **WHEN** a user scrolls to the bottom of any page
- **THEN** the non-affiliation disclaimer is visible

### Requirement: SSL and HTTPS enforcement
The website SHALL be served over HTTPS only. HTTP requests SHALL redirect to HTTPS.

#### Scenario: HTTP redirects to HTTPS
- **WHEN** a user navigates to http://mpps.io
- **THEN** they are redirected to https://mpps.io

### Requirement: Pricing display
The pricing section SHALL show: Free tier (10 attestations per hour, no signup), Paid tier ($0.01 per attestation via Stripe MPP).

#### Scenario: Pricing is clear
- **WHEN** a developer views the pricing section
- **THEN** both tiers are displayed with clear limits and costs
