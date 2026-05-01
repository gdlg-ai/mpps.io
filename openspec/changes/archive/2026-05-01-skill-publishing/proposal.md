## Status

Archived on 2026-05-01 as superseded by `reposition-agent-receipts`. Historical only; the current skill positioning is agent action receipts, not payment-ecosystem distribution.

## Why

mpps.io API is live. mpp.dev PR submitted. Next distribution wave: agent skill ecosystems. Our skill is the simplest on any registry — no API key, no SDK, no registration, one HTTP call. This simplicity IS the differentiator. The /skills page on the website and the SKILL.md must communicate this zero-friction story.

## What Changes

1. Create `/skills` page on mpps.io website — installation + "tell your agent" prompts
2. Create `skills/mpps-attestation/SKILL.md` in repo — the actual skill file
3. Add nav link to /skills on all website pages
4. Submit to ClawHub (PR to openclaw/clawhub)
5. Ensure skills.sh compatibility (SKILL.md in repo root or skills/ dir)

## /skills Page Design

Extreme minimalism. Core message: "No API key. No SDK. One HTTP call."

Sections:
- Hero: "Give your agent provable memory."
- Install: 3 methods (ClawHub, skills.sh, manual)
- Tell your agent: 2-3 prompt templates agents/users can copy
- That's it: Reinforce zero-friction
- Compatibility: Logo-less list of 17+ agents

## SKILL.md Design

```yaml
---
name: mpps-attestation
description: >
  Attest agent actions via mpps.io. Use after any transaction,
  API call, data exchange, or decision to create immutable,
  HSM-signed proof. Free, no auth required.
license: MIT
metadata:
  author: gdlg-ai
  version: "0.4.0"
  homepage: https://mpps.io/skills
compatibility: Network access to api.mpps.io. No API key needed.
---
```

Body: hash → call → done. Bash + Python examples. Verify example. Key facts.

## ClawHub Submission

- PR to github.com/openclaw/clawhub with skills/gdlg-ai/mpps-attestation/SKILL.md
- Or `clawhub publish` from gdlg-ai account
- VirusTotal auto-scan (we have no scripts, no env vars — should pass clean)

## Capabilities

### New Capabilities
- `skill-page`: /skills website page with install commands and agent prompts
- `skill-file`: SKILL.md compatible with ClawHub + skills.sh + Claude Code
- `skill-distribution`: ClawHub submission + skills.sh compatibility

### Modified Capabilities

## Impact

- New page: website/skills.html
- New file: skills/mpps-attestation/SKILL.md (in repo)
- Nav update: all website pages get /skills link
- External PR: openclaw/clawhub (we don't control merge timeline)
