---
id: 2025-12-11T14-45-00Z-celery-agent-run-persistence
date: 2025-12-11T14:45:00Z
participants: [human, codex]
models: [gpt-5.1]
tags: [backend, tasks, celery]
related_paths:
  - ai-pic-backend/app/core/celery_app.py
  - ai-pic-backend/app/services/task_worker.py
  - ai-pic-backend/app/api/v1/endpoints/stories.py
  - ai-pic-backend/app/api/v1/endpoints/episodes.py
  - ai-pic-backend/app/api/v1/endpoints/scripts.py
  - ai-pic-backend/tests/conftest.py
  - ai-pic-backend/tests/test_api.py
  - ai-pic-backend/TESTING_GUIDE.md
  - docker/docker-compose.prod.yml
  - tasks.md
summary: "接入 Celery 任务队列并为 Story/Episode/Script 落库 agent_run 元信息"
---

## User Prompt

后端需要把任务管理从 FastAPI `BackgroundTasks` 升级为 Celery 队列：  
- 为故事/剧集/剧本生成(`/generate-async`)接入统一任务队列与独立 worker；  
- 让 LangGraph Agents 每一次执行的输入/输出（模型、provider、usage、reasoning 等）在实体和任务层都能落库追踪；  
- 更新生产 `docker-compose.prod` 与测试文档，保证本地/生产环境都能稳定跑异步任务。

## Goals

- 引入集中管理的 Celery 应用与 worker 入口，复用现有 Task 表做异步调度。  
- 将 Story/Episode/Script 的同步与异步生成路径统一写入 `extra_metadata.agent_run`。  
- 调整部分 API 测试以匹配新的响应结构，同时新增对 agent_run 持久化的最小集成校验。  
- 在生产 docker-compose 中增加独立 Celery worker 服务，并在测试文档中说明本地运行方式。  
- 在任务看板 `tasks.md` 上同步该特性的阶段性进展。

## Changes

- 新增 `app/core/celery_app.py`，基于 `settings.REDIS_URL` 创建全局 `celery_app`，统一配置 JSON 序列化、时区和 worker 进程回收策略。  
- 新增 `app/services/task_worker.py`，定义 `story_generate_task` / `episode_generate_task` / `script_generate_task` 三个 Celery 任务，内部按需导入对应 endpoint 中的 `_process_*_generation_task`，避免循环依赖。  
- 在 `app/api/v1/endpoints/stories.py` 中：  
  - 为同步 `/stories/generate` 生成路径组装 `agent_run` 字段，并写入 Story 的 `extra_metadata.agent_run`；  
  - 保持异步 `_process_story_generation_task` 的 agent_run 写入逻辑；  
  - `/stories/generate-async` 改为调用 `story_generate_task.delay(...)`，真正由 Celery worker 执行。  
- 在 `app/api/v1/endpoints/episodes.py` 中：  
  - 同步 `/episodes/generate` 为每一集的 `extra_metadata.agent_run` 写入当前 AI 调用信息；  
  - 异步 `_process_episode_generation_task` 继续在创建 Episode 时写入 `extra_metadata.agent_run`；  
  - `/episodes/generate-async` 改为通过 `episode_generate_task.delay(...)` 进入 Celery 队列；  
  - `regenerate_episode` 新增 agent_run 采集并回写到 `episode.extra_metadata.agent_run`。  
- 在 `app/api/v1/endpoints/scripts.py` 中：  
  - 同步 `/scripts/generate` 为生成的 Script 写入 `extra_metadata.agent_run`；  
  - 异步 `_process_script_generation_task` 在 Script `extra_metadata.agent_run` 中落库 agent 运行信息；  
  - `regenerate_script` 在重新生成内容时同样更新 `extra_metadata.agent_run`；  
  - `/scripts/generate-async` 切换为 `script_generate_task.delay(...)`。  
