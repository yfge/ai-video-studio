# Structured Outline And Platform Lengths

**Status:** Active

**Goal:** Make a confirmed, editable StorySeed chapter outline the only source
of chapter structure, while each Novel Revision independently owns its platform
length profile, per-chapter overrides, model, generation state, and approval
evidence.

**Design source:** `docs/design/story-novel-episode-script.md`

**Architecture:** Extend `story_seed_v1` compatibly to `story_seed_v2`; reuse
`story_novel_exports.generation_plan`, chapter checkpoints, continuity ledger,
Narrative Events, and Character Memories. Materialize a frozen
`generation_plan` v4 from the confirmed outline plus Revision-owned length
settings. Do not add a database or storage dependency.

## Delivery slices

### 1. Contracts and compatibility

- [x] Add `story_seed_v2` with versioned `outline_text` and
      `structured_outline`.
- [x] Validate non-empty contiguous chapters, required chapter fields, explicit
      ending coverage, and complete v1 text-outline upgrade with one repair.
- [x] Validate endpoint-dumped StorySeed dictionaries again at the service
      boundary; use the Story model for asynchronous structuring or the stable
      `deepseek:<DEEPSEEK_DEFAULT_MODEL>` default.
- [x] Add configurable short/standard/long/custom length profiles and integer
      `min <= target <= max` validation.
- [x] Accept per-chapter overrides and derive planned min/target/max totals.
- [x] Keep prose legacy length/chapter inputs ignored with a compatibility
      warning; preserve Zhihu semantics.

### 2. Revision plan and lifecycle

- [x] Materialize `generation_plan` v4 with StorySeed version, outline hash,
      profile snapshot, resolved chapter ranges, totals, and plan version.
- [x] Freeze outline, profile, overrides, and model atomically at dispatch.
- [x] Keep length-only edits local: `target_changed` when the body still fits,
      `length_mismatch` when it does not, without invalidating unchanged-source
      facts or memories.
- [x] Mark content-plan edits, reorder, split, merge, add, and delete operations
      stale from the earliest affected chapter.
- [x] Preserve optimistic concurrency, immutable approvals, clone semantics, and
      revision-local candidate isolation.

### 3. Generation and recovery

- [x] Preflight provider output capability against every resolved chapter
      maximum and fail before dispatch when unsupported.
- [x] Generate sequentially with chapter-specific ranges and locally computed
      non-whitespace counts.
- [x] Replace fixed output ceilings with provider-aware token budgeting.
- [x] Perform at most one bounded length repair without echoing an oversized
      body in full.
- [x] Preserve valid body checkpoints, support extraction-only resume, and
      expose body/extraction progress separately.
- [x] Make approval verify plan/outline/source/body hashes, all resolved ranges,
      extraction coverage, and continuity coverage, and reject every Revision with
      any blocking issue. Reviewer acknowledgement/reason remains audit-only.

### 4. API and operator UI

- [x] Add length-profile read, StorySeed save/confirm, Revision create/update,
      and Revision generation endpoints from the design source.
- [x] Add a structured-outline table with add, delete, reorder, split, merge,
      and all required story fields.
- [x] Add preset/custom defaults, bulk application, per-chapter overrides, and
      live min/target/max totals.
- [x] Lock plan controls while generation is running and show stale,
      mismatch, body, extraction, and resume states.
- [x] Preserve the existing Story stages and legacy Zhihu entry.

### 5. Deterministic validation

- [x] Cover v1 upgrade, 48-chapter completeness, no application cap, invalid
      plan repair, profile inheritance, overrides, and total calculation.
- [x] Cover per-chapter short/long/empty/alias handling and exactly one repair.
- [x] Cover body and extraction checkpoints, extraction-only resume, and
      provider capability preflight.
- [x] Cover length-only versus content-plan invalidation.
- [x] Cover Story, Revision, source-hash, and future-chapter isolation plus
      current-Revision-only Canon promotion.
