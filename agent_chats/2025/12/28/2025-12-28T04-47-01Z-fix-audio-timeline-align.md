---
id: 2025-12-28T04-47-01Z-fix-audio-timeline-align
date: "2025-12-28T04:47:01Z"
participants: [human, codex]
models: [gpt-5.2]
tags: [backend, audio, timeline, duration]
related_paths:
  - ai-pic-backend/app/services/dialogue_audio_service.py
  - ai-pic-backend/app/services/audio/time_stretch.py
  - ai-pic-backend/app/services/audio/dialogue_processing/segment_padding.py
  - ai-pic-backend/tests/unit/services/audio/test_dialogue_segment_padding.py
summary: "对齐对白音轨/时间轴：超预算对白自动 time-stretch，非对白段超预算自动裁剪；episode 拼接改为 WAV concat 避免 ffmpeg/libmp3lame 报错。"
---

## User Prompt

用户要求继续解决“剧本→对白→分镜时间轴对不齐（对白过少/音频过短）”，并指定用 Chrome 在 `http://localhost:8089/episodes/cd378417b7f143eab5bc6d063cd7f6e7/workspace?tab=script&scriptId=51` / `scriptId=52` 做验证与回归。

## Goals

- 让场景对白音轨时长可稳定对齐到场景预算（避免超短/超长）。
- 让剧集级时间轴与 `episode.duration_minutes` 对齐（例：3 分钟=180s）。
- 修复时间轴流水线在 episode 音轨拼接阶段的 ffmpeg/libmp3lame 报错，确保流水线可完成。

## Changes

- `generate_scene_dialogue_audio`：
  - 当对白音轨（dialogues）时长接近/超过场景预算时，先对对白做 time-stretch（ffmpeg `atempo`），再进入时间轴规划与补齐，避免对白自身就超预算导致 scene 音轨整体超长。
  - 修复 pause/action 段对 `planned_duration_ms=0` 的错误处理（避免 `or 300/800` 把 0 误当成默认值）。
- `segment_padding._pad_segments_to_target_duration_ms`：
  - 新增“超预算裁剪”：当 `dialogue_ms + non_dialogue_ms > target_ms` 时，优先裁剪 pause，再裁剪 action，确保最终总时长回到 target。
- `audio/time_stretch.py`：
  - 新增 atempo 链构建与 ffmpeg 命令生成，支持 >2.0 / <0.5 的链式变速。
- `dialogue_audio_service._concat_mp3s`：
  - episode 级拼接改为：MP3 → 归一化 WAV → concat WAV → encode MP3，规避 concat demuxer 直连 libmp3lame 触发的 `inadequate AVFrame plane padding`。
- 单测：
  - `test_dialogue_segment_padding.py` 增加“超预算裁剪”覆盖。

## Validation

- Backend quick gate：`cd ai-pic-backend && pytest tests/unit tests/services tests/scripts`（通过）。
- Backend full suite：`cd ai-pic-backend && pytest`（当前基线存在大量失败用例：90 failed / 7 errors，本次改动未触达相关域，暂不在此提交内修复）。
- Docker：`./docker/build_prod_images.sh`（通过）。
- Chrome（MCP）+ 真实数据回归：
  - 触发 `scriptId=52` 的一键时间轴流水线（overwrite=true），任务完成后在 `http://localhost:8089/episodes/cd378417b7f143eab5bc6d063cd7f6e7/workspace?tab=timeline&scriptId=52` 确认：
    - 场景 1/2/3/4 的对白音轨时长分别对齐为 30s/15s/15s/120s；
    - 剧集音轨与时间轴生成成功，时间轴总时长为 180s。

## Next Steps

- 将“对白被 time-stretch”的信息回写到 beat 元数据中并在前端提示（避免无感知的语速变化）。
- 若用户偏好“补充对白而不是变速”，可在 script REACT 阶段对超预算场景做对白压缩重写（保持语速自然）。

## Linked Commits

- (pending)
