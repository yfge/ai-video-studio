---
id: 2025-12-05T16-39-25Z-virtualip-content-into-prompts
date: 2025-12-05T16:39:25Z
participants: [human, codex]
models: [gpt-4o-mini]
tags: [backend, prompt]
related_paths:
  - ai-pic-backend/app/api/v1/endpoints/virtual_ip_images.py
  - ai-pic-backend/app/services/ai_service.py
summary: "Make Virtual IP image prompts include all character fields from the Virtual IP page"
---

## User Prompt

http://localhost:8089/virtual-ip 我在这个页面已经写了自己的内容，为啥 AI 的提示词中没有？

## Goals

- Ensure the image-generation prompt actually contains the Virtual IP fields the user edits on the `/virtual-ip` page (简介、背景故事、小传、风格设定).

## Changes

- In `generate_virtual_ip_image` endpoint, aggregate `description`, `background_story`, `biography`, and `style_prompt` from the `VirtualIP` row into a single `aggregated_description` string.
- Pass this aggregated description plus `background_story` into `AIService.generate_virtual_ip_image`, so both the simple English prompt and the IMAGE_GENERATION template have access to full character context.

## Validation

- ai-pic-backend: `cd ai-pic-backend && pytest tests/test_story_structure_endpoints.py -q`

## Next Steps

- Optionally log the final image-generation prompt for easier manual inspection, and extend the image prompt template to also consider tags/style_reference_images if needed.

## Linked Commits

- (pending)
