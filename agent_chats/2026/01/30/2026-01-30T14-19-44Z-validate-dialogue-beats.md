---
id: 2026-01-30T14-19-44Z-validate-dialogue-beats
date: 2026-01-30T14:19:44Z
participants: [human, codex]
models: [gpt-5]
tags: [validation, storyboard, video]
related_paths:
  - tasks.md
summary: "Validated 2 dialogue beats have visible speaking motion and no burned-in text"
---

## User Prompt

- 检查 tasks
- 先 build prod
- 验证：抽检至少 2 个 dialogue beat（嘴型/说话动作明显，且无字幕/无可读文字）

## Goals

- 完成 `./docker/build_prod_images.sh` 生产镜像构建验证。
- 生成至少 2 段对话分镜视频，并人工抽检：
  - 嘴型/说话动作明显
  - 无字幕/无可读文字（含屏幕读屏/水印文字等）

## Changes

- 标记验证项完成：`tasks.md`
- 新增本次验证记录：`agent_chats/2026/01/30/2026-01-30T14-19-44Z-validate-dialogue-beats.md`

## Validation

- `./docker/build_prod_images.sh`（tag: `76ea860`）构建并推送 backend/frontend 镜像成功。
- Chrome (MCP)：
  - 登录 `http://localhost:8089`（geyunfei / Gyf@845261）
  - 打开 Story `雨夜离婚协议（爽剧测试01300524）` → Episode `2cc86daad6bf4305baa5d4aa0c433834` → 分镜页
  - 选择对话帧并生成关键帧（首/尾）：
    - 帧 5（0-index=4，顾辰对白）：首帧 `http://resource.lets-gpt.com/ai-generated/storyboard/image/20260130/135736/87e5e3ec.png`；尾帧 `http://resource.lets-gpt.com/ai-generated/storyboard/image/20260130/135744/56cfb193.png`
    - 帧 6（0-index=5，林晚对白）：首帧 `http://resource.lets-gpt.com/ai-generated/storyboard/image/20260130/135839/e2dd3919.png`；尾帧 `http://resource.lets-gpt.com/ai-generated/storyboard/image/20260130/135850/b0f4098d.png`
- 通过后端 API 提交视频生成（绕过弹窗“选择首/尾帧候选”的 UI 操作）：
  - `POST /api/v1/scripts/118/storyboard/generate-video`
  - model: `google:veo-3.1-generate-preview`
  - ratio: `9:16`
  - resolution: `720p`
  - task_id: `5913`（最终状态 completed）
- 产物（写回分镜 `script_id=118`）：
  - 帧 5（顾辰对白）视频：`http://resource.lets-gpt.com/ai-generated/videos/video/20260130/141357/98c4d054.mp4`
    - `ffprobe`: 720x1280, 24fps, duration=2.458s
  - 帧 6（林晚对白）视频：`http://resource.lets-gpt.com/ai-generated/videos/video/20260130/141359/9bf86eb2.mp4`
    - `ffprobe`: 720x1280, 24fps, duration=2.333s
- 抽检结论（人工观看抽帧 + 对比）：
  - 两段视频均可见口型变化（与对白场景一致），满足“开口说话/嘴型明显”的验收标准。
  - 抽帧未见字幕/可读文字（含画面角落/水印/读屏字幕）。

## Next Steps

- 继续扩展抽检：覆盖至少 1 段包含“屏幕/文件/手机”道具的对白镜头，重点验证仍无可读文字。
- 若仍出现字幕/读屏：考虑在视频 prompt 的约束中增加“no on-screen text / no captions / no subtitles / no UI text”等强约束并统一模板化。

## Linked Commits

- (pending)

