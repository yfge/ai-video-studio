---
id: 2025-12-17T03-07-14Z-soft-delete-backfill-validation
date: 2025-12-17T03:07:14Z
participants: [human, codex]
models: [gpt-4o-mini]
tags: [backend, migration]
related_paths:
  - ai-pic-backend/alembic/versions/e7d5f9d2c3b0_backfill_business_links_validation.py
summary: "Added data-only migration to re-backfill business_id and link columns"
---

## User Prompt

- 用户要求增加专门的校验/修正迁移，为已有数据补齐 uuid 并填充业务关联列。

## Goals

- 确保所有表的 `business_id` 非空，`*_business_id` 链接列按父表 business_id 回填，缺失时用 uuid4 hex 兜底。

## Changes

- 新增迁移 `e7d5f9d2c3b0_backfill_business_links_validation.py`：再次回填所有表的 `business_id`，并针对 episodes/scripts/story_characters/story_step_outlines/scenes/scene_beats/shots/virtual_ip_images 等链接列通过 join 父表补齐业务主键（缺失则生成 uuid4）。

## Validation

- 未跑自动化测试（数据补丁迁移，后续整体测试需覆盖）。

## Next Steps

- 继续唯一约束 + 软删过滤/删除/再生成语义改造，并跑 pytest 验证。

## Linked Commits

- (pending)
