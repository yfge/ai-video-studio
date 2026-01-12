---
id: 2026-01-12T03-03-19Z-backend-storyboard-frame-image-gen-audit
date: "2026-01-12T03:03:19Z"
participants: [human, codex]
models: [gpt-5.2]
tags: [backend, storyboard, image-gen, audit, generation-profile]
related_paths:
  - ai-pic-backend/app/api/v1/endpoints/scripts_legacy.py
  - ai-pic-backend/tests/unit/test_storyboard_image_task_image_gen_persistence.py
summary: "Persist storyboard per-frame image_gen metadata for reproducible img2img quality"
---

## User Prompt

- 继续 Phase 2：提升“质量一致性”，统一梳理虚拟 IP / 环境 / 分镜的图生图链路。
- 分镜侧需要把 profile/normalize 后的最终参数落库，避免只在返回值里、无法审计复现。

## Goals

- 分镜图像生成落库审计补齐最后一段：把 `generate_storyboard_image_urls()` 的 `image_gen` 元数据写入 `scripts.extra_metadata.storyboard.frames[*]`。
- 兼容旧字段：`keyframe_mode=single` 继续写 `image_url`，`keyframe_mode=start_end` 写 `start_* / end_*` 并保留 `image_url` 指向 start。

## Changes

- 分镜落库：
  - `keyframe_mode=single`：将 `result.image_gen` 写入 `frame["image_gen"]`。
  - `keyframe_mode=start_end`：将 `start_result.image_gen` 写入 `frame["start_image_gen"]`（并同步到 `frame["image_gen"]`），将 `end_result.image_gen` 写入 `frame["end_image_gen"]`。
- 新增单测覆盖：
  - 覆盖 `single` 与 `start_end` 两种模式，验证 `image_gen`/`start_image_gen`/`end_image_gen` 均能落库到 `Script.extra_metadata.storyboard.frames`。

## Validation

- 后端测试：
  - `cd ai-pic-backend && pytest tests/unit tests/services tests/scripts`
- Chrome 端到端（真实后端接口 + 落库核验）：
  - 登录 `http://localhost:8089/login`（geyunfei）。
  - 通过 DevTools 触发 `POST http://localhost:8000/api/v1/scripts/15/storyboard/generate-images`（`model=keling:kling-v1-5`、`generation_profile=identity`、`keyframe_mode=start_end`、`frames=[0]`、`reference_images=[...]`）创建任务 `task_id=567` 并等待完成。
  - 通过 DevTools 拉取 `GET http://localhost:8000/api/v1/scripts/15/storyboard`，验证 `frames[0]` 已包含 `start_image_gen/end_image_gen/image_gen`，且其中包含 `image_reference=subject`、`image_fidelity=0.7`、`human_fidelity=0.6`、`generation_profile=identity`。

## Next Steps

- 前端：在分镜图像详情/任务详情中展示 `image_gen`（profile + fidelity + prompt_sha256），并统一 UI 的“模型参数档位”选择。
- 后端：补齐 prompt template 的统一管理（PromptTemplate Registry + 版本化），让 `prompt_template` 与 `prompt_sha256` 在各域都稳定一致。

## Linked Commits

- (pending)

