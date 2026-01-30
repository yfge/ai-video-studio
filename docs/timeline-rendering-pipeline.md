# AI 漫剧平台：时间轴（Timeline）与渲染流水线设计

## 背景与问题

当前项目的内容分层是 `IP → Story → Episode → Script → Scene → Storyboard`（另有规范化表：Scene/Shot 等），已经能支撑“写作/拆分/分镜”的生产过程。但当目标变成：

1. 为每个镜头生成分镜的首尾关键帧
2. 基于关键帧生成视频片段（image-to-video / video diffusion）
3. 拼接、剪辑、混音，导出单集成片（≤5分钟）

会出现一个结构性缺口：**缺少一个“可渲染的编排主线”**。

> Story/Episode/Script/Scene/Shot/Storyboard 是“内容与资产层级”；
> Timeline/Sequence/EDL 是“剪辑与渲染主线”（决定顺序、时长、轨道、版本、导出）。

因此建议在现有架构上新增“时间轴/剪辑序列”域模型与渲染任务链路，而不是推倒重来改成“只以声音为主线”。声音可以作为主线的来源之一，但落地仍需要时间轴承载。

## 目标（Goals）

- 为“首尾帧 → 视频片段 → 拼接导出”的流水线提供**稳定、可审计、可重渲**的编排层。
- 支持两种生成策略：
  - **声音优先**：先生成对白/TTS，得到每句时长 → 自动切分镜头/片段 → 生成关键帧与视频。
  - **视觉优先**：先生成分镜与（估算）时长 → 生成视频 → 再生成对白/TTS并微调时长。
- 明确 MVP：单集 ≤5分钟，主要是镜头级剪辑（少量转场、字幕、BGM/SFX 基础混音），重活由后端渲染。

## 非目标（Non-Goals）

- 不在浏览器端实现专业 NLE（如 PR/CapCut）的实时特效与全量渲染。
- 不在第一阶段做复杂口型（lip-sync）与高阶表演驱动；保留接口扩展点。

## 现状盘点（基于当前代码库）

### 内容结构与规范化层

- `stories/episodes/scripts`：叙事与剧本层（`ai-pic-backend/app/models/script.py`）。
- 规范化表：`scenes/scene_beats/shots/environments`（`ai-pic-backend/app/models/story_structure.py`）。
  - `shots.character_ids` 已能绑定虚拟 IP；
  - `scenes.environment_id` 已能绑定环境资产；
  - `shots.storyboard_frame_asset_id` 可用于挂载某张关键帧（目前主要是规划性字段）。

### 分镜（Storyboard）

- `StoryboardFrame` 结构（`ai-pic-backend/app/schemas/generation.py`）包含：
  - `duration_seconds`、`ai_prompt`、`reference_images`、`image_url`、`video_url`
- 目前分镜主体存储在 `script.extra_metadata.storyboard`（JSON），并提供 `/scripts/{id}/storyboard` 等接口。

### 任务与资产

- `Task` 表与异步处理已存在（Celery/BackgroundTasks 混用）。
- 图像持久化走统一抽象（本地 + OSS/CDN），并已补充 CDN 上传日志（`ai-pic-backend/app/services/ai_service.py`）。
- 视频生成存在基础能力（`ai_service.generate_video`），但**缺少“视频资产落库+与镜头/时间轴关联”的一致结构**。

## 核心设计：新增“时间轴/剪辑序列”域模型

### 为什么必须有 Timeline

Storyboard 解决“镜头列表与画面意图”，但不能完整表达：

- 片段顺序、入点/出点（trim）、可变速；
- 多轨：对白、BGM、SFX、字幕；
- 版本与导出（render jobs）；
- 可重渲/可回溯：哪些片段由哪个关键帧/模型/提示词生成；
- 预览与最终导出（proxy vs final）的产物管理。

Timeline 是最终成片（Episode Output）的“单一事实来源（SSOT）”。

### 术语（建议统一）

- **Shot（镜头）**：叙事/拍摄规划单元，属于 Scene，来自 `shots` 表（规范化）。
- **StoryboardFrame（分镜帧）**：面向生成的镜头描述（当前以 JSON 存在 script.extra_metadata）。
- **Clip（片段）**：时间轴上的可播放单元（视频片段/音频片段/字幕片段）。
- **Track（轨道）**：时间轴上的一条轨道（video/dialogue/bgm/sfx/subtitle）。
- **Timeline / Sequence**：轨道+片段的集合，绑定到 Episode（或 Script 版本）。
- **RenderJob（导出任务）**：从某个 Timeline 版本渲染出 proxy/final 的一次作业。
- **MediaAsset（媒体资产）**：统一的 image/video/audio 产物记录（URL、对象键、元数据、来源）。
- **EDL（Edit Decision List）**：时间轴决策（可 JSON 表达），用于审计/复现。

