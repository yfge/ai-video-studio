---
id: 2026-01-12T04-50-09Z-backend-keling-v2-1-img2img-model-map
date: 2026-01-12T04:50:09Z
participants: [human, codex]
models: [gpt-5.2]
tags: [backend, image-gen, keling, consistency]
related_paths:
  - ai-pic-backend/app/services/image_gen/normalize.py
  - ai-pic-backend/tests/unit/services/image_gen/test_keling_img2img_profiles.py
summary: "Prevent Keling v2.1 from silently degrading img2img by mapping kling-v2-1 to kling-v2 in image_to_image normalization."
---

## User Prompt

- 你看一下 `docs/api/keling/capability-map.md` 和你理解的有误吧？？现在重新进行验证，我充值了
- 继续提升“质量一致性”

## Goals

- 当用户在 **图生图** 场景选择 `keling:kling-v2-1` 时，避免后台悄悄走“无参考图”的降级路径导致一致性崩坏。
- 让行为与 `docs/api/keling/capability-map.md` 的结论一致：`kling-v2-1` 不支持 img2img，应使用 `kling-v2`（或 v1/1-5）。
- 通过 audit_warnings 让“模型被纠正”的事实可被追溯。

## Changes

- 在统一归一化层 `normalize_image_gen_request()` 中新增规则：当 `provider=keling` 且 `mode=image_to_image` 且模型为 `kling-v2-1` 时，自动将 `model_id` 映射为 `kling-v2`，并写入 `audit_warnings`。
- 新增单测覆盖该映射行为，确保 `build_ai_manager_call()` 下发的实际 model 为 `kling-v2`。

## Validation

- `cd ai-pic-backend && pytest tests/unit tests/services tests/scripts`
- Chrome（Docker + Nginx dev，`http://localhost:8089`）：
  - 登录 `geyunfei` / `Gyf@845261`
  - 通过 `POST /api/v1/story-structure/environments/aab17f172446462a97e738772337d272/images/variants-async` 创建环境图生图任务（task_id=`571`），请求中显式传 `model=keling:kling-v2-1`
  - 轮询 `GET /api/v1/tasks/571` 至 `status=completed`
  - 再请求 `GET /api/v1/story-structure/environments/aab17f172446462a97e738772337d272`，确认 `metadata.last_image_to_image_generation.model == \"kling-v2\"` 且 `audit_warnings` 含 `keling model kling-v2-1 ... using kling-v2`

## Next Steps

- 前端在 img2img 模式下对 `supports_reference_image=false` 的模型做 UI 限制/提示（避免用户误选），并展示该类 audit_warnings。

## Linked Commits

- feat: map keling kling-v2-1 to kling-v2 for img2img consistency
