## User Prompt

Use the completed real 48-chapter novel as the current quality sample, run GPT-5.6 batch and global review through the real product chain, judge reader appeal, and do not approve a manuscript that fails the quality bar.

## Goals

- Make the continuity endpoint accept a one-run review model without mutating the frozen generation model policy.
- Persist and validate the actual reviewer model through task payload, prompt budgeting, report evidence, and v3 approval.
- Expose GPT-5.6 as the default selectable full-book review model in the operator UI.
- Run the existing eight-window plus global review against the real MySQL-backed 48-chapter Revision.

## Changes

- Added optional, normalized `review_model` request input to the continuity endpoint and task payload.
- Routed the override through every continuity window and the global synthesis while preserving the Revision model policy.
- Bound global context budgeting, report metadata, persisted invocation verification, and v3 approval to the actual report reviewer model.
- Added a dedicated frontend review selector defaulting to `codex:gpt-5.6-sol`.
- Added focused backend API/unit/approval coverage and frontend selector/API coverage.

## Validation

- Backend focused: `6 passed`.
- Full Story Novel unit suite: `873 passed, 1 skipped`.
- Frontend focused Story Novel tests: `10 passed`.
- Frontend lint: `0 errors`, 3 unrelated warnings.
- Frontend production build: passed with `next build --webpack`; Turbopack rejects the worktree-external `node_modules` symlink.
- Backend quick with `--no-setup`: `3644 passed, 80 skipped, 20 deselected, 2 unrelated baseline failures` (legacy length-profile list and removed story-parser re-export).
- Repository contracts for the exact slice: passed; backend black/isort and `git diff --check`: passed.
- Real browser/API/MySQL: Task `6906` completed; invocations `3804–3812` all used `codex:gpt-5.6-sol`, `finish_reason=stop`, and covered 48/48 chapters.
- GPT-5.6 result: 71/100, structure 6.8, character 8.2, world 6.9, eight blocking issues; Revision remains draft and continuity status is failed.

## Next Steps

- Add planning-time causal/resource/obligation watchpoints and deterministic duplicate detection without turning growth into per-chapter KPIs.
- Repair or regenerate the affected chapter chain, then rerun GPT-5.6 review.
- Export the failed manuscript as a clearly labelled draft Word document; do not approve or promote it.

## Linked Commits

- This commit
