# 对白音轨与声音驱动时间轴 — Spec（MVP）

> 目标：Episode 生成后，在单集内一键产出「场景对白混音音轨（1 scene = 1 track）→ scene_beats → episode 时间轴 → 分镜帧占位」，并确保**所有最终音频均上传 OSS**。时长以声音为准（TTS 实际时长）。

## 1. 输入与范围

- 输入数据源：
  - `scripts.dialogues[]`（按 list 顺序视为对白顺序；`scene_number` + `character` + `content`）
  - `scripts.stage_directions[]`（`scene_number` + `content` + 可选 `timing`）
  - 规范化场景：`scenes`（`script_id` 下按 `scene_number` 排序）
- MVP 输出粒度：
  - **每个 Scene 生成 1 条对白音轨**（把该场景的对白片段按顺序拼接，并按规则补足留白）
  - Scene 级 beats 落库到 `scene_beats`（不在 episode 级存 beats 表）
  - Episode 级时间轴以 JSON 形式落到 `episodes.extra_metadata`（后续可迁移到 Timeline Spec/EDL）

## 2. 音色绑定（VirtualIP / 衍生角色）

### 2.1 VirtualIP（已有 IP 库角色）

- 若 `virtual_ips.voice_config` 缺失：运行 agent 从系统音色候选集中选择 `voice_id`，并**自动落库**到 `virtual_ips.voice_config`（无需人工确认）。

### 2.2 衍生角色（脚本出现但 IP 库不存在）

- 定义：脚本 `dialogues[].character` 出现，但无法映射到 Story 的 `StoryCharacter.virtual_ip_id` 的角色名（例如「路人」「店员」）。
- 使用 agent 判断 voice binding scope：
  - `scene` / `episode` / `story`
- voice binding 的存储位置（JSON）：
  - `scene`：`scenes.metadata.derived_character_voice_bindings`
  - `episode`：`episodes.extra_metadata.derived_character_voice_bindings`
  - `story`：`stories.extra_metadata.derived_character_voice_bindings`

## 3. Scene 音轨生成

### 3.1 Segment 类型（用于 beats 与音频拼接）

- `dialogue`：对白（TTS）
- `action`：舞台指示/留白（MVP 用静音补足；后续可扩展为环境音/旁白）
- `pause`：对白间停顿（静音）

### 3.2 默认补足规则（可后续参数化）

- 每条对白后追加 `pause`（默认 300ms）
- `action` 静音时长（默认 800ms；可根据文本长度线性放大）
- 当某 Scene 无任何对白/舞台指示时：生成 2s 静音音轨并产出 1 个 `action` beat

### 3.3 Scene 级落库

- Scene 音频落库（JSON，存于 `scenes.metadata.dialogue_audio`）：
  - `oss_url`: string
  - `duration_seconds`: number
  - `generated_at`: ISO8601
  - `version`: int（自增）
  - `script_id`: int
- Beats 落库到 `scene_beats`（每个 segment 1 行）：
  - `beat_type`: `dialogue` | `action` | `pause`
  - `dialogue_excerpt`: 对白文本（仅 dialogue），或留空
  - `beat_summary`: 舞台指示文本（仅 action），或留空
  - `duration_seconds`: segment 实际时长（来自音频）
  - `metadata`（建议字段）：
    - `start_ms` / `end_ms`
    - `speaker_name`（dialogue）
    - `speaker_kind`: `virtual_ip` | `derived` | `narrator`
    - `voice_config`（快照，便于审计）
    - `source`: `dialogue_audio_pipeline`

## 4. Episode 音轨拼接与时间轴

- Episode 音频：按场景顺序拼接 `scenes.metadata.dialogue_audio.oss_url`，产出 1 条 episode 级音频并上传 OSS。
- Episode 级时间轴：把各 scene 的 beats 做 offset 合并（`start_ms/end_ms` + cumulative scene duration）。
- Episode 级落库（JSON，存于 `episodes.extra_metadata.audio_timeline`）：
  - `script_id`: int
  - `episode_audio`: `{ oss_url, duration_seconds, generated_at, version }`
  - `beats[]`: `scene_id/scene_number/beat_id/beat_type/speaker_name/text/start_ms/end_ms`

## 5. 从时间轴生成分镜帧占位

- MVP：从 episode `audio_timeline.beats` 生成 `storyboard.frames`（结构占位，无图像 URL）。
- 默认策略：
  - 仅为 `dialogue` 与 `action` beats 生成帧；`pause` 默认跳过（除非 > 1.5s）
  - `duration_seconds` 来自 beat
  - 额外字段可写入 frame（如 `start_ms/end_ms`）用于后续剪辑
