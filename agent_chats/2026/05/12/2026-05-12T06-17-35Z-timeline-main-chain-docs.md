---
id: 2026-05-12T06-17-35Z-timeline-main-chain-docs
date: 2026-05-12T06:17:35Z
participants: [human, codex]
models: [gpt-5]
tags: [docs, timeline, spec, audio, render]
summary: "Freeze Timeline Spec v1 docs for the audio-first render/export main chain"
---

## User Prompt

PLEASE IMPLEMENT THIS PLAN: Timeline 主链文档与规范完善计划.

## Goals

- Keep this pass docs/spec-only.
- Make Timeline Spec v1 the documented Episode output SSOT.
- Define `scene_beats -> audio_timeline.beats -> Timeline Spec v1 clips`.
- Document stable `clip_id`, media asset references, render jobs, and the next
  implementation plan.

## Changes

- Rewrote `docs/timeline-rendering-pipeline.md` as the Timeline Spec v1 and
  render/export main-chain contract.
- Rewrote `docs/dialogue-audio-timeline-spec.md` as the audio transition spec
  that feeds Timeline Spec v1.
- Extended `docs/media-asset-persistence.md` with the target `media_assets`
  contract and its relationship to timeline clips, render jobs, OSS metadata,
  and current `video_generation_tasks`.
- Added `docs/exec-plans/active/timeline-main-chain.md`.
- Updated `docs/README.md` and marked only docs/spec tasks complete in
  `tasks.md`.

## Validation

- Docs/spec-only change. No frontend, backend, browser, migration, or API
  validation was run because no runtime code changed.
- `python scripts/check_repo_docs.py` passed.
- `python scripts/check_repo_contracts.py --mode diff docs/timeline-rendering-pipeline.md docs/dialogue-audio-timeline-spec.md docs/media-asset-persistence.md docs/exec-plans/active/timeline-main-chain.md docs/README.md tasks.md agent_chats/2026/05/12/2026-05-12T06-17-35Z-timeline-main-chain-docs.md` completed with no diff-sensitive rules for these files.
- `rg -n "视觉优先|先出分镜" docs/timeline-rendering-pipeline.md docs/dialogue-audio-timeline-spec.md docs/media-asset-persistence.md docs/exec-plans/active/timeline-main-chain.md tasks.md -S` returned no matches.
- `git diff --check` passed.

## Next Steps

- Implement the DB/API foundation for `timelines`, `media_assets`, and
  `render_jobs`.
- Add the import bridge from existing `audio_timeline.beats` into Timeline Spec
  v1.
- Then add render/export and operator UI E2E coverage.

## Linked Commits

- Pending.