- [x] Cover frontend removal of whole-book inputs, outline editing, profiles,
      overrides, totals, progress, locking, and legacy Zhihu behavior.
- [x] Run repository docs, changed-path contracts, and whitespace diff checks
      for the documentation/ledger synchronization slice.
- [ ] Run the remaining focused backend/frontend suites, lint, build where
      required, and the complete non-paid real-browser flow.

### 5.1 Current implementation evidence

- [x] The latest focused backend group covering StorySeed dictionary/model
      boundaries plus Canon milestone/outcome, plan replay, actual-body, and resume
      behavior passed 39 tests.
- [x] The real Story UI confirmed a 48-chapter `story_seed_v2` for Story
      `702dcae4a23c4533ae11f0d2e2a69eda` and created standard-serial Revision
      `53dee6c31d8d4f0eada05bb0e45eb0b3`.
- [x] Chrome DevTools was attempted first but
      `127.0.0.1:9222/json/version` returned HTTP Not Found; the confirmation and
      Revision screens were exercised through the Chrome extension fallback.
- [ ] Complete profile override, two-Revision isolation, full console/network,
      and end-to-end generation browser evidence.

### 6. Real-model acceptance

- [ ] Obtain explicit approval before any paid provider run.
- [ ] Generate one complete long novel from a confirmed v2 outline using a
      Revision profile and at least one chapter override.
- [ ] Record provider/model/request IDs and usage, frozen plan/hash evidence,
      per-chapter actual counts, extraction/source hashes, resume behavior, browser
      network/console evidence, and continuity verdict.
- [ ] Demonstrate two differently configured Revisions from one StorySeed using
      deterministic generation or fixtures; prove their candidates, memories, and
      future state do not cross.
- [ ] Approve only a blocker-free current Revision and prove only its valid
      candidates enter Story Canon.

Tasks `#6513`–`#6519` and text invocations `#372`–`#384` are current
phase evidence only. At this checkpoint task `#6519` remains in chapter
planning and the Revision has 0/48 generated bodies; these records do not
satisfy profile-override, two-Revision, completed-novel, approval, or quality
acceptance.

## Acceptance criteria

- [x] A user can upgrade text into a complete editable structured outline and
      confirm a frozen StorySeed version.
- [x] The confirmed chapter list alone determines chapter count and order.
- [ ] Profiles, custom defaults, chapter overrides, and derived totals work
      without a whole-book target input.
- [ ] Every generated body is checked against its own resolved range.
- [x] A failed body or extraction resumes from the correct checkpoint.
- [ ] Length-only changes preserve unchanged-source facts and memories.
- [ ] Content-plan changes deterministically expose stale downstream state.
- [ ] Two Revisions from one StorySeed remain isolated before approval.
- [ ] Approval promotes only current, hash-valid candidates.
- [ ] One real-model long novel passes its configured per-chapter ranges.

## Evidence contract

Evidence lives under `artifacts/runs/<run_id>/` and the matching delivery ledger
references, rather than embeds, large artifacts. A final run bundle includes:

- StorySeed version and structured-outline hash;
- both Revision IDs, profile snapshots, overrides, and generation-plan versions;
- planned and actual per-chapter counts plus aggregate totals;
- task/request IDs, provider/model/usage, checkpoints, and resume evidence;
- event/memory IDs with Revision and source hashes;
- approval/Canon diff;
- browser engine, fallback reason, network results, console errors, and
  screenshots.

`artifacts/runs/story-novel-longform-real-20260723/` remains evidence for the
completed uniform 3K–5K baseline. It does not satisfy this plan's profile,
override, two-Revision isolation, or blocker-free approval criteria.

## Exit condition

Move this plan to `docs/exec-plans/completed/` only after every acceptance item
has durable test or runtime evidence and the matching task-board and delivery
ledger state are updated in the same logical delivery.
