---
id: 2025-12-13T08-15-00Z-episode-validation
date: 2025-12-13T08:15:00Z
participants: [human, codex]
models: [gpt-4o-mini]
tags: [backend, episode, validation]
related_paths:
  - ai-pic-backend/app/services/episode_agent.py
  - ai-pic-backend/tests/unit/test_episode_step_outline_light.py
summary: "Added post-generation episode sanity checks and updated tests."
---

## User Prompt
对剧集的规范性检查是不是应该在每一集生成以后做？

## Goals
- 在每集生成后做轻量规范检查，避免不完整的剧集落库。

## Changes
- `EpisodeLangGraphAgent` 增加 `_is_episode_valid`：校验 summary 和 conflicts 存在（并为 list），无效时记录 reasoning 并跳过该集。
- 单测更新为包含 conflicts，覆盖校验通过场景（logline-only/repair）。

## Validation
- `pytest tests/unit/test_episode_step_outline_light.py` ✅

## Next Steps
- 在端到端生成中观察是否有剧集被过滤；如需更严格规则或重试机制，再按需增强。

## Linked Commits
- TODO: add commit hash after commit
