---
id: 2025-12-17T02-34-07Z-soft-delete-business-id
date: 2025-12-17T02:34:07Z
participants: [human, codex]
models: [gpt-4o-mini]
tags: [backend, docs, design]
related_paths:
  - docs/soft-delete-business-id.md
  - tasks.md
summary: "Drafted soft delete + business_id design and added task board entries"
---

## User Prompt

- 用户询问重新生成逻辑是覆盖还是伪删除，随后要求“所有逻辑加软删除”、引入 `business_id`（`replace(uuid(),'-','')`）作为业务主键，关联改为 business_id，regenerate 返回新 ID，设计文档存入 docs 并更新任务板。

## Goals

- 产出全局软删除 + business_id 设计文档，明确字段、索引、关联、再生成语义与迁移分阶段方案。
- 在 `tasks.md` 添加对应工作项与下一步计划。

## Changes

- 新增设计稿 `docs/soft-delete-business-id.md`，覆盖目标、范围、模型方案、关联切换、迁移阶段、验证与风险。
- 在 `tasks.md` 增加“全局软删除 + business_id”功能板块，填入阶段性工作与下一步。

## Validation

- 文档/任务清单更新，未跑代码或测试。

## Next Steps

- Phase 1：Alembic/mixin 落地 `business_id` 与软删字段、回填、查询默认过滤。
- Phase 2：子表补充 `*_business_id` 并回填，服务层双写，唯一约束含 `is_deleted`。
- Phase 3：删除/恢复改软删，regenerate 新建记录+软删旧记录并处理派生数据；前端切换 business_id。

## Linked Commits

- (pending)
