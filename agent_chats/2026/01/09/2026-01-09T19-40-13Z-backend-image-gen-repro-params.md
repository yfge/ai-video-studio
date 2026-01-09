---
id: 2026-01-09T19-40-13Z-backend-image-gen-repro-params
date: "2026-01-09T19:40:13Z"
participants: [human, codex]
models: [gpt-5.2]
tags: [backend, image-gen, quality, reproducibility]
related_paths:
  - ai-pic-backend/app/services/image_gen/types.py
  - ai-pic-backend/app/services/image_gen/normalize.py
  - ai-pic-backend/app/services/image_gen/provider_params.py
  - ai-pic-backend/app/services/image_gen/coerce.py
  - ai-pic-backend/app/services/ai/images_generation.py
  - ai-pic-backend/app/services/virtual_ip/image_variant_service.py
  - ai-pic-backend/app/services/story_structure/environment_image_requests.py
  - ai-pic-backend/app/services/story_structure/environment_image_generation.py
  - ai-pic-backend/app/services/storyboard/storyboard_image_generation.py
  - ai-pic-backend/app/services/task_worker.py
  - ai-pic-backend/app/api/v1/endpoints/virtual_ip_images/generation.py
  - ai-pic-backend/app/api/v1/endpoints/virtual_ip_images/generation_helpers.py
  - ai-pic-backend/app/api/v1/endpoints/virtual_ip_images/variants.py
  - ai-pic-backend/app/api/v1/endpoints/virtual_ip_images/async_tasks.py
  - ai-pic-backend/app/api/v1/endpoints/virtual_ip_images/async_variant_task.py
  - ai-pic-backend/app/api/v1/endpoints/story_structure/environment_generation.py
  - ai-pic-backend/app/api/v1/endpoints/story_structure/environment_variants.py
  - ai-pic-backend/app/api/v1/endpoints/scripts_legacy.py
  - ai-pic-backend/tests/unit/test_image_gen_repro_params.py
  - docs/design/image-generation-unification.md
summary: "贯通 seed/steps/cfg_scale/negative_prompt/strength 到统一图像生成归一化层，提高质量一致性与可复现性"
---

## User Prompt

继续 Phase 2，先做后端：把虚拟 IP 图生图、环境文生图/图生图、分镜图生图统一梳理，并继续提升图片生成“质量一致性”（可控参数统一、可复现、可审计）。

## Goals

- 在后端统一支持 `seed/steps/cfg_scale/negative_prompt/strength`，让不同 domain 的图像生成行为更可控、更可复现。
- 通过 provider 白名单映射，确保参数安全透传，避免“未知字段”导致不确定行为。
- 在 Task.parameters 与落库/元数据中记录关键参数，便于问题回放与质量迭代。
- 增加单测覆盖归一化与 provider 过滤。

## Changes

- 扩展统一归一化层：`ImageGenRequest/ImageGenNormalized` 新增 `seed/steps/cfg_scale/negative_prompt/strength`，并在 `normalize_image_gen_request()` 中完成类型转换与范围约束。
- Provider 参数透传：`build_ai_manager_call()` 统一注入这些字段，再按 provider 白名单过滤（例如 Keling 保留 `negative_prompt`，Jimeng 支持 `steps/cfg_scale/seed/strength`）。
- Virtual IP 文生图：API/worker 支持新字段；调用 `ai_service.generate_virtual_ip_image()` 透传到归一化层；生成参数落库/Task.parameters 记录这些字段。
- Virtual IP 图生图（variants）：API/worker 支持新字段（含 `strength`）；统一透传与落库记录。
- 环境文生图/图生图：API/worker 支持新字段；落库到 `Environment.extra_metadata` 的 last_generation 信息中。
- 分镜图像生成：`StoryboardImageRequest` 增加新字段；task payload → worker → `_process_storyboard_image_task` → `generate_storyboard_image_urls` 全链路透传；返回 `image_gen` meta 增加这些字段。
- 新增单测：覆盖参数归一化、clamp/drop 行为与 provider 过滤结果。
- 更新设计文档：补齐 Phase 5 与参数字段说明。

## Validation

- `cd ai-pic-backend && pytest tests/unit/test_image_gen_repro_params.py -q`
- `pre-commit run`
- `./docker/build_prod_images.sh`
- Chrome E2E（Docker dev 环境，重启 `ai-video-backend`/`ai-video-celery-worker`/`ai-video-celery-beat` 后验证）：
  - Virtual IP 文生图：调用 `POST http://localhost:8000/api/v1/virtual-ips/1/images/generate-async` 创建 Task `548`，Task.parameters 含 `seed=123/steps=28/cfg_scale=7.5/negative_prompt`。
  - 环境文生图：调用 `POST http://localhost:8000/api/v1/story-structure/environments/1/images/generate-async` 创建 Task `549`，Task.parameters 含 `seed=456/steps=30/cfg_scale=7/negative_prompt`。
  - 分镜图像生成：调用 `POST http://localhost:8000/api/v1/scripts/15/storyboard/generate-images` 创建 Task `550`，Task.parameters 含 `seed=789/steps=32/cfg_scale=7.5/negative_prompt/strength=0.7`。
  - 前端页面 `http://localhost:8089/tasks` 中点击“详情”可看到以上字段已展示并与后端返回一致。

## Next Steps

- 为不同 provider/model 提供“推荐质量参数 preset”（例如 steps/cfg/negative_prompt 模板片段），并在前端统一控件与默认策略。
- 扩展 provider 支持矩阵（例如 Volcengine/Google 的 image params），并将“provider 不支持字段”的丢弃情况写入 audit。
- 将关键参数与 `prompt_template` 一起纳入统一的 `image_gen` 元数据 schema，便于后续质量评分/门禁接入。

## Linked Commits

- (pending) feat(backend): unify image-gen reproducibility params
