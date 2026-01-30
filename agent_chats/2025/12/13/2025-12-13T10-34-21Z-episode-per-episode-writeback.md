---
id: 2025-12-13T10-34-21Z-episode-per-episode-writeback
date: 2025-12-13T10:34:21Z
participants: [human, codex]
models: [gpt-5.2]
tags: [backend, episode, celery, langgraph, prompts]
related_paths:
  - ai-pic-backend/app/api/v1/endpoints/episodes.py
  - ai-pic-backend/app/services/ai_service.py
  - ai-pic-backend/app/services/episode_agent.py
  - ai-pic-backend/app/prompts/templates/episode_step_outline.txt
  - ai-pic-backend/tests/unit/test_episode_agent_callbacks.py
summary: "异步剧集生成按集校验并逐集落库；大纲校验通过即写入故事信息并展示；任务进度细化到每集。"
---

## User Prompt

用户反馈：ai-video-celery-worker 已经生成到第 11 集，但 `http://localhost:8089/stories/21` 看不到任何剧集/剧集规划；任务状态也一直停在“准备调用模型”。要求：

1. 剧集大纲校验通过后立即写库到故事信息并展示；
2. 每一集生成后校验通过就逐集写库；
3. 任务列表展示更细的节点进度（生成第几集/校验第几集/已落库）；
4. 在 Docker 环境 `http://localhost:8089/` 用 Chrome 做端到端验证。

## Goals

- 让异步流程在生成过程中可见产物：大纲与剧集逐步落库。
- 让任务进度能反映 agent 的真实执行节点（按集粒度）。
- 简化大纲阶段：每集 1 句概要，包含起承转合与钩子；后续细节交给分集生成。
- 在每集生成提示词中带上“前序集概要列表 + 角色”，保证连贯性。

## Changes

- `ai-pic-backend/app/services/episode_agent.py`：新增 `EpisodeGenerationCallbacks`（on_progress/on_outline/on_episode），在 LangGraph 分集循环中逐集触发回调；每集生成后做 schema+轻量校验，不通过则基于 outline 兜底，避免“跑完无产物”。
- `ai-pic-backend/app/services/ai_service.py`：`generate_episodes` 透传 callbacks 给 `EpisodeLangGraphAgent.generate`，便于 Celery worker 逐步落库与更新任务进度。
- `ai-pic-backend/app/api/v1/endpoints/episodes.py`：异步任务 `_process_episode_generation_task` 使用 callbacks：
  - 大纲校验通过立即写入 `Story.extra_metadata.episode_step_outlines` 并更新任务描述；
  - 每集生成后立即插入 `Episode`（逐集 commit），并将任务描述更新为“生成第N集：已落库”；
  - 修复 JSON 列就地修改不触发脏写的问题：写入大纲时改为拷贝 dict 再赋值。
- `ai-pic-backend/app/prompts/templates/episode_step_outline.txt`：强化“一集一句话 logline”要求，并建议同一句内包含“起承转合 + 钩子”。
- `ai-pic-backend/tests/unit/test_episode_agent_callbacks.py`：新增单测覆盖 callbacks 触发、outline 兜底、以及提示词包含重点角色。

## Validation

- Backend lint/format：
  - `cd ai-pic-backend && ruff check app/services/ai_service.py app/services/episode_agent.py app/api/v1/endpoints/episodes.py tests/unit/test_episode_agent_callbacks.py`
  - `cd ai-pic-backend && black --check app/services/ai_service.py app/services/episode_agent.py app/api/v1/endpoints/episodes.py tests/unit/test_episode_agent_callbacks.py`
- Backend tests（与本改动强相关的单测）：
  - `cd ai-pic-backend && pytest -q tests/unit/test_episode_agent_callbacks.py tests/unit/test_episode_step_outline_light.py`
- Chrome E2E（Docker / Nginx）：
  - 访问 `http://localhost:8089/`，使用测试账号 `geyunfei` 登录（密码未记录）。
  - 打开 `http://localhost:8089/stories/22`，异步生成剧集（集数=12）。
  - 在 `http://localhost:8089/tasks` 观察到任务进度按集推进（例如“生成第8集：调用模型/生成第11集：调用模型”），最终显示“剧集生成完成：共写入 2 集”。
  - 回到 story 页刷新后确认：
    - “剧集大纲”从 3 集更新为 12 集（大纲校验通过即写库展示，且 logline 含起承转合+钩子）。
    - “剧集概览”从 10 集增长为 12 集（第 11、12 集在任务未结束前即已落库可见）。
  - 额外核验：`http://localhost:8089/stories/21` 已可看到已写入的剧集列表。

注：本机 Python 3.13 环境下执行全量 `pytest` 存在大量与本次改动无关的既有失败；本次仅确保相关单测与格式检查通过，并以 Docker + Chrome E2E 验证主流程。

## Next Steps

- 可选优化：对于已存在的 Episode，避免重复调用 LLM 生成（仅生成缺失集数），减少成本与时延。
- 可选增强：对单集输出增加“修复重试”节点（类似 outline repair），进一步降低兜底占比。
- 在 CI/本地使用 Python 3.11 环境跑全量测试，解决依赖在 3.13 下的兼容问题（例如 psycopg wheels）。

## Linked Commits

- TBD
