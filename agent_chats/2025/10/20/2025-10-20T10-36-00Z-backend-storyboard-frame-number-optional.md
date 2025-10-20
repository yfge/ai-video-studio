---
id: 2025-10-20T10-36-00Z-backend-storyboard-frame-number-optional
date: 2025-10-20T10:36:00Z
participants: [human, codex]
models: [gpt-4o-mini]
tags: [backend, api]
related_paths:
  - ai-pic-backend/app/schemas/generation.py
summary: "Make StoryboardFrame.frame_number optional to accept generator outputs without explicit numbering."
---

## User Prompt

Storyboard 生成再次校验失败：`frame_number` 缺失。生成器未显式提供帧序号。

## Goals

- 允许缺少 `frame_number` 的帧通过校验；后续在保存或渲染阶段可根据索引补齐展示。

## Changes

- 将 `StoryboardFrame.frame_number` 从必填 `int` 改为 `Optional[int] = None`。

## Validation

- 生成端点放宽校验后可接受缺失序号的帧；UI 已有回退逻辑（以列表索引显示）。

## Next Steps

- 如需保证持久化时有序号，`update_storyboard` 已在保存路径中统一赋值。

## Linked Commits

- pending（本地增量补丁将与此台账条目一并提交）

