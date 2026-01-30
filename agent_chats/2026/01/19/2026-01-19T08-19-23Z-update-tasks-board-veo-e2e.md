---
id: 2026-01-19T08-19-23Z-update-tasks-board-veo-e2e
date: 2026-01-19T08:19:23Z
participants: [human, codex]
models: [gpt-5.2]
tags: [chore, tasks]
related_paths:
  - tasks.md
summary: "Update tasks.md to reflect the Google Veo storyboard video fix and outline the next E2E and UI follow-ups."
---

## User Prompt

检查和更新 `tasks.md`，并说明下一步可以做哪些工作。

## Goals

- 把本轮已完成的 Veo 分镜视频修复与验证同步到任务看板。
- 明确下一步：短剧模板（每集爽点）+ 全流程 E2E + 前端视频弹窗修复。

## Changes

- 更新 `tasks.md`：
  - 在“短剧微类型与投流驱动创作闭环”加入“短剧故事/剧本模板（每集爽点）”与“全流程 E2E 抽检”待办
  - 在“场景/环境资产与分镜联动”记录 Google Veo 分镜视频修复已完成，并新增前端“无尾帧候选仍强制尾帧”弹窗问题待办

## Validation

- 人工校对 `tasks.md` 的状态标记（`[x]` / `[ ]`）与条目归类，确保反映当前实际进度与下一步。

## Next Steps

- 优先修复分镜“生成视频”弹窗的尾帧强制逻辑，恢复 UI 直出视频能力。
- 新增短剧故事/剧本模板（每集爽点）并跑通完整 E2E（DeepSeek 文生文 + Google 图/视频），逐张下载抽检资产。

## Linked Commits

- (pending) `chore: update tasks board`
