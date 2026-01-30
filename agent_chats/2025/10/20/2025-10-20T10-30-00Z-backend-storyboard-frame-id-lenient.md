---
id: 2025-10-20T10-30-00Z-backend-storyboard-frame-id-lenient
date: 2025-10-20T10:30:00Z
participants: [human, codex]
models: [gpt-4o-mini]
tags: [backend, api]
related_paths:
  - ai-pic-backend/app/schemas/generation.py
  - ai-pic-backend/app/api/v1/endpoints/scripts.py
summary: "Relax StoryboardFrame.frame_id to string to accept non-UUID IDs from generators (e.g., 'S1-F1')."
---

## User Prompt

调用 `/api/v1/scripts/{id}/storyboard/generate` 报错：StoryboardModel 校验失败，`frame_id` 不是 UUID（值如 `S1-F1`）。

## Goals

- 放宽分镜帧 `frame_id` 的输入校验，兼容现有生成器输出的自定义字符串 ID；
- 仍为缺省情况提供 UUID 字符串默认值。

## Changes

- `StoryboardFrame.frame_id` 由 `UUID` 改为 `str`，`default_factory` 生成 `str(uuid4())`；
- 兼容传入 `S1-F1` 这类 ID，不再触发 Pydantic v2 的 UUID 解析错误。

## Validation

- 生成端点将接受字符串 ID；既有使用索引定位帧的流程不受影响。

## Next Steps

- 如需进一步约束，可在将来改为 `Union[str, UUID]`（优先匹配 `str`），或引入格式校验但允许非 UUID。

## Linked Commits

- pending（本地增量补丁将与此台账条目一并提交）
