---
id: 2026-06-09T09-51-57Z-storyboard-prompt-v2
date: "2026-06-09T09:51:57Z"
participants: [human, codex]
models: [gpt-5]
tags: [backend, storyboard, prompts]
related_paths:
  - ai-pic-backend/app/services/storyboard/storyboard_prompt_compiler.py
  - ai-pic-backend/app/services/storyboard/storyboard_prompt_sections.py
  - ai-pic-backend/app/api/v1/endpoints/storyboard/image_task_processor.py
  - ai-pic-backend/tests/unit/services/storyboard/test_storyboard_prompt_compiler.py
summary: "Added storyboard prompt v2 compilation, preserved Timeline shot-plan sections, and enriched clip storyboard context prompts."
---

## User Prompt

PLEASE IMPLEMENT THIS PLAN: 分镜故事板提示词改进方案。核心要求：新增后端
`StoryboardPromptCompiler`，保留 Timeline shot-plan 五层字段，区分单帧图像与
I2V motion prompt，clip storyboard sheet prompt 注入角色/环境上下文，并沿用
provider-aware prompt/negative/reference_images 策略。

## Goals

- 保持 Timeline-first：故事板仍是选中 video clip 的视觉参考资产。
- 避免下游把 `timeline_shot_plan` 的五层 prompt 信息压扁成短通用提示词。
- 让关键帧/图片提示词强调单幅电影静帧，让 I2V/rework 提示词只描述运动与镜头。
- 在 clip storyboard sheet prompt 中显式携带角色、环境和参考图角色说明。

## Changes

- Added `StoryboardPromptCompiler` for `storyboard_prompt_v2` bundles with
  clip identity, image prompt, start/end keyframe prompts, I2V motion prompt,
  reference notes, provider constraints, prompt hash, and warnings.
- Wired storyboard placeholder optimization and storyboard image generation tasks
  to persist/use the v2 prompt bundle.
- Covered both top-level `timeline_shot_plan`/`shot_plan_prompt_layers` and raw
  Timeline `source_refs.timeline_shot_plan` inputs.
- Updated clip/grid storyboard video prompts to use motion-focused compiler output.
- Enriched clip storyboard sheet prompts with `bound_context` character,
  environment, reference-role, and warning lines.
- Split oversized storyboard prompt/image-task code paths into focused helper
  modules so touched files stay within repository contract limits.
- Added/updated unit tests for prompt sections, keyframe roles, motion-only I2V
  prompts, context injection, and image task persistence.

## Validation

1. RED:

- `ai-pic-backend/.venv/bin/python -m pytest ai-pic-backend/tests/unit/services/storyboard/test_storyboard_prompt_compiler.py ai-pic-backend/tests/unit/services/storyboard/test_clip_storyboard_prompt_context.py -q`
  -> failed as expected with `ModuleNotFoundError: No module named 'app.services.storyboard.storyboard_prompt_compiler'`.

2. GREEN and targeted regression:

- `ai-pic-backend/.venv/bin/python -m pytest ai-pic-backend/tests/unit/services/storyboard/test_storyboard_prompt_compiler.py ai-pic-backend/tests/unit/services/storyboard/test_clip_storyboard_prompt_context.py -q`
  -> passed, `5 passed`.
- `ai-pic-backend/.venv/bin/python -m pytest ai-pic-backend/tests/unit/services/storyboard/test_storyboard_prompt_compiler.py ai-pic-backend/tests/unit/services/storyboard/test_clip_storyboard_prompt_context.py ai-pic-backend/tests/unit/services/storyboard/test_grid_storyboard_prompt_bridge.py ai-pic-backend/tests/unit/services/storyboard/test_clip_storyboard_context.py ai-pic-backend/tests/unit/test_storyboard_prompt_templates.py ai-pic-backend/tests/unit/test_storyboard_image_task_image_gen_persistence.py -q`
  -> passed, `21 passed`.
- `ai-pic-backend/.venv/bin/python -m pytest ai-pic-backend/tests/unit/services/storyboard/test_storyboard_prompt_compiler.py ai-pic-backend/tests/unit/services/storyboard/test_clip_storyboard_prompt_context.py ai-pic-backend/tests/unit/services/storyboard/test_grid_storyboard_prompt_bridge.py ai-pic-backend/tests/unit/services/storyboard/test_clip_storyboard_context.py ai-pic-backend/tests/unit/test_storyboard_prompt_templates.py ai-pic-backend/tests/unit/test_storyboard_image_task_image_gen_persistence.py ai-pic-backend/tests/unit/test_storyboard_image_task_reference_requirement.py -q`
  -> passed, `27 passed`.
- `git diff --check -- <touched files>` -> passed.
- `python scripts/check_repo_contracts.py --mode diff <touched files>` -> passed.
- `pre-commit run --files <touched files>` -> formatting/doc/contract hooks ran, but
  repo-level `backend-pytest` failed during unrelated all-test collection on existing
  import drift (`_BEAT_CONTRACT_MAX_TOKENS`, `structured_script_score`,
  `STRUCTURED_SCORE_PASS`).
- `SKIP=backend-pytest pre-commit run --files <touched files>` -> passed:
  merge-conflict check, whitespace, EOF, ruff, black, isort, prettier, repository
  doc drift, repository contracts, and agent_chats ledger enforcement.
- File-size/function-size check after splitting: prompt/image-task helper files are
  36-220 lines; `generate_frame_image` is 19 lines and its largest helper is 40
  lines.

## Next Steps

- Optional low-cost provider smoke can generate one selected clip storyboard image
  and one I2V rework task to compare visual quality against the previous prompt.
- If a future UI task exposes prompt preview, show `storyboard_prompt_v2` sections
  rather than only the flattened `ai_prompt`.

## Linked Commits

- Pending.
