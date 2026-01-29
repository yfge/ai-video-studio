---
id: 2026-01-29T10-13-12Z-docs-media-asset-persistence
date: 2026-01-29T10:13:12Z
participants: [human, codex]
models: [gpt-5]
tags: [docs, media, oss]
related_paths:
  - docs/media-asset-persistence.md
  - docs/README.md
  - tasks.md
summary: "Document generated media persistence (OSS/CDN) naming + metadata contract and update tasks board."
---

## User Prompt

- "视频生成后保存上传到 OSS 不是统一的抽象么？"
- "按tasks.md推进，保证 原子化提交，及时 更新文档"

## Goals

- Write a clear, auditable reference for OSS/CDN object key naming and metadata fields.
- Keep `docs/README.md` and `tasks.md` in sync with the new work.

## Changes

- Added `docs/media-asset-persistence.md` documenting:
  - object key naming rules
  - standard OSS metadata keys (ASCII-only)
  - where rich/non-ASCII data should be stored instead
  - expected storyboard video persistence flow
- Updated `docs/README.md` index to include the new doc.
- Updated `tasks.md` to mark Docker E2E and documentation items complete for P0 Task #2.

## Validation

- Doc-only change; no runtime behavior changes.
- `./docker/build_prod_images.sh` still succeeds after prior commits (kept as the pre-commit gate).

## Next Steps

- Continue P0 Task #2: unify remaining image persistence callsites onto `media_persistence.py`.
- Continue P0 Task #2: add regression test + migration verification for `video_generation_tasks.provider_task_id` length.

## Linked Commits

- (pending)

