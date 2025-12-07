---
id: 2025-12-07T13-15-00Z-episode-prompt-scenes
date: 2025-12-07T13:15:00Z
participants: [human, codex]
models: [gpt-4o-mini]
tags: [backend, prompts]
related_paths:
  - ai-pic-backend/app/prompts/templates/episode_generation.txt
  - ai-pic-backend/app/prompts/templates/episode_generation.yaml
summary: "Episode generation prompt now explicitly requests scenes array"
---

## User Prompt

- 生成剧本时还是没有场景信息，需要补齐场景链路。

## Goals

- 强制剧集生成输出 scenes 数组，包含基本场景信息，确保后续分镜/场景展示可用。

## Changes

- Prompt YAML expected fields新增 scenes。
- 文本模板新增“场景拆分”要求，并在输出格式与示例中加入 scenes 列表（scene_number/slug_line/location/time_of_day/summary）。

## Validation

- 未跑自动化；需重新生成剧集验证 scenes 返回。

## Next Steps

- 如仍缺少 scenes，考虑提升提示强度或在生成后回退通过故事梗概自动拆分场景。

## Linked Commits

- (pending)
