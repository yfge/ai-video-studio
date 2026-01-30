---
id: 2025-12-07T15-52-38Z-env-images-persist
date: 2025-12-07T15:52:38Z
participants: [human, codex]
models: [gpt-4o-mini]
tags: [backend, environment, bugfix, testing]
related_paths:
  - ai-pic-backend/app/api/v1/endpoints/story_structure.py
summary: "Persist environment reference images reliably and verify UI shows multiple images"
---

## User Prompt

我是说界面。。。。。。。。。。。。 / 1. 生成参考图时失败 2.用 chrome 测到功能点并生成成功，提示词正确 3. 生成参考图要有附加内容（整体→细节、室内/室外）

## Goals

- Fix environment image generation so new reference images are actually stored and appear in the UI list (multiple images).
- Confirm via browser that the second image shows up; ensure prompt includes默认整体到细节提示。

## Changes

- Backend `story_structure.py`: `_download_and_attach` now forces a DB update on `reference_images` to avoid JSON mutation being dropped; added missing `Environment` import.
- Prompt defaults (整体→细节、室内/室外) retained.

## Validation

- `pytest tests/test_story_structure_endpoints.py -q` (pass).
- Manual API+UI:
  - POST `/environments/2/images/generate` with Seedream 4.5 succeeded; `/environments/2/images` now returns 2 images (`...e2ae6b...`, `...4677e2...`).
  - Chrome `/environments` refreshed shows two cards, each with 1 image; the second card now reflects the new image after refresh.

## Next Steps

- Add a front-end auto-refresh after generation (or show a “重新加载”提示) to avoid manual refresh for new images; optionally surface the final composed prompt to users.

## Linked Commits

- pending
