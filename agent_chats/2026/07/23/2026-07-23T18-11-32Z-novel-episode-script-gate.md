---
id: 2026-07-23T18-11-32Z-novel-episode-script-gate
date: "2026-07-23T18:11:32Z"
participants: [user, codex]
models: [gpt-5]
tags: [backend, frontend, story, novel, episode, script, lineage, browser]
related_paths:
  - ai-pic-backend/app/services/story/story_novel_downstream_gate.py
  - ai-pic-backend/app/services/story/story_novel_adaptation_service.py
  - ai-pic-backend/app/services/episode/novel_workflow_guard.py
  - ai-pic-backend/app/services/script/novel_source_context.py
  - ai-pic-frontend/src/components/features/story-detail/StoryNovelAdaptationPanel.tsx
  - ai-pic-frontend/src/components/features/story-detail/storyNovelAdaptationGate.ts
  - ai-pic-frontend/src/components/features/stories/StoryProjectCard.tsx
  - docs/exec-plans/active/novel-episode-script-downstream-gate.md
summary: Enforce approved canonical novel and frozen adaptation evidence before Episode materialization, with explicit legacy boundaries and operator-visible gates.
---

## User Prompt

Make the authoritative production path
`IP → confirmed StorySeed/structured outline → approved canonical novel revision
→ adaptation plan → Episode → Script`. Reject prose paths that bypass the
novel, preserve only explicit legacy non-prose compatibility, add complete
lineage and UI gates, validate at backend/frontend/browser levels, and isolate
the delivery from concurrent long-form, audio, LLM-invocation, and output work.

## Goals

- Fail closed unless the revision is approved, current canonical, hash-valid,
  fully generated, and covered by current continuity evidence.
- Freeze an approved adaptation plan against the exact revision, generation
  plan, chapter IDs, body hashes, and source hashes.
- Materialize Episodes only from the frozen mapping; keep Script sourced from
  Episode while exposing the inherited novel evidence.
- Reject synchronous, asynchronous, preview, queued-worker, and freeform
  regenerate bypasses for novel workflows.
- Make the operator sequence and locked states explicit and keep task refresh
  behavior intact.
- Commit only the exact owned slice in the dirty shared worktree.

## Changes

- Added a fail-closed downstream gate for revision lifecycle/canonical
  identity, plan version/hash/coverage, chapter ledger/body/source hashes,
  continuity coverage, adaptation mapping, and adaptation hash.
- Reworked adaptation save/approval/application to freeze and revalidate
  evidence before idempotent return, then persist plan/revision/chapter lineage
  on Treatment, Episode, and step outlines.
- Removed StorySeed from adaptation generation context; the provider prompt now
  receives only approved canonical chapter bodies and revision/plan evidence.
- Guarded direct Episode prompt/context preview, synchronous/async generation,
  queued workers, and both regeneration routes; retained explicit
  `workflow_mode=direct`.
- Extended Script source evidence with generation/adaptation plan hashes and
  chapter body/source hashes while leaving Episode as the Script source.
- Added operator-visible production-chain text, disabled states for
  unapproved/stale/hash-incomplete plans, replaced the novel Story-card direct
  Episode entry with `小说与改编`, and added focused frontend behavior coverage.
- Kept the adaptation panel under the repository size limit by extracting its
  pure frozen-evidence checks into a colocated helper.
- Added an independent execution plan. The shared design source and `tasks.md`
  remain untouched pending main-thread acceptance.

## Validation

- Focused backend in the pinned Python 3.11 `.venv`:
  `./.venv/bin/python -m pytest -q --no-cov
tests/unit/test_story_novel_downstream_gate.py
tests/unit/test_story_novel_adaptation_prompt_boundary.py
tests/unit/test_episode_novel_workflow_boundary.py
tests/unit/test_story_novel_adaptation_chain.py` — 16 passed.
- Actual module imports for the task processor, downstream gate, and async
  Episode worker — passed.
- Frontend focused:
  `npx tsx --test tests/storyNovelAdaptationGate.test.tsx
tests/storyNovelWorkflowPanel.test.tsx
tests/storyProjectCardWorkflow.test.tsx` — 14 passed.
- `npm run lint` — 0 errors and 3 existing warnings. `npm run build` — passed.
- `npm run test` — 458 passed / 9 failed; every failure is in concurrent
  Production Canvas planning-settings or auto-execution WIP. The three owned
  focused suites remain green.
- `python run_tests.py quick --no-setup` — 2839 passed / 1 transient unrelated
  Production Canvas failure; that test immediately passed in isolation. The
  normal setup mode did not enter tests because PATH selected Python 3.13 and
  the pinned pydantic/langchain requirements cannot resolve there.
- `./.venv/bin/python -m pytest -q` — 2842 passed / 7 failed / 5 errors. The
  errors are the known shared `test.db` readonly fixture failure; the failures
  are Timeline/Canvas and main long-form WIP. The sampled Canvas and long-form
  failures passed immediately in isolation. No owned focused test failed.
- `python scripts/check_repo_docs.py` — passed.
- `python scripts/check_repo_contracts.py --mode audit` — passed. Targeted diff
  mode also passed after keeping both regeneration handlers at 50 lines and
  extracting the adaptation evidence helper; the new downstream service is 244
  lines and the touched Episode service is 249.
- Scoped `pre-commit run --files <owned paths>` — formatting, repository-doc,
  repository-contract, ledger, and frontend-lint hooks passed after applying
  their edits. The backend quick hook reported only
  `test_overflow_marks_only_minimal_surplus_rows` and
  `test_patch_rejects_previous_assignment_when_chapter_has_no_slot` from the
  concurrent StorySeed/thread-repair slice; rerunning those exact nodes in the
  pinned `.venv` passed 2/2.
- Chrome DevTools was attempted first and failed because
  `http://127.0.0.1:9222/json/version` returned HTTP Not Found. Playwright
  fallback with the installed Google Chrome executable logged in and verified:
  the authoritative path text; disabled unapproved plan/Episode controls;
  `小说与改编` on novel cards with the direct entry preserved for explicit
  direct Stories; an old applied plan without frozen hashes disabled; and
  prompt preview, context preview, and async generation each returning the
  structured `NOVEL_APPROVAL_REQUIRED` 409.
- Evidence:
  `artifacts/runs/novel-episode-script-gate-20260724T021500/summary.json`.
  No live revision had the new complete approved canonical hash evidence, so
  the positive provider/plan/apply path remains unavailable and is not claimed.
- `./docker/build_prod_images.sh --help` unexpectedly entered the real
  multi-architecture `docker buildx --push` path because the helper has no
  help/dry-run handling. It was terminated with exit 130 before completion;
  no production-build success is claimed, and it must be rerun from the clean
  committed tree to avoid publishing concurrent WIP.

## Next Steps

- Wait for the main long-form slice to commit the untracked generation-plan
  dependencies, then stage only this owned slice and the two precise shared
  hunks.
- Rerun the production image build from that clean committed tree.
- Keep the positive provider/plan/apply browser path open until a genuinely
  hash-valid approved canonical revision exists.

## Linked Commits

- Pending.
