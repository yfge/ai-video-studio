# Canon-gated Long-form Quality Loop

**Status:** Active

**Goal:** Compile one immutable Canon before prose, validate each chapter's
actual state change against a typed contract, support human-confirmed Canon
repair plus earliest-safe resume, and produce deterministic continuity evidence
and independent editorial quality scores.

**Design sources:**

- `docs/design/story-novel-episode-script.md`
- `docs/design/narrative-memory-and-dramatic-state.md`

**Architecture:** Reuse `story_novel_exports.generation_plan`,
`continuity_ledger`, `continuity_report`, chapter rows, Narrative Events, and
Character Memories. Add focused Canon, context, state-extraction, gate,
continuity-contract, and Canon-edit services. Do not add a database table,
vector store, or dependency.

This plan hardens the completed uniform 3000–5000-character baseline. It does
not replace or weaken the separate structured-outline/platform-length plan.
When that plan materializes a later generation-plan version, it must carry
forward the Canon/state guarantees defined here.

## Delivery slices

### 1. Canon compilation and chapter contracts

- [x] Split planning into bounded Canon compilation and chapter-contract
      generation, with one format repair per phase.
- [x] Add typed Canon IDs/hash for timeline, entities, initial states, knowledge
      and permission boundaries, world rules, one-shot milestones, and character
      arcs.
- [x] Require strict Canon `gate_version=1` plus entity-backed milestone typed
      outcomes with real JSON values; mirror the gate version on the plan.
- [x] Add chapter preconditions, required/forbidden events, typed transitions,
      knowledge/location grants, consumed milestones, due payoffs, and Canon refs.
- [x] Add deterministic ID/reference, state-chain, knowledge-order, milestone,
      payoff, and character-arc validation before prose.
- [x] Restrict knowledge changes to source-event-backed `knowledge_grants`;
      reject `knowledge` in ordinary state transitions.
- [x] Gate future milestone outcomes at chapter-zero Canon validation,
      deterministic whole-plan replay, and actual-body state validation.
- [x] Keep old plans readable and prevent the long-form path from reintroducing
      a fixed 8192-output-token cap.

### 2. Actual-body state gate and checkpoint

- [x] Restrict chapter N prose to the current frozen structured-outline
      contract; exclude the whole outline, ending, later chapter contracts, and
      future character-arc checkpoints/end state from the prose prompt.
- [x] Give only the independent state auditor a compact future-event denylist,
      reject `premature_future_event_ids` and all unplanned typed deltas, and never
      apply a failed delta.
- [x] Put non-truncatable `hard_constraints` before optional facts, memories,
      summaries, and prose tail in the roughly 32K-character context budget.
- [x] Independently extract a typed state delta from actual prose rather than
      trusting the generation response's plot delta.
- [x] Validate length, preconditions, location, knowledge, permissions, object
      ownership, world rules, milestones, and threads.
- [x] Combine all body/state failures into one prose repair, re-extract, and
      stop with a preserved `gate_failed/review_required` body on the second
      failure.
- [x] Record Canon/context/body/source/state hashes, typed delta, validation,
      repair counts, and Narrative IDs/hashes in
      `story_novel_continuity.v3`.
- [x] Resume only matching `ready` checkpoints; run extraction-only recovery
      when the body/state gate is complete; regenerate from the earliest
      `gate_failed` or `stale` position.
- [x] Reject failed, old-gate, invalid, or hash-mismatched planning checkpoints;
      reuse only a hash-valid `gate_version=1` Canon for chapter-planning repair,
      never the failed chapter plan itself.

### 3. Canon repair, continuity, and approval

- [x] Add optimistic typed Canon save without a model call and compute the
      earliest invalid chapter from changed Canon refs.
- [x] Mark that chapter through the end stale and require an explicit
      sequential Resume.
- [x] Upgrade layered review to `story_novel_continuity_review.v3` with complete
      Canon, state hash chain, typed deltas, facts, memories, open threads, and all
      current chapter IDs/hashes.
- [x] Return Canon-targeted repair groups and independent editorial scores.
- [x] Compute seven deterministic hard metrics plus observational
      `chapter_repair_rate`.
- [x] Require complete current hashes, state validation, report coverage, zero
      hard metrics, and no unaccepted model blockers before approval; audit reasons
      cannot bypass deterministic gates.

### 4. API and operator UI

- [x] Add
      `PATCH /stories/novel/revisions/{revision}/canon` with expected plan version,
      expected Canon hash, and complete typed Canon.
- [x] Extend revision response types with Canon, chapter contracts, state
      validation, quality metrics, repair groups, and earliest stale position.
