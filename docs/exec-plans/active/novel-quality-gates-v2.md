# Novel Quality Gates V2: Separate Prose From Audit

**Status:** Active

## Decision

Keep the immutable StorySeed, Canon, chapter contracts, length range, source
hashes, and state lineage.  Split chapter handling into two durable paths:

1. **Prose acceptance** is synchronous and fail-closed only for objective
   boundaries: non-empty/parseable body, provider truncation, chapter-length
   contract, immutable plan/context hashes, and deterministic future-scope
   violations.
2. **Narrative audit** is asynchronous: extract state/evidence from the saved
   body, validate cross-chapter consistency in batches, and attach an
   evidence-addressed report.  An audit failure never silently changes the body
   or authoritative state.

The downstream novel-to-episode approval boundary remains fail-closed. A
revision cannot be approved until every body is accepted, every audit has
coverage, and no unresolved blocking contradiction remains.

## Why

The current path couples creative drafting with quote-shaped knowledge evidence,
state extraction, date anchors, future-event detection, and editorial review.
It creates repair loops where a technically sound body is rewritten to satisfy
an extraction prompt. Recent long-form research supports event-level planning
and separate evidence-grounded consistency evaluation rather than requiring the
writer to emit its audit trace.

## State model

| Body state | Audit state | Meaning |
| --- | --- | --- |
| `body_ready` | `pending` | P0/P1 prose checks passed; not usable as future state yet. |
| `body_ready` | `passed` | Typed delta and evidence are validated; becomes `ready`. |
| `body_ready` | `review_required` | Prose is retained; a reviewer or targeted extractor repair is needed. |
| `gate_failed` | `not_run` | A P0/P1 boundary failed; body may be retained for diagnosis only. |

## Delivery slices

### 1. Preserve prose on audit-only failures

- [ ] Classify violations at the chapter gate as `hard` or `audit`.
- [ ] Persist `audit_pending`/`review_required` records without calling the
      body-rewrite path when only audit violations exist.
- [ ] Keep audit failures from invalidating the saved body hash.
- [ ] Keep later chapter generation blocked until a typed state is promoted;
      do not invent a state transition from an unverified body.

### 2. Independent audit job and report

- [ ] Add an idempotent audit-only task operating on an immutable body hash.
- [ ] Persist source offsets, error type, confidence, severity, and report
      version; never overwrite body text or Canon.
- [ ] Permit one targeted extraction repair; do not ask the prose writer to
      rewrite an otherwise P0/P1-valid chapter.

### 3. Batch consistency and publication gate

- [ ] Run local audits every three chapters and one whole-revision audit.
- [ ] Separate blocking factual/time/state contradictions from editorial scores.
- [ ] Make approval require audit coverage and zero unresolved blockers, but not
      first-pass audit success for every chapter.

## Three-chapter acceptance

- [ ] Three generated bodies pass P0/P1 without truncation, length, or
      hash/lineage failures.
- [ ] An evidence-only extraction failure preserves the body and records a
      recoverable audit item without triggering body regeneration.
- [ ] No unverified state is used to generate a later chapter.
- [ ] A batch report contains stable IDs and source locations for every finding.
- [ ] Human reading confirms audit wording did not distort prose style.

## Stop rule

Stop a full 48-chapter run if any sample chapter has a truncation or
hash/lineage failure, or if the same chapter cannot pass P0/P1 after one
targeted repair. Resolve the output contract before spending on a larger run.
