---
id: 2025-12-10T06-39-21Z-img2img-modal-refactor
date: 2025-12-10T06:39:21Z
participants: [human, codex]
models: [gpt-4o-mini]
tags: [frontend, ui, image]
related_paths:
  - ai-pic-frontend/src/components/ImageToImageModal.tsx
  - ai-pic-frontend/src/app/virtual-ip/[id]/images/page.tsx
  - ai-pic-frontend/src/app/environments/page.tsx
  - ai-pic-frontend/src/app/episodes/[id]/storyboard/page.tsx
  - ai-pic-frontend/src/utils/api.ts
  - ai-pic-frontend/src/hooks/useAvailableModels.ts
summary: "Introduce a shared image-to-image modal and apply it across virtual IP images, environments, and storyboard flows with model/resolution/count controls."
---

## User Prompt

- 重构虚拟 IP 图像、环境资产和分镜管理中的图生图体验，统一弹窗，展示参考图与提示词，可选模型/生成张数/分辨率/风格，提交以任务形式处理。

## Goals

- 提供一套可复用的图生图 Modal，内置模型下拉、参考图展示、提示词输入与分辨率/风格/数量配置。
- 在虚拟 IP 图像管理、环境资产管理、分镜管理三处替换旧弹窗或交互，保持参数透传（模型、size/宽高、count等）。
- 保持任务式提交体验和清晰的成功/失败反馈。

## Changes

- 新增 `ImageToImageModal` 组件：展示参考图与提示词，支持模型选择、生成张数、风格和分辨率（尺寸或宽高）配置。
- 虚拟 IP 图像页改用统一 modal 触发变体生成，锁定参考图，透传模型/数量/分辨率并提示任务提交。
- 环境资产列表的参考图“变体”操作接入统一 modal，可调模型/数量/分辨率后调用环境图生图接口。
- 分镜帧与首/尾帧生成改用统一 modal，支持参考图选择、提示词回显、宽高/风格/模型设置；API 包装添加可选 count 透传。
- 移除多余的模型 hook 导入，保持 lint 干净（仍有既存 MultiModelSelector 依赖告警）。

## Validation

- `npm run lint`（通过，存在既有的 MultiModelSelector 依赖警告未改动）。
- MCP/Chrome 自测未完成：尝试在端口 3000/3010 启动前端 dev server 报 EPERM（端口绑定受限），后端未运行，无法进行登录端到端验证。

## Next Steps

- 待本地服务允许端口监听时，使用 geyunfei / Gyf@845261 登录前端，验证虚拟 IP/环境/分镜的图生图弹窗与任务提交流程。

## Linked Commits

- pending
