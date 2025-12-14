---
id: 2025-12-14T14-47-25Z-friendly-task-titles
date: 2025-12-14T14:47:25Z
participants: [human, codex]
models: [gpt-4o]
tags: [backend, tasks, storyboard]
related_paths:
  - ai-pic-backend/app/api/v1/endpoints/scripts.py
summary: "Use story/episode names in storyboard task titles and verify storyboard page"
---
## User Prompt
- 用户希望“分镜视频生成 - 剧本17”等任务名称改为基于故事/剧集名的友好格式，并提到类似任务也应调整。

## Goals
- 让分镜相关的异步任务标题带上故事/剧集名称，避免只显示“剧本{ID}”。
- 维持现有任务创建逻辑，其它行为不变。

## Changes
- 添加 `_friendly_task_title` 工具函数，根据故事/剧集信息拼接任务标题。
- 在分镜生成、分镜图像生成、分镜视频生成任务创建时使用友好标题（故事/剧集优先，缺失时回退到剧本ID）。

## Validation
- `pytest tests/test_tasks_minimal.py -q`（通过；首次跑全量 `pytest tests -q` 120s 超时未完成）。
- Chrome 自测：打开 `http://localhost:8089/episodes/10/storyboard`（已登录状态），点击“场景 2 INT. 文闻公寓 - 夜”验证页面加载和场景切换正常。

## Next Steps
- 如需进一步验证，可在完整后端测试环境下跑全量 `pytest` 以覆盖更多路径。
- 观察生产/预发任务列表中的标题显示，确认新格式符合预期。

## Linked Commits
- chore(backend): friendly storyboard task titles
