---
id: 2026-06-08T08-45-49Z-unmounted-endpoint-dead-code-cleanup
date: "2026-06-08T08:45:49Z"
participants:
  - user
  - codex
models:
  - GPT-5 Codex
tags:
  - backend
  - frontend
  - dead-code
related_paths:
  - ai-pic-backend/app/api/v1/endpoints/images.py
  - ai-pic-backend/app/api/v1/endpoints/users.py
  - ai-pic-backend/app/api/v1/endpoints/scripts/crud.py
  - ai-pic-backend/app/api/v1/endpoints/scripts/generation.py
  - ai-pic-backend/app/api/v1/endpoints/story_structure/helpers.py
  - ai-pic-backend/app/services/context_pack/episode_context_pack_builder.py
  - ai-pic-frontend/src/utils/api/endpoints/image.endpoints.ts
  - ai-pic-frontend/src/utils/api/endpoints/index.ts
  - ARCHITECTURE.md
summary: Removed unmounted endpoint modules, an unused context-pack wrapper, and a dead frontend image API barrel export.
---

## User Prompt

Continue goal: `清理项目的死代码，直到没有`

## Goals

- Continue removing code that current imports, router mounts, and frontend usage prove is dead.
- Keep public router behavior covered by the current replacement modules.
- Leave unrelated in-progress frontend work untouched.

## Changes

- Deleted unmounted backend endpoint modules:
  - `ai-pic-backend/app/api/v1/endpoints/images.py`
  - `ai-pic-backend/app/api/v1/endpoints/users.py`
  - `ai-pic-backend/app/api/v1/endpoints/scripts/crud.py`
  - `ai-pic-backend/app/api/v1/endpoints/scripts/generation.py`
  - `ai-pic-backend/app/api/v1/endpoints/story_structure/helpers.py`
- Deleted unused `ai-pic-backend/app/services/context_pack/episode_context_pack_builder.py`; the live episode context-pack builder is in `story_context_pack_builder.py`.
- Deleted the unused frontend generic `image.endpoints.ts` and removed its barrel export from `src/utils/api/endpoints/index.ts`.
- Updated `ARCHITECTURE.md` so the known choke-point list no longer points at retired files.

## Validation

- Import/reference proof:
  - AST reverse-import scan over `ai-pic-backend/app`, backend tests/scripts, and repo `scripts` reported no unimported backend app modules after deletion.
  - `rg -n "app\\.api\\.v1\\.endpoints\\.(images|users)|app\\.api\\.v1\\.endpoints\\.scripts\\.(crud|generation)|app\\.api\\.v1\\.endpoints\\.story_structure\\.helpers|app\\.services\\.context_pack\\.episode_context_pack_builder|\\./image\\.endpoints|image\\.endpoints\\.ts" ai-pic-backend/app ai-pic-backend/tests ai-pic-frontend/src ai-pic-frontend/tests scripts docs ARCHITECTURE.md tasks.md || true`
- Static checks:
  - `ai-pic-backend/.venv/bin/python -m pyflakes ai-pic-backend/app ai-pic-backend/tests ai-pic-backend/scripts scripts`
  - `ai-pic-backend/.venv/bin/python -m compileall -q ai-pic-backend/app scripts`
  - `cd ai-pic-frontend && npm exec -- tsc --noEmit --noUnusedLocals --noUnusedParameters --pretty false`
  - `cd ai-pic-frontend && npm exec -- eslint src/utils/api/endpoints/index.ts`
- Repo checks:
  - `python scripts/check_repo_docs.py`
  - `python scripts/check_repo_contracts.py --mode audit`
- Focused backend tests:
  - `ai-pic-backend/.venv/bin/python -m pytest ai-pic-backend/tests/test_api.py::TestScriptAPI ai-pic-backend/tests/scripts/test_script_prompt_preview_api.py ai-pic-backend/tests/scripts/test_script_story_structure_sync.py`
  - `ai-pic-backend/.venv/bin/python -m pytest ai-pic-backend/tests/test_story_structure_endpoints.py`
  - `ai-pic-backend/.venv/bin/python -m pytest ai-pic-backend/tests/unit/services/context_pack/test_story_context_pack_builder.py`
- Note: An initial parallel pytest run failed because multiple processes shared the same SQLite `test.db`; the same scopes passed when rerun sequentially.

## Next Steps

- Continue the dead-code pass with actual call-chain proof; legacy naming alone is still not evidence of removability.

## Linked Commits

- This commit: `chore: remove unmounted dead modules`.
