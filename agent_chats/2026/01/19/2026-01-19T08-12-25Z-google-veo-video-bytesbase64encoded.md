---
id: 2026-01-19T08-12-25Z-google-veo-video-bytesbase64encoded
date: 2026-01-19T08:12:25Z
participants: [human, codex]
models: [gpt-5.2]
tags: [backend, provider, google, veo, video]
related_paths:
  - ai-pic-backend/app/services/providers/google_provider/helpers.py
  - ai-pic-backend/app/services/providers/google_provider/provider.py
  - ai-pic-backend/app/services/providers/google_provider/video_tasks.py
  - ai-pic-backend/tests/unit/test_google_provider_video_tasks.py
  - docs/api/google/google-veo-video-generation.md
summary: "Fix Google Veo image-to-video requests by using the correct base64 image field so storyboard video generation succeeds."
---

## User Prompt

全局检查文生图/图生图提示词规范，并按 provider 做进一步优化；同时做短剧全流程测试：生文用 deepseek-chat，生图用 Google Image 3.5（gemini-3-pro-image-preview），生视频用 Google Veo 最新版本；每次生成后都要下载检查，乱图就要修。

## Goals

- 修复 Google Veo 生视频失败（HTTP 400）导致分镜视频任务无法完成的问题。
- 完成一次真实端到端验证：从分镜首帧提交 Veo 任务 → 轮询完成 → 可下载视频并抽帧检查画面质量。

## Changes

- 调整 Google Veo 图像入参结构：将首帧/尾帧/参考图的 base64 字段从 `imageBytes` 改为 `bytesBase64Encoded`（Veo `:predictLongRunning` REST 形态要求）。
- 新增 `ai-pic-backend/app/services/providers/google_provider/video_tasks.py`，实现 Veo 的异步 submit + polling（operation name 作为 task_id）。
- 在 `GoogleProvider` 中补齐 `submit_video_task` / `fetch_video_task_status` 的模块化实现。
- 更新单测覆盖：断言提交请求包含 `bytesBase64Encoded`，并验证轮询成功/失败的映射逻辑。
- 更新 `docs/api/google/google-veo-video-generation.md`：补充 REST image-to-video 示例并纠正 `durationSeconds` 类型描述。

## Validation

- Backend tests: `cd ai-pic-backend && pytest tests/unit tests/services tests/scripts`
- Build: `./docker/build_prod_images.sh`（中途遇到一次 Docker Hub TLS 握手超时，重试后通过）
- Chrome / E2E:
  - 登录 `http://localhost:8089`（geyunfei / Gyf@845261）
  - 打开分镜页 `http://localhost:8089/episodes/a75602ec397a46d09b37f8964074a89d/storyboard?scriptId=103`
  - 通过后端接口提交第 1 帧（frame 0）的 Veo 3.1 生视频任务并等待轮询完成（task_id=640 / provider_task_id=models/.../operations/cgzho9yfqj6r）
  - 页面分镜帧展示了 “查看/下载视频” 链接（可见 `files/...:download?alt=media`）
  - 下载视频到本地 `tmp/e2e_assets/veo_task_640.mp4`，并用 `ffmpeg` 抽帧检查画面（`tmp/e2e_assets/veo_task_640_frame_0_5s.jpg` / `tmp/e2e_assets/veo_task_640_frame_3s.jpg`）

## Next Steps

- 修复前端分镜“生成视频”弹窗：当前无尾帧候选时，不应强制勾选且禁用 “使用尾帧”，导致无法在 UI 里直接提交。
- 按用户要求补齐短剧故事/剧本模板（每集爽点），并继续做完整链路：IP → 环境 → 故事 → 剧本 → 分镜图 → 分镜视频。
- 继续推进 provider-aware 的提示词/参数动态 UI（根据 provider/model 动态展示约束与额外输入项）。

## Linked Commits

- (pending) `fix(backend): correct veo image input payload`

