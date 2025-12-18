---
id: 2025-12-18T14-16-44Z-model-ui-metadata
date: 2025-12-18T14:16:44Z
participants: [human, codex]
models: [gpt-4o-mini]
tags: [frontend, ui]
related_paths:
  - ai-pic-frontend/src/components/ModelUiFields.tsx
  - ai-pic-frontend/src/utils/modelUi.ts
  - ai-pic-frontend/src/components/ImageToImageModal.tsx
  - ai-pic-frontend/src/components/StoryboardVideoModal.tsx
summary: "Add shared model-UI renderer and hook image/video modals to backend metadata for dynamic parameters."
---

## User Prompt

- 把 ImageToImageModal/StoryboardVideoModal 接入一个通用 ModelUI 组件，动态渲染 metadata.ui 的可选项/开关，并为环境关键帧 modal 回填模型元数据（aspect_ratio、尺寸、服务等级等）。

## Goals

- 抽象模型 UI 配置读取，支持后端返回的 resolution/ratio/duration/watermark/camera 等选项。
- 让图生图、分镜视频弹窗按模型元数据渲染参数控件，避免前端硬编码。

## Changes

- 新增 `ModelUiFields` 组件与 `modelUi` 工具，解析模型 `metadata.ui` 并提供默认分辨率、画幅、时长、水印、固定镜头等开关。
- ImageToImageModal 使用通用字段渲染尺寸/画幅或宽高输入，移除硬编码分辨率 props。
- StoryboardVideoModal 改为使用 ModelUiFields，动态展示分辨率/画幅/时长/水印/固定镜头，保持摄像机控制校验。

## Validation

- `npm run lint`（前端 lint 通过）。
- `./docker/build_prod_images.sh`（通过，镜像 tag fa97e91）。
- 浏览器自测：Chrome 登录 `geyunfei/Gyf@845261`，进入分镜页，打开帧 1 “生成视频”弹窗，看到分辨率/画幅/时长/水印/固定镜头根据模型元数据动态渲染。

## Next Steps

- 后端补充更多模型的 metadata.ui（含摄像机控制提示等），前端可直接呈现。
- 补充首尾帧候选加载逻辑，避免“暂无候选图”影响提交。

## Linked Commits

- (pending)
