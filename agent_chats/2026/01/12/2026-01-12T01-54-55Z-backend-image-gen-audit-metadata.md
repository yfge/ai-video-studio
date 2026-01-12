---
id: 2026-01-12T01-54-55Z-backend-image-gen-audit-metadata
date: "2026-01-12T01:54:55Z"
participants: [human, codex]
models: [gpt-5.2]
tags: [backend, image-gen, audit, generation-profile]
related_paths:
  - ai-pic-backend/app/services/image_gen/normalize.py
  - ai-pic-backend/app/services/story_structure/environment_image_generation.py
  - ai-pic-backend/app/services/storyboard/storyboard_image_generation.py
  - ai-pic-backend/app/services/virtual_ip/image_variant_requests.py
  - ai-pic-backend/app/services/virtual_ip/image_variant_service.py
  - ai-pic-backend/app/api/v1/endpoints/virtual_ip_images/async_variant_task.py
  - ai-pic-backend/app/api/v1/endpoints/virtual_ip_images/variants.py
  - ai-pic-backend/tests/unit/services/image_gen/test_keling_img2img_profiles.py
  - ai-pic-backend/tests/unit/services/storyboard/test_storyboard_image_generation.py
summary: "Persist normalized image-to-image fidelity params into environment & virtual IP audit metadata"
---

## User Prompt

- 继续 Phase 2：后端引入“生成参数 preset/profile”，并提升“质量一致性”。
- 把 profile 生效后的关键参数（含 `image_fidelity/human_fidelity`）写入环境 / 虚拟 IP / 分镜的落库元数据，便于审计/复现。
- 重新验证（已充值）。

## Goals

- 将 img2img 场景的“最终生效参数”（profile 默认值 + 用户覆盖 + normalization 纠正）落库到业务对象的元数据中。
- 覆盖环境图生图（Environment）、虚拟 IP 图生图（VirtualIPImage variant）与分镜生成（Storyboard result meta）。
- 保证历史兼容：不要求前端显式传 `image_fidelity/human_fidelity`，只要选 profile 也能落库。

## Changes

- 环境图生图：在 `Environment.extra_metadata.last_image_to_image_generation` 中补齐 `image_reference/image_fidelity/human_fidelity`。
- 分镜图像生成：在 `storyboard_image_generation.generate_storyboard_image_urls()` 返回的 `image_gen` 元数据中补齐 `image_reference/image_fidelity/human_fidelity`。
- 虚拟 IP 图生图：
  - 新增 `image_variant_requests.py` 拆分请求解析与 Celery payload 构造，避免 `image_variant_service.py` 超出 300 行限制。
  - 在 `VirtualIPImage.generation_params` 与 `metadata.image_gen` 中补齐 `image_reference/image_fidelity/human_fidelity`，与 `steps/cfg_scale/strength` 同级。
- Keling v1.5 约束：当 `model=keling:kling-v1-5` 且 img2img 未指定 `image_reference` 时，normalize 默认补齐 `subject`，并记录到 `audit.defaults_applied`。

## Validation

- 后端测试：
  - `cd ai-pic-backend && pytest tests/unit tests/services tests/scripts`
- Chrome 端到端（含参数落库核验）：
  - 登录 `http://localhost:8089/login`（geyunfei）。
  - 环境图生图：环境详情 `http://localhost:8089/environments/aab17f172446462a97e738772337d272`（env_id=7）→ 选择一张参考图点「图生图」→ Provider 选「可灵」→ profile 选「身份优先」→ 提交；任务 `564` 完成后，通过 DevTools `fetch http://localhost:8000/api/v1/story-structure/environments/7` 验证 `last_image_to_image_generation` 已包含 `image_fidelity=0.7`、`human_fidelity=0.6`、`generation_profile=identity`。
  - 虚拟 IP 图生图：虚拟 IP「老拐」详情 `http://localhost:8089/virtual-ip/233525e9045146d580a1d18ef4a28161` → 任选图片点「图生图」→ Provider 选「可灵」→ profile 选「身份优先」→ 提交；任务 `565` 完成后，通过 DevTools `fetch http://localhost:8000/api/v1/virtual-ips/1/images` 验证最新变体图 `id=74` 的 `generation_params` 已包含 `image_fidelity=0.7`、`human_fidelity=0.6`、`generation_profile=identity`。

## Next Steps

- 分镜：在后续迁移 `scripts_legacy.py` 分镜图像链路时，将 `generate_storyboard_image_urls()` 返回的 `image_gen` 元数据写入 `scripts.extra_metadata.storyboard.frames[*]` 以完成全链路落库审计。
- 前端：在图片详情/任务详情中更友好地展示 `generation_params`（尤其是 fidelity/strength/profile）。

## Linked Commits

- (pending)
