---
id: 2025-10-20T07-40-00Z-docs-story-structure-api
date: 2025-10-20T07:40:00Z
participants: [human, codex]
models: [gpt-4o-mini]
tags: [docs, backend]
related_paths:
  - docs/story-structure-api.md
  - ai-pic-backend/app/api/v1/endpoints/story_structure.py
summary: "Document minimal normalized story structure API and usage notes."
---

## User Prompt

为新增的规范化叙事结构 API 提供简明文档，便于前后端对齐和验证。

## Goals

- 概述可用端点、路径前缀与注意事项；
- 指出与迁移/模型对齐及前端调用入口。

## Changes

- 新增 `docs/story-structure-api.md`，列出 5 个最小端点与说明。

## Validation

- 文档自洽、路径与后端实现一致。

## Next Steps

- 随后在前端页面中加入试读开关并补充截图/使用说明。

## Linked Commits

- pending（本地增量补丁，后续与此台账一并提交）
