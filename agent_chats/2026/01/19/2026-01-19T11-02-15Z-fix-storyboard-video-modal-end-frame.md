---
id: 2026-01-19T11-02-15Z-fix-storyboard-video-modal-end-frame
date: 2026-01-19T11:02:15Z
participants: [human, codex]
models: [gpt-5.2]
tags: [frontend, storyboard, video]
related_paths:
  - ai-pic-frontend/src/components/shared/modals/StoryboardVideoModal.tsx
summary: "Fix StoryboardVideoModal to not require an end frame when no end candidates exist."
---

## User Prompt
短剧全流程测试前，修复分镜视频生成弹窗在没有尾帧候选时仍强制选择尾帧导致无法提交的问题。

## Goals
- 在 `StoryboardVideoModal` 中：当尾帧候选为空时，默认关闭“使用尾帧”，并允许仅用首帧提交视频生成。
- 保持现有模型能力判断逻辑（supports_end_frame）不变。

## Changes
- `ai-pic-frontend/src/components/shared/modals/StoryboardVideoModal.tsx`：当 `endList.length === 0` 时自动 `setUseEndFrame(false)` 并清空 `endSelected`，避免被 `endOk` 校验阻塞提交。

## Validation
- Frontend lint: `cd ai-pic-frontend && npm run lint`（0 errors）。
- Chrome E2E（MCP）:
  - 登录：`http://localhost:8089/login`（geyunfei / Gyf@845261）。
  - 打开分镜页：`http://localhost:8089/episodes/1cca3cc61d7740b4b5f73bccf8fe4d32/storyboard?scriptId=72`。
  - 定位到“分镜帧 61（首帧）”仅有首帧、无尾帧候选的帧，点击“生成视频”打开 `StoryboardVideoModal`。
  - 观察到：尾帧区域显示“暂无候选图”，且“使用尾帧（可选）”为禁用状态；底部“生成视频”按钮可点击（不再提示必须选择尾帧）。
  - 点击“生成视频”成功创建任务，弹窗提示“已创建视频生成任务”。

## Next Steps
- 在短剧全流程测试中统一把视频模型切到 Google Veo 最新版本（如 `Veo 3.1 Generate (preview)`），并对生成结果做下载/抽帧检查。

## Linked Commits
- (pending)
