---
id: 2026-01-29T08-23-23Z-aspect-ratio-resolution
date: "2026-01-29T08:23:23Z"
participants: [human, codex]
models: [gpt-5]
tags: [backend, aspect-ratio, storyboard, video]
related_paths:
  - ai-pic-backend/app/core/aspect_ratio.py
  - ai-pic-backend/app/api/v1/endpoints/scripts_legacy.py
  - ai-pic-backend/tests/unit/core/test_aspect_ratio.py
  - tasks.md
summary: "Centralize aspect ratio resolution (request > episode > story > default) and wire into storyboard image/video endpoints."
---

## User Prompt

把屏幕比/画幅抽象到 Story/Episode 层面（默认 9:16，仅支持 9:16/16:9），允许临时覆盖；按 `tasks.md` 推进并保持原子化提交。

## Goals

- 统一画幅解析优先级：`request override > episode > story > 9:16`。
- 让分镜图/分镜视频生成在未显式传参时能正确继承 Episode/Story 的默认画幅。
- 补单测，避免后续在 legacy 路径继续散落重复逻辑。

## Changes

- `ai-pic-backend/app/core/aspect_ratio.py`
  - 新增 `resolve_aspect_ratio()`：按优先级解析并对脏值回落到默认 `9:16`。
- `ai-pic-backend/app/api/v1/endpoints/scripts_legacy.py`
  - `/{script_id}/storyboard/generate-images`：`aspect_ratio` 解析改为 `request > episode > story > default`。
  - `/{script_id}/storyboard/generate-video`：`ratio` 解析改为 `request > episode > story > default`。
- `ai-pic-backend/tests/unit/core/test_aspect_ratio.py`
  - 新增单元测试覆盖优先级与非法值回退。
- `tasks.md`
  - P0-1 “统一画幅解析优先级并贯通分镜图/视频参数”标记完成。

## Validation

- `cd ai-pic-backend && pytest tests/unit tests/services tests/scripts`
- `./docker/build_prod_images.sh`
- Chrome（MCP）冒烟：
  - 登录 `http://localhost:8089/login`
  - 打开 `http://localhost:8089/episodes/131/storyboard` 页面正常渲染（验证改动未引入运行时异常）

## Next Steps

- 前端补齐 Story/Episode 画幅设置与分镜视频“临时覆盖”UI，并做 9:16/16:9 各 1 条真实视频生成抽检（`ffprobe`）。

## Linked Commits

- (pending)
