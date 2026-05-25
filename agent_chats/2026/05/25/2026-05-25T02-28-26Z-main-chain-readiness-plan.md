## User Prompt

PLEASE IMPLEMENT THIS PLAN: 落成计划及待办文档.

## Goals

- Convert the current main-chain status judgment into repository source-of-truth docs.
- Keep the product direction focused on professional production, not C端 APP, generic SaaS, or social platform expansion.
- Make the next work sequence explicit: close current changes, prove real E2E, then harden Timeline rollback, validation, lineage, and production samples.

## Changes

- Updated `tasks.md` with the current highest priority, completed baseline, and P0/P1/P2 execution structure.
- Added `docs/exec-plans/active/main-chain-commercial-readiness.md` as the commercial-readiness execution plan.
- Updated Timeline execution plans to reflect that render/export is implemented in the current worktree but still needs real E2E evidence and production sample validation.

## Validation

- `git diff --check`: passed.
- `python scripts/check_repo_docs.py`: passed.
- `python scripts/check_repo_contracts.py --mode diff tasks.md docs/exec-plans/active/main-chain-commercial-readiness.md docs/exec-plans/active/timeline-main-chain.md docs/exec-plans/active/timeline-main-chain-optimization.md agent_chats/2026/05/25/2026-05-25T02-28-26Z-main-chain-readiness-plan.md`: exited 0; no diff-sensitive rules applied to this doc-only file set.
- `python scripts/check_repo_contracts.py --mode diff $(git diff --name-only) $(git ls-files --others --exclude-standard)`: passed across the current dirty worktree.
- `pre-commit run --all-files`: failed outside this doc-only change. Formatter hooks modified unrelated historical files and the backend quick gate failed while importing `tests.fixtures.client` because `app.services.script_quality.checks` does not export `check_cliffhanger`; the unrelated formatter mutations were reverted to preserve atomic commits.
- `BUILD_PUSH=false ./docker/build_prod_images.sh`: passed for the whole dirty worktree before final commits; backend and frontend images were built locally without push with `IMAGE_TAG=f6cc4461`.
- Backend and frontend tests are not required because this change only updates docs and ledger entries.

## Next Steps

- Package the current worktree into reviewable commit boundaries.
- Run real `Episode -> Timeline -> Render -> Export` validation with a script that has video clip assets.
- Start Timeline delete/rollback and schema/import validation after the current worktree is closed.

## Linked Commits

- Pending.
