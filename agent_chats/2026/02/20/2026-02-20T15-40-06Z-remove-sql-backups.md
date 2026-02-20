---
id: 2026-02-20T15-40-06Z-remove-sql-backups
date: "2026-02-20T15:40:06Z"
participants: [human, codex]
models: [gpt-5]
tags: [repo-hygiene, docs, tasks]
related_paths:
  - .gitignore
  - docs/README.md
  - docs/db-backup-policy.md
  - ai-pic-backend/backups/backup_20250812_154351.sql
  - ai-pic-backend/backups/backup_20250824_172339.sql
  - ai-pic-backend/backups/backup_20250824_201301.sql
  - ai-pic-backend/backups/backup_20250825_100133.sql
  - ai-pic-backend/backups/backup_20250924_123655.sql
  - tasks.md
summary: "Removed tracked SQL backup dumps, added backup policy doc, and updated task board status"
---

## User Prompt

对比这个项目（你可以clone到本地） ，https://github.com/chatfire-AI/huobao-drama 分析我们有哪些不足；更新到 tasks.md 中；开始执行。

## Goals

- 执行仓库治理任务：移除仓库内跟踪的 SQL 备份文件。
- 增加外部备份与恢复流程文档，避免后续重复提交备份文件。
- 更新 tasks.md 状态，确保执行进度可追踪。

## Changes

- 删除仓库中已跟踪的 5 个 SQL 备份文件（ai-pic-backend/backups/\*.sql）。
- 在 .gitignore 增加规则 ai-pic-backend/backups/\*.sql，防止再次误提交。
- 新增 docs/db-backup-policy.md，定义外部备份存储与恢复验证流程。
- 更新 docs/README.md，加入新文档索引。
- 更新 tasks.md，将仓库治理对应任务标记为已完成。

## Validation

- git 状态检查确认备份 SQL 文件已从仓库移除且由 .gitignore 保护。
- pre-commit（目标文件）将于提交前执行。
- 提交前执行 ./docker/build_prod_images.sh（按仓库规范）。

## Next Steps

- 继续执行 src/utils/api.ts 迁移，减少旧 API 聚合入口引用。
- 分阶段迁出 scripts_legacy.py 的剩余路由。

## Linked Commits

- 待本次原子提交后补充
