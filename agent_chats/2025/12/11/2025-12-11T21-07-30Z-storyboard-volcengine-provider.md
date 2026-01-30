---
id: 2025-12-11T21-07-30Z-storyboard-volcengine-provider
date: 2025-12-11T21:07:30Z
participants: [human, codex]
models: [gpt-4o-mini]
tags: [backend, ai]
related_paths:
  - ai-pic-backend/app/utils/model_utils.py
  - ai-pic-backend/app/api/v1/endpoints/story_structure.py
  - ai-pic-backend/app/services/ai_service_manager.py
summary: "Map doubao/seedream model ids to volcengine so storyboard img2img uses correct provider"
---

## User Prompt

然后分镜的图生图火山引擎也不对

## Goals

- Ensure Seedream/doubao img2img flows (including storyboard) route to Volcengine provider so reference images are honored.

## Changes

- Expanded provider inference to treat `doubao-*`/`seedream` model ids as Volcengine across model_utils, environment helper, and AI service fallback.

## Validation

- Not run (pending Volcengine environment); logic-level change only.

## Next Steps

- [ ] Re-run storyboard/environment/IP img2img with doubao/Seedream models to confirm Volcengine is selected and reference images are applied.

## Linked Commits

- (pending)
