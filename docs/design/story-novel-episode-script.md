# Story → Novel → Episode → Script v1

> Narrative memory follow-up: `docs/design/narrative-memory-and-dramatic-state.md`
> defines story-scoped Canon, anchored character memory/growth, manual shared
> memory promotion, audience disclosure, subtext, and the related operator UI.

## Decision

New narrative series use this chain:

`Story Seed → approved novel revision → approved adaptation plan → Episode → Script → Timeline`

There are two complementary sources of truth:

- The approved canonical novel revision is the narrative SSOT for a new series.
- Timeline remains the production-time, clip-order, asset-lineage, render, and delivery SSOT.

`Story`, `Episode`, and `Script` remain the aggregate roots already used by production. v1 does not add a `Series` entity and does not change anything after Script enters Timeline.

## Compatibility boundary

- New Story requests default to `workflow_mode=novel_adaptation_v1`.
- ORM-created rows, historical Story rows, production-canvas compatibility paths, and single-video projects remain `direct`.
- No historical Story or legacy novel export is migrated into chapters.
- Legacy `style=zhihu`, download, task, and `/novel/exports` contracts remain available.
- Direct Episode generation for a `novel_adaptation_v1` Story returns HTTP 409 with code `NOVEL_APPROVAL_REQUIRED`.

## Data model

`story_novel_exports` is the novel revision table. Legacy exports retain `lifecycle_status=legacy`; prose revisions add:

- monotonic `revision_number` per Story;
- lifecycle `legacy | draft | approved | superseded`;
- continuity `unchecked | review_required | checking | passed | failed`;
- adaptation plan `empty | draft | stale | approved | applied`;
- Story snapshot, generation plan, continuity ledger/report, adaptation plan, approval evidence, and content hash.

`story_novel_chapters` stores ordered chapter checkpoints with business ID, title, text, summary, cliffhanger, review status, content hash, and timestamps.

Story stores its workflow mode and current canonical revision FK. Episode freezes:

- source novel FK and business ID;
- adaptation-plan version;
- selected chapter business IDs, summaries, and content hashes;
- the adaptation goal and source novel content hash.

An Episode never follows the Story canonical pointer after it is created.

## State and mutation rules

1. Prose generation creates the draft revision before dispatch, enters
   `generation_plan.status=planning`, and asks the planning model to turn the
   frozen StorySeed outline into a finite, contiguous chapter list.
2. The outline alone determines chapter count and planned total characters.
   There is no application-level chapter or total-length cap. Every chapter has
   a 3000–5000 non-whitespace-character target.
3. One task generates chapters in order and commits each chapter independently.
   Resume skips a complete body only when its context hash still matches; if
   extraction is missing, resume extracts facts/memory without rewriting prose.
4. Only `draft` content is editable. An approved revision must be cloned before editing.
5. Saving or moving chapter N marks affected successors `review_required`, marks continuity `review_required`, and marks an existing adaptation plan `stale`.
6. Saves and reorder requests carry `expected_updated_at`; plan saves carry `expected_version`. Conflicts return 409.
7. Saving never invokes a model. It invalidates that chapter's extraction,
   successor context, continuity, and adaptation state.
8. After every generated chapter, Narrative Event and Character Memory
   candidates are extracted and recorded with their source chapter/hash. They
   are revision-local Canon for later chapters only; approval promotes the
   still-valid candidates to Story Canon in one human boundary.
9. Continuity checks are explicit paid operations: overlapping adjacent
   full-text windows run first, followed by one global synthesis over every
   chapter summary/hash, the plan, facts, character states, and open threads.
10. Unaccepted blocking continuity issues prevent approval. A user may accept a blocker only with a recorded reason.
11. Approving a revision makes it canonical and supersedes the prior canonical revision; old Episode references do not change.
12. An adaptation plan is editable only while draft. Applying an approved plan is idempotent and returns the existing Episode set after the first application.

## Model context boundaries

Prose generation reads only the frozen StorySeed/IP/world snapshot, the current
chapter plan, approved Story Canon, current-revision candidates from valid
earlier chapter hashes, the rolling plot ledger, recent summaries, and the
previous chapter tail. The serialized context is bounded to approximately 32K
characters and records included IDs/hashes plus every truncation reason. It
never concatenates the complete earlier novel and never reads Episode, removing
the former `Episode → Novel → Episode` loop.

Script request schemas do not gain operator parameters. The Episode context builder automatically includes only its mapped source chapter summaries, business IDs, hashes, adaptation goal, novel hash, and plan version. The same evidence is copied into Script metadata and the Task agent run; full unrelated chapters are excluded.

## API surface

All new identifiers are business IDs.

- `POST /stories/business/{story}/novel/generate-async` with `style=prose`;
  `target_words` and `chapter_count` are accepted from old clients but ignored
- `GET /stories/business/{story}/novel/revisions`
- `GET /stories/novel/revisions/{revision}`
- `POST /stories/novel/revisions/{revision}/resume-async`
- `PATCH /stories/novel/revisions/{revision}/chapters/{chapter}`
- `POST /stories/novel/revisions/{revision}/chapters/reorder`
- `POST /stories/novel/revisions/{revision}/chapters/{chapter}/regenerate-async`
- `POST /stories/novel/revisions/{revision}/clone`
- `POST /stories/novel/revisions/{revision}/continuity-check-async`
- `POST /stories/novel/revisions/{revision}/continuity-issues/{issue}/accept`
- `POST /stories/novel/revisions/{revision}/approve`
- `POST /stories/novel/revisions/{revision}/adaptation-plan/generate-async`
- `PATCH /stories/novel/revisions/{revision}/adaptation-plan`
- `POST /stories/novel/revisions/{revision}/adaptation-plan/approve`
- `POST /stories/novel/revisions/{revision}/adaptation-plan/apply`

The Story page presents four stages: Story Seed, novel revision/chapter editor, adaptation-plan editor, and Episode production state.

## Explicit non-goals

- Rich text, drag-and-drop, comments, real-time collaboration, or chapter branching/merge.
- Automatic parsing or migration of historical exports.
- Paragraph-to-scene traceability.
- Cascading regeneration of later chapters, Episode, Script, or Timeline.
- Any change to audio, storyboard, video, render, or export after Script.
