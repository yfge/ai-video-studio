---
id: 2025-12-13T14-05-57Z-frontend-task-style-details
date: 2025-12-13T14:05:57Z
participants: [human, codex]
models: [gpt-5.2]
tags: [frontend, tasks, styles]
related_paths:
  - ai-pic-frontend/src/app/tasks/page.tsx
  - ai-pic-frontend/src/utils/api.ts
summary: "Add expandable task details showing request parameters and persisted style_spec/style_spec_resolution."
---

## User Prompt

1. 任务详情中展示 style_spec/resolution 信息（后端已落库，可直接读）；2) 前端按页面语境只传部分 style_spec。

## Goals

- 任务列表支持展开“详情”，直观看到 `task.parameters` 的 `style_preset_id/style_spec`。
- 对可识别的任务类型（环境/虚拟IP/分镜），在任务详情中展示落库后的 `style_spec` / `style_spec_resolution`。

## Changes

- Extended `Task` type to include `task_type` + `parameters`.
- Added `virtualIPImageAPI.getImage()` wrapper for `GET /api/v1/virtual-ips/{id}/images/{image_id}`.
- Added per-task “详情/收起详情” toggle in `ai-pic-frontend/src/app/tasks/page.tsx`.
- On expand, fetch persisted style info:
  - env tasks → `Environment.metadata.last_*_generation.style_spec/_resolution`
  - virtual ip tasks → `VirtualIPImage.generation_params.style_spec/_resolution`
  - storyboard image tasks → `script storyboard meta.image_generation_style_spec/_resolution`

## Validation

- `cd ai-pic-frontend && npm run lint`
- Chrome E2E (http://localhost:8089):
  - 打开 `http://localhost:8089/tasks` → 点击最新任务的“详情”
  - 确认“请求风格”展示 `parameters.style_spec`，且“落库风格”展示 `spec/resolution`（含 `source: script:18:storyboard` 等来源）

## Next Steps

- 若需要更强一致性：在 task rows 上增加“跳转到资产详情”快捷入口（env/vip/script），并在任务完成时显示相关资产链接。

## Linked Commits

- feat(frontend): show style spec in task details
