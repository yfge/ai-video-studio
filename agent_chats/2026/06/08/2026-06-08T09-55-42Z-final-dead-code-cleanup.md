---
id: 2026-06-08T09-55-42Z-final-dead-code-cleanup
date: "2026-06-08T09:55:42Z"
participants:
  - user
  - codex
models:
  - GPT-5 Codex
tags:
  - frontend
  - backend
  - dead-code
related_paths:
  - ai-pic-frontend/src/hooks/useVirtualIPDetail.ts
  - ai-pic-frontend/src/hooks/useVirtualIPDetailVoice.ts
  - ai-pic-frontend/src/hooks/useVirtualIPDetailVoiceUtils.ts
  - ai-pic-frontend/src/components/features/episode/WorkspaceStoryboardSupportModel.ts
  - ai-pic-frontend/src/components/features/episode/WorkspaceStoryboardSupportUtils.ts
  - ai-pic-backend/app/services/ai/images_ops.py
  - ai-pic-backend/app/services/providers/volcengine_provider/video_request.py
summary: Split oversized frontend files to remove final knip findings and removed backend production vulture hits.
---

## User Prompt

Continue goal: `清理项目的死代码，直到没有`

## Goals

- Remove the final frontend `knip` findings without violating file-size contracts.
- Keep split files below the TypeScript hard limit.
- Remove production backend `vulture` findings while preserving current behavior.

## Changes

- Split virtual-IP detail voice state, options, and preview logic into `useVirtualIPDetailVoice.ts` and `useVirtualIPDetailVoiceUtils.ts`.
- Kept `hexToAudioUrl` private in the voice utility path, removing the last frontend unused export.
- Split storyboard support parsing and formatting helpers into `WorkspaceStoryboardSupportUtils.ts`.
- Made `StoryboardGridPanel` private after reducing the original storyboard support model below the file-size limit.
- Deleted unused backend image edit/enhance stubs from `ImageOpsMixin`.
- Removed the unused `has_image` parameter from Volcengine video model normalization.

## Validation

- `wc -l <split files>`
- `npm exec tsc -- --noEmit --noUnusedLocals --noUnusedParameters --pretty false`
- `npm exec --package=knip -- knip --no-progress`
- `npm run lint`
- `npm run test`
- `python scripts/check_repo_docs.py`
- `python scripts/check_repo_contracts.py --mode diff <changed files>`
- `pipx run vulture ai-pic-backend/app --min-confidence 80`
- `git diff --check -- <changed files>`
- `SKIP=backend-pytest pre-commit run --files <staged files>`
- Result: split file sizes are 207/233/87/234/153 lines; typecheck, knip, lint, frontend tests, docs, contracts, targeted backend pytest, production backend vulture, whitespace, and targeted pre-commit passed.
- Backend pre-commit pytest was skipped on the final rerun because the repo-level hook collected unrelated current-worktree import errors (`structured_script_score`, `clip_storyboard_context`) outside this cleanup batch.

## Next Steps

- No frontend `knip` findings or production backend `vulture` findings are expected after this batch.
- Test-only vulture fixture findings can be handled separately if the team wants a zero-output test scan.

## Linked Commits

- This commit: `chore: finish dead-code cleanup`.
