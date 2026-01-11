---
id: 2026-01-11T02-27-20Z-backend-image-prompt-quality
date: "2026-01-11T02:27:20Z"
participants: [human, codex]
models: [gpt-5.2]
tags: [backend, image-gen, prompts, quality]
related_paths:
  - ai-pic-backend/app/services/image_gen/normalize.py
  - ai-pic-backend/app/services/image_gen/normalize_helpers.py
  - ai-pic-backend/app/services/image_gen/negative_prompts.py
  - ai-pic-backend/app/services/image_gen/profiles.py
  - ai-pic-backend/app/prompts/templates/fragments/image_macros.txt
  - ai-pic-backend/app/prompts/templates/virtual_ip_image_variant.txt
  - ai-pic-backend/app/prompts/templates/virtual_ip_image_variant.yaml
  - ai-pic-backend/app/prompts/templates/environment_image.txt
  - ai-pic-backend/app/prompts/templates/environment_image.yaml
  - ai-pic-backend/app/prompts/templates/storyboard_image_prompt.txt
  - ai-pic-backend/app/prompts/templates/storyboard_image_prompt.yaml
  - ai-pic-backend/tests/unit/services/image_gen/test_normalize.py
  - ai-pic-backend/tests/unit/test_image_prompt_templates.py
summary: "Unify image prompt quality fragments and apply safer negative-prompt defaults for consistent generation quality."
---

## User Prompt

用户希望继续提升图像生成的“质量一致性”，先做后端：引入并统一“提示词管理”，并围绕虚拟 IP 图生图、环境文生图/图生图、分镜图生图做统一治理。

## Goals

- 统一图像生成提示词的质量片段（跨 Virtual IP / Environment / Storyboard）
- 让默认 negative_prompt 更“域安全”（避免影响分镜多角色场景）
- 保持可追溯性（模板版本/来源哈希可落库）

## Changes

- 将 `normalize_image_gen_request` 的数值/尺寸归一化逻辑抽到 `normalize_helpers.py`，把 `normalize.py` 压到 <300 行，避免继续扩大超标文件。
- 更新 `generation_profile` 的默认 `negative_prompt`：加入 `collage/split-screen/multi-panel` 等通用噪点项，并移除 `multiple faces/duplicate` 这类会误伤分镜多角色的项。
- 为 Virtual IP 域在“使用 profile 默认 negative_prompt”时追加 `multiple faces / multiple people / crowd` 等额外约束（仅 Virtual IP 生效）。
- 提示词模板统一注入 `Quality: {{ img.quality_high() }}`：
  - `virtual_ip_image_variant`（并将模板版本升到 `1.1`）
  - `environment_image`（并将模板版本升到 `1.1`）
  - `storyboard_image_prompt`（新增 `Constraints:` 行，使用新的 `constraint_no_deformities_basic()`，并将模板版本升到 `1.3`）
- 新增/更新单测覆盖：Virtual IP overlay 行为、Storyboard negative_prompt 不含 `multiple faces`、Storyboard prompt 模板包含 `Quality/Constraints`。

## Validation

- `pytest -q tests/unit/services/image_gen/test_normalize.py tests/unit/test_image_prompt_templates.py tests/unit/services/virtual_ip/test_virtual_ip_image_prompts.py`
- Chrome（MCP）端到端：
  - 重新登录 `geyunfei / Gyf@845261`
  - 虚拟 IP 详情页（老拐）→ 任意图片点“图生图”→ 选择 `keling:kling-image-v1` + `generation_profile=balanced` 提交任务；Task 参数中可见 `prompt_template.version=1.1`（本次任务 `task_id=553`，但该次生成失败：`所有图生图提供商都失败了`）。
  - 环境资产“办公室”详情页 → 使用火山引擎 `doubao-seedream-3-0-t2i` 创建环境文生图任务；任务完成后在任务列表的 prompt 中可见 `Quality: high quality, ultra detailed...` 已注入（`环境文生图 - 环境5da63b15b5a640b380ef22cc30dc192b`）。

## Next Steps

- 排查 Virtual IP 图生图失败原因（provider 报错栈/配额/参数不兼容），补齐“失败可观测性”（将 provider 错误摘要落到 Task.error_message）。
- 评估是否需要按 `domain+provider+model+mode` 提供更细粒度的 negative_prompt/profile（避免不同域对“人物数量”的约束冲突）。

## Linked Commits

- feat(backend): unify image prompt quality defaults
