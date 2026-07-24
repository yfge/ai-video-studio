# Canonical Novel → Episode → Script Downstream Gate

**Goal:** Make the approved current novel revision and its approved adaptation
plan the only prose source for Episode materialization, while preserving the
explicit legacy `direct` boundary and keeping Script sourced from Episode.

**Architecture:** Reuse `StoryNovelExport`, its generation-plan/continuity
evidence, `adaptation_plan`, and `Episode.source_chapter_refs`. Add a fail-closed
service gate and connect existing API, Celery, adaptation, and operator UI
surfaces without a schema or dependency change.

## Delivery slices

- [x] Validate approved lifecycle, current canonical identity, revision content
      hash, generation-plan version/hash/coverage, and chapter ledger/report
      evidence.
- [x] Freeze adaptation-plan version/hash plus revision, generation-plan, and
      chapter body/source hashes.
- [x] Require complete current-chapter coverage and reject cross-revision or
      stale references with structured 409/422 errors.
- [x] Apply Episodes and step outlines only from the approved frozen plan and
      preserve complete lineage for downstream Script evidence.
- [x] Reject Story/StorySeed direct generate, prompt/context preview, queued
      worker, and legacy freeform regenerate paths for novel workflows.
- [x] Preserve explicit `workflow_mode=direct` compatibility.
- [x] Show `故事大纲 → 小说审批 → 改编计划 → 剧集 → 剧本` and disable downstream
      actions until each gate passes.
- [x] Add focused backend and frontend boundary tests.
- [x] Run backend quick/full and frontend lint/test/build, recording unrelated
      shared-worktree and test-database baseline failures without claiming green.
- [x] Complete real-browser API/UI validation and record console/network
      evidence without fabricating provider or database success.
- [x] Run repository contracts and scoped pre-commit, recording the two
      shared StorySeed/thread-repair quick-gate failures that pass in isolation.
- [ ] Run the production image build from the eventual clean committed tree;
      the script is a multi-architecture registry push, so the dirty-worktree
      invocation was stopped before completion.
- [ ] Stage only the owned slice after the main long-form dependency commit,
      excluding concurrent long-form, audio, LLM-invocation, and `outputs/`
      work.

## Acceptance evidence

- Focused backend: 16 passed in the pinned Python 3.11 `.venv`.
- Import-safe: task processor, downstream gate, and async Episode worker import
  successfully.
- Frontend focused: adaptation, workflow, and list-card gates 14 passed; lint
  has 0 errors and production build passed.
- Backend quick reached 2839 passed / 1 unrelated transient Canvas failure,
  which passed in isolation. Backend full reached 2842 passed / 7 failures / 5
  errors; the errors are the shared `test.db` readonly fixture defect and the
  failures are Timeline/Canvas/long-form WIP, with sampled failures passing in
  isolation.
- Frontend full reached 458 passed / 9 failures, all in concurrent Production
  Canvas planning-settings/auto-execution WIP.
- Chrome DevTools failed at `127.0.0.1:9222/json/version` with HTTP Not Found.
  Playwright using the installed Chrome executable verified the visible locked
  states and three structured 409 bypass responses. Evidence:
  `artifacts/runs/novel-episode-script-gate-20260724T021500/summary.json`.
- Live data had no new hash-valid approved canonical revision. The positive
  plan/apply path remains blocked rather than fabricating approval; an old
  applied plan lacking frozen hashes was visibly disabled.
- Shared hotspots were limited to `_generate_adaptation` plus necessary imports
  and the final adaptation-panel render condition, then returned to the main
  long-form task.
- The adaptation panel's pure evidence checks were extracted into a 70-line
  colocated helper; the component is 207 lines, and the targeted repository
  contract check passes without adding a baseline exemption.
- Scoped pre-commit static, formatting, repository-contract, ledger, and
  frontend-lint hooks passed after applying their edits. Its backend quick gate
  reported two shared StorySeed/thread-repair failures; both exact nodes passed
  immediately in isolation.
- The production build helper has no dry-run/help path and invokes
  multi-architecture `docker buildx --push`. It was stopped with exit 130
  because the shared tree is dirty and must not publish an image that mixes
  concurrent WIP.
- Design source and `tasks.md` remain owned by the main task until it accepts a
  minimal append.
