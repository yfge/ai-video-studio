---
id: 2026-01-06T11-23-48Z-generation-flow-fixes
date: 2026-01-06T11:23:48Z
participants: [human, codex]
models: [gpt-5]
tags: [backend, e2e, bugfix]
related_paths:
  - ai-pic-backend/app/api/v1/endpoints/scripts_legacy.py
  - ai-pic-backend/app/services/providers/openai_provider/image.py
summary: "Unblocked script regeneration and DALL-E 3 image counts after full generation flow tests"
---

## User Prompt
Run Chrome end-to-end generation on http://localhost:8089 and fix any errors encountered.

## Goals
- Complete timeline + storyboard generation flow end-to-end.
- Resolve errors seen during regeneration and image generation.

## Changes
- Apply marketing overrides during script regeneration so regenerated prompts carry the marketing fields.
- Clamp DALL-E 3 image request count to 1 to match API constraints.

## Validation
- Chrome (http://localhost:8089): logged in with test account `geyunfei`, generated timeline for script 71 at `/episodes/80/workspace?tab=timeline&scriptId=71`, ran storyboard batch generation at `/episodes/80/storyboard?scriptId=71`, verified storyboard images and opened `https://resource.lets-gpt.com/ai-generated/storyboard/image/20260106/105307/3ebe8ea3.png`.
- `./docker/build_prod_images.sh` (completed; Next build emitted ESLint warnings about unused vars and `<img>` usage).
- `pytest` in `ai-pic-backend` (failed: 89 failed, 13 errors; missing fixtures in `tests/e2e/test_user_management_e2e.py` plus multiple integration/API failures).

## Next Steps
- Decide whether to address failing pytest suite or allow commit with current failures.
- Investigate Keling provider 400 responses observed during generation (fallback succeeded).

## Linked Commits
- Pending.
