---
id: 2025-12-14T13-57-51Z-storyboard-keyframe-targets
date: 2025-12-14T13:57:51Z
participants: [human, codex]
models: [gpt-5.2]
tags: [frontend, backend, storyboard]
related_paths:
  - ai-pic-frontend/src/app/episodes/[id]/storyboard/page.tsx
  - ai-pic-frontend/src/utils/api.ts
  - ai-pic-backend/app/api/v1/endpoints/scripts.py
  - ai-pic-backend/app/services/task_worker.py
summary: "Allow choosing start/end when generating keyframes; prompt hint and backend skip unwanted sides"
---

## User Prompt

选择参考图生成关键帧的部分要可以选择生成的是首帧还是尾帧，同时在生成的时候要对提示词进行调整

## Goals

- 在分镜帧的“选择参考图生成关键帧”弹窗中，允许只生成首帧、只生成尾帧或两者。
- 请求时带上首/尾开关，后端只生成所选关键帧，避免额外生成。
- 针对单选场景，对提示词附加说明以强调首/尾帧语义。

## Changes

- 前端：为 per-frame 图生图弹窗新增“生成首帧/尾帧”勾选，必选至少一项；根据选择对提示词追加目标说明；调用时传 `start_enabled`/`end_enabled` 与调整后的 prompt (`ai-pic-frontend/src/app/episodes/[id]/storyboard/page.tsx`，`ai-pic-frontend/src/utils/api.ts`)。场景批量首/尾帧也显式传启用标志。
- 后端：Storyboard 图像任务支持 `start_enabled`/`end_enabled`，日志显示选择。生成流程在首尾模式下按开关生成/跳过对应关键帧，合并去重图集保持原有兼容逻辑 (`ai-pic-backend/app/api/v1/endpoints/scripts.py`，`ai-pic-backend/app/services/task_worker.py`)。

## Validation

- `cd ai-pic-frontend && npm run lint`
- `cd ai-pic-backend && pytest tests/unit/test_storyboard_keyframes_schema.py`
- Chrome：登录后在 `http://localhost:8089/episodes/10/storyboard` 打开分镜帧弹窗，勾选“场景 10 …”可正常切换场景；弹窗显示首/尾帧勾选项。

## Next Steps

- 如需进一步确认后端跳过未选关键帧，可在同一帧仅勾选尾帧生成并检查回填仅更新 `end_image_urls`。

## Linked Commits

- fix(frontend): keep manual storyboard scene selection
- fix(backend): preserve storyboard keyframe galleries
