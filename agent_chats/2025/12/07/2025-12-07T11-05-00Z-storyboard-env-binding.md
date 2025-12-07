---
id: 2025-12-07T11-05-00Z-storyboard-env-binding
date: 2025-12-07T11:05:00Z
participants: [human, codex]
models: [gpt-4o-mini]
tags: [frontend, storyboard, env]
related_paths:
  - ai-pic-frontend/src/app/episodes/[id]/storyboard/page.tsx
  - ai-pic-frontend/src/utils/api.ts
  - task.md
summary: "Allow binding environments and characters on storyboard normalized scenes"
---

## User Prompt

- 继续：推进场景相关工作。

## Goals

- 在分镜编辑中加载环境资产与角色列表。
- 支持按规范化场景选择环境并保存绑定，镜头支持角色绑定。
- 更新任务看板的进度记录。

## Changes

- 扩充 story-structure API 类型，携带 environment_id/character_ids，并拉取环境列表与虚拟 IP 供选择。
- 分镜页面新增场景环境选择与保存，展示标签/参考图等上下文。
- 规范化镜头支持多选角色绑定并保存，界面展示当前分配的角色。
- 更新 task.md，标记环境建模完成并注明 UI 进展。

## Validation

- npm --prefix ai-pic-frontend run lint
- 浏览器端到端未在本轮复跑（需后续跟进）。

## Next Steps

- 将绑定的环境/角色注入图像/视频生成提示词与校验。
- 补充分镜页环境/角色绑定的浏览器自测记录。
- 扩充环境/镜头绑定流程的测试与文档。

## Linked Commits

- (pending)
