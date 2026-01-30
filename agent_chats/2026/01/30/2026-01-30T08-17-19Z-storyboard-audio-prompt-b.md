---
id: 2026-01-30T08-17-19Z-storyboard-audio-prompt-b
date: 2026-01-30T08:17:19Z
participants: [human, codex]
models: [gpt-5]
tags: [tasks, storyboard, backend]
related_paths:
  - tasks.md
summary: "Plan B: add tasks for audio_timeline storyboard visual prompt separation and character identity injection."
---

## User Prompt

进行 B 工作：分离 audio_timeline 分镜的“对白/屏幕文字”和视觉提示词，并优化让视觉提示词能区分角色（谁是林晚/顾辰）。

## Goals

- 把本轮 B 工作拆成可执行任务并落到 `tasks.md`，作为后续原子化提交的推进依据。

## Changes

- 更新 `tasks.md`：新增 3 条任务，覆盖：
  - audio_timeline → storyboard 的 ai_prompt 去对白/去屏幕文字，按 beat 类型使用不同模板；
  - 注入人物身份提示 + Veo 传 reference_images；
  - 抽检验证口径（嘴型说话 + 无字幕/无可读文字）。

## Validation

- `git diff` 确认仅修改 `tasks.md`。

## Next Steps

- 实现 audio_timeline 分镜 prompt 分离与角色身份注入，并在 Docker 内抽检 2 个对白镜头视频的嘴型与“无字幕/无可读文字”。

## Linked Commits

- (pending) 提交将与本 ledger 同步落库。

