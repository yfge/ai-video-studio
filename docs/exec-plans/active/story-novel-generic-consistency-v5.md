# Story Novel Generic Consistency V5

**Status:** Implemented; rollout acceptance pending

**Goal:** Deliver a topic-neutral consistency engine and continuous-chapter
quality loop for new novel revisions while preserving V2-V4 behavior.

**Design source:** `docs/design/story-novel-generic-consistency-v5.md`

## Delivery slices

### 1. Source of truth and boundaries

- [x] Add the V5 design, execution plan, task-board entry, and delivery ledger.
- [x] Add a mechanical boundary rule: the generic core cannot import Story
      Novel, API, DB, provider, or topic-specific state modules.
- [x] Keep old state vocabulary inside V2-V4 compatibility paths.

### 2. Generic engine

- [x] Add typed schema, fact graph, event graph, perspective, evidence, and
      narrative-obligation contracts.
- [x] Validate references/operators/types and compile stable hashes.
- [x] Simulate event preconditions/effects and reject cycles, future leakage,
      perspective leakage, and invalid observational dependencies.
- [x] Cover four unrelated schemas without predicate-ID conditionals.

### 3. V5 generation and recovery

- [x] Materialize V5 plans and continuity v6 without a migration.
- [x] Compile and auto-freeze schema/initial graph/causal graph before prose.
- [x] For outlines above 32 chapters, freeze the foundation once and compile
      16-chapter causal batches with deterministic simulation and checkpoints.
- [x] Generate scene cards and one continuous plain-text chapter.
- [x] Extract evidence-bound generic claims and apply only validated patches.
- [x] Gate readability, perform one sentence-range repair, then one optional
      whole-chapter rewrite, and stop `review_required` after the bounded budget.
- [x] Preserve hash-safe checkpoints, extraction-only recovery, and fail-closed
      state application.

### 4. Approval, projection, and UI

- [x] Require complete V5 hash, claim, patch, readability, and report coverage
      for approval and downstream adaptation.
- [x] Project approved generic events/perspectives into existing Narrative
      candidates without making those candidates graph inputs.
- [x] Add a read-only consistency model panel and chapter quality status.

### 5. Validation

- [x] Pass focused V5 backend/frontend tests, docs/contracts, frontend lint and
      build, and a local non-pushing production image build.
- [ ] Clear repository-wide inherited failures: the full non-slow backend run
      has one pre-existing `story_parser` re-export failure; whole-repo Ruff and
      frontend tests also retain unrelated baseline failures.
- [x] Record real-browser login, StorySeed, V5 Revision, auto-frozen Schema and
      read-only quality panel evidence. Chrome DevTools transport was unavailable,
      so the recorded engine is Playwright and the fallback is explicit.
- [ ] Record paid/provider-backed local repair, whole-chapter rewrite, resume,
      quality failure, and approval-block browser paths.
- [ ] After explicit paid-run approval, complete the three six-chapter samples,
      blind V4/V5 comparison, and fresh 48-chapter GPT-5.6 acceptance run.

## Current evidence

- Generic/V5 focused backend slice: `53 passed, 1 skipped`.
- Long-form batched-compiler regression: `33 passed, 1 skipped` across the V5
  core/plan/prose/resume slice, including explicit 16/16/1 chapter boundaries.
- Story Novel compatibility slice: `985 passed, 3 skipped`; its only
  temporary-cwd prompt-path failure passes from the supported backend cwd.
- Full backend non-slow slice: `3783 passed, 9 skipped, 94 deselected`, plus one
  inherited `tests/unit/test_story_parser.py` failure outside the V5 diff.
- Focused frontend V5/workflow slice: `9 passed`; lint has zero errors and the
  production build passes.
- Browser artifacts: `artifacts/runs/story-novel-v5-20260803/`.
- Default new-Revision version remains V4. V5 requires the internal version
  switch until the paid exit condition is met.

## Exit condition

V5 may become the default only after all deterministic and browser checks pass,
paid acceptance has durable artifacts, all 48 chapters are hash-valid, no
blocking issue remains, overall is at least 80, prose at least 8, structure /
character / world at least 7, and prose repair or rewrite rate is at most 25%.
