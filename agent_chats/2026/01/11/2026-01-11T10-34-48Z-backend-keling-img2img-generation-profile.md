---
id: 2026-01-11T10-34-48Z-backend-keling-img2img-generation-profile
date: "2026-01-11T10:34:48Z"
participants: [human, codex]
models: [gpt-5.2]
tags: [backend, image-gen, keling]
related_paths:
  - ai-pic-backend/app/api/v1/endpoints/image_gen_profiles.py
  - ai-pic-backend/app/schemas/image_gen_profiles.py
  - ai-pic-backend/app/services/image_gen/normalize.py
  - ai-pic-backend/app/services/image_gen/normalize_helpers.py
  - ai-pic-backend/app/services/image_gen/profiles.py
  - ai-pic-backend/app/services/image_gen/provider_params.py
  - ai-pic-backend/app/services/image_gen/types.py
  - ai-pic-backend/tests/unit/services/image_gen/test_keling_img2img_profiles.py
summary: "为可灵图生图接入 generation_profile 默认 fidelity 参数，并贯通 normalize→provider 调用链"
---

## User Prompt

- 继续 Phase 2：先做后端，在后端引入“生成参数 preset / profile”（按 provider+model 给默认参数），并修复/验证可灵图生图能力与质量一致性。

## Goals

- 让可灵图生图（img2img）也能通过统一的 `generation_profile` 收敛关键生成参数，提升“质量一致性”。
- Profiles API 能返回可灵图生图的 profile 列表与默认参数，前端统一展示/选择。
- 真实浏览器 E2E 跑通一次可灵环境图生图链路，确认任务成功并落库出新图。

## Changes

- 扩展 `ImageGenProfileDefaults` / `ImageGenRequest` / `ImageGenNormalized`：新增可灵图生图相关可选参数 `image_reference`、`image_fidelity`、`human_fidelity`。
- 可灵图生图 `generation_profile` 预设：
  - `balanced`：`image_fidelity=0.5`、`human_fidelity=0.45`
  - `identity`：`image_fidelity=0.7`、`human_fidelity=0.6`
  - `creative`：`image_fidelity=0.35`、`human_fidelity=0.35`
- Normalize：当 `mode=image_to_image` 时，若请求未传入 fidelity 字段则从 profile defaults 回填，并做 `[0,1]` clamp（记录 audit warning）。
- Provider call payload：`build_ai_manager_call()` 在图生图路径透传 `image_reference/image_fidelity/human_fidelity`（由 provider-safe filter 兜底）。
- Profiles API：`/api/v1/image-gen/profiles` 响应 schema 与 mapping 补齐上述 defaults 字段。
- 单测覆盖：新增 unit tests 验证 defaults 生效、payload 透传、以及 clamp 行为。

## Validation

- Backend quick gate：`cd ai-pic-backend && pytest tests/unit tests/services tests/scripts`
- Chrome E2E（使用账号 `geyunfei`）：
  - 打开 `http://localhost:8089/environments/aab17f172446462a97e738772337d272`（env_id=7）
  - 在任一参考图点击“图生图”，选择模型：`可灵图像生成 V2 — 可灵`（`keling:kling-v2`）
  - 选择质量档位：`身份优先`（`generation_profile=identity`），尺寸：`1:1 · 2K`，提交任务
  - 任务创建成功（任务列表详情显示 `任务ID：563`），状态已完成；环境参考图数量 `12 → 13`，新增图片 URL：`http://resource.lets-gpt.com/ai-generated/environments/image/20260111/103359/efab564b.png`

## Next Steps

- 前端：在“默认参数”区域展示并解释可灵图生图的 `image_fidelity/human_fidelity`（以及后续其他 provider 的 profile defaults），并统一各入口的 profile 选择组件。
- 观测：将 `image_fidelity/human_fidelity` 写入环境/虚拟 IP/分镜的 `extra_metadata`（与 `steps/cfg/strength` 同级）便于审计与复现。

## Linked Commits

- (pending)
