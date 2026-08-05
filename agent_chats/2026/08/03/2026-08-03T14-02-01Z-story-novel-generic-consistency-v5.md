# Story Novel Generic Consistency V5

## User Prompt

Implement the approved Story Novel V5 plan: topic-neutral consistency schemas,
continuous chapter prose, evidence-bound validation, readability repair/rewrite,
compatibility, operator UI, and validation.

## Goals

- Keep V2-V4 readable and resumable without silent migration.
- Add a pure generic consistency engine with enforceable dependency boundaries.
- Add V5 generation, checkpoint, approval, and read-only operator surfaces.
- Produce focused, repository-wide, and browser evidence without unapproved paid
  provider calls.

## Changes

- Added the V5 design source, active execution plan, task-board entry, and docs
  index links.
- Added a pure `narrative_consistency` engine for dynamic entity types,
  predicates, fact/event graphs, constraints, perspectives, evidence, state
  transitions, simulation, obligations, and deterministic hashes. The core has
  no Story Novel, database, API, provider, or topic-vocabulary dependencies.
- Added repository contracts that reject topic-specific legacy state terms or
  orchestration imports inside the generic engine, plus four unrelated dynamic
  schema fixtures without predicate-ID branches.
- Added V5 planning and generation: source-bound Schema compilation/repair and
  auto-freeze, initial/causal graph simulation, continuous chapter prose,
  one-time truncation continuation with overlap removal, independent claim and
  readability audits, bounded sentence-span repair, optional whole-chapter
  rewrite, best-candidate selection, and fail-closed `review_required` state.
- Added continuity v6 checkpoints, invocation/evidence replay gates, snapshot
  hash chaining, extraction-only recovery, approval/downstream gates, and
  one-way Narrative Event/Character Memory candidate projection.
- Kept V2-V4 read/resume/clone behavior versioned in place, added an internal
  V5 default switch that still defaults to V4, and added V5 API summaries.
- Added the read-only V5 consistency/quality panel and an isolated browser
  scenario that records its frozen Schema, hashes, generic counts, chapter
  status, console, network, DOM, and screenshot evidence.
- Hardened the lite harness so generated env files reach Compose, truthy SQLite
  fallback values work, Story IDs can parameterize browser scenarios, and the
  evidence screenshot scrolls the required UI into view.

## Validation

- `python scripts/check_repo_docs.py`: passed.
- `python scripts/check_repo_contracts.py --mode audit`: passed, including the
  generic-core boundary audit; harness contract tests: 6 passed.
- V5/prompt/task focused backend slice: 53 passed, 1 skipped.
- Story Novel compatibility slice: 985 passed, 3 skipped. A temporary-cwd-only
  prompt template failure passes from the supported `ai-pic-backend` cwd.
- Full non-slow backend slice: 3783 passed, 9 skipped, 94 deselected, with one
  inherited `tests/unit/test_story_parser.py` re-export failure outside the V5
  diff.
- Focused frontend V5/workflow slice: 9 passed. Frontend lint completed with
  zero errors and three existing warnings; `next build` passed. The wider test
  run retains ten untouched Production Canvas failures.
- Exact pre-commit reached and passed doc drift, contracts, ledger, Black,
  frontend lint, Prettier, and isort. It remains non-green because whole-repo
  Ruff reports 76 inherited issues and backend quick reaches the same inherited
  `story_parser` failure.
- `BUILD_PUSH=false BUILD_PLATFORMS=linux/amd64
  ./docker/build_prod_images.sh`: passed for backend and frontend locally.
- Browser run `story-novel-v5-20260803`: doctor passed; authenticated Story
  `73bd8ae886cf40f69b568e3508a94cac` and V5 Revision
  `f6bf7f79bd204d72a0ee942d304445a4` rendered the frozen consistency panel.
  Chrome DevTools at `127.0.0.1:9222` timed out; the explicit Playwright
  fallback passed. Expected mock-environment model-list 503 responses are
  preserved in console/network evidence.
- No paid provider generation or 48-chapter acceptance was run.
- Operational incident: the repository production-image script defaults to
  `BUILD_PUSH=true`; it was interrupted after publishing the backend tag
  `18476cb0` from the dirty V5 worktree. The frontend tag was not pushed. A
  restore from the clean `18476cb0` archive was refused by the permission gate,
  so correcting that shared backend tag requires explicit user authorization.

## Next Steps

- Obtain explicit authorization to restore the shared backend image tag
  `18476cb0` from the clean commit build.
- Resolve or explicitly baseline the unrelated repo-wide test/lint failures.
- Obtain explicit paid-run approval before provider-backed repair/rewrite/resume
  browser evidence, multi-story samples, the blind V4/V5 comparison, or the
  fresh 48-chapter GPT-5.6 acceptance run.
- Keep V4 as the default until every exit condition is met.

## Linked Commits

- Pending.
