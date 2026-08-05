# Story Novel Frozen Snapshot v4

## Goal

Replace the chapter-package context-rebuild boundary with one immutable input
snapshot per provider call, then add current-arc planning and Revision-local
character/world evolution without weakening Canon/state/future gates.

## Source of truth

- `docs/design/story-novel-episode-script.md` owns the generation architecture.
- `docs/design/narrative-memory-and-dramatic-state.md` owns Event/Memory and
  promotion semantics.
- This file owns implementation order and acceptance evidence.
- `tasks.md` owns current work state.

## Delivery slices

1. Add v4/v5 compatibility boundaries and typed Series Bible/Roadmap/Arc,
   character slot, scope node/edge, planner snapshot, intent, and audit contracts.
2. Extend StorySeed hierarchical planning with exact count, soft future arcs,
   character/scope slots, and genre-defined scope taxonomy/graph.
3. Persist a normalized planner snapshot and source manifest before each chapter
   planning call. Make the v4 parser pure: it accepts only response + snapshot.
4. Compile typed chapter effects and expected delta on the server; keep raw
   Event/Memory and future outline data out of the prose packet.
5. Bind proof sentence IDs to the current contract and atomically commit body,
   ledger, candidates, state, and proved provisional world entities.
6. Add arc-boundary slot/directive freezing plus current-state chapter-intent
   refinement, and UI visibility for roadmap, frozen arc, snapshot, stage
   metrics, and provisional entity/scope proposals.
7. Validate compatibility, then run a fresh paid 48-chapter acceptance with
   formal cancel/resume, GPT-5.6 batch/global review, Word export, and approval.

## Invariants

- Total chapter count and positions never change after StorySeed confirmation.
- Only the current arc is detailed; later arcs expose no event/date/outcome text
  to chapter or prose calls.
- Parser, repair, checkpoint, Resume, and approval use the persisted snapshot;
  a live source-hash change makes it stale instead of changing its meaning.
- The model never authors authoritative IDs, state origins, evidence quotes, or
  deltas in v4.
- Failed chapters never mutate Revision-local world state.
- Reader appeal remains an editorial report, not a deterministic chapter gate.

## Validation

- Focused contracts: exact positions, current-arc visibility, snapshot
  determinism, no parser DB access, source drift, entity/scope promotion and
  rollback, semantic time, and prompt visibility.
- Scale: deterministic 800-chapter roadmap plus at least three arc transitions.
- Repository: Story Novel unit suite, backend quick/full, frontend lint/test/
  build, docs/contracts, pre-commit, and production images.
- Runtime: new v4 Story/Revision through UI/API/MySQL; cancel after at least two
  ready chapters; record hashes; Resume to 48/48 without rewriting; continuity,
  GPT-5.6 eight batches plus global review, Word export, approval, and canonical
  isolation.

## Evidence

Store the run under
`artifacts/runs/story-novel-frozen-snapshot-v4-<timestamp>/` with Seed, Bible,
Roadmap, Arc Plans, snapshots, invocations, manifests, hashes, browser/network/
console evidence, review reports, export, and approval proof.
