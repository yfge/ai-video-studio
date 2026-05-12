# 任务看板（6 周执行版）

> 本文件只保留未来 6 周内可执行、且直接支撑产品主线的任务。历史完成记录保留在 `agent_chats/`、`docs/` 和 git，不再在这里堆叠。

## 产品定位

- 目标用户：专业短剧制作团队，不是小白一键成片用户。
- 产品模式：ToB 生产工作流系统，不是通用 AI 视频玩具。
- 第一性原理：`Timeline` 是系统的单一事实来源（SSOT）。
- 默认生产模式：对白/音轨时间轴驱动时长，图像/视频生成只是向时间轴填充 clip 资产。
- 当前目标：把 `audio -> timeline -> clip -> render -> export` 做成产品核心闭环。

## 看板规则

- 只记录未来 6 周内的活跃任务，不保留长线愿景和历史清单。
- 任何不直接支撑时间轴第一性的工作，不进入本看板。
- `Storyboard` 是时间轴的支撑视图，不再作为系统主编排入口。
- 新任务必须回答两个问题：
  - 是否让时间轴更像 SSOT？
  - 是否缩短从音轨到可导出成片的路径？

## 状态概览

- P0：Timeline Spec v1 文档、DB/API foundation 和 `audio_timeline.beats` 导入桥已落地，下一步把真实 render/export 回写迁入 versioned timeline jobs。
- P0：把对白音轨、beats、占位分镜、渲染导出收成一条可重渲主链。
- P0：优先清理会阻断这条主链的 legacy 和稳定性问题。
- P1：把默认操作路径从 `Episode -> Storyboard` 改成 `Episode -> Timeline`。

## P0: Timeline SSOT

:link: `docs/timeline-rendering-pipeline.md`, `docs/dialogue-audio-timeline-spec.md`

当前阻塞：

- `audio_timeline`、`scene_beats`、`storyboard.frames` 仍然并存，但 timeline-pipeline 已能把 `audio_timeline.beats` 导入 `Timeline Spec v1`。
- 渲染结果仍有一部分写回临时 metadata，而不是稳定的 timeline/versioned jobs。

### 任务（功能→后端→验证）

- [x] 文档冻结 `Timeline Spec v1`，定义 `tracks / clips / assets / source / version` 的目标字段和约束。
- [x] 文档明确现有 `audio_timeline`、`scene_beats`、`storyboard.frames` 到 `Timeline Spec v1` 的导入规则、优先级和冲突处理。
- [x] 完成 `timelines`、`render_jobs`、`media_assets` 数据模型与迁移，明确和现有图片/视频记录的关系。
- [x] 实现 timeline list/create/read/update、版本锁、自增保存和 render-job 幂等入队/读取 API。
- [x] 将现有 timeline-pipeline 的 `audio_timeline.beats` 导入 `timelines.spec`，生成 dialogue/video/subtitle clips。
- [ ] 补齐 timeline delete/rollback、真实 export 触发和 completed render output 回写。
- [x] 文档定义稳定 `clip_id` 生成规则，保证后续 re-dub / re-cut / re-render 不丢身份。
- [ ] 渲染结果统一回写到 timeline/versioned render jobs，不再只写 ad hoc metadata。
- [ ] 为 Timeline Spec 增加 schema 校验、导入校验、权限校验和导出幂等测试。

## P0: Audio-First Production Chain

:link: `docs/dialogue-audio-timeline-spec.md`

当前阻塞：

- 场景音轨、episode 音轨、beats、分镜占位已经有雏形，但 clip 级 lineage 和 timing source 还不稳定。
- 重新配音、重新切分、重新导出还没有统一挂在稳定 clip identity 上。

### 任务（功能→后端→验证）

