---
id: 2026-07-19T14-26-47Z-silent-tail-padding
date: "2026-07-19T14:26:47Z"
participants: [user, codex]
models: [gpt-5]
tags: [audio, timeline, padding, regression]
related_paths:
  - ai-pic-backend/app/services/audio/episode_audio_padding.py
  - ai-pic-backend/tests/unit/test_audio_timeline_storyboard.py
summary: Replace fixed-story tail padding with silent timeline pauses and verify downstream behavior.
---

## User Prompt

> "AP手机倒计时继续跳动，投影原始文件删除进度条缓慢推进。",
> "小陈连续敲键盘维持日志锁定，蓝色锁图标被红光压住。",
> "张总把签字纪要压在桌上，会议室只剩键盘声和倒计时。",
> "AP盯着屏幕不眨眼中，备份硬盘指示灯一下一下闪烁。",
>
> 全局检查生成链路里还有没有这种内容，先进行修复

## Goals

- 全局定位生产生成链路中会把固定示例剧情注入用户内容的入口。
- 修复时长补齐行为，同时保留目标总时长和视频时间轴覆盖。
- 验证音频时间轴、Timeline、分镜和静音镜头计划都接受修复后的数据。

## Changes

- 删除 `episode_audio_padding.py` 中循环注入 AP、小陈、张总等固定剧情的 `_tail_padding_action`。
- 将 episode 尾部补时 beat 改为无文本 `pause`，继续按最多 8 秒分段并保留上一有效 beat 的角色锚点。
- 更新回归测试，约束补时 beat 必须为 `pause`、`text=None`，且下游分镜只生成“停顿”语义。
- 全仓扫描确认四句固定内容不再存在于生产代码；剩余“日志锁定账号”只位于独立测试夹具。提示词 YAML 的人名只在 `usage_examples` 元数据中，`PromptManager.render_prompt()` 不会渲染该字段。
- 重启 `ai-video-celery-worker`，确保后续任务加载新实现。重启命中了正在运行的长任务 6485；该任务没有被 Celery 自动重新投递，已从错误的 `processing` 修正为 `failed`，保留手动重试入口且未擅自再次发起 30 集模型调用。

## Validation

- `pytest tests/unit/test_audio_timeline_storyboard.py -q -o addopts=''`
  - 通过：6 passed。
- `pytest tests/test_timeline_import_service.py tests/test_timeline_import_repair.py tests/test_timeline_shot_plan_silent_clips.py -q -o addopts=''`
  - 通过：12 passed。
- `python run_tests.py quick --no-setup`
  - 结果：2658 passed, 79 skipped, 20 deselected, 1 failed。
  - 唯一失败为既有且与本次改动无关的 `test_single_video_canvas_plan_reuses_unique_prompt_asset`：`resolved_context.virtual_ip_id` 为 `None`；单独复跑稳定失败。本次 diff 未触碰 Production Canvas。
- `python scripts/check_repo_docs.py`
  - 通过：`[check_repo_docs] ok`。
- `python scripts/check_repo_contracts.py --mode diff ai-pic-backend/app/services/audio/episode_audio_padding.py ai-pic-backend/tests/unit/test_audio_timeline_storyboard.py`
  - 通过：`[check_repo_contracts] ok (diff)`。
- 实际 worker 容器只读验证：50 秒源内容补齐到 60 秒时，输出 8 秒和 2 秒两个 `pause`，均为 `text=None`，总时长仍为 60000 ms。
- worker 重启后状态：`celery@515a5dc4ed3b ready`，并已正常处理轮询任务。
- Chrome 验证路径：`/episodes/0d2c8a2adfb9464b85116ecf8ca68c16/workspace?tab=timeline&scriptId=128&clipId=video_scene_561_beat_4386_001`。
  - 页面正常加载，显示 60 秒、10 段 Timeline；控制台只有 React DevTools 和 HMR 信息，无 error/warning。
  - 当前持久化的历史 Timeline v13 仍包含旧污染文案；本次没有自动重跑付费 TTS/LLM/分镜链路。
  - 截图：`artifacts/runs/20260719T142539Z-tail-padding-silence/timeline-existing-v13.jpg`。

## Next Steps

- 如需清理页面现有 v13，需要用户确认后重新生成 script 128 的 Timeline；新结果会使用无文本 pause 补时。
- 如需继续任务 6485，可在任务页手动重试；本次未自动重复发起长耗时生成。
- Quick suite 的 Production Canvas 既有失败应在独立改动中修复。

## Linked Commits

- None (commit not requested).
