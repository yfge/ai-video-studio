---
id: 2026-07-22T08-00-00Z-story-novel-adaptation-chain
date: "2026-07-22T08:00:00Z"
participants: [user, codex]
models: [gpt-5]
tags: [story, novel, episode, script, lineage]
related_paths:
  - docs/design/story-novel-episode-script.md
  - ai-pic-backend/app/services/story/story_novel_revision_service.py
  - ai-pic-backend/app/services/story/story_novel_adaptation_service.py
  - ai-pic-frontend/src/components/features/story-detail/StoryNovelWorkflowPanel.tsx
  - ai-pic-frontend/src/components/features/story-detail/StoryNovelAdaptationEpisodeCard.tsx
summary: Implement the versioned Story to Novel to Episode to Script production chain.
---

## User Prompt

Implement the “故事 → 小说 → 剧集 → 剧本” production-chain v1 plan, preserving current uncommitted story-outline and novel-entry work and avoiding paid model calls during validation.

## Goals

- Make an approved chaptered novel the narrative SSOT for new series.
- Add editing, optimistic concurrency, explicit continuity review, approval, adaptation planning, and immutable Episode lineage.
- Keep historical/direct and single-video flows compatible and leave the existing Timeline/video chain unchanged.

## Changes

- Added the design truth, active execution plan, task-board positioning, schema migration, revision/chapter models, repository, services, task processor, and business-ID APIs.
- Added chapter checkpoint/resume, local regeneration, downstream invalidation, explicit continuity issues/acceptance, canonical approval, cloning, plan approval, and idempotent Episode application.
- Added direct-generation gating for novel-adaptation Stories and mapped novel source evidence in Script prompt/runtime metadata.
- Added the four-stage Story UI with plain-text chapter editing, ordering, explicit model actions, plan editing, and Episode application.
- Preserved the existing uncommitted outline and legacy Zhihu export UI; unrelated audio-tail WIP and outputs were not modified.

## Validation

- Focused backend chain, payload, migration CRUD, and task-audit tests: `11 passed`.
- Full backend: `2665 passed, 96 skipped`; two shared-`test.db` SQLite I/O failures passed independently. The remaining failure is the pre-existing `test_single_video_canvas_plan_reuses_unique_prompt_asset` baseline (`resolved_context.virtual_ip_id` is `None`).
- Frontend focused workflow/outline/legacy tests: `5 passed`, including editable character-arc mappings; full frontend: `443 passed`, with 9 pre-existing Production Canvas failures. `npm run lint` has 0 errors and 3 pre-existing warnings. `npm run build` passed after allowing the existing Google Geist font fetch.
- Targeted pre-commit formatting, repository contracts, docs, ledger enforcement, and frontend lint passed. Its shared-database backend quick gate reported 2 Timeline failures and 3 SQLite errors; all five nodes passed together immediately afterward (`5 passed`), confirming test-database isolation noise rather than story-chain regressions.
- `./docker/build_prod_images.sh` passed for linux/amd64 and linux/arm64, including both Next.js production builds; the script published backend/frontend images with its pre-commit HEAD tag `e90702a4`.
- `python scripts/check_repo_docs.py`, diff and audit repository contracts, exact-file Black, Python compile/import smoke, and `git diff --check`: passed.
- MySQL migration applied from `d4e5f6a7b8c9` to `e6f7a8b9c0d1`; SQLAlchemy inspection confirmed `stories.workflow_mode`, Episode novel lineage, and `story_novel_chapters`.
- Browser fallback evidence: `artifacts/runs/story-novel-v1-20260722T170000/summary.json`. Chrome DevTools failed twice because `127.0.0.1:9222/json/version` returned HTTP 404, so Playwright used system Chrome. The flow edited and reordered chapters, approved the canonical revision, saved/approved/applied the plan twice with one Episode, inherited three source hashes into Script, and opened Timeline. Console errors and failed API responses: 0.
- After splitting the adaptation editor for repository size limits, Playwright/system Chrome rechecked the real Story 72 page with intercepted draft-plan reads/writes: the `第1集角色弧` editor saved `主角: 接受责任` and `反派: 暴露弱点`; console errors, failed API responses, and paid mutation requests were all 0. Screenshot: `artifacts/runs/story-novel-v1-20260722T170000/character-arcs-editor.png`.
- The final inspectable browser fixture is Story `72` / `547fb6f4be7f42d6b4ba6ff837e5f06e`; retry fixtures Story `64`–`71` were recoverably soft-deleted after validation.
- Paid provider calls: 0. Prose, continuity, adaptation-plan, and Script provider boundaries used deterministic mocks; all editing, approval, plan persistence/application, lineage, Script loading, and Timeline reads used the live API/MySQL stack.

## Next Steps

- Optional product sample tuning remains separate and requires explicit paid-provider approval.

## Linked Commits

- This commit.
