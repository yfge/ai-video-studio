---
id: 2026-01-29T23-56-28Z-e2e-deepseek-banana-veo3
date: 2026-01-29T23:56:28Z
participants: [human, codex]
models: [gpt-5]
tags: [validation, e2e, google, deepseek, storyboard, audio, video]
related_paths:
  - tasks.md
summary: "Docker 内跑通 deepseek 文生文 + banana pro 生图 + veo3 生视频的全流程，并抽检时间轴/音轨/画幅与逻辑一致性。"
---

## User Prompt

做全流程测试：生文用 DeepSeek；生图用 Google banana pro；生视频用 Google Veo 3。生成 1 个 Story、1 个 Episode、以及剧内的时间轴/音轨/视频，然后校验图和视频是否合乎逻辑。

## Goals

- 在 Docker 环境跑通：Story -> Episode -> Script -> timeline/audio -> storyboard image -> storyboard video。
- 验证画幅与元数据一致（9:16 / 720p）并可下载抽检。
- 验证人物/剧情没有“未知角色”漂移（仅 Story 注册角色 + 允许的泛化小角色）。
- 把关键 IDs/产物 URL/校验结果记录到 ledger，便于复现与排障。

## Changes

- 更新任务看板：`tasks.md` 标记“deepseek + banana pro + veo3 全流程 E2E”已完成（Chrome MCP 不可用时使用 API/curl 抽检）。
- 新增本次 E2E 验证记录：`agent_chats/2026/01/29/2026-01-29T23-56-28Z-e2e-deepseek-banana-veo3.md`。

## Validation

- Chrome MCP：`chrome-devtools/list_pages` 返回 `Transport closed`，无法执行浏览器自动化；改用 API/curl + 下载抽检。
- Docker API 全流程（localhost:8000）：
  - Story（DeepSeek）异步生成：
    - task_id=5882 -> story_id=40（title=`E2E全流程测试-角色规范-20260130-071752`）
    - 角色：character_ids=[1(老拐),2(文闻)]
  - Episode（DeepSeek + repair/校验）异步生成：
    - task_id=5883 -> episode_id=133（title=`雨夜代码与诗`）
  - Script（DeepSeek）异步生成：
    - task_id=5884 -> script_id=117（title=`雨夜代码与诗 - 剧本`）
    - 角色抽检：对白 speaker 仅出现 `文闻/老拐/旁白`（无未知命名角色）
  - Timeline + Audio + Storyboard（timeline-pipeline）：
    - task_id=5885 -> episode.extra_metadata.audio_timeline.version=1；beats=19
    - episode_audio.oss_url=`http://resource.lets-gpt.com/episode-dialogue/episodes/audio/20260129/234036/b6342fbe.mp3`
    - `ffprobe /tmp/e2e_media/episode133.mp3`：mp3/24000Hz/mono，duration=200.001625s；beats[-1].end_ms=200000（与音轨时长对齐）
  - Storyboard Image（Banana Pro，frame_index=2）：
    - task_id=5886 -> image_url=`http://resource.lets-gpt.com/ai-generated/storyboard/image/20260129/234340/53ae6e00.png`
    - 下载抽检：`/tmp/e2e_media/frame3.png`，分辨率 768x1376（9:16）
  - Storyboard Video（Veo 3，frame_index=2）：
    - task_id=5887 -> video_url=`http://resource.lets-gpt.com/ai-generated/videos/video/20260129/234627/0e7c211b.mp4`
    - `ffprobe /tmp/e2e_media/frame3.mp4`：720x1280，24fps，duration=8s（9:16/720p 符合预期）
    - 逻辑抽检：frame3 prompt/画面为“雨夜窗边电脑蓝屏，文闻看向老拐”，与剧本/分镜描述一致。

## Next Steps

- 等 Chrome MCP 恢复后补一次浏览器端 E2E（按 tasks.md 要求记录 UI 操作链路）。
- 继续推进 readiness 检查与生成后逻辑一致性校验（阻断/修复策略 + 单测 + 端到端验证）。

## Linked Commits

- (pending) chore(tasks): record deepseek+banana+veo3 full e2e validation
