---
id: 2025-12-15T15-14-50Z-dialogue-audio-e2e-verified
date: 2025-12-15T15:14:50Z
participants: [human, codex]
models: [gpt-5.2]
tags: [e2e, frontend, backend, audio, storyboard]
related_paths:
  - tasks.md
summary: "Browser E2E: generate scene dialogue audio → episode audio_timeline → storyboard frames; verify beats and OSS uploads"
---

## User Prompt

好的，现在整体完成这个 Feature，记得所有音频都要上传 OSS；每完成一个工作项，及时更新 `tasks.md`、及时自测，提交后再开始下一项，保持工作区干净。

## Goals

- 在真实浏览器路径下跑通 Episode 内「生成对白音轨 → 生成时间轴 → 生成分镜帧占位」闭环
- 校验 `scene_beats`（scene 级）与 episode `audio_timeline`（beat offset 合并）数据正确落库
- 校验最终音频已上传 OSS 并可访问

## Changes

- `tasks.md`：将“对白音轨与声音驱动时间轴”Feature 的浏览器 E2E 验证项标记为完成（并注明 MCP transport closed，改用 Playwright Chromium）

## Validation

- MCP Chrome DevTools 工具调用 `chrome-devtools/list_pages` 返回 `Transport closed`，无法使用 MCP 驱动 Chrome；改用 Playwright Chromium（headless）完成浏览器 E2E（完整跑通并截图留存）。
- Playwright 用例（Episode=7，Script=14）：
  - 打开 `http://localhost:8089/episodes/7`（通过后端登录获取 token 并注入 `localStorage.auth_token`）
  - 勾选覆盖选项，依次点击：`生成对白音轨` → `生成时间轴` → `生成分镜帧占位`（每次创建任务后点击弹窗 `确定` 关闭遮罩）
  - 任务卡片均达到 `状态: 已完成`
- API 校验（带 Bearer token）：
  - `GET /api/v1/episodes/7`：`extra_metadata.audio_timeline.episode_audio.oss_url` 存在，`beats=62`
  - `curl -I <episode_audio_oss_url>`：返回 `HTTP/1.1 200 OK`，可见 `x-oss-meta-episode-id: 7`、`x-oss-meta-script-id: 14`
  - `GET /api/v1/story-structure/scripts/14/scenes`：scene(5) 的 `metadata.dialogue_audio.oss_url` 存在
  - `GET /api/v1/story-structure/scenes/5/beats`：beats>0，且 `metadata.start_ms/end_ms` 为数字（示例首个 beat `[0,1788]`）
  - `GET /api/v1/scripts/14/storyboard`：frames=31，且 frame[0].start_ms/end_ms 为数字（示例 `[0,1788]`）
- 证据文件：`/tmp/ai-video-studio-e2e-1765811569418/`（截图 + `result.json`）

## Next Steps

- （可选）修复/恢复 MCP Chrome DevTools transport，使后续强制用例可继续走 MCP 路径。

## Linked Commits

- (pending)
