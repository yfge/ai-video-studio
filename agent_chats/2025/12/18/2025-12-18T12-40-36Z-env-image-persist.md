---
id: 2025-12-18T12-40-36Z-env-image-persist
date: 2025-12-18T12:40:36Z
participants: [human, codex]
models: [gpt-4o-mini]
tags: [backend, environment]
related_paths:
  - ai-pic-backend/app/api/v1/endpoints/story_structure.py
summary: "Commit environment reference images after downloads so newly generated variants show up in listings."
---

## User Prompt

- 前端环境图生成后刷新没有新图；检查是否有类似持久化问题，并完成端到端验证。

## Goals

- 确保 `_download_and_attach` 写入的环境参考图会落库并能通过 `/environments/{id}/images` 返回。
- 运行必需的验证（pytest、pre-commit、镜像构建），记录结果。
- 使用 Chrome MCP 端到端确认环境页面与任务列表的行为。

## Changes

- 在 `_download_and_attach` 保存引用图后追加 `db.commit()`，避免 JSON mutation 未持久化导致刷新看不到新图（包含 isort/black 自动整理）。

## Validation

- `cd ai-pic-backend && pytest`（失败）：基线环境缺少若干 fixtures 与数据库/migration 依赖，出现 `fixture 'admin_token' not found`、SQLAlchemy 连接错误及 async plugin 缺失等大量已知失败。
- `pre-commit run --files ai-pic-backend/app/api/v1/endpoints/story_structure.py`（通过）。
- `bash docker/build_prod_images.sh`（通过，推送 tag 6d620f7 后端/前端镜像）。
- Chrome MCP：使用账号 geyunfei 登录 → 环境“老拐的家”详情 → 触发文生图生成任务，任务创建为“等待中”，点击“开始”提示状态不允许执行，队列未实际运行，暂未看到新增图片。

## Next Steps

- 重启后端服务/worker 以加载提交，重新跑环境图生成任务，确认参考图数量增加。
- 确认任务队列可执行当前“等待中”的环境文生图任务，并刷新环境详情页验证图片列表。

## Linked Commits

- (pending)
