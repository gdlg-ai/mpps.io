## 1. Server & Infrastructure

- [ ] 1.1 Install certbot and obtain Let's Encrypt SSL cert for mpps.io
- [ ] 1.2 Create Nginx site config for mpps.io (HTTPS + HTTP redirect)
- [ ] 1.3 Create /var/www/mpps.io directory structure
- [ ] 1.4 Verify mpps.io resolves and serves HTTPS

## 2. Website — Landing Page

- [ ] 2.1 Create index.html with all sections: hero, problem, how-it-works, three-principles, code-snippet, security, pricing, footer
- [ ] 2.2 Create css/style.css with industrial/protocol-grade aesthetic
- [ ] 2.3 Footer includes GlideLogic attribution and Stripe non-affiliation disclaimer

## 3. Website — Legal Pages

- [ ] 3.1 Create privacy.html — standalone privacy policy (data collection, hashes only, 10-year retention, contact@mpps.io)
- [ ] 3.2 Create terms.html — standalone terms of service (attestation only, not legal certification, limitation of liability)

## 4. Website — Verification Page

- [ ] 4.1 Create verify.html — template page that displays attestation details (uuid, timestamp, hash, agent_id, signature, storage info)
- [ ] 4.2 Include "Download Receipt (JSON)" button and "Verify Offline" instructions link

## 5. GitHub — Documentation

- [ ] 5.1 Write README.md — project overview, quick start code, three principles, architecture summary, pricing, links
- [ ] 5.2 Write PROTOCOL.md — MAP (Machine Attestation Protocol) specification: request/response format, UUID structure, signature scheme
- [ ] 5.3 Write ARCHITECTURE.md — five-layer trust chain: identity anchor, temporal consensus, hardware signing, immutable storage, public verification
- [ ] 5.4 Write SECURITY.md — security model, threat analysis, what we store/don't store, disclaimers
- [ ] 5.5 Write docs/api.md — API reference for POST /v1/notarize and GET /v1/verify/{uuid}
- [ ] 5.6 Write docs/verify.md — offline verification guide with OpenSSL commands

## 6. SDK & Tools

- [ ] 6.1 Create sdk/mpps.py — Python SDK with notarize() and verify() functions, receipt dataclass
- [ ] 6.2 Create verifier/verifier.py — CLI tool that validates receipt JSON against public key offline
- [ ] 6.3 Create verifier/README.md — usage instructions for the CLI verifier

## 7. Deploy & Verify

- [ ] 7.1 Deploy all website files to server via scp
- [ ] 7.2 Push all repo content to gdlg-ai/mpps.io on GitHub
- [ ] 7.3 Smoke test: visit https://mpps.io, /privacy, /terms, /verify/demo
- [ ] 7.4 Smoke test: verify GitHub README renders correctly
