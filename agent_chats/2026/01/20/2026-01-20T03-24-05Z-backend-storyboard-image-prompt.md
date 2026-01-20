---
id: 2026-01-20T03-24-05Z-backend-storyboard-image-prompt
date: 2026-01-20T03:24:05Z
participants: [human, codex]
models: [gpt-5.2]
tags: [backend, prompts, providers, image]
related_paths:
  - ai-pic-backend/app/services/providers/google_provider/helpers.py
  - ai-pic-backend/app/prompts/templates/fragments/image_macros.txt
  - ai-pic-backend/app/prompts/templates/storyboard_image_prompt.txt
  - ai-pic-backend/tests/unit/test_google_provider_image.py
summary: "Prevented storyboard image collages/labels and forced image-only modality for Google image generation."
---

## User Prompt

- 全局检查文生图/图生图提示词规范，确保跨 provider 语义一致，并可按 provider 进一步优化。
- 做短剧全流程测试：生文 deepseek-chat、生图 Google Image 3.5 preview、生视频 Google Veo；每张图生成后下载检查质量，异常就调整修复。
- 查看 worker 日志，定位生成问题。

## Goals

- 降低分镜生图出现“拼贴/联系表/多帧合成/帧号标签/文字覆盖”的概率。
- Google 图片生成默认只要图片输出，避免 Gemini 返回混合文本/拼贴内容影响下游。

## Changes

- Updated `normalize_response_modalities()` to default to `["IMAGE"]` for image generation.
- Strengthened the shared “no text artifacts” constraint to include captions/labels.
- Reordered storyboard prompt template so constraints are emphasized first, and added an explicit “no contact sheet / no frame labels” rule.
- Updated unit test to match the new Google request payload.

## Validation

- `docker exec ai-video-backend pytest tests/unit/test_google_provider_image.py -q`
- `./docker/build_prod_images.sh`
- Chrome MCP E2E:
  - Opened storyboard workspace and verified generated frames from `google:gemini-3-pro-image-preview` are single-frame images (no collage/contact sheet, no frame labels, no text overlays) by opening the image URLs in browser and visually inspecting them.

## Next Steps

- Handle Google Veo `429 RESOURCE_EXHAUSTED` more gracefully (clear UI error + retry/backoff strategy) so video E2E is not blocked by quota/rate-limit.
- Extend provider-aware prompt/schema validation so UI inputs and backend templates align with each provider’s supported parameters.
- Update `tasks.md` to reflect the above work items and remaining blockers.

## Linked Commits

- (pending) fix(backend): prevent storyboard image collages and enforce Google image-only modality