## 数据模型设计（推荐：表结构 + JSON Spec 混合）

> 原则：关键链路“可追溯、可重渲、可关联任务”，同时允许迭代（JSON spec 承载灵活字段）。

### 1) timelines（序列）

- `id`
- `episode_id`（或 `script_id`；推荐 episode 维度，允许多个 script 版本）
- `script_id`（生成该时间轴的基准脚本版本）
- `title`
- `status`：draft / ready / rendering / exported / failed
- `spec`（JSON）：EDL 主体（tracks/clips 的序列化结构，便于一次性读写）
- `version`（int）：每次保存 +1（用于乐观锁、可回滚）
- `created_by` / `updated_by`
- `created_at` / `updated_at`

索引建议：`(episode_id, updated_at desc)`、`(episode_id, status)`。

### 2) media_assets（统一媒体资产）

为避免 image/video/audio 分散存储，建议新增统一表（未来可替代/并存 `images` 表）：

- `id`
- `asset_type`：image / video / audio / subtitle
- `origin`：ai_generated / user_uploaded / imported / rendered
- `mime_type`
- `file_url`（CDN/OSS URL）
- `object_key`（OSS key，可选）
- `file_path`（本地相对路径，可选）
- `duration_ms`（video/audio 可用）
- `width/height`（image/video 可用）
- `hash`（用于复用/去重，例如基于关键参数算）
- `metadata`（JSON）：prompt/model/provider/usage 等
- `created_by`
- `created_at`

### 3) render_jobs（导出任务）

- `id`
- `timeline_id`
- `timeline_version`（快照版本，确保可复现）
- `render_type`：proxy / final
- `preset`：分辨率/码率/fps/音频采样率等（JSON）
- `status`：queued / running / succeeded / failed
- `progress`：0-100（可选）
- `output_asset_id` → `media_assets.id`
- `log`（JSON/Text）：关键步骤与产物
- `created_by`
- `created_at` / `updated_at`

### 与现有 Storyboard/Shot 的关联方式

MVP 建议：

- Timeline Clip 里保留 `source` 字段（JSON），允许引用：
  - `shot_id`（规范化 shots）
  - `storyboard_frame_id`（JSON frame_id）
  - `scene_id`
  - `character_ids`、`environment_id`
- “关键帧/视频片段/对白音频”都写入 `media_assets`，再在 Clip 中引用其 `asset_id`。

> 这样可以逐步从“纯 JSON storyboard”过渡到“shots 主导 + storyboard 辅助”的结构，而不破坏现有链路。

## Timeline Spec（EDL）JSON 结构（建议）

最小结构（MVP）：

```json
{
  "timeline_id": 123,
  "version": 7,
  "fps": 24,
  "resolution": "1280x720",
  "tracks": [
    {
      "track_id": "video-1",
      "type": "video",
      "clips": [
        {
          "clip_id": "c1",
          "order": 1,
          "duration_ms": 3200,
          "source": {
            "shot_id": 9001,
            "scene_id": 501,
            "storyboard_frame_id": "..."
          },
          "start_frame_asset_id": 111,
          "end_frame_asset_id": 112,
          "video_asset_id": 210,
          "generation": {
            "model": "keling-video",
            "provider": "keling",
            "prompt": "...",
            "seed": null
          }
        }
      ]
    },
    {
      "track_id": "dialogue-1",
      "type": "dialogue",
      "clips": [
        {
          "clip_id": "d1",
          "order": 1,
          "duration_ms": 3200,
          "audio_asset_id": 310,
          "subtitle": "..."
        }
      ]
    }
  ]
}
```

说明：

- 以 `duration_ms` 做 MVP，后续可以升级为 `start_ms/end_ms` 支持 trim。
- `generation` 保留模型/提示词/参数，用于重渲与审计。
- `*_asset_id` 引用 `media_assets.id`，避免直接散落 URL。

## 后端任务链路（首尾帧→视频→拼接导出）

> 核心原则：**每个 clip 可独立重跑**；整条链路可从任何阶段续跑；输出全部落库（Task + media_assets + render_jobs）。

### 1) 生成对白（可选：声音优先）

- 输入：SceneBeat.dialogue_excerpt 或 Script.dialogues（JSON），加角色信息。
- 输出：DialogueLine（可用 JSON 先挂在 timeline spec 或新表），并做 TTS：
  - `audio_asset_id`
  - `duration_ms`
- 结果：确定每个镜头/片段的目标时长（可驱动分镜帧数/镜头切分）。

