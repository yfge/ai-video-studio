---
id: 2025-12-12T13-24-28Z-timeline-rendering-design
date: 2025-12-12T13:24:28Z
participants: [human, codex]
models: [gpt-5.1]
tags: [docs, architecture, timeline]
related_paths:
  - docs/timeline-rendering-pipeline.md
  - tasks.md
summary: "新增时间轴/剪辑与渲染流水线设计文档，并将实现工作拆分到 tasks.md。"
---

## User Prompt

写详细 的设计文档到docs目录下，同时拆分工作项写到tasks.md 中

## Goals

1. 明确 AI 漫剧平台在现有架构下如何落地“首尾帧→视频→拼接剪辑导出”的主线能力。
2. 在不推翻现有 Story/Episode/Script/Scene/Storyboard 分层的前提下，引入时间轴（Timeline/Sequence）作为可渲染编排层。
3. 将可执行的后端/前端/验证工作拆解到 `tasks.md`，便于按阶段推进。

## Changes

- 新增设计文档 `docs/timeline-rendering-pipeline.md`：
  - 解释为何需要 Timeline（编排 SSOT）以及音频优先/视觉优先两种策略的适用边界。
  - 给出推荐的数据模型（timelines/media_assets/render_jobs）与 Timeline Spec（EDL JSON）示例。
  - 梳理后端任务链路：对白/TTS（可选）→ 关键帧 → 视频片段 → FFmpeg 拼接导出（proxy/final）→ OSS/CDN。
  - 描述前端 Timeline MVP（列表+编辑器+proxy 播放）与端到端验证路径。
- 更新 `tasks.md`：
  - 新增 Feature “时间轴/剪辑与渲染导出（首尾帧→视频→拼接）”并拆分工作项与决策点。

## Validation

- 文档/任务拆分变更，无需运行 `pytest` 或 `npm run lint`。
- 未进行 Chrome 端到端验证：本次仅新增文档与任务拆分，不涉及运行时逻辑变更。

## Next Steps

- 根据 `docs/timeline-rendering-pipeline.md` 冻结 Timeline MVP 字段与 API 形态，并按 `tasks.md` 分阶段实现后端渲染与前端编排。

## Linked Commits

- docs: add timeline rendering pipeline design
