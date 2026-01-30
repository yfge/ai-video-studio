---
id: 2025-10-17T09-41-07Z-story-structure-db-probe
date: 2025-10-17T09:41:07Z
participants: [human, codex]
models: [gpt-5.1-codex]
tags: [backend, migration, tooling]
related_paths:
  - ai-pic-backend/scripts/prototype_story_structure_migration.py
  - docs/story-structure-gap-analysis.md
summary: "Enabled live DB extraction mode with transactional insert probe hooks"
---

## User Prompt

演练提取器对真实数据库快照的处理能力，增加插入/回滚探针，并处理边缘情况。

## Goals

- 改造原型脚本以支持 live 数据源和可选的插入验证。
- 保留 sample 模式行为，便于比较输出。
- 在文档中补充运行说明，指导后续团队复现。

## Changes

- 重写 `ai-pic-backend/scripts/prototype_story_structure_migration.py`：引入 CLI 参数、live 模式（含事务性插入探针）、原型 ID 映射元数据、数据库连接工具。
- 更新 `docs/story-structure-gap-analysis.md`，列出 live 模式用法与 `--insert-probe` 选项。

## Validation

- `python ai-pic-backend/scripts/prototype_story_structure_migration.py --dump-json`（sample 模式输出成功）。
- `python ai-pic-backend/scripts/prototype_story_structure_migration.py --mode live --script-id 1 --insert-probe`（受限环境无法连接 127.0.0.1:13306，确认报错并记录限制）。

## Next Steps

- 在具备数据库访问权限的环境运行 live 模式，校验真实数据映射并观察需要的字段兼容性修正。
- 依据探针结果补充自动化测试或 SQL 对比脚本。

## Linked Commits

- (pending)
