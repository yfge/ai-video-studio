---
id: 2026-07-10T10-58-15Z-canvas-reference-artifact-backend
date: "2026-07-10T10:58:15Z"
participants:
  - user
  - codex
models:
  - gpt-5-codex
tags:
  - canvas
  - backend
  - storyboard
  - reference-images
related_paths:
  - ai-pic-backend/app/schemas/production_canvas.py
  - ai-pic-backend/app/repositories/environment_repository.py
  - ai-pic-backend/app/repositories/virtual_ip_image_repository.py
  - ai-pic-backend/app/services/production_canvas/reference_artifacts.py
  - ai-pic-backend/app/services/production_canvas/media_execution.py
  - ai-pic-backend/app/services/storyboard/storyboard_image_autogen.py
  - ai-pic-backend/tests/integration/test_production_canvas_reference_artifacts_api.py
summary: Resolve completed canvas asset references into owned image URLs for the existing storyboard image worker.
---

## User Prompt

继续完善无限画布功能，保持原子化提交。

## Goals

- Connect completed role and environment image artifacts to the real `image.candidates` backend execution path.
- Preserve asset ownership checks while resolving persisted artifact references.
- Reuse the existing storyboard image worker rather than introducing a parallel generation path.

## Changes

- Added `reference_artifacts` to the production-canvas skill execution contract.
- Added repository-backed resolution for `virtual_ip_image:<virtual_ip_id>:<image_id>` and `environment_images:<environment_id>:<count>` references.
- Passed resolved image URLs into the existing storyboard image queue and worker payload.
- Allowed global canvas references to satisfy the queue's reference-image eligibility gate even when storyboard frames do not already contain references.
- Returned resolved/unresolved artifact evidence and reference-image counts in the canvas skill result.

## Validation

- `cd ai-pic-backend && python -m pytest tests/integration/test_production_canvas_media_api.py -q` -> pass, 4 tests before the new case was split for the file-size contract.
- `cd ai-pic-backend && python -m pytest tests/integration/test_production_canvas_reference_artifacts_api.py -q` -> pass, 1 test after the split.
- `cd ai-pic-backend && python run_tests.py quick --no-setup` -> pass, 2403 passed, 77 skipped, 20 deselected.
- The integration case removed all frame-level references, supplied generated role/environment artifact refs, and verified two resolved URLs in the `STORYBOARD_IMAGE_GENERATION` task payload.
- `python scripts/check_repo_contracts.py --mode diff ...` -> pass after splitting the integration case into a dedicated file.
- `git diff --check` -> pass.
- `BUILD_PUSH=false BUILD_PLATFORMS=linux/amd64 ./docker/build_prod_images.sh` -> pass; both production images built locally without push.
- Scoped `pre-commit run --files ...` -> pass after applying the repository isort order.

## Next Steps

- Propagate completed artifact refs through the frontend canvas context and include them when `Image Candidates` executes.
- Validate a real restored run using a script with storyboard frames and the previously completed role/environment tasks.

## Linked Commits

Pending.
