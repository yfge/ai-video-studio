---
id: 2025-12-17T03-54-43Z-soft-delete-filters-regenerate
date: 2025-12-17T03:54:43Z
participants: [human, codex]
models: [gpt-4o-mini]
tags: [backend, api]
related_paths:
  - ai-pic-backend/app/api/v1/endpoints/episodes.py
  - ai-pic-backend/app/api/v1/endpoints/scripts.py
summary: "Add soft-delete filters to episode/script APIs and make regenerate create new records with soft deletion of old"
---

## User Prompt

- 继续推进软删过滤、删除/再生成语义和业务层重复校验的改造；前台不暴露软删。

## Goals

- 默认查询过滤掉软删数据；删除接口改软删但对前端保持原有响应。
- 再生成走“新记录 + 旧记录软删”。

## Changes

- 添加 `_not_deleted` 助手并在剧集/剧本相关查询中默认过滤 `is_deleted=false`。
- `episodes/{id}/regenerate`：生成新 Episode 记录（保留集号/参数/场景落 meta），旧记录软删。
- `scripts/{id}/regenerate`、`delete_script`、`get_episode_scripts` 等查询/删除改用软删过滤；删除仍返回“剧本删除成功”不暴露软删。

## Validation

- 未运行自动化测试（需后续 pytest 验证）。

## Next Steps

- 扩散软删过滤到其他端点；调整业务层重复校验；前端切换 business_id。

## Linked Commits

- (pending)
