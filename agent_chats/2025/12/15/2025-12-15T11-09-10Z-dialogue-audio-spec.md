---
id: 2025-12-15T11-09-10Z-dialogue-audio-spec
date: 2025-12-15T11:09:10Z
participants: [human, codex]
models: [gpt-5.2]
tags: [docs, audio, timeline]
related_paths:
  - docs/dialogue-audio-timeline-spec.md
  - tasks.md
summary: "Documented the MVP spec for scene dialogue audio, scene_beats storage, episode timeline JSON, and storyboard placeholders."
---

## User Prompt

整体完成「对白音轨与声音驱动时间轴」Feature，并要求：声音优先定时长、scene_beats 存 scene 级、音色回退 agent 自动绑定无需人工确认、衍生角色由 agent 判定 scope（scene/episode/story），所有音频上传 OSS；每完成一项就更新 tasks.md、自测并提交保持工作区干净。

## Goals

- 冻结 MVP 的输入/输出契约：scene 音轨、beats 字段、episode 时间轴 JSON、分镜占位生成规则与 OSS 约束。
- 将该工作项在 `tasks.md` 标记为已完成。

## Changes

- 新增 `docs/dialogue-audio-timeline-spec.md`：定义 dialogue audio pipeline 的 MVP 规则与落库/元数据字段。
- 更新 `tasks.md`：将“冻结输出规范”工作项标记为完成，并链接到 spec 文档。

## Validation

- `pre-commit run --files docs/dialogue-audio-timeline-spec.md tasks.md agent_chats/2025/12/15/2025-12-15T11-09-10Z-dialogue-audio-spec.md`

## Next Steps

- 实现音色绑定 agent（VirtualIP + 衍生角色 scope）并落库审计字段。
- 实现场景音轨生成（TTS + 静音补足）与 `scene_beats` 写入。

## Linked Commits

- (pending)
