## User Prompt

先提交现有变更

## Goals

- Submit the current infinite-canvas collaboration backend as one runnable, atomic change.
- Preserve existing standalone execution compatibility while preventing collaborators from exceeding their assigned role.

## Changes

- Added persisted canvas collaborators, targeted comments, and shared activity records.
- Added Owner, Viewer, Commenter, Editor, and Approver capability checks across run loading, state editing, execution, candidate review, branching, and Timeline placement.
- Kept candidate and Timeline assets owned by the canvas owner while recording candidate review identity as the acting approver.
- Added API integration coverage for role boundaries, comments, activity, blank input validation, and shared candidate approval.

## Validation

- `cd ai-pic-backend && pytest -q tests/integration/test_production_canvas_api.py tests/integration/test_production_canvas_asset_generation_api.py tests/integration/test_production_canvas_media_api.py tests/integration/test_production_canvas_collaboration_api.py` - passed, 13 tests.
- `cd ai-pic-backend && pytest -q` - passed, 2466 tests; 88 skipped.
- `python scripts/check_repo_docs.py` - passed.
- `python scripts/check_repo_contracts.py --mode diff <changed files>` - passed.
- `pre-commit run --files <changed files>` - passed, including the backend quick gate.
- `DOCKER_CONFIG=<temporary-empty-config> BUILD_PUSH=false BUILD_PLATFORMS=linux/amd64 ./docker/build_prod_images.sh` - backend and frontend production images built locally without push.

## Next Steps

- Add the collaboration panel and role-aware controls to the canvas frontend.
- Extend activity recording to explicit review, branch, run-control, and Timeline placement actions.

## Linked Commits

- This commit: `feat(canvas): add collaboration access controls`.
