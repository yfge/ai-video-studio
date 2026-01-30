---
id: 2026-01-28T09-02-25Z-limit-aspect-ratio-ui
date: 2026-01-28T09:02:25Z
participants: [human, codex]
models: [gpt-5.2]
tags: [frontend, ui, aspect-ratio]
related_paths:
  - ai-pic-frontend/src/utils/aspectRatios.ts
  - ai-pic-frontend/src/utils/modelUiImage.ts
  - ai-pic-frontend/src/utils/modelUiVideo.ts
summary: "Restrict model UI aspect ratio options to 9:16 and 16:9"
---

## User Prompt

继续执行选项 2：前端强制过滤仅允许 9:16/16:9 画幅选项。

## Goals

- 在模型 UI 层统一限制画幅/比例为 9:16 或 16:9
- 确保默认值落在允许的画幅集合

## Changes

- 新增 `aspectRatios` 工具，集中定义允许画幅与默认选择规则
- 图像/视频模型 UI 解析时过滤 ratio/aspect_ratio 选项，仅保留 9:16/16:9

## Validation

- `cd ai-pic-frontend && npm run lint` ⚠️ 7 warnings（无错误）
- `pre-commit run --all-files` ❌ trailing-whitespace/end-of-file-fixer 修改大量历史文件；`ruff` 报历史问题；`backend-pytest` 失败（Minimax API key 缺失与 `to_int` 导入错误）；已恢复非本次改动
- `./docker/build_prod_images.sh` ✅ backend/frontend 镜像构建并推送成功（tag: f07c3e8），Next.js 多 lockfile 与 npm audit warning
- Chrome MCP ✅ 登录后进入“环境资产”详情页，打开图生图弹窗，确认“画幅比例”仅显示 9:16/16:9

## Next Steps

- 若需进一步限制 API 层比率枚举，可在后端统一校验错误提示文案

## Linked Commits

- TBD
