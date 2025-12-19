---
id: 2025-12-19T12-16-31Z-storyboard-prompt-optimization
date: 2025-12-19T12:16:31Z
participants: [human, codex]
models: [gpt-4o-mini]
tags: [backend, storyboard, prompts]
related_paths:
  - ai-pic-backend/app/api/v1/endpoints/scripts_legacy.py
  - ai-pic-backend/app/prompts/templates.py
  - ai-pic-backend/app/prompts/templates/storyboard_generation.txt
  - ai-pic-backend/app/prompts/templates/storyboard_generation.yaml
  - ai-pic-backend/app/prompts/templates/storyboard_plan.txt
  - ai-pic-backend/app/prompts/templates/storyboard_plan.yaml
  - ai-pic-backend/app/prompts/templates/storyboard_scene.txt
  - ai-pic-backend/app/prompts/templates/storyboard_scene.yaml
  - ai-pic-backend/app/prompts/templates/storyboard_shot.txt
  - ai-pic-backend/app/prompts/templates/storyboard_shot.yaml
  - ai-pic-backend/app/prompts/templates/storyboard_keyframe.txt
  - ai-pic-backend/app/prompts/templates/storyboard_keyframe.yaml
  - ai-pic-backend/app/prompts/templates/storyboard_image_prompt.txt
  - ai-pic-backend/app/prompts/templates/storyboard_image_prompt.yaml
  - ai-pic-backend/app/prompts/templates/storyboard_image_fallback.txt
  - ai-pic-backend/app/prompts/templates/storyboard_image_fallback.yaml
  - ai-pic-backend/app/schemas/generation.py
  - ai-pic-backend/app/services/ai_service.py
  - ai-pic-backend/app/services/audio/timeline_processor.py
  - ai-pic-backend/app/services/dialogue_audio_service.py
  - ai-pic-backend/app/services/storyboard/__init__.py
  - ai-pic-backend/app/services/storyboard/storyboard_prompt_utils.py
summary: "Route storyboard prompts through prompt_manager and normalize storyboard prompts for video/image generation"
---

## User Prompt
只在分镜生成阶段优化提示词，补充运镜/镜头切换与首尾关键帧提示，统一通过 prompt_manager 管理。

## Goals
- Move storyboard generation and keyframe prompt text into prompt_manager templates.
- Normalize storyboard prompts to remove dialogue/system prefixes and add camera/transition cues.
- Ensure audio-timeline storyboard generation and image keyframe prompts use the same normalization.

## Changes
- Added storyboard prompt templates for generation, plan, scene expansion, shot prompts, keyframe prompts, image prompt assembly, and fallback image prompts.
- Switched AIService storyboard generation/plan/scene prompts to prompt_manager templates and JSON strict system prompt.
- Normalized storyboard frames after generation (including audio-timeline paths) and added keyframe prompt fields.
- Updated storyboard image generation to assemble prompts via templates and reuse precomputed keyframe prompts.

## Validation
- `pytest` (ai-pic-backend): timed out after 120s (collected 728 items).
- `./build_prod_images.sh` missing at repo root; ran `./docker/build_prod_images.sh` successfully.
- Chrome MCP: logged in on `http://localhost:8089/`, attempted `http://localhost:8089/stories` and `http://localhost:8089/stories/23` (and `/scripts/30`), pages stayed on loading; console showed API request failures to `http://localhost:8000/api/v1/*`.

## Next Steps
- Investigate why frontend API calls to `localhost:8000` are failing during E2E checks.
- Re-run `pytest` with a longer timeout or targeted tests once backend services are healthy.

## Linked Commits
- (pending)
