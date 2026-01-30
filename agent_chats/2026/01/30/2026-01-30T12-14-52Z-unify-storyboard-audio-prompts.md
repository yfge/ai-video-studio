---
id: 2026-01-30T12-14-52Z-unify-storyboard-audio-prompts
date: 2026-01-30T12:14:52Z
participants: [human, codex]
models: [gpt-5]
tags: [backend, prompts, storyboard, video]
related_paths:
  - tasks.md
  - ai-pic-backend/app/prompts/templates.py
  - ai-pic-backend/app/prompts/templates/storyboard_audio_visual_action.txt
  - ai-pic-backend/app/prompts/templates/storyboard_audio_visual_action.yaml
  - ai-pic-backend/app/prompts/templates/storyboard_audio_visual_dialogue_read_text.txt
  - ai-pic-backend/app/prompts/templates/storyboard_audio_visual_dialogue_read_text.yaml
  - ai-pic-backend/app/prompts/templates/storyboard_audio_visual_dialogue_spoken.txt
  - ai-pic-backend/app/prompts/templates/storyboard_audio_visual_dialogue_spoken.yaml
  - ai-pic-backend/app/prompts/templates/storyboard_audio_visual_dialogue_voiceover.txt
  - ai-pic-backend/app/prompts/templates/storyboard_audio_visual_dialogue_voiceover.yaml
  - ai-pic-backend/app/prompts/templates/storyboard_audio_visual_pause.txt
  - ai-pic-backend/app/prompts/templates/storyboard_audio_visual_pause.yaml
  - ai-pic-backend/app/services/dialogue_audio_service.py
  - ai-pic-backend/app/services/storyboard/storyboard_audio_prompt_builder.py
  - ai-pic-backend/app/services/storyboard/storyboard_prompt_utils.py
  - ai-pic-backend/app/services/video/video_task_submission_helpers.py
  - ai-pic-backend/app/services/video/video_task_submission_service.py
  - ai-pic-backend/app/services/video/video_task_utils.py
  - ai-pic-backend/tests/unit/test_dialogue_audio_service.py
  - ai-pic-backend/tests/unit/test_storyboard_prompt_templates.py
summary: "Unify audio_timeline->storyboard prompt handling: keep dialogue in UI description, generate visual-only prompts, and pass reference images into Veo video tasks."
---

## User Prompt

所有的提示词统一管理；并修正 audio_timeline 分镜提示词里“对话/读屏/字幕”等污染，提升角色一致性（谁是林晚/哪个角色是哪个）。

## Goals

- audio_timeline → storyboard：把“对白文本（UI 展示）”与“视觉提示词（用于生图/生视频）”彻底分离。
- 对 dialogue/action/pause 使用不同视觉模板，强制 no subtitles/no readable text，避免生成字幕/可读文字。
- 在音轨 → 分镜链路里保留/注入角色集合，降低多角色镜头漏人概率。
- 视频提交阶段把 storyboard frame 的 `reference_images` 传给 Veo（上限 3）以提升身份一致性。

## Changes

- 新增 `storyboard_audio_visual_*` 模板（dialogue/action/pause 细分）并纳入 `PromptTemplate` 枚举。
- 新增 `app/services/storyboard/storyboard_audio_prompt_builder.py`：
  - 从音轨 beat 推导视觉描述（不包含台词、不包含可读文字），区分口播/旁白/读屏。
- `app/services/storyboard/storyboard_prompt_utils.py`：
  - `apply_storyboard_prompt_optimizations()` 支持 `prompt_description`（视觉-only）驱动 `ai_prompt`，同时保留 `description` 作为 UI 文本。
- `app/services/dialogue_audio_service.py`：
  - 生成 SceneBeat 时写入 `characters_involved`（基于场景对白角色集合）。
  - `build_episode_timeline_beats()` 回填 `characters_involved`/dialogue_action/emotion 供下游使用。
  - `build_storyboard_frames_from_audio_timeline()` 为每帧写入 `prompt_description` + `characters`（多角色集合）并保留 UI 的 `description`（可含台词）。
- `app/services/video/*`：
  - 提交视频任务时把 frame 的 `reference_images` 透传给 provider（存参时仅保留前 3 张）。
- 测试：
  - 新增断言：`ai_prompt` 不泄露台词文本，读屏类文本被模糊处理。
  - 校验新增模板可渲染。
- `tasks.md`：更新本轮 B 工作任务状态与拆分项。

## Validation

- `cd ai-pic-backend && pytest --no-cov`（1104 passed, 21 skipped）。
- `./docker/build_prod_images.sh`（成功，IMAGE_TAG=2374275）。

## Next Steps

- 继续补齐：注入 Story 角色卡简述 + 自动选取 reference_images（人物锚点+环境）到 audio_timeline storyboard（不依赖先跑分镜图）。
- 做一次真实链路抽检：2 个 dialogue beat 生成视频，验证“嘴型说话明显 + 无字幕/无可读文字”（Chrome E2E 或 API+下载对比）。

## Linked Commits

- (pending) 将在本次提交完成后补全。

