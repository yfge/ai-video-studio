---
id: 2026-05-25T10-28-59Z-legacy-backend-gate-fixes
date: "2026-05-25T10:28:59Z"
participants: [human, codex]
models: [gpt-5]
tags: [backend, prompts, scripts, tests, legacy]
related_paths:
  - ai-pic-backend/app/prompts/templates/storyboard_audio_visual_context.txt
  - ai-pic-backend/app/prompts/templates/storyboard_audio_visual_context.yaml
  - ai-pic-backend/app/prompts/templates/storyboard_audio_visual_dialogue_read_text.txt
  - ai-pic-backend/app/prompts/templates/storyboard_audio_visual_dialogue_read_text.yaml
  - ai-pic-backend/tests/scripts/test_script_regeneration_soft_delete.py
summary: "Repair legacy backend quick gate failures"
---

## User Prompt

- “按项目规范，依次完成对应计划，保证原子性提交”
- “继续”

## Goals

- Follow the legacy stability cleanup surfaced by the previous backend quick
  gate.
- Fix the three independently reproducible backend quick-gate failures without
  mixing them into the Timeline rework/render commit.
- Keep this commit scoped to prompt template wording drift and script
  regeneration test isolation.

## Changes

- Restored the explicit `屏幕文字模糊不可读` safety phrase in the
  `storyboard_audio_visual_dialogue_read_text` prompt while preserving the
  existing `屏幕/纸面内容只能模糊呈现` wording.
- Restored the `角色卡` keyword in the storyboard audio visual context prompt
  while preserving the existing `角色一致性:` prefix used by context-enricher
  tests.
- Bumped the touched prompt template metadata versions to `1.2` with
  `updated_at: 2026-05-25`.
- Patched `test_script_regeneration_creates_new_script_and_soft_deletes_old` to
  stub the script quality gate, matching nearby script tests and keeping the
  test focused on new-script creation plus old-script soft delete.

## Validation

- `cd ai-pic-backend && pytest tests/unit/test_dialogue_audio_service.py::test_audio_timeline_storyboard_prompt_description_blurs_readable_text tests/unit/test_storyboard_prompt_templates.py::test_storyboard_audio_visual_prompt_templates_exist tests/scripts/test_script_regeneration_soft_delete.py::test_script_regeneration_creates_new_script_and_soft_deletes_old tests/unit/services/storyboard/test_storyboard_audio_context_enricher.py::test_audio_timeline_storyboard_enricher_injects_cards_and_reference_images tests/unit/services/storyboard/test_storyboard_audio_context_enricher.py::test_audio_timeline_storyboard_enricher_does_not_override_manual_reference_images -q`
  - Result: passed, 5 tests.
- `pre-commit run --files <staged files>`
  - Result: passed, including `pytest (backend quick gate)`.

## Next Steps

- Continue legacy stability cleanup after the gate is green.

## Linked Commits

- Pending
