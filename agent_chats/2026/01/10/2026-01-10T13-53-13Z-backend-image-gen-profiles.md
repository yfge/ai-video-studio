---
id: 2026-01-10T13-53-13Z-backend-image-gen-profiles
date: "2026-01-10T13:53:13Z"
participants: [human, codex]
models: [gpt-5.2]
tags: [backend, image-gen, quality]
related_paths:
  - ai-pic-backend/app/services/image_gen/profiles.py
  - ai-pic-backend/app/services/image_gen/normalize.py
  - ai-pic-backend/app/services/image_gen/types.py
  - ai-pic-backend/app/api/v1/endpoints/image_gen_profiles.py
  - ai-pic-backend/app/schemas/image_gen_profiles.py
  - ai-pic-backend/app/api/v1/api.py
  - ai-pic-backend/app/api/v1/endpoints/virtual_ip_images/generation.py
  - ai-pic-backend/app/api/v1/endpoints/virtual_ip_images/generation_helpers.py
  - ai-pic-backend/app/api/v1/endpoints/virtual_ip_images/variants.py
  - ai-pic-backend/app/api/v1/endpoints/virtual_ip_images/async_tasks.py
  - ai-pic-backend/app/services/ai/images_generation.py
  - ai-pic-backend/app/services/virtual_ip/image_variant_service.py
  - ai-pic-backend/app/api/v1/endpoints/story_structure/environment_generation.py
  - ai-pic-backend/app/api/v1/endpoints/story_structure/environment_variants.py
  - ai-pic-backend/app/services/story_structure/environment_image_requests.py
  - ai-pic-backend/app/services/story_structure/environment_image_generation.py
  - ai-pic-backend/app/services/storyboard/storyboard_image_generation.py
  - ai-pic-backend/app/api/v1/endpoints/scripts_legacy.py
  - ai-pic-backend/app/services/task_worker.py
  - ai-pic-backend/tests/unit/services/image_gen/test_normalize.py
  - ai-pic-backend/tests/unit/test_image_gen_repro_params.py
  - docs/design/image-generation-unification.md
  - tasks.md
summary: "Introduce generation_profile presets for consistent image-gen quality and expose a profiles API"
---

## User Prompt

后端引入“生成参数 preset/profile”（按 provider+model 给默认 steps/cfg_scale/negative_prompt），并让前端统一选择与展示（不再散落在各页面表单）；先做后端。

## Goals

- 在后端建立可扩展的 image-gen profile registry（provider+model+mode → defaults）
- 统一归一化层应用 defaults，提升“质量一致性”
- 提供 profiles 查询 API，供前端统一选择与展示
- 让 Virtual IP / Environment / Storyboard 入口支持透传 `generation_profile` 并记录到元数据

## Changes

- 新增 `ai-pic-backend/app/services/image_gen/profiles.py`：定义 profiles（jimeng/keling 初版）与默认 negative_prompt
- 扩展 `ImageGenRequest/ImageGenNormalized` 增加 `generation_profile`，并在 `normalize_image_gen_request()` 内按 profile 填充缺省 `steps/cfg_scale/negative_prompt`
- 新增 profiles API：`ai-pic-backend/app/api/v1/endpoints/image_gen_profiles.py`（`GET /api/v1/image-gen/profiles`）
- Virtual IP（文生图/图生图）、Environment（文生图/图生图）、Storyboard（generate-images）入口增加 `generation_profile` 透传与元数据记录
- 更新测试：覆盖 jimeng 默认/quality/unknown profile 行为；调整 jimeng img2img invalid steps/cfg 回退为 profile defaults
- 更新文档与任务看板：补充 Phase 6 与 profile 说明

## Validation

- `cd ai-pic-backend && pytest -q tests/unit/services/image_gen/test_normalize.py`
- `cd ai-pic-backend && pytest -q tests/unit/test_image_gen_repro_params.py`
- Chrome (MCP)：
  - 使用测试账号登录前端（`geyunfei`）
  - 调用 `GET /api/v1/image-gen/profiles` 验证：
    - `model=jimeng:jimeng-sdxl` 返回 `balanced/quality/fast`
    - `model=keling:kling-image-v2` 返回 `balanced`（negative_prompt defaults）
    - `model=volcengine:doubao-seedream-4-5-251128` 返回空 profiles
  - 调用 `POST /api/v1/virtual-ips/1/images/generate`（Seedream 4.5）并传 `generation_profile=quality`：
    - 生成成功（返回 OSS URL）
    - `generation_params` 中不包含 `generation_profile`（unsupported provider 时忽略）

## Next Steps

- 前端：新增统一的 profile 选择组件（按 model+mode 拉取 `/api/v1/image-gen/profiles`），并在 Virtual IP / Environment / Storyboard 入口复用；payload 仅传 `generation_profile`（不再散落 steps/cfg/negative_prompt 表单）
- 继续扩展 profiles registry：补齐 Seedream/Keling/更多模型族的 defaults（或明确返回空 profiles）

## Linked Commits

- (pending)
