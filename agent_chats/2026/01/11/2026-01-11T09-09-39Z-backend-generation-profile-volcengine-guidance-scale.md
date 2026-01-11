---
id: 2026-01-11T09-09-39Z-backend-generation-profile-volcengine-guidance-scale
date: "2026-01-11T09:09:39Z"
participants: [human, codex]
models: [gpt-5.2]
tags: [backend, image-gen, profile, preset, volcengine]
related_paths:
  - ai-pic-backend/app/services/image_gen/profiles.py
  - ai-pic-backend/app/services/image_gen/provider_params.py
  - ai-pic-backend/app/services/providers/volcengine_provider/guidance_scale.py
  - ai-pic-backend/app/services/providers/volcengine_provider/image.py
  - ai-pic-backend/tests/unit/services/image_gen/test_normalize.py
  - ai-pic-backend/tests/unit/test_volcengine_provider_image_guidance_scale.py
summary: "Expand generation_profile coverage and map volcengine cfg_scale to guidance_scale"
---

## User Prompt

- 在后端引入“生成参数 preset / profile”（按 provider+model 给默认 steps/cfg_scale/negative_prompt），并让前端统一选择与展示。
- 继续提升图像生成“质量一致性”，整体覆盖并调整（虚拟 IP、环境、分镜链路）。

## Goals

- 扩展 `generation_profile` 覆盖范围（provider+model+mode），让默认参数可被稳定解析与复现。
- 为火山引擎（Ark）补齐 `cfg_scale` 映射到官方 `guidance_scale`（仅对支持的模型生效），避免参数被静默丢弃。
- 为 img2img 场景补齐可复现的默认 `strength`（即梦），并避免对不支持字段的“假默认值”误导。

## Changes

- 更新 `list_image_gen_profiles()`：
  - 即梦 img2img：新增 `strength` 默认值（balanced/quality/fast），并移除该模式下无效的 `negative_prompt` 默认值。
  - 可灵 img2img：返回 `None`（可灵 img2img 不支持 negative_prompt，避免生成 profile “看似生效但实际无效”）。
  - 火山引擎：为 `doubao-seedream-3-0-t2i*` / `doubao-seededit-3-0-i2i*` 增加默认 profile（cfg=2.5 / cfg=5.5）。
- Volcengine provider：支持将入参 `cfg_scale`/`guidance_scale` 写入请求体的 `guidance_scale`（范围 clamp 到 [1,10]，仅对支持模型生效）。
- Provider-safe 参数过滤：允许 volcengine 在 image/t2i 与 img2img 中透传 `cfg_scale`（内部再映射为 `guidance_scale`）。
- 新增/更新单测：覆盖 volcengine profile 默认 cfg、jimeng img2img strength 默认值、以及 volcengine 请求体 guidance_scale 注入/忽略规则。

## Validation

- 后端测试：`cd ai-pic-backend && pytest tests/unit tests/services tests/scripts`（733 passed）。
- Chrome 端到端：
  - 登录 `http://localhost:8089/login`（geyunfei）。
  - 进入环境详情 `http://localhost:8089/environments/aab17f172446462a97e738772337d272`（env_id=7）。
  - 在“AI 生成参考图”选择「火山引擎 / doubao-seedream-3-0-t2i」，看到“质量档位”为「默认」，并展示默认参数 `cfg=2.5`。
  - 点击「创建生成任务」，任务页查看任务 `562` 状态为「已完成」；回到环境详情页，参考图数量从 11 增加到 12。

## Next Steps

- 将 `generation_profile` 扩展到更多 provider/model（必要时映射到各家等价参数），并在前端统一展示“该 profile 实际会影响哪些字段”。
- 继续梳理虚拟 IP / 环境 / 分镜 的 img2img 参数（如可灵 `image_fidelity/human_fidelity`）是否也需要纳入 profile 统一管理。

## Linked Commits

- (pending)
