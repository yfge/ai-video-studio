---
id: 2025-12-08T14-52-21Z-script-scene-sync
date: 2025-12-08T14:52:21Z
participants: [human, codex]
models: [gpt-4o-mini]
tags: [backend, storyboard, story_structure]
related_paths:
  - ai-pic-backend/app/api/v1/endpoints/scripts.py
  - ai-pic-backend/tests/scripts/test_script_story_structure_sync.py
summary: "Auto-sync generated/saved scripts into normalized story_structure scenes (with placeholder shots) so storyboard UI can work immediately."
---

## User Prompt

在后端生成/保存剧本时自动同步 scenes→story_structure.scenes（必要时生成 beats/shots 占位），保证新剧本可立即用于分镜。 先完成 这个，同时保证 自测充分

## Goals

- Ensure new or regenerated scripts automatically populate normalized scenes for storyboard usage.
- Avoid blocking storyboard UI by creating placeholder shots when none exist.
- Add backend coverage to guard against regressions.

## Changes

- Added a helper to translate `Script.scenes` (or extra_metadata scenes fallback) into normalized `story_structure` scenes with deduped scene numbers and default slug lines, plus one planned shot per scene.
- Wired the sync into script create/generate (sync & async), regenerate, and update flows so normalized scenes exist without manual imports.
- Added regression test `tests/scripts/test_script_story_structure_sync.py` to verify script generation creates normalized scenes/shots and regeneration does not duplicate them.

## Validation

- `pytest tests/scripts/test_script_story_structure_sync.py`

## Next Steps

- Consider mapping additional fields (beats/character/env hints) when available to enrich normalized scenes without overwriting manual edits.
- Evaluate whether overwrite mode is needed when scripts change structure significantly while preserving existing environment/role bindings.

## Linked Commits

- (pending)
