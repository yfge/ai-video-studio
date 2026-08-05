# Story Novel Generic Consistency V5

> Status: Implemented; rollout acceptance pending
> Updated: 2026-08-05
> Applies to: newly created `story_novel_generation_plan.v5` revisions only

## Decision

V5 replaces the fixed novel state vocabulary with one Story-scoped consistency
schema. The platform core knows only entities, predicates, facts, events,
constraints, perspectives, evidence, and narrative obligations. Topic meaning
lives in versioned data compiled from the frozen StorySeed.

V5 prose is generated as one continuous chapter. Scene cards are planning
artifacts, not output blocks. Claims are extracted after writing and only a
validated causal patch can advance the next chapter snapshot.

Historical V2-V4 plans keep their current readers, resume paths, ledgers, and
approval semantics. There is no in-place migration and no new database table.

## Sources of truth

- Frozen StorySeed: authorial structure and source constraints.
- `consistency_schema`: Story-private vocabulary and executable rules.
- `initial_fact_graph`: objective and perspective state before chapter one.
- `causal_event_graph`: ordered chapter obligations and allowed effects.
- `continuity_ledger.v6`: immutable before/after hashes, prose evidence, claims,
  validated patches, readability evidence, and recovery state.
- Approved novel revision: downstream narrative SSOT.

`canon_view` is a read-only projection for operators. It is never validator
input and cannot become a second state authority.

## Generic contracts

### Schema

`story_novel_consistency_schema.v1` contains:

- dynamic entity types with optional generic capabilities;
- predicates declaring value kind, cardinality, mutability, temporal behavior,
  and `causal | observational` persistence;
- event types with roles, preconditions, and effects;
- constraints and perspective definitions;
- a source manifest and stable schema hash.

Condition operators are limited to `all`, `any`, `not`, `exists`, `equals`,
`contains`, and `event_before`. Effect operators are limited to `assert`,
`retract`, `replace`, `reveal`, and `conceal`. Unknown operators and unresolved
references fail closed.

### Facts and evidence

A fact has a stable ID, subject, predicate, typed value, objective or
perspective scope, valid-from/valid-until anchors, and evidence IDs. Only
`causal` facts enter snapshot hashes and blocking validation. Observational
claims remain evidence unless a future event depends on them; such a dependency
must promote the predicate before schema freeze or planning fails.

Evidence identifies the source artifact/version/hash and contiguous sentence
IDs. A model assertion without matching evidence cannot update state.

### Narrative obligations

Setup/payoff, character-arc, scene-purpose, and chapter-hook obligations are
checked separately. They do not masquerade as world facts and cannot mutate the
fact graph.

## Pipeline

1. Compile schema, initial graph, and causal graph from the frozen StorySeed.
   Plans above 32 chapters freeze the Schema/initial graph once, then compile
   the causal graph in 16-chapter batches with a checkpoint after every batch.
2. Run deterministic validation after the foundation and every causal batch,
   then simulate the merged whole-plan graph. Each bounded compile stage allows
   one model repair; a second failure stops before prose.
3. Build chapter scene cards from the current snapshot and chapter obligations.
4. Generate one plain-text chapter body and index stable sentence spans.
5. Extract schema-bound claims, events, perspective changes, and evidence.
6. Validate preconditions, effects, constraints, time, perspective, and future
   boundaries; produce a patch without applying it.
7. Review applicable readability dimensions: scene flow, prose naturalness,
   character voice, dialogue, repetition, and exposition density.
8. Repair the smallest contiguous sentence range once. When consistency passes
   but readability still fails, allow one source-free whole-chapter rewrite.
9. Apply the patch only when both gates pass; otherwise preserve the best body
   as `review_required` and stop the chain.

## Invariants

1. The consistency core imports no Story Novel service, database, API, provider,
   or topic predicate registry.
2. Topic predicate and event IDs occur only in a Story's frozen schema.
3. V5 code never writes V2-V4 state fields such as location/knowledge grants,
   possessions, or owner IDs.
4. A failed body cannot change graph, memory, downstream context, or approval.
5. Resume reuses only schema/plan/body/snapshot hashes from the same Revision.
6. All applicable readability dimensions must score at least 7 and evidence-
   backed blocking issues must be empty.
7. Human acknowledgement cannot bypass hash, consistency, or readability gates.
8. Approved generic events and perspectives may project into existing Narrative
   Event and Character Memory candidates; those projections never write back to
   the generic graph.

## Compatibility and rollout

- V2-V4 clone to the same plan version; V5 clones to V5.
- New revisions use an internal default-schema setting. It stays V4 until V5
  deterministic, browser, and paid acceptance is complete.
- V5 exposes a read-only consistency summary through the existing revision
  response. There is no schema editor or confirmation pause in v1.
- StorySeed changes require a new V5 revision.

## Acceptance

Unit fixtures cover four unrelated genres without core branches on predicate or
event IDs. Local validation covers graph replay, perspective isolation,
continuous prose, repair/rewrite, checkpoint recovery, V2-V4 compatibility,
API serialization, and the operator view.

Paid acceptance requires explicit approval. It consists of three six-chapter
V5 samples, one six-chapter V4/V5 blind comparison, and one fresh 48-chapter V5
run with interruption/resume plus GPT-5.6 batch and global review. Until all
criteria in the active execution plan pass, V5 must not become the production
default.
