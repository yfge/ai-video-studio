# Story Novel Chapter-Planning Quality v3

**Status:** Active

**Goal:** Make the product capable of a roughly two-million-character serial
whose finite chapter count comes from the frozen StorySeed, while using a new
48-chapter product/API/MySQL run as the bounded acceptance sample. The runtime
uses per-chapter planning, block prose, proof-only audit, deterministic Narrative
materialization, one real cancel/resume recovery, and GPT-5.6 batch plus global
acceptance.

**Design sources:**

- `docs/design/story-novel-episode-script.md`
- `docs/design/narrative-memory-and-dramatic-state.md`

**Persistence boundary:** Reuse `generation_plan`, `continuity_ledger`,
`continuity_report`, chapter rows, Narrative Events, Character Memories, and
the existing LLM invocation audit. Add no database table, vector store, package,
or provider bypass.

## Delivery slices

### 1. Structured outline and frozen model policy

- [x] Accept an explicit positive chapter count and selectable planning model
      for StorySeed structuring; require exact contiguous output after at most
      one repair.
- [x] Keep the confirmed structured-outline list as the only novel chapter-count
      authority, with no application-level chapter or total-character ceiling.
- [x] Add bounded hierarchical structuring for outlines longer than 32 chapters:
      one progression plan plus fixed 32-chapter detail batches, every call at
      most 16K output tokens and one repair, with exact contiguous coverage.
- [x] Store optional cognition/capability/resource/activity-time curves on
      progression arcs as soft whole-book guidance, never per-chapter KPIs.
- [x] Add the planning/prose/audit model policy with legacy `model`
      compatibility and mirror the prose model on the Revision.
- [x] Freeze model and length policies after task dispatch or the first chapter;
      require a new Revision for later changes.
- [x] Route planning with reasoning enabled and prose/audit with reasoning
      disabled; keep 12K planning, dynamic 12K–16K prose, 6K audit, and 4K repair
      budgets without an 8192 cap.

### 2. Chapter planning and prose isolation

- [x] Split global planning into model narrative effects plus a versioned server
      state compiler that owns state origins/preconditions, hierarchical
      persistent versus scene locations, and deterministic replay.
- [x] Replace parseable whole-batch repair with full error-vector, field-level
      patches; make batches complexity-adaptive and bind each to one next
      boundary anchor.
- [x] Make semantic planning audit add missing effects and remove exact
      unsupported effects before a plan can become executable.
- [x] Freeze a typed execution contract per required event and separate hard
      Canon/state/time contradictions from advisory web-fiction plausibility,
      pacing, dramatization, and prose-style feedback.
- [x] Add hash-bound `story_novel_chapter_brief.v1`; current commercial policy
      uses 4–6 larger, non-overlapping beats, while historical policy v3 keeps
      6–12 for checkpoint compatibility. Freeze budgets, allowed entity/event/
      effect IDs, motivations, causal bridge, and setup/payoff coverage.
- [x] Limit planning input to current/past contracts, visible Canon/state,
      earlier ready Event/Memory evidence, unresolved threads, recent summaries,
      and prior body tail.
- [x] Exclude all later chapter contracts and record the excluded count and
      optional-context truncation reasons.
- [x] Keep raw Event/Memory and server `expected_delta` out of prose input;
      prose receives only brief, visible Canon, style, length, and a sanitized
      current-chapter projection of events plus visible people/relationships.
- [x] Generate contiguous prose blocks, normalize them before hashing, and
      preserve untouched bytes during one bounded local block repair.
- [x] Rank verified Event/Memory evidence before budgeting and recover complete
      leading prose blocks after transport truncation without rewriting them.
- [x] Bound hard Canon/state context to current references and their direct
      state dependencies, so hundreds of previously introduced entities do not
      accumulate in every later prompt.
- [x] Add source-bound continuity watchpoints for current-chapter resources,
      obligations, elapsed time, causal prerequisites, and relationships. Raw
      Event/Memory stays planning-only; prose omission is valid and audit blocks
      only a concrete contradiction. Prompt policy v10 preserves v1-v9 as
      historical snapshots.
- [x] Reject an exact long-paragraph replay even when both copies occur inside
      the same prose block, so local repair can replace only that block.

### 3. Proof audit, state, and Narrative materialization

- [x] Compile the only expected state delta from the chapter plan and
      `state_before`; reject model-authored state fields.
- [x] Split final prose into stable Unicode sentence IDs/offsets and reconstruct
      every proof quote/span from the stored body.
- [x] Compile a hash-addressed future guard and send only current-body-matched
      claim cards to the audit model, never to prose.
- [x] Remove literal-date and duplicate timeline/milestone/thread prose proofs;
      keep event/state/location/knowledge semantic proofs, and send current state
      plus related future state boundaries only to the audit model.
- [x] Create required World Event and knowledge/arc-intent Character Memory
      candidates deterministically from verified spans, with no Narrative
      extraction model call.
- [x] Commit chapter body plus ledger atomically; make candidate-only and
      evidence-only recovery prose-model-free.
