---
id: 2025-12-28T08-52-30Z-storyboard-image-params
date: "2025-12-28T08:52:30Z"
participants: [human, codex]
models: [gpt-5.2]
tags: [frontend, backend, storyboard, image]
related_paths:
  - ai-pic-frontend/src/components/shared/ImageModelUiFields.tsx
  - ai-pic-frontend/src/components/shared/modals/ImageToImageModal.tsx
  - ai-pic-frontend/src/app/episodes/[id]/storyboard/page.tsx
  - ai-pic-frontend/src/utils/api.ts
  - ai-pic-frontend/src/utils/api/endpoints/script.endpoints.ts
  - ai-pic-backend/app/api/v1/endpoints/scripts_legacy.py
  - ai-pic-backend/app/services/task_worker.py
summary: "Storyboard 图生图统一使用 size + aspect_ratio，移除宽高输入，修复 Google image preview 宽高比被覆盖"
---

## User Prompt
在选择参考图片生成视频/关键帧的图生图部分（Google image=preview），选择宽高比会被分辨率覆盖；要求所有生图入口去掉“分辨率单独输入”，与宽高比对齐，并对照 docs/api 做到前后端一致。

## Goals
- 修复 storyboard 图生图：Google Gemini 3 Pro Image Preview 的 `aspect_ratio` 不再被宽高/分辨率逻辑覆盖。
- 前端移除“宽度/高度”单独输入，统一走 `size` + `aspect_ratio`。
- 后端 storyboard 生图接口支持 `size` 字段并贯穿到 Celery worker/生成流程。

## Changes
- 前端 `ImageModelUiFields` 移除宽度/高度输入，仅保留模型 UI 元数据驱动的 `size` 与 `aspect_ratio` 下拉。
- 前端 `ImageToImageModal` 去掉 `useDimensions/defaultWidth/defaultHeight`，提交时始终透传 `size` 与（模型支持时）`aspect_ratio`。
- 前端 `scriptAPI.generateStoryboardImages`（legacy + 新 endpoints）支持 `size`，并在存在 `size/aspect_ratio` 时不再默认注入 `width/height=1024`。
- 前端 storyboard 页调用 `generateStoryboardImages` 改为传 `size`，不再传 `width/height`。
- 后端 `StoryboardImageRequest` 增加 `size`，`width/height` 改为可选（兼容旧字段），并在任务执行侧把 `size` 传给 `ai_manager`。
- Celery worker `storyboard_image_generate_task` 支持透传 `size`，并安全解析可选 `width/height`。

## Validation
- 前端：`cd ai-pic-frontend && npm run lint`（有既有警告，但 lint 通过）。
- 后端：本地/容器内全量 `pytest` 存在大量既有失败用例（本改动未新增对应覆盖用例）；已在容器内执行 `python -m py_compile` 校验改动文件无语法错误。
- Docker：`./docker/build_prod_images.sh` 构建并推送成功。
- Chrome E2E（MCP）：
  - 登录 `geyunfei / Gyf@845261`
  - 打开 `http://localhost:8089/episodes/cd378417b7f143eab5bc6d063cd7f6e7/storyboard?scriptId=58`
  - 点击某帧「选择参考图生成关键帧」→ 选择 `Google / Gemini 3 Pro Image Preview`
  - 选择 `size=2K`、`aspect_ratio=16:9` 提交
  - Network `POST /api/v1/scripts/58/storyboard/generate-images` 请求体包含 `size` 与 `aspect_ratio`，且不再包含 `width/height`（确认不再被分辨率覆盖）。

## Next Steps
- 继续排查并修复「生成对白/时间轴对齐」链路中对白过少、异常文本混入（如“阿盖儿 明白，这里可以突出冲突或情绪”）的问题，并在剧本层增加质量/时长约束校验。
- 如需更强一致性：考虑后端将 storyboard 生图接口进一步标准化，逐步移除 `width/height` 旧字段，仅保留 `size/aspect_ratio`（需要迁移与回滚策略）。

## Linked Commits
- (pending)
