---
id: 2026-03-30T16-34-47Z-tasks-timeline-first-board
date: 2026-03-30T16:34:47Z
participants: [human, codex]
models: [gpt-5]
tags: [planning, tasks, timeline]
related_paths:
  - tasks.md
summary: "Rewrote tasks.md into a 6-week timeline-first execution board."
---

## User Prompt

Rewrite `tasks.md` around a timeline-first execution model, delete non-supporting sections, and then commit the change.

## Goals

- Make `tasks.md` an execution board instead of a project archive.
- Encode the product thesis that timeline is the system SSOT.
- Remove roadmap items that do not directly support `audio -> timeline -> clip -> render -> export`.
- Commit only the board rewrite and its matching ledger entry.

## Changes

- Replaced the old long-form board in `tasks.md` with a short 6-week execution board.
- Added a top-level product thesis: professional short-drama teams, ToB workflow system, timeline-first, audio-constrained production.
- Reduced the board to four active sections:
  - `P0: Timeline SSOT`
  - `P0: Audio-First Production Chain`
  - `P0: Stability And De-Legacy`
  - `P1: Operator Workflow`
- Added a compact `6-Week Exit Criteria` section.
- Deleted historical completed sections and long-range roadmap items that do not directly support the timeline-first core.

## Validation

- Read the rewritten `tasks.md` top-to-bottom to confirm it only contains the 4 timeline-first execution sections and the 6-week exit criteria.
- Verified the removed legacy section headings no longer appear in `tasks.md`.
- Ran `./docker/build_prod_images.sh` successfully before commit; backend and frontend production images built and pushed with tag `4ef8a05`.
- Kept unrelated in-progress audio service edits out of scope for this commit.

## Next Steps

- Use the rewritten board as the only active planning surface for the next 6 weeks.
- Land Timeline Spec v1 and clip identity before expanding any new feature scope.
- Continue keeping unrelated in-progress workspace edits out of this commit.

## Linked Commits

- Pending
