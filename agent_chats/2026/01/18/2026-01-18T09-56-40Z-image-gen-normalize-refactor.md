---
id: 2026-01-18T09-56-40Z-image-gen-normalize-refactor
date: 2026-01-18T09:56:40Z
participants: [human, codex]
models: [gpt-5.2]
tags: [backend, image-gen, refactor]
related_paths:
  - ai-pic-backend/app/services/image_gen/normalize.py
  - ai-pic-backend/app/services/image_gen/normalize_profile.py
summary: "拆分 image_gen normalize.py，降低文件体积并保持现有行为不变。"
---

## User Prompt

全局检查文生图/图生图提示词规范与 provider 参数一致性；并按 provider 进一步优化，且要求原子化分布提交。

## Goals

- 将 `ai-pic-backend/app/services/image_gen/normalize.py` 拆分到 ≤300 行并保持逻辑等价。
- 为后续“按 provider+mode 做能力丢弃审计/提示”铺路，降低改动风险。

## Changes

- 新增 `ai-pic-backend/app/services/image_gen/normalize_profile.py`：抽离 generation_profile 与采样/图生图参数的默认值与归一化逻辑。
- 精简 `ai-pic-backend/app/services/image_gen/normalize.py`：保留主流程，调用 `resolve_profile_params()`。

## Validation

- `cd ai-pic-backend && pytest tests/unit tests/services tests/scripts`
- `./docker/build_prod_images.sh`（tag=586fddb，提交后会再次执行以对齐新 commit）

## Next Steps

- 在 normalize 层加入按 provider+mode(+model) 的“参数不支持→丢弃+审计”，避免 silent drop。
- 同步前端：切换模型/provider 时清理不支持的高级参数（seed/steps/cfg/strength 等），并展示后端审计信息。

## Linked Commits

- (pending)
