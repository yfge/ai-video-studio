# Story → Novel → Episode → Script v1

## Decision

New narrative series use this chain:

`Story contract → approved novel revision → approved adaptation plan → Episode → Script → Timeline`

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

1. Prose generation creates the draft revision before dispatch and commits each chapter independently.
2. Resume skips existing chapter positions and generates only missing checkpoints.
3. Only `draft` content is editable. An approved revision must be cloned before editing.
4. Saving or moving chapter N marks affected successors `review_required`, marks continuity `review_required`, and marks an existing adaptation plan `stale`.
5. Saves and reorder requests carry `expected_updated_at`; plan saves carry `expected_version`. Conflicts return 409.
6. Continuity checks are explicit paid operations. Saving never invokes a model.
7. Unaccepted blocking continuity issues prevent approval. A user may accept a blocker only with a recorded reason.
8. Approving a revision makes it canonical and supersedes the prior canonical revision; old Episode references do not change.
9. An adaptation plan is editable only while draft. Applying an approved plan is idempotent and returns the existing Episode set after the first application.

## Model context boundaries

Prose generation reads only the frozen Story/IP/world/structured-contract snapshot and previous generated chapter summaries. It never reads Episode, removing the former `Episode → Novel → Episode` loop.

Script request schemas do not gain operator parameters. The Episode context builder automatically includes only its mapped source chapter summaries, business IDs, hashes, adaptation goal, novel hash, and plan version. The same evidence is copied into Script metadata and the Task agent run; full unrelated chapters are excluded.

## API surface

All new identifiers are business IDs.

- `POST /stories/business/{story}/novel/generate-async` with `style=prose`
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

The existing Story page presents four stages: Story contract, novel revision/chapter editor, adaptation-plan editor, and Episode production state.

## Explicit non-goals

- Rich text, drag-and-drop, comments, real-time collaboration, or chapter branching/merge.
- Automatic parsing or migration of historical exports.
- Paragraph-to-scene traceability.
- Cascading regeneration of later chapters, Episode, Script, or Timeline.
- Any change to audio, storyboard, video, render, or export after Script.
