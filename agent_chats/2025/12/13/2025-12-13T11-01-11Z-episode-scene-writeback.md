---
id: 2025-12-13T11-01-11Z-episode-scene-writeback
date: 2025-12-13T11:01:11Z
participants: [human, codex]
models: [gpt-5.2]
tags: [backend, episode, scenes, persistence]
related_paths:
  - ai-pic-backend/app/api/v1/endpoints/episodes.py
  - ai-pic-backend/tests/unit/test_episode_scene_fallback.py
summary: "确保清洗后的 scenes 会写回 payload，从而在 extra_metadata 已含 scenes 字段时也能覆盖无效空对象数组。"
---

## User Prompt

用户指出 `episodes/21` 场景不稳定；已定位到 `extra_metadata.scenes` 可能写入空对象数组（`[{},{},...]`）。

## Goals

- 让 `_ensure_scenes` 的清洗/补全结果真正影响落库：即使原始 payload 已包含 `scenes` 字段，也要覆盖为清洗后的内容。

## Changes

- `ai-pic-backend/app/api/v1/endpoints/episodes.py`
  - `_ensure_scenes` 在返回前写回 `ep_data["scenes"]` 与 `ep_data["scene_count"]`，确保后续由 payload 生成的 `extra_metadata` 使用的是清洗后的 scenes，而不是原始的空对象数组。

## Validation

- `cd ai-pic-backend && ruff check app/api/v1/endpoints/episodes.py`
- `cd ai-pic-backend && black --check app/api/v1/endpoints/episodes.py`
- `cd ai-pic-backend && pytest -q tests/unit/test_episode_scene_fallback.py`
- Chrome E2E：
  - 重启后端容器后重新登录，访问 `http://localhost:8089/episodes/21`，确认场景列表可稳定显示 `slug_line/summary/location/time_of_day`。

## Next Steps

- 考虑将 “写回清洗结果” 抽成独立的 episode normalizer，便于复用与更细粒度的单测覆盖。

## Linked Commits

- TBD

