---
id: 2026-01-09T11-04-05Z-image-gen-normalization-phase3-environment
date: "2026-01-09T11:04:05Z"
participants: [human, codex]
models: [gpt-5.2]
tags: [backend, image, refactor]
related_paths:
  - ai-pic-backend/app/api/v1/endpoints/story_structure/async_tasks.py
  - ai-pic-backend/app/api/v1/endpoints/story_structure/environment_generation.py
  - ai-pic-backend/app/api/v1/endpoints/story_structure/environment_variants.py
  - ai-pic-backend/app/api/v1/endpoints/story_structure/environment_image_helpers.py
  - ai-pic-backend/app/prompts/templates/environment_image.txt
  - ai-pic-backend/app/prompts/templates/environment_image.yaml
  - ai-pic-backend/app/services/story_structure/__init__.py
  - ai-pic-backend/app/services/story_structure/environment_image_generation.py
  - ai-pic-backend/app/services/story_structure/environment_image_prompts.py
  - ai-pic-backend/app/services/story_structure/environment_image_requests.py
  - ai-pic-backend/app/services/story_structure/environment_image_storage.py
  - ai-pic-backend/tests/test_story_structure_endpoints.py
summary: "Phase 3: wire image-gen normalization into Environment txt2img/img2img (sync+async) and unify prompts via PromptManager templates"
---

## User Prompt

用户要求继续 Phase 2/Phase 3：对“虚拟 IP 图生图、环境文生图、环境图生图、分镜图生图”进行统一梳理并落地；并追问为什么没有使用统一提示词管理。

## Goals

- 环境文生图/图生图（sync + async + worker）统一接入 `normalize_image_gen_request` + `build_ai_manager_call`，消除重复的 provider/model/size/aspect_ratio/refs 处理。
- 环境生成提示词使用仓库内的 `prompt_manager` 模板体系（PromptManager），而不是散落在 endpoint 内的字符串拼接。
- 端到端验证：在真实浏览器中跑通环境文生图异步任务与环境图生图异步任务。

## Changes

- 新增环境图像生成 Service 层（`ai-pic-backend/app/services/story_structure/`）：
  - `environment_image_requests.py`：统一从 query/body 解析生成请求并构造 task payload。
  - `environment_image_generation.py`：统一走 image-gen normalization 构建安全参数并调用 `ai_manager.generate_image` / `ai_manager.image_to_image`，并落库 `env.extra_metadata`。
  - `environment_image_storage.py`：集中处理持久化与追加 `Environment.reference_images`。
  - `environment_image_prompts.py`：改为使用 `prompt_manager.render_prompt(PromptTemplate.ENVIRONMENT_IMAGE)` 生成环境图提示词（带防御性 fallback）。
- 更新提示词模板 `environment_image`：
  - `ai-pic-backend/app/prompts/templates/environment_image.txt`：加入 indoor/outdoor focus 分支，补充 tags/description 输出位。
  - `ai-pic-backend/app/prompts/templates/environment_image.yaml`：补充 tags/description 变量元信息与示例。
- 更新环境 endpoint（保持 API 路径不变，变薄为 service 调用）：
  - `environment_generation.py` / `environment_variants.py`：sync/async 都走统一 service；提取出 `environment_image_helpers.py` 以保证 route handler < 50 行。
  - `async_tasks.py`：Celery worker 统一调用同一套 service（anyio.run 执行异步逻辑）。
- 修复测试补丁点：
  - `ai-pic-backend/tests/test_story_structure_endpoints.py`：将 monkeypatch 点对齐到 `environment_variants` 模块级 `ai_service`，确保能捕获 `extra_images` 传递行为。

## Validation

- Backend targeted tests：
  - `cd ai-pic-backend && pytest tests/test_story_structure_endpoints.py::test_environment_variants_pass_reference_images -q`
- Chrome E2E（Docker dev + Nginx，`http://localhost:8089`）：
  1. 重启容器加载新 worker 代码：`docker compose -f docker/docker-compose.dev.yml restart ai-video-backend ai-video-celery-worker`
  2. 登录：`http://localhost:8089/login`（`geyunfei` / `Gyf@845261`）
  3. 打开环境资产并进入测试环境：`/environments` → `模型参数测试环境`
  4. 点击「创建生成任务」提交环境文生图 async：
     - 任务列表出现：`环境文生图 - 环境aab17f172446462a97e738772337d272`
     - 本次环境下游 provider 失败，任务状态为失败（用于验证链路已跑通且无运行时错误）
  5. 在参考图卡片点击「图生图」→「提交图生图任务」：
     - 任务列表出现：`环境图生图 - 环境aab17f172446462a97e738772337d272`，状态完成
     - 回到环境详情页，参考图数量从 9 增加到 10，新增图片路径：`.../ai-generated/environments/image/20260109/110313/...png`

## Next Steps

- Phase 4：将 storyboard 图生图接入同一套归一化层与提示词模板体系，并补齐相同粒度的 Chrome E2E 记录。

## Linked Commits

- TBD
