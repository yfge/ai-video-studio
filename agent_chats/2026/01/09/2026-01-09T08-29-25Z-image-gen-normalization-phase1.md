---
id: 2026-01-09T08-29-25Z-image-gen-normalization-phase1
date: "2026-01-09T08:29:25Z"
participants: [human, codex]
models: [gpt-5.2]
tags: [backend, image, design]
related_paths:
  - docs/design/image-generation-unification.md
  - docs/README.md
  - ai-pic-backend/app/services/image_gen/__init__.py
  - ai-pic-backend/app/services/image_gen/normalize.py
  - ai-pic-backend/app/services/image_gen/policies.py
  - ai-pic-backend/app/services/image_gen/provider_params.py
  - ai-pic-backend/app/services/image_gen/refs.py
  - ai-pic-backend/app/services/image_gen/types.py
  - ai-pic-backend/tests/unit/services/image_gen/test_normalize.py
summary: "Phase 1: add image-generation unification design doc and a new normalization layer (no endpoint wiring yet)"
---

## User Prompt

用户要求对虚拟 IP 图生图、环境文生图/图生图、分镜图生图进行整体梳理，并先整理成设计文档；随后确认可以开始落地 Phase 1（先搭归一化层，不接入业务）。

## Goals

- 输出可落地的“图像生成统一化”设计文档，明确现状差异、统一方向与迁移阶段。
- 增加一个可复用的请求归一化层：统一 model/provider 解析、size/aspect_ratio 归一化、reference_images 归一化、并提供 provider 安全参数白名单映射。
- 提供单元测试覆盖核心归一化规则，保证后续接入时可控。

## Changes

- 新增设计文档：`docs/design/image-generation-unification.md`
- 更新 docs 索引：`docs/README.md`
- 新增归一化模块：`app/services/image_gen/`
  - `normalize_image_gen_request(...)`：生成 `ImageGenNormalized` + audit 信息
  - `build_ai_manager_call(...)`：按 provider 白名单过滤/映射参数（不执行调用）
  - domain policy：环境域禁用 `style_spec/style_preset_id`（与现有行为一致）
- 新增单元测试：`tests/unit/services/image_gen/test_normalize.py`

## Validation

- `cd ai-pic-backend && pytest tests/unit/services/image_gen -q --cov-fail-under=0`
- 额外运行了全量 `pytest`，存在大量既有失败（与本次新增模块未接入业务无直接关联），本阶段不处理。

## Next Steps

- Phase 2：将虚拟 IP 图生图（sync/async）接入归一化层，统一 provider/model/size/aspect_ratio/reference_images 的行为，并补充对应测试与 E2E 验证记录。

## Linked Commits

- TBD
