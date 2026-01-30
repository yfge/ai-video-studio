---
id: 2025-12-13T10-54-44Z-episode-scene-sanitize
date: 2025-12-13T10:54:44Z
participants: [human, codex]
models: [gpt-5.2]
tags: [backend, episode, validation, scenes, frontend]
related_paths:
  - ai-pic-backend/app/api/v1/endpoints/episodes.py
  - ai-pic-backend/tests/unit/test_episode_scene_fallback.py
summary: "修复 Episode scenes 不稳定：过滤空对象并自动补全占位场景，避免前端仅显示“场景1/2/3”空卡片。"
---

## User Prompt

`http://localhost:8089/episodes/21` 的场景列表不稳定，怀疑“每一集生成后的检查”仍有问题。

## Goals

- 识别并修复 `Episode.extra_metadata.scenes` 为空对象数组（`[{},{},...]`）导致的前端不稳定展示。
- 让落库前的场景结构至少包含稳定字段（scene_number/slug_line/summary/location/time_of_day），并与 scene_count 对齐。
- 增加单测覆盖该回归场景。

## Changes

- `ai-pic-backend/app/api/v1/endpoints/episodes.py`
  - 强化 `_ensure_scenes`：当模型返回 `scenes=[{}, {}, ...]` 或场景条目缺失关键字段时，过滤无效对象并基于 `plot_points/summary` 自动补全可用场景。
  - 若请求里带了 `scene_count`，则对齐场景数量（不足补齐、超出截断），并统一 `scene_number`，避免前端展示抖动。
- `ai-pic-backend/tests/unit/test_episode_scene_fallback.py`
  - 新增单测：输入 `scenes=[{},…]` + `scene_count` 时，输出为带关键字段的场景列表且数量对齐。

## Validation

- `cd ai-pic-backend && ruff check app/api/v1/endpoints/episodes.py tests/unit/test_episode_scene_fallback.py`
- `cd ai-pic-backend && black --check app/api/v1/endpoints/episodes.py tests/unit/test_episode_scene_fallback.py`
- `cd ai-pic-backend && pytest -q tests/unit/test_episode_scene_fallback.py`
- Chrome E2E（Docker / Nginx）：
  - 访问 `http://localhost:8089/episodes/21`，确认此前场景为无内容空对象数组（仅显示“场景1/2/3…”）。
  - 重启后端容器使修复生效；调用 `POST /api/v1/episodes/21/regenerate` 后刷新页面，场景列表稳定展示 `slug_line/summary/location/time_of_day`。

## Next Steps

- 对历史数据的批量修复可考虑提供显式“修复场景”脚本/接口（避免 GET 产生副作用）。
- 进一步收紧 LLM 输出 schema（为 scenes 定义结构化模型）可减少出现空对象的概率。

## Linked Commits

- TBD
