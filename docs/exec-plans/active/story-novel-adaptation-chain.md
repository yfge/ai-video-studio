# Story → Novel → Episode → Script v1 Execution Plan

**Goal:** Make an approved, editable, chaptered novel the narrative source for new series while preserving Timeline as production SSOT.

**Architecture:** Upgrade `story_novel_exports` into revisions, add chapter checkpoints, store draft adaptation plans on the revision, and freeze source evidence on Episode. Reuse the current Story/Episode/Script/Timeline chain and existing text-generation task.

## Delivery slices

- [x] Establish the design source of truth, task-board entry, and migration surface.
- [x] Add revision/chapter lifecycle, optimistic editing, reorder invalidation, clone, continuity approval, and canonical pointer.
- [x] Add checkpoint/resume and local chapter regeneration on the existing Celery task.
- [x] Add adaptation-plan generation/edit/approval and idempotent Episode application into StoryTreatment/StoryStepOutline.
- [x] Block direct Episode generation for new novel-adaptation Stories while preserving direct/single-video compatibility.
- [x] Inherit mapped novel anchors in Script prompt context and runtime evidence.
- [x] Add the four-stage Story operator UI without overwriting the existing outline/export WIP.
- [x] Add focused backend and frontend tests using mocks only.
- [x] Complete repository-wide gates and non-billable real-browser validation.

## Acceptance evidence

- A provider failure after chapter 1 preserves chapter 1; resume calls the mock only for missing positions.
- An approved revision is immutable and cloning creates the next draft revision.
- Editing chapter N invalidates successor review and an existing plan.
- Reapplying an applied plan returns the same Episode IDs.
- Episode and Script evidence contain only mapped chapter anchors and hashes.
- Legacy direct Story and single-video paths are unaffected.
- Browser flow uses intercepted generation/check/plan calls; no paid provider is invoked.
- Browser evidence: `artifacts/runs/story-novel-v1-20260722T170000/summary.json`.
