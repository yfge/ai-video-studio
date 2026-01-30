---
id: 2026-01-19T23-51-53Z-frontend-modelui-video-duration
date: 2026-01-19T23:51:53Z
participants: [human, codex]
models: [gpt-5.2]
tags: [frontend, video, ui, provider, refactor]
related_paths:
  - ai-pic-frontend/src/components/shared/VideoModelUiFields.tsx
  - ai-pic-frontend/src/utils/modelUi.ts
  - ai-pic-frontend/src/utils/modelUiImage.ts
  - ai-pic-frontend/src/utils/modelUiImageGen.ts
  - ai-pic-frontend/src/utils/modelUiTypes.ts
  - ai-pic-frontend/src/utils/modelUiVideo.ts
summary: "按 provider/resolution 动态展示视频时长选项，并拆分 modelUi 以满足文件大小限制"
---

## User Prompt

要求“按 provider 再进一步优化”，在选择不同 provider 时动态加载输入，且遵守文件大小上限与原子化提交。

## Goals

- 视频生成表单根据所选模型能力（尤其分辨率→可用时长）动态约束输入
- 避免前端工具文件超 250 行，保持可维护性

## Changes

- `ai-pic-frontend/src/components/shared/VideoModelUiFields.tsx`: 时长下拉根据 `resolution` 显示 provider 支持的选项
- `ai-pic-frontend/src/utils/modelUi.ts`: 拆分为按域模块并 re-export，避免单文件膨胀
- `ai-pic-frontend/src/utils/modelUiTypes.ts`: 抽离 types
- `ai-pic-frontend/src/utils/modelUiVideo.ts`: 抽离视频相关 UI 元数据解析
- `ai-pic-frontend/src/utils/modelUiImage.ts`, `ai-pic-frontend/src/utils/modelUiImageGen.ts`: 抽离图片/生图相关逻辑

## Validation

- `cd ai-pic-frontend && npm run lint`
- Chrome（本地）：打开分镜页视频生成弹窗，模型从后端加载后，画幅/分辨率与时长选项按模型能力动态渲染（例如 Veo 2.0 Generate 显示 `16:9 · 720P`，时长 `5/6/8s`）

## Next Steps

- 后端补齐真实错误回传（目前任务失败会被“所有提供商都失败了”掩盖）
- 全流程 E2E：补齐剩余分镜视频并逐个下载抽检

## Linked Commits

- fix(frontend): provider-aware video duration options
