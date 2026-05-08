## User Prompt

Implement IP 环境接入 V1: add a real `IP 环境池 + 场景绑定` path with a lightweight backend migration, IP environment association APIs, official environment asset UI, story readiness warnings, Timeline scene environment selection, Storyboard wording alignment, validation, browser evidence, and ledger.

## Goals

- Add a first-class `VirtualIP -> Environment` association without changing provider flows or existing scene/environment generation semantics.
- Make IP detail the first visible entry for linking existing environments and creating an environment that is immediately linked to the IP.
- Replace "migration only" environment wording with official environment asset language while preserving unlinked status.
- Surface environment coverage as warning-level readiness, not a generation blocker.
- Let Timeline and Storyboard present scene environment binding as formal workflow language.

## Changes

- Added `virtual_ip_environments` model and Alembic migration with user ownership, business ids, usage metadata, default/sort fields, soft delete fields, and pair uniqueness.
- Added repository/service/API layers for:
  - `GET /api/v1/virtual-ips/{ip_id}/environments`
  - `POST /api/v1/virtual-ips/{ip_id}/environments`
  - `PUT /api/v1/virtual-ips/{ip_id}/environments/{environment_id}`
  - `DELETE /api/v1/virtual-ips/{ip_id}/environments/{environment_id}`
  - matching `business/{ip_business_id}` routes.
- Added environment response link summaries via `linked_virtual_ips` and `linked_virtual_ip_count`.
- Added environment readiness warnings through an API-facing readiness wrapper and repository-backed queries, keeping direct SQLAlchemy access out of endpoints/services.
- Split environment schemas into `app/schemas/environment_assets.py` to keep the touched schema file under contract limits.
- Added IP detail "环境资产" panel, link existing environment, create-and-link environment, unlink, and image-management navigation.
- Updated environment list/detail to official "环境资产" language and linked IP chips/status.
- Added story environment coverage display from story character IP pools.
- Added Timeline inspector scene-environment selection and save path to existing scene update API.
- Updated Storyboard labels from experimental scene attributes to formal "场景环境".
- Added frontend helper tests for virtual IP environment link view-model and Timeline scene derivation.
- Added harness scenario `environment_asset_smoke` while keeping `environment_migration_smoke` as a legacy alias.

## Validation

- `cd ai-pic-backend && pytest tests/integration/test_virtual_ip_environments_api.py tests/integration/test_readiness_environment_warnings_api.py tests/integration/test_readiness_api.py tests/test_migration_environment_assets.py -q`
  - Passed: 23 passed.
- `cd ai-pic-backend && pytest`
  - Passed: 1951 passed, 87 skipped.
- `cd ai-pic-frontend && npm run lint`
  - Passed with 0 errors and 19 existing warnings in eslint config, image tags, and legacy Storyboard hooks.
- `cd ai-pic-frontend && npm run test`
  - Passed: 10 tests.
- `cd ai-pic-frontend && npm run build`
  - Passed.
- `git diff --check`
  - Passed.
- `python scripts/check_repo_docs.py`
  - Passed.
- `python scripts/check_repo_contracts.py --mode diff <changed files>`
  - Passed.
- Browser run id: `ip-environment-integration-20260507T155212Z`
  - `doctor.py`: degraded/failed because `localhost:3000` was not listening; API health and nginx `localhost:8089` were OK.
  - Chrome DevTools attempts timed out at `http://127.0.0.1:9222`; Playwright fallback passed all browser scenarios.
  - Passed via Playwright fallback:
    - `virtual_ip_detail_smoke`
    - `environment_asset_smoke`
    - `environment_detail_smoke`
    - `story_master_detail_smoke`
    - `episode_timeline_smoke`
    - `episode_workspace_storyboard_smoke`
    - `environment_migration_smoke`
  - Evidence stored under `artifacts/runs/ip-environment-integration-20260507T155212Z/`.

## Next Steps

- Add a dedicated story/IP environment picker instead of loading all environments in the first Timeline V1 inspector.
- Consider formalizing scene environment unbinding once the scene update service is moved out of the oversized legacy service file.
- When frontend dev server on port 3000 is required, start it before `doctor.py` or point doctor only at nginx for this harness mode.

## Linked Commits

- This commit.
