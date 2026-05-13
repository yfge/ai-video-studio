---
id: 2026-05-13T05-58-07Z-storyboard-support-prompts
date: "2026-05-13T05:58:07Z"
participants: [human, codex]
models: [gpt-5]
tags: [backend, storyboard, prompts, timeline]
related_paths:
  - ai-pic-backend/app/services/storyboard/storyboard_audio_prompt_builder.py
  - ai-pic-backend/app/prompts/templates/storyboard_audio_visual_dialogue_spoken.txt
  - ai-pic-backend/app/prompts/templates/storyboard_shot.txt
  - ai-pic-backend/tests/unit/services/storyboard/test_storyboard_audio_prompt_builder.py
summary: "Refine Timeline/audio storyboard support-view prompts for short-drama production shots"
---

## User Prompt

PLEASE IMPLEMENT THIS PLAN: 分镜 Support View 提示词细化计划。

## Goals

- Make default `Timeline/audio -> storyboard support view` prompts richer and
  more useful for short-drama shot generation.
- Keep deterministic prompt generation; do not add an LLM rewrite chain.
- Preserve UI-facing `description`, support-view metadata, references, and
  Timeline source fields.

## Changes

- Expanded deterministic audio storyboard prompt fragments for spoken dialogue,
  voiceover, document-reading beats, action beats, and pauses.
- Added structured short-drama prompt sections: visual subject, performance,
  scene lighting, continuity, and forbidden artifacts.
- Updated context injection so character cards and environment anchors read as
  production shot guidance while keeping existing reference image selection.
- Strengthened `storyboard_shot` output with vertical short-drama, single-shot,
  continuity, and no-text/no-collage constraints.
- Added prompt-builder tests and updated context/Timeline support tests to lock
  visual-only behavior and source metadata preservation.

## Validation

- `cd ai-pic-backend && pytest tests/unit/services/storyboard/test_storyboard_audio_prompt_builder.py tests/unit/services/storyboard/test_storyboard_audio_context_enricher.py tests/unit/services/audio/test_storyboard_from_timeline_spec.py tests/unit/services/audio/test_timeline_processor.py -q`
  - Passed: 35 passed.
- `python scripts/check_repo_docs.py`
  - Passed.
- `python scripts/check_repo_contracts.py --mode diff $(git diff --name-only)`
  - Passed.
- `git diff --check`
  - Passed.

## Next Steps

- If image quality is still too generic after this deterministic pass, evaluate
  a separate optional LLM rewrite step with cached per-frame output.
- Keep P3 render/export worker work separate.

## Linked Commits

- Pending commit for this change set.
