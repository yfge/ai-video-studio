---
id: 2026-01-29T17-55-41Z-storyboard-character-anchors
date: 2026-01-29T17:55:41Z
participants: [human, codex]
models: [gpt-5]
tags: [backend, storyboard, image-generation]
related_paths:
  - ai-pic-backend/app/api/v1/endpoints/scripts_legacy.py
  - ai-pic-backend/app/services/storyboard/storyboard_character_anchors.py
  - ai-pic-backend/tests/unit/services/storyboard/test_storyboard_character_anchors.py
  - docs/TESTING_GUIDE.md
summary: "Storyboard image generation falls back to Story-registered character anchors via prompt name matching"
---

## User Prompt

在 docker 容器中跑一次全流程，并把分镜图像/视频的生成质量做闭环；剧中人物需要集中管理，分镜图像生成时应自动注入角色锚点参考图。

## Goals

- 让分镜生图在未显式绑定 `shot.character_ids` 时，仍能基于 Story 级角色注册表注入角色参考图（提升一致性）。
- 记录可审计的参考图来源与验证路径（符合 AGENTS 原子提交/ledger 规范）。

## Changes

- 新增 `ai-pic-backend/app/services/storyboard/storyboard_character_anchors.py`：
  - 读取 Story 级注册角色（`story_characters`）的 `virtual_ip_id` 列表。
  - 从 `VirtualIP.name` 解析可匹配的别名片段（如 `短剧E2E女主-林雪-...` -> `林雪`）。
  - 提供 prompt 文本匹配推断角色 ID、以及缺失 `VirtualIPImage` 时的兜底 anchor URL（avatar/style refs）。
- 更新 `ai-pic-backend/app/api/v1/endpoints/scripts_legacy.py`（`_process_storyboard_image_task`）：
  - 构建角色候选集合时，合并 `shot.character_ids` 与 Story 注册角色。
  - 当镜头绑定缺失时，回退为“按 prompt/description 匹配角色名”注入角色参考图（`reference_notes.source=prompt`）。
  - 支持从带前后缀的 `VirtualIP.name` 中匹配到“人类可读名”片段。
- 新增单测 `ai-pic-backend/tests/unit/services/storyboard/test_storyboard_character_anchors.py` 覆盖：
  - Story 注册角色排序/去重
  - prompt 名字匹配（避免子串误命中）
  - alias 提取与 fallback URL 规则
- 更新 `docs/TESTING_GUIDE.md`：补充当 `shot.character_ids` 为空时的 prompt 匹配回退验证预期。

## Validation

- Backend tests:
  - `cd ai-pic-backend && pytest tests/unit tests/services tests/scripts`
- Docker production build:
  - `./docker/build_prod_images.sh`
- Docker/API E2E（Chrome MCP DevTools 当前报错 `Transport closed`，因此用 API + worker logs 记录）：
  - `POST /api/v1/scripts/116/storyboard/generate-images`（task `5881`）带 `prompt="老拐，林雪，..."` 覆盖
  - `ai-video-celery-worker` 日志出现：`[SBIMG] frame refs ... char_anchor=2 total_refs=2`
  - MySQL 校验 `scripts.id=116`：`JSON_LENGTH(extra_metadata->'$.storyboard.frames[0].reference_images') = 2`

## Next Steps

- 落地“未知角色禁止引入”的硬校验/repair：当前样例中 Story 注册角色与分镜 prompt 中角色名不一致会导致 `char_anchor=0`，需要在 story/episode/script 生成阶段做一致性校验与修复。
- 把“角色名/别名”提升为 StoryCharacter 的显式字段并在生成链路强制使用，减少依赖启发式 split/match。
- 完成 P0-3 其余两项：readiness 检查 + 生成后一致性检查（episode→script→timeline→storyboard）。

## Linked Commits

- (pending) feat(backend): storyboard character anchor fallback via story registry

