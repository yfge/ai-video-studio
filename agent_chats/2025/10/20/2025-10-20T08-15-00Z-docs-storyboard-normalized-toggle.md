---
id: 2025-10-20T08-15-00Z-docs-storyboard-normalized-toggle
date: 2025-10-20T08:15:00Z
participants: [human, codex]
models: [gpt-4o-mini]
tags: [docs, frontend]
related_paths:
  - docs/storyboard-normalized-toggle.md
  - ai-pic-frontend/README.md
summary: "Add docs for storyboard normalized toggle and new env flag."
---

## User Prompt

完善文档，说明前端分镜页的规范化结构读取开关及相关环境变量。

## Goals

- 简要说明开关行为、使用的端点与 API 客户端；
- 在前端 README 中记录 `NEXT_PUBLIC_USE_NORMALIZED_BY_DEFAULT`。

## Changes

- 新增 `docs/storyboard-normalized-toggle.md`；
- 更新 `ai-pic-frontend/README.md` 增加环境变量配置。

## Validation

- 静态校验，无运行时依赖；与代码实现一致。

## Next Steps

- 如需默认开启可在部署环境设置为 `true`。

## Linked Commits

- pending（本地增量补丁，后续与此台账一并提交）
