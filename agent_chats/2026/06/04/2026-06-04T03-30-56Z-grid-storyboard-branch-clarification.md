---
id: 2026-06-04T03-30-56Z-grid-storyboard-branch-clarification
date: "2026-06-04T03:30:56Z"
participants:
  - user
  - codex
models:
  - gpt-5
tags:
  - timeline
  - storyboard-grid
  - prompt
summary: Clarify grid storyboard as a direct Timeline sheet branch.
related_paths:
  - ai-pic-backend/app/prompts/templates/storyboard_grid_sheet.txt
  - docs/timeline-rendering-pipeline.md
---

## User Prompt

The user clarified that after Timeline reaches storyboard production there are
two valid visual generation forms:

- generate start/end images, then generate video clips;
- generate a grid/storyboard sheet image, then use that sheet directly as the
  video reference.

The grid image itself is the storyboard artifact.

## Goals

- Keep grid storyboard generation as a direct Timeline-to-sheet path.
- Avoid making grid storyboard generation depend on pre-existing single-frame
  storyboard images.
- Document the two supported visual branches after Timeline shot planning.
- Allow production-board style sheet labels, timing, and notes outside the
  cinematic panels while still forbidding subtitles, captions, readable UI, and
  title cards inside panels.

## Changes

- Reverted the abandoned single-image-first requirement for grid sheets before
  finalizing this change set.
- Updated `docs/timeline-rendering-pipeline.md` to describe the start/end-frame
  branch and the grid-storyboard-sheet branch as separate Timeline support
  forms.
- Updated `ai-pic-backend/app/prompts/templates/storyboard_grid_sheet.txt` so
  board-level shot labels, timing ranges, and production notes may appear in
  gutters, borders, or header/footer areas outside the cinematic panels.
- Added prompt-template assertions in
  `ai-pic-backend/tests/unit/test_storyboard_prompt_templates.py`.

## Validation

- `cd ai-pic-backend && pytest tests/test_timeline_storyboard_grid_api.py tests/test_timeline_storyboard_grid_processor.py tests/unit/services/storyboard/test_grid_storyboard_prompt_bridge.py tests/unit/test_storyboard_prompt_templates.py -q`
  - Passed: 17 tests.
- `cd ai-pic-frontend && npx tsx --test tests/workspaceStoryboardTabContent.test.tsx`
  - Passed: 3 tests.
- `cd ai-pic-frontend && npm run lint`
  - Passed with 0 errors and 18 existing warnings.
- `cd ai-pic-frontend && npm run test`
  - Passed: 35 tests.
- `cd ai-pic-backend && python run_tests.py quick`
  - Not completed: terminated after the command spent about five minutes in
    `pip install -r requirements-test.txt` with no stdout/stderr, stuck under
    a `maturin pep517 write-dist-info` child process. Focused backend tests
    above passed.
- `cd ai-pic-backend && pytest tests/unit/test_storyboard_prompt_templates.py::test_storyboard_grid_sheet_template_allows_sheet_but_limits_text -q`
  - Passed: 1 test after the active branch HEAD changed during the session.
- Browser validation was not run in this correction pass; the completed changes
  are prompt, documentation, and focused regression tests, with no local server
  exercised.

## Next Steps

- Use the normal image provider path for Timeline-to-grid-sheet generation.
- Use start/end-frame generation separately when the production path is
  per-clip keyframe-to-video.
- Re-run backend quick in a Python environment where the test dependency
  install does not stall in `maturin`.

## Linked Commits

- This commit.
