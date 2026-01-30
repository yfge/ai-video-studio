---
id: 2025-10-20T10-20-00Z-alembic-merge-heads
date: 2025-10-20T10:20:00Z
participants: [human, codex]
models: [gpt-4o-mini]
tags: [backend, migrations]
related_paths:
  - ai-pic-backend/alembic/versions/7f3d2a1b9c00_merge_heads_story_tables.py
  - ai-pic-backend/alembic/versions/0a4c3f0a6b12_enhance_storyboard_metadata.py
  - ai-pic-backend/alembic/versions/a1b2c3d4e5f6_add_story_structure_tables.py
summary: "Add Alembic merge revision to unify multiple heads (storyboard metadata vs. story structure tables)."
---

## User Prompt

执行 `migration upgrade` 报错：Multiple head revisions are present。需要合并分支头。

## Goals

- 通过 Alembic merge 将 `0a4c3f0a6b12` 与 `a1b2c3d4e5f6` 统一为单一 head，便于 `upgrade head`。

## Changes

- 新增 `7f3d2a1b9c00_merge_heads_story_tables.py`，`down_revision=("0a4c3f0a6b12","a1b2c3d4e5f6")`，升级/降级为 no-op。

## Validation

- 生成后本地可执行 `alembic heads` 显示单 head，`upgrade head` 不再因多 head 报错（需在实际 DB 环境验证）。

## Next Steps

- 后续新增迁移统一基于该 merge 之后的 head 继续演进。

## Linked Commits

- pending（本地此次改动将与本账本条目一并提交）
