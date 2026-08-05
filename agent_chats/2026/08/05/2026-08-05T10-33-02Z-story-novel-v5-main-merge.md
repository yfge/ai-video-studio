# Story Novel V5 Main Merge

## User Prompt

Merge the completed Story Novel V5 implementation back into the main workspace.
The immediately preceding request to start a paid million-character novel run was
paused before any provider task was launched.

## Goals

- Package only the V5 implementation relative to its isolated worktree base.
- Preserve main-workspace changes and avoid merging the unrelated historical
  commits that precede the V5 worktree.
- Validate the long-form V5 compiler before committing and merging.
- Keep V4 as the default until paid acceptance is complete.

## Changes

- Prepared the topic-neutral V5 consistency core, continuous-prose generation,
  evidence/readability gates, bounded repair/rewrite flow, hash-safe recovery,
  approval projection, compatibility adapters, read-only UI, repository
  contracts, harness scenario, docs, and task-state updates for delivery.
- Added scalable V5 planning for outlines above 32 chapters: the Story-specific
  Schema and initial graph freeze once, then the causal graph compiles in
  16-chapter batches with deterministic simulation and durable checkpoints.
- Split long-form orchestration, contracts, model calls, and checkpoints into
  focused service modules; every new backend service stays below the repository
  250-line hard limit.
- Added dedicated managed prompt templates for long-form foundation compilation,
  causal batches, and their single repair attempts.
- Added a 33-chapter regression proving batch boundaries, merged causal coverage,
  final hashes, and source-bound plan validity.

## Validation

- `/opt/homebrew/Caskroom/miniconda/base/bin/python -m black ...` for the changed
  V5 planning modules and test: passed.
- `/opt/homebrew/Caskroom/miniconda/base/bin/python -m ruff check ...` for the
  changed V5 planning modules and test: passed.
- `/opt/homebrew/Caskroom/miniconda/base/bin/python -m pytest -q --no-cov
  tests/unit/test_narrative_consistency_v5.py
  tests/unit/test_narrative_consistency_v5_transition.py
  tests/unit/test_story_novel_v5_invocation_gate.py
  tests/unit/test_story_novel_v5_plan.py
  tests/unit/test_story_novel_v5_prose_quality.py
  tests/unit/test_story_novel_v5_resume.py`: 33 passed, 1 skipped.
- Prompt policy/runtime/template/genre-neutrality slice: 29 passed.
- `python scripts/check_repo_docs.py`, repository contract audit, harness
  contract tests (6 passed), and `git diff --check`: passed after the long-form
  split.
- Full `pre-commit run --all-files` completed with merge-conflict, whitespace,
  YAML/JSON, Black, isort, Prettier, repository-contract, ledger, and frontend
  lint hooks passing. It remained non-green on the inherited whole-repository
  Ruff backlog, the doc hook's unavailable `python` executable, and two existing
  backend quick-gate failures; the backend run still completed with 3381 passed
  and 65 skipped.
- `BUILD_PUSH=false BUILD_PLATFORMS=linux/amd64
  ./docker/build_prod_images.sh`: backend and frontend production images built
  successfully and remained local; no registry push occurred.
- Earlier V5 delivery evidence remains recorded in the 2026-08-03 V5 ledger:
  Story Novel compatibility 985 passed / 3 skipped, frontend focused 9 passed,
  lint/build/docs/contracts/local non-pushing images passed, and the real page
  was captured with an explicit Playwright fallback.
- No paid provider generation was launched during merge preparation.

## Next Steps

- Commit the exact V5 paths on `codex/story-novel-v5`.
- Cherry-pick that feature commit into `main` instead of merging the branch's
  unrelated pre-V5 history.
- Re-run merge-sensitive contracts and focused tests on `main`.
- Keep V5 disabled by default until paid sample and long-form acceptance pass.

## Linked Commits

- V5 feature commit: this ledger's commit (`feat(story): add generic
  consistency V5`).
- Main integration: the cherry-picked equivalent of the V5 feature commit.
