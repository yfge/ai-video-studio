## User Prompt

Implement the outline-driven long-form novel generation plan: StorySeed alone
determines a finite chapter plan, one task generates 3000–5000-character
chapters sequentially, prior plot/facts/character memory are bounded context,
checkpoints resume safely, approval promotes valid revision-local candidates,
and the completed real novel receives a GPT-5.6 consistency and quality review.

## Goals

- Remove prose target-length and chapter-count controls without changing legacy
  Zhihu export limits.
- Add dynamic planning, bounded context evidence, per-chapter length/repair,
  extraction checkpoints, deterministic resume, invalidation, and approval.
- Show planning, generated chapter, and extraction progress in the Story UI.
- Validate the implementation with focused/full gates, a real browser, a
  provider-backed novel, and GPT-5.6 review artifacts.

## Changes

- Added structured dynamic planning with one repair and no application chapter
  cap; persisted `planning`, plan chapter count, and summed target characters.
- Added a 32K context builder prioritizing frozen Canon, knowledge boundaries,
  revision-local prior facts/memory, rolling plot state, recent summaries, and
  previous prose tail, with ID/hash/truncation evidence.
- Added sequential 3000–5000 non-whitespace-character generation, one bounded
  repair, chapter/body/context checkpoints, extraction-only resume, source-hash
  invalidation, and revision-local candidate promotion at novel approval.
- Removed the legacy 8192-output-token branch: `deepseek-chat` now normalizes to
  DeepSeek V4 Flash, omitted limits stay omitted, and the whole-book continuity
  synthesis explicitly uses a 16000-token output budget.
- Replaced monolithic continuity input with overlapping full-text windows and
  a global summary/plan/fact/character/open-thread synthesis whose report lists
  every chapter ID/hash; window issue IDs are namespaced before aggregation so
  the UI has stable unique React keys.
- Removed prose target/chapter controls, refreshed revisions during task
  polling, and exposed planning/extraction progress in a small status component.
- Updated both design sources, the task board, docs index, and the completed
  execution plan.

## Validation

- Focused backend long-form, recovery, provider, task-limit, continuity,
  Narrative Memory, and task-agent persistence suites passed: 33 passed.
- `python run_tests.py quick --no-setup` — 2687 passed, 79 skipped, 20
  deselected; one unrelated existing Production Canvas assertion failed:
  `test_single_video_canvas_plan_reuses_unique_prompt_asset`
  (`resolved_context.virtual_ip_id` was `None`).
- Full backend `pytest` — 2687 passed, 90 skipped; three unrelated existing
  Production Canvas failures.
- `npx tsx --test tests/storyNovelWorkflowPanel.test.tsx` — passed, 3 tests;
  full frontend test run passed 445 tests and retained nine unrelated existing
  Production Canvas failures.
- `npm run lint` — passed with three pre-existing warnings and no errors.
- `python scripts/check_repo_docs.py` — passed.
- `python scripts/check_repo_contracts.py --mode audit` — passed.
- `./docker/build_prod_images.sh` — passed for linux/amd64 and linux/arm64;
  the frontend production build completed successfully. After commit, the same
  build was repeated from a clean detached worktree so the published
  backend/frontend image tag matches the final Git commit.
- `pre-commit run --all-files` was intentionally not run in the dirty worktree
  because it can rewrite unrelated user WIP. The staged snapshot instead passed
  focused tests, frontend lint/build, repository checks, and
  `git diff --cached --check`.
- Real DeepSeek V4 Flash run planned 48 chapters/201600 characters and produced
  48 chapters/198691 characters; all chapters were 3265–4997 characters and
  all 48 extraction checkpoints were ready.
- Resume proof included a rejected 2205-character chapter 44 followed by a
  valid 3665-character retry, plus extraction-only recovery of chapter 11 with
  an unchanged body hash.
- Whole-book continuity task `6512` covered 48/48 chapter ID/hash pairs and
  completed with 117602 prompt tokens, 5171 completion tokens, and an explicit
  `max_tokens=16000`. It reported 167 issues/65 blockers, so the revision
  correctly remains draft and was not promoted to Story Canon.
- Chrome DevTools was unavailable because
  `http://127.0.0.1:9222/json/version` returned HTTP Not Found. The recorded
  fallback was Playwright/System Chrome; its final metrics matched the backend
  and its console error list was empty.
- GPT-5.6 read eight six-chapter batches and produced a global 66/100 review.
  Evidence is under
  `artifacts/runs/story-novel-longform-real-20260723/`.

## Next Steps

- Before approving this particular generated revision, resolve the P0/P1
  timeline, state-ledger, world-rule, duplicate-event, and causal-transition
  findings in the GPT-5.6 report, then rerun extraction and continuity.
- The unrelated Production Canvas backend/frontend baseline failures remain
  outside this change.

## Linked Commits

- This commit.