- [x] 文档冻结 `scene -> episode audio -> beats -> timeline` 映射规则，补齐 `scene_beats` 与 episode offset 合并说明。
- [ ] 在短剧模式下，把 dialogue/audio timing 明确为默认 clip duration source，并在任务审计中记录来源。
- [x] 文档定义 timeline clip 的 `timing_source`、`voice_source`、`clip_replacement_of`、`render_source_version` 等审计字段。
- [x] 在导入桥中按 `track_type + scene_id + beat_id + ordinal` 生成稳定 `clip_id`。
- [ ] 支持基于稳定 `clip_id` 的 re-dub、re-cut、re-render，不允许靠临时 frame index 追踪资产。
- [ ] 确保 storyboard placeholder 只消费 timeline facts，不再依赖自由估算时长。
- [ ] 将首尾帧、分镜图、分镜视频都视为 clip asset，和 timeline clip 显式关联。
- [ ] 写通一条回归链路：`scene audio -> episode timeline -> storyboard placeholder -> clip render -> export`。

## P0: Stability And De-Legacy

:link: `ai-pic-backend/app/api/v1/endpoints/scripts_legacy.py`, `ai-pic-backend/app/services/dialogue_audio_service.py`, `ai-pic-backend/app/services/ai_service_manager.py`, `ai-pic-frontend/src/app/episodes/[id]/storyboard/page.tsx`

当前阻塞：

- `scripts_legacy.py` 仍然是 scripts 路由的实际挂载中心。
- 后端关键服务和前端 storyboard 页面仍然是高耦合 choke point。
- 当前仓库已观察到主链可靠性漂移，说明只加功能不收口会继续失稳。

### 任务（后端→前端→测试→验证）

- [ ] 继续拆分并下线 `scripts_legacy.py`，让 timeline/audio/storyboard 主链不再依赖 legacy router。
- [ ] 拆分 `dialogue_audio_service.py`，至少分离 scene audio 生成、episode 拼接、beats 落库、timeline 占位转换。
- [ ] 拆分 `ai_service_manager.py`，把 provider routing、fallback、model cache、request logging 收成独立模块。
- [ ] 修复 story fallback 测试漂移：统一 `ai_fallback` / `ai_fallback_invalid` 语义与断言。
- [ ] 修复 AI 初始化中的 `asyncio.run() cannot be called from a running event loop` 警告，避免 warm-cache 逻辑污染任务链。
- [ ] 收敛 step-by-step pipeline 的 deprecation 状态，防止 UI 和后端继续沿旧路径分叉。
- [ ] 拆分 `ai-pic-frontend/src/app/episodes/[id]/storyboard/page.tsx`，并将默认操作导向 timeline workspace。
- [ ] 为 `audio -> timeline -> storyboard -> render` 主链补齐一组最小回归测试。

## P1: Operator Workflow

:link: `docs/timeline-rendering-pipeline.md`

当前阻塞：

- 当前主操作面仍偏向 storyboard 页面，而不是 timeline。
- 专业团队真正需要的 clip 状态、源音轨、源帧、导出状态没有集中在一个默认界面。

### 任务（前端→后端→验证）

- [ ] 将默认操作路径改为 `Episode -> Timeline`，减少从 episode/detail/workspace 跳到 storyboard 的主流程依赖。
- [ ] 实现 timeline operator 视图：clip 列表、源音轨、源帧、render status、retry、replace clip、export。
- [ ] 把 storyboard 调整为支持视图：查看占位、关键帧、镜头上下文，不再承担主编排职责。
- [ ] 在 timeline 视图直接展示 proxy/final 输出、render job 状态和失败原因。
- [ ] 为 operator workflow 增加一条标准 E2E：`Episode -> Timeline -> Render -> Export`。

## 6-Week Exit Criteria

- [ ] `Timeline Spec v1` 冻结，并被用作系统唯一时间轴事实来源。
- [ ] 至少 1 个 episode 可以从 audio-driven timeline 重建到最终导出。
- [ ] re-dub / re-render 不会打断 stable `clip_id`。
- [ ] 不再有主要用户路径依赖 `scripts_legacy.py`。
- [ ] storyboard 页面不再是系统主编排入口。
- [ ] `audio -> timeline -> storyboard -> render` 核心回归测试通过。
