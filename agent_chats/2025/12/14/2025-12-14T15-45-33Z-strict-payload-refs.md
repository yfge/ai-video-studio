---
id: 2025-12-14T15-45-33Z-strict-payload-refs
date: 2025-12-14T15:45:33Z
participants: [human, codex]
models: [gpt-4o]
tags: [backend, storyboard, reference-images]
related_paths:
  - ai-pic-backend/app/api/v1/endpoints/scripts.py
summary: "Use only user-provided references when generating storyboard frames"
---
## User Prompt
- 用户传 3 张参考图生成分镜图像，却被处理成 4 张（额外带上环境默认图）。

## Goals
- 当请求 body.reference_images 非空时，生成阶段只使用用户提供的参考图，不自动附加帧/角色/环境参考图，避免数量被放大。

## Changes
- 在分镜图像生成中，若 payload_refs 存在则仅用 payload_refs 作为参考图；否则才回退到帧内参考图、角色锚点、环境参考图的组合后过滤去重。（`_normalize_reference_images` 仍保证 URL 合法性。）

## Validation
- `pytest tests/test_tasks_minimal.py -q`。

## Next Steps
- 线上再用同一请求复现，确认只加载 3 张参考图；如需要在用户未提供参考图时继续自动补齐，现逻辑保持不变。

## Linked Commits
- fix(backend): honor user reference images only
