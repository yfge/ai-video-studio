---
id: 2025-12-18T15-41-59Z-keling-i2v-mode-pro
date: 2025-12-18T15:41:59Z
participants: [human, codex]
models: [gpt-5.2]
tags: [backend, provider, keling, video]
related_paths:
  - ai-pic-backend/app/services/providers/keling_provider.py
  - docs/api/keling/imagetovideo.md
summary: "Fix keling image2video 400 by forcing mode=pro (std rejected by API)."
---

## User Prompt

- 可灵的视频生成一直 400，要求对照 `docs/api/keling/imagetovideo.md` 排查并在 Docker/Chrome 里做完整验证。

## Goals

- 修复可灵 image2video 的 `400 code=1201 mode value 'std' is invalid`。
- 保证分镜视频生成链路（API -> Celery -> Provider -> Kling）不再因为 mode 失败。
- 对齐仓库文档与实测行为，并完成一次真实浏览器端到端验证。

## Changes

- 后端：`KelingProvider.generate_video` / `generate_video_from_multiple_images` 统一发送 `mode=pro`，避免 std/省略 mode 导致的 400。
- 文档：在 `docs/api/keling/imagetovideo.md` 的 `mode` 参数说明中补充实测注意事项（std/省略 mode 会报 1201）。

## Validation

- `cd ai-pic-backend && pytest tests/unit tests/services tests/scripts`
- `./docker/build_prod_images.sh`（tag `509e48a`）
- Docker（worker 容器内）直连可灵：`POST /v1/videos/image2video` 使用 `mode=pro` 返回 `200 code=0` 并拿到 `task_id`。
- Chrome（MCP）端到端：打开 `http://localhost:8089/episodes/cd378417b7f143eab5bc6d063cd7f6e7/storyboard` -> 帧 1「生成视频」-> 选择模型「可灵 V2.6」-> 关闭尾帧（只用首帧）-> 提交后提示“已创建视频生成任务”；worker 日志显示 `POST https://api-beijing.klingai.com/v1/videos/image2video` 返回 `200` 并进入轮询。

## Next Steps

- 观察该任务最终产出视频并回写到分镜（避免触发 429 资源包并发限制）。
- 如上游 API 后续恢复 std，可考虑把 mode 做成可配置（默认 pro，std 仅在可用时开放）。

## Linked Commits

- (pending)