- [x] Add Canon editing/suggestion staging, quality overview, state-validation
      progress, gate failure details, and range-resume controls.
- [x] Keep prose requests free of whole-book target/chapter inputs and preserve
      legacy Zhihu behavior.

### 5. Deterministic validation

- [x] Latest focused backend milestone-outcome, plan replay, actual-body,
      checkpoint/resume, StorySeed boundary, and planning-model regressions:
      39 passed.
- [ ] Complete remaining focused backend approval/API/invalidation coverage.
- [x] Run repository docs, changed-path contracts, and whitespace diff checks
      for the documentation/ledger synchronization slice.
- [ ] Run `python run_tests.py quick`, full backend `pytest`, frontend lint and
      tests, and production image build.
- [ ] Run `pre-commit run --all-files` from a state that cannot rewrite
      unrelated user WIP, or record the exact safety fallback and scoped evidence.
- [x] Attempt Chrome DevTools first and record the actual transport failure:
      `127.0.0.1:9222/json/version` returned HTTP Not Found; use the Chrome
      extension fallback for the real Story UI rather than claiming DevTools proof.
- [ ] Complete the StorySeed → generation → gate failure → Canon repair → range
      resume → continuity → approval browser path with console/network evidence.

### 6. Real-model acceptance

Current staged evidence is not acceptance: Story
`702dcae4a23c4533ae11f0d2e2a69eda` has a confirmed 48-chapter StorySeed v2 and
Revision `53dee6c31d8d4f0eada05bb0e45eb0b3` uses
`deepseek:deepseek-v4-flash`. Tasks `#6513`–`#6518` record one structuring
provider failure, a successful structuring retry, Canon/plan validation
failures, and one user cancellation. Task `#6519` is still in
`planning/chapters`, with 0/48 bodies generated. Text invocations `#372`–`#384`
are persisted provider attempts, not proof that deterministic planning or the
novel passed. Therefore none of the acceptance items below is complete.

- [ ] Create a new StorySeed unrelated to the earlier “memory tax” sample whose
      outline explicitly contains 48 chapters and exercises fixed dates, travel
      time, a unique transferable object, permission escalation, delayed identity
      reveal, one-shot milestones, and cross-chapter payoffs.
- [ ] Generate 48/48 chapters with the latest production generation model; keep
      every body within 3000–5000 non-whitespace characters.
- [ ] Prove 48/48 Narrative fact/memory extraction and typed-state validation,
      complete Canon/source/state hash chains, zero deterministic hard metrics, no
      unaccepted blocker, and one real checkpoint/resume recovery.
- [ ] Run GPT-5.6 review in eight six-chapter batches plus one global synthesis.
- [ ] Require no blocking time, location, knowledge, relationship, ability,
      world-rule, or causal contradiction; require at least 75/100 overall and at
      least 7/10 for structure, character, and world-building.
- [ ] Save the StorySeed, Canon, chapter contracts, prompt evidence, hashes,
      product report, batch reviews, and global review under
      `artifacts/runs/story-novel-canon-quality-real-<timestamp>/`.
- [ ] Do not approve or claim acceptance if any criterion fails.

## Acceptance criteria

- [ ] Canon and chapter contracts fail closed before prose after one repair.
- [ ] Prompt evidence proves chapter N contains its current contract and no
      semantic/title/state marker from N+1 or later.
- [ ] No non-negotiable Canon item is truncated from a chapter prompt.
- [ ] A gate-failed chapter preserves its body/evidence but cannot affect later
      state, memory, or generation.
- [ ] Resume reuses only fully matching checkpoints and never reads future,
      cross-Revision, or cross-Story state.
- [ ] A human-confirmed Canon edit invalidates exactly the earliest affected
      chapter and all successors without invoking a model.
- [ ] Approval cannot be forced through a nonzero hard metric, broken hash
      chain, missing extraction, missing report coverage, or invalid length.
- [ ] Real-model evidence meets every criterion in slice 6.

## Evidence contract

The matching `agent_chats` record lists commands and compact verdicts. Large
runtime outputs stay under `artifacts/runs/<run_id>/` and include provider,
model, parameters, task/revision IDs, chapter/hash coverage, browser
engine/fallback, console/network results, `gate_version`, milestone outcome
coverage, plan-replay evidence, and GPT-5.6 review inputs/outputs. A succeeded
provider invocation is recorded separately from the task's deterministic gate
result.

## Exit condition

Move this file to `docs/exec-plans/completed/` only after all deterministic
validation, real-browser, and real-model acceptance boxes above have durable
evidence; then update `tasks.md`, `docs/README.md`, and the delivery ledger in
the same logical commit.