### 2) 生成关键帧（每个 clip 两张）

对每个 video clip：

- 计算 start/end 关键帧 prompt（可复用 `StoryboardFrame.ai_prompt`，或对同一镜头追加“开头/结尾状态”）
- 注入参考图：
  - 环境参考图（`environments.reference_images`）
  - 角色参考图（虚拟 IP 默认图/指定表情/全身像）
- 输出：两个 image `media_assets`（并保存到 OSS/CDN）

### 3) 生成视频片段（image-to-video）

对每个 clip：

- 输入：start/end 两张关键帧（或至少 start 关键帧）+ prompt + duration
- 调用 provider video API（Keling/Volcengine/...）
- 输出：video `media_assets`（OSS/CDN URL），回填 timeline spec 的 `video_asset_id`

### 4) 拼接与剪辑导出（FFmpeg）

从 timeline spec 构建渲染任务：

- 合成 video track：按顺序 concat（需要统一编码参数；必要时先转码成中间格式）
- 合成 audio tracks：
  - dialogue 对齐 clip 时长（必要时静音补齐/轻微 time-stretch）
  - bgm/sfx 混音与音量曲线（MVP 可先做固定音量）
- 字幕：
  - MVP：可选 burn-in（ASS）或输出外挂字幕
- 输出：
  - proxy：低清 HLS（方便前端预览与拖动定位）
  - final：mp4（用于发布/下载）

建议：RenderJob 产物落 `media_assets` 并记录参数快照，确保可复现。

### 5) 复用与幂等（节省成本）

每个 clip 生成一个 `generation_hash`（由 prompt/model/refs/seed/duration 等组成）：

- 若 hash 未变化且已有 `video_asset_id`，允许复用；
- 变更时只重跑受影响 clip；
- 全片导出（RenderJob）依赖当前 timeline version，版本固定可复现。

## 前端：时间轴管理（MVP）

目标：先做“能用且可扩展”的 MVP，不追求复杂拖拽特效。

### 页面建议

- Episode 详情页增加入口：`时间轴/剪辑`
- Timeline 列表页：每集可多个 timeline（不同版本/风格/长度）
- Timeline 编辑页（MVP）：
  - Clip 列表（可排序、可改时长、可绑定镜头/对白）
  - 单 clip 的关键帧预览（复用现有 `ImagePreviewModal` 思路）
  - “生成关键帧/生成视频片段/导出预览/导出成片”按钮（触发后端 Task）
  - 预览播放器：播放 proxy（HLS），并高亮当前 clip

### 交互边界（建议）

- Web 做编辑与预览；渲染/拼接在后端做。
- 单集 ≤5分钟可接受频繁导出 proxy；final 导出走显式按钮。

## 声音优先 vs 视觉优先：推荐策略

推荐默认：**声音优先（对白/TTS → 时长 → 分镜/时间轴）**，原因：

- 漫剧节奏主要由台词驱动；时长确定后镜头切分更稳定；
- 后续做口型/表演驱动会更自然（先有音频对齐）。

但保留视觉优先入口：

- 先出分镜画面与镜头意图，适合偏 PV/情绪短片；
- 再补对白可走“字幕+旁白”为主的风格。

## 里程碑（建议分阶段落地）

### Phase 0：定义与对齐（本设计文档）

- 冻结 Timeline/Asset/RenderJob 的最小字段与 API 形态
- 明确“声音优先”是否作为默认

### Phase 1：MVP 时间轴 + 导出

- Timeline CRUD + spec JSON 落库
- Clip 列表编排（顺序 + 时长）
- RenderJob：将已有 video_url（若存在）拼接导出 proxy/final（先不做关键帧）

### Phase 2：首尾帧 → 视频片段

- 每个 clip 关键帧生成（start/end）
- 每个 clip 视频生成
- RenderJob 使用生成的视频片段拼接导出

### Phase 3：对白/TTS 与混音

- DialogueLine/TTS 产物落库
- Timeline audio track 对齐与混音
- 字幕生成与导出

## 验证路径（Chrome E2E，建议写入 agent_chats）

1. 登录（`geyunfei / Gyf@845261`）
2. 创建虚拟 IP（或复用已有），确保有角色参考图
3. 创建环境资产，确保有环境参考图
4. 创建 Story → Episode → Script
5. 生成/编辑分镜（确保每帧有 ai_prompt 与 duration）
6. 创建 Timeline（从 shots/storyboard frames 自动生成 clip 列表）
7. 对某个 clip 生成首尾帧（验证 CDN URL）
8. 对该 clip 生成视频片段
9. 导出 proxy，前端播放验证 clip 顺序与时长
10. 导出 final，下载/播放验证音画同步与拼接正确