- 更新测试基座 `tests/conftest.py`：  
  - `mock_ai_service` 现在同时覆盖 service 模块和 stories/episodes/scripts 三个 endpoint 模块中的 `ai_service` 引用；  
  - 调整 `generate_episodes` 的 mock payload，使 `conflicts` 变为符合 `EpisodeResponse` 期望的字典列表。  
- 调整 `tests/test_api.py` 中与 AI 生成相关的几个用例：  
  - 将 `/stories/generate`、`/episodes/generate`、`/scripts/generate` 的请求体更新为新的 Pydantic 请求模型字段；  
  - 更新断言以匹配当前 API 响应结构（Story 返回 `{success, data}`，Episode 返回列表，Script 返回单体对象）；  
  - 在这三个测试中新增对 `extra_metadata.agent_run` 存在性的检查，确保 agent 运行信息已写入实体。  
- 在 `ai-pic-backend/TESTING_GUIDE.md` 中新增“异步任务与 Celery Worker”章节，说明本地启动 Celery worker 的命令以及与 `/generate-async` 的关系。  
- 更新 `docker/docker-compose.prod.yml`：  
  - 新增 `ai-video-celery-worker` 服务，复用 backend 镜像与 `.env`，在 `/app/ai-pic-backend` 下以 `celery -A app.core.celery_app.celery_app worker -l info` 启动；  
  - 保持与 `ai-video-backend`、`ai-video-redis` 的依赖顺序。  
- 更新 `tasks.md` 中“Feature: 任务队列与 Agent 执行落库（高优）”部分：  
  - 标记 Celery app / task_worker / `ai-video-celery-worker` 服务为已完成；  
  - 新增一条进度项说明 Story/Episode/Script 的 `extra_metadata.agent_run` 已经覆盖同步与异步生成路径；  
  - 保留 `Task.parameters.agent_run` 和图像任务队列改造为后续待办。

## Validation

- 安装 Celery 运行时依赖：  
  - 在本地 Python 环境中执行 `pip install celery==5.3.4`，以满足 `app/core/celery_app.py` 的导入需求。  
- 目标化后端测试：  
  - 运行 `pytest tests/test_api.py::TestStoryAPI::test_generate_story_outline`，验证故事概要生成接口在使用 mock AI 的情况下正确返回数据并写入 `extra_metadata.agent_run`。  
  - 运行 `pytest tests/test_api.py::TestEpisodeAPI::test_generate_episodes`，确认剧集批量生成返回 Episode 列表且每条记录包含 `extra_metadata.agent_run`。  
  - 运行 `pytest tests/test_api.py::TestScriptAPI::test_generate_script`，确认剧本生成返回 Script 对象且附带 `extra_metadata.agent_run`。  
- 目前完整的 `tests/test_api.py` 仍有若干历史用例与改造后的 API 不匹配（如 Virtual IP 与老式响应包装），本次未一并重构，需后续单独清理。  
- 本轮未执行基于 Chrome MCP/DevTools 的端到端 UI 自测（本次改动聚焦后端任务队列与持久化逻辑），建议后续在任务列表/故事生成页面补一条真实浏览器路径验证。

## Next Steps

- 将 Task 层的 `parameters` JSON 补充 `agent_run` 摘要，使任务管理页在不查实体表的情况下也能看到 provider/model/usage/reasoning。  
- 为虚拟 IP 图像、环境图像和分镜图像生成统一接入 Celery 任务队列，收敛日志与错误处理逻辑。  
- 为 Story/Episode/Script/图像任务补整体集成测试（任务创建 → Celery handler 执行 → Task 更新 + 实体落库校验）。  
- 前端 `/tasks` 页面接入 `task_type` 过滤并展示 agent_run 关键字段，配合诊断 API 做任务可视化。  
- 后续清理 `tests/test_api.py` 中针对老响应结构的断言，使整套 API 集成测试重新绿灯。

## Linked Commits

- (pending — 将在本次代码变更合并时由人工补充具体 commit hash)

