## User Prompt

时间轴，分镜，组装，IP 生成，环境生成，都有么？ image.candidates 和 video.candidates 需要也做到自动跑

## Goals

- Make whole-canvas creation continue into all ready production skills instead of stopping after canvas creation.
- Add production canvas execution coverage for selected Virtual IP image generation and selected environment image generation.
- Ensure `image.candidates` and `video.candidates` are eligible for automatic execution when their required context is present.

## Changes

- Added `virtual_ip.image` and `environment.image` production canvas skill definitions, layout nodes, planning readiness, and executor dispatch.
- Reused existing `tasks.virtual_ip_image_generate` and `tasks.environment_image_generate` workers by creating matching task rows and forwarding normalized payloads.
- Removed the frontend auto-run exclusion for media candidate skills, while preserving the `required_inputs` gate for blocked nodes.
- Added frontend and backend tests for media auto-run, asset generation skill registration/planning, and API dispatch.

## Validation

- RED: `cd ai-pic-frontend && npx tsx --test --test-name-pattern "automatically executes ready image and video candidate nodes" tests/productionCanvasBoard.test.tsx` failed before implementation with `0 !== 2`.
- RED: targeted backend registry/plan/API tests failed before `virtual_ip.image` and `environment.image` dispatch existed.
- GREEN: `cd ai-pic-frontend && npx tsx --test tests/productionCanvasBoard.test.tsx tests/productionCanvasPersistence.test.tsx tests/productionCanvasMediaControls.test.tsx` passed 11 tests.
- GREEN: `cd ai-pic-backend && pytest tests/unit/test_production_canvas_skill_registry.py tests/unit/test_production_canvas_skill_plan.py tests/unit/test_production_canvas_executor.py tests/integration/test_production_canvas_api.py tests/integration/test_production_canvas_asset_generation_api.py tests/integration/test_production_canvas_media_api.py -q` passed 18 tests.
- GREEN: `cd ai-pic-frontend && npm run lint` passed with the existing three warnings in `eslint.config.mjs`, `EnvironmentReferenceImagesField.tsx`, and `VirtualIPReferenceImagesField.tsx`.
- GREEN: `python scripts/check_repo_docs.py`, `{ git diff --name-only; git ls-files --others --exclude-standard; } | sort | xargs python scripts/check_repo_contracts.py --mode diff`, and `git diff --check` passed.
- Browser evidence: `artifacts/runs/canvas-full-auto-execute-20260623T094344Z/browser_flow.canvas_full_auto_execute.json` records Playwright system Chrome fallback with mocked production-canvas plan/execute APIs. It captured six automatic execute requests: `virtual_ip.image`, `environment.image`, `storyboard.plan`, `image.candidates`, `video.candidates`, and `timeline.assemble`.
- Browser screenshot: `artifacts/runs/canvas-full-auto-execute-20260623T094344Z/browser_flow.canvas_full_auto_execute.png`.
- Skipped before commit: `pre-commit run --all-files` and `./docker/build_prod_images.sh`. This change is scoped to production canvas orchestration and tests; the repository pre-commit all-files path is known to be noisy/mutating, and Docker image build is outside this targeted validation pass.

## Next Steps

- The current implementation generates images for selected IP/environment assets. It does not create new Virtual IP or environment entities from zero when no asset context is available; those nodes remain blocked with explicit `virtual_ip_id` or `environment_id` requirements.
- Local user data for `geyunfei` had no existing Virtual IP or environment assets during validation, so browser validation mocked the production-canvas APIs to avoid triggering paid AI calls. Backend API tests covered real task dispatch with workers monkeypatched.

## Linked Commits

- This commit.
