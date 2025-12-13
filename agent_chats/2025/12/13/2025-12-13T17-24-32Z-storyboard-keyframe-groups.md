---
id: 2025-12-13T17-24-32Z-storyboard-keyframe-groups
date: "2025-12-13T17:24:32Z"
participants: [human, codex]
models: [gpt-5.2]
tags: [storyboard, backend, frontend, video]
related_paths:
  - ai-pic-backend/app/api/v1/endpoints/scripts.py
  - ai-pic-backend/app/schemas/generation.py
  - ai-pic-backend/app/services/ai_service.py
  - ai-pic-backend/app/services/task_worker.py
  - ai-pic-backend/tests/unit/test_storyboard_keyframes_schema.py
  - ai-pic-frontend/src/app/episodes/[id]/storyboard/page.tsx
  - ai-pic-frontend/src/utils/api.ts
summary: "让分镜首/尾关键帧支持成组存储，并在生成视频时可按选择组合传参"
---

## User Prompt
分镜的首帧尾帧，不是一张图，而是首帧是一组，尾帐是一组，在生成视频的时候可以任意组合

## Goals
- 分镜帧支持 start/end 关键帧列表字段并可回写
- 前端展示关键帧组，允许选择具体 start/end
- 生成视频时把所选 start/end 作为参数传给后端，任务可追溯
- 保持对旧字段 `start_image_url/end_image_url/image_url` 兼容

## Changes
- Backend: 扩展 `StoryboardFrame` schema 支持 `start_image_urls/end_image_urls`
- Backend: 分镜图像生成支持多图返回并回填 `start_image_urls/end_image_urls`（`keyframe_mode=start_end`）
- Backend: 分镜视频生成接口新增 `selections`，worker 生成时使用 selection，并将 `end_image_url` 透传给视频生成；写入 `video_generation.start_image_url/end_image_url`
- Frontend: 分镜工作台展示首/尾关键帧组缩略图，可点击切换选中的 start/end；生成视频时携带 selections
- Tests: 更新 schema 单测覆盖新字段

## Validation
- `cd ai-pic-frontend && npm run lint && npm run build`
- `cd ai-pic-backend && pytest -q tests/unit/test_storyboard_keyframes_schema.py tests/unit/test_storyboard_prompt.py tests/unit/test_storyboard_merge.py`
- `cd ai-pic-backend && pytest` 在当前环境存在大量与本改动无关的失败（多为集成/迁移/外部依赖），本次仅对相关单测做门禁验证
- Chrome (http://localhost:8089):
  - 使用账号 `geyunfei` 登录 -> 进入 `episodes/11/storyboard`
  - 通过 `storyboard/update` 向脚本 18 的 `frame_index=0` 写入 `start_image_urls/end_image_urls` 两个候选
  - 页面出现首/尾候选缩略图；点击切换 start/end 选项
  - 点击“生成视频”后，确认 POST `/api/v1/scripts/18/storyboard/generate-video` Request Body 含 selections（`frame_index=0` + 选中的 start/end URL），并返回 task_id

## Next Steps
- Provider 侧确认 `end_image_url` 的字段名映射（如需 `tail_image_url/ending_image_url`）
- 如需“无需点保存分镜也记住选择”，可在生成视频时将 selection 同步写回 frame 的 selected start/end

## Linked Commits
- feat(storyboard): keyframe groups for video generation