- [x] Persist per-stage calls, tokens, latency, invocation ID, finish reason,
      response hash, block/proof evidence, and the full Canon/context/body/source/
      state hash chain in `story_novel_continuity.v4`.
- [x] Support preplanned-but-later-revealed Canon entities and gated
      chapter-introduced Revision-local people, locations, organizations,
      objects, and concepts with stable IDs and first-appearance ordering.

### 4. Continuity, approval, downstream, and UI

- [x] Review adjacent full-text windows in six-chapter batches and perform one
      global synthesis with Canon, plan, state, candidates, threads, and every
      current chapter/hash. Report conflict, payoff cadence, relationship
      movement, repetition, and hook effectiveness as nonblocking reader signals.
- [x] Add global reader-appeal and optional four-curve progression scores while
      explicitly allowing buildup, failure, and costly regression.
- [x] Recompute v3 brief/block/proof/state/invocation evidence at approval and
      require complete review invocation coverage plus zero deterministic gates.
- [x] Reject v2, stale, noncanonical, incomplete, or hash-mismatched novel
      revisions at the Novel-to-Episode boundary.
- [x] Add three model selectors, task-time locking, six-stage chapter progress,
      calls/tokens/latency, and failed-block presentation.
- [x] Keep legacy Zhihu and v2 read/resume behavior compatible without claiming
      v3 quality guarantees.
- [x] Route the V3 system prompt, outline/repair, Canon/repair, thread schedule,
      batch/full plan, brief, prose, audit/repair, and continuity prompts through
      the shared PromptManager; freeze policy v2 template version/source hashes
      and persist user rendered plus system fingerprints, including truncated
      provider attempts.

### 5. Automated validation

- [x] Add focused tests for policy compatibility/freeze, prompt isolation,
      brief/block contracts, expected delta, sentence spans, future guard,
      atomic checkpoint, evidence-only/candidate-only Resume, invocation binding,
      approval tamper, and v3-only downstream.
- [x] Rerun the complete Story Novel plus StorySeed unit suite after PromptManager
      migration, execution-contract hardening, commercial brief policy, dynamic
      world expansion, hierarchical outline planning, bounded hard context, and
      genre-neutral prompt audit: 867 passed, 1 skipped.
- [x] Commercial length frontend focused suite: 3 passed; lint has zero errors
      and three unrelated existing warnings.
- [x] Full frontend test baseline: 485 passed, 9 unrelated ProductionCanvas
      failures; no Story Novel failure. Webpack production build passes; default
      Turbopack rejects the worktree's external `node_modules` symlink.
- [x] Changed-path repository contracts and whitespace diff checks pass at the
      code checkpoint; rerun after documentation and ledger changes.
- [ ] Run backend quick and full pytest, frontend lint/test/build, repo docs,
      scoped and all-file pre-commit, and production image build.
- [ ] Complete Chrome-first real UI/API validation and store network, console,
      task, and database evidence.

### 6. Real paid 48-chapter acceptance

- [ ] Start Docker dev Compose backend, worker, frontend, nginx, and real MySQL
      with the current source mounted and migration head verified.
- [ ] Preserve old revisions as failure evidence; create a new v3 Revision from
      the confirmed 48-chapter StorySeed through the public product API.
- [ ] Record Story/Seed/Revision/Task IDs plus every provider invocation/model,
      token count, finish reason, latency, request identifier, and response hash.
- [ ] After at least two `ready` chapters, call the official cancel endpoint and
      snapshot chapter business IDs plus body/source/context/state hashes from
      read-only API/MySQL queries.
- [ ] Call `resume-async` once, prove prior body/hash bytes are unchanged, and
      complete 48/48 within each frozen non-whitespace-character range.
- [ ] Prove 48/48 brief, block, proof, expected-delta, future/world audit,
      Narrative candidate, and hash-chain coverage with all hard metrics zero.
- [ ] Run product continuity review, then GPT-5.6 over eight complete six-chapter
      batches and one global synthesis; do not reuse historical manuscripts or
      reports.
- [ ] Require no blocking time/location/knowledge/relationship/ability/world/
      causality issue, overall score at least 75, and structure/character/world
      scores each at least 7.
- [ ] If and only if all gates and editorial thresholds pass, approve the
      Revision, verify canonical promotion and old-Revision candidate isolation,
      and confirm Episode/Script downstream accepts only that canonical v3.

## Artifact contract

Store the run under
`artifacts/runs/story-novel-planning-quality-v3-<timestamp>/` with:

- frozen Seed, structured outline, Canon, generation plan, and model policy;
- per-chapter brief, prompt evidence, block/sentence/proof manifest, expected
  delta, candidates, hashes, and invocation evidence;
- cancel snapshot, Resume comparison, task/network/console/MySQL read evidence;
- continuity metrics/issues and the eight GPT-5.6 batch reports plus global
  report;
- approval/canonical/downstream evidence, or a clear failed/draft verdict.

## Exit condition

Move this plan to `completed/` only when every checkbox in slices 5 and 6 is
backed by current-run artifacts. A green mock suite, provider success, old 48
chapters, or a manually accepted blocker is not acceptance.
