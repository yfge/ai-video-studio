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
- 当前不新增 C 端 APP、通用 SaaS、社交 feed、素材市场等横向平台任务。
- 新任务必须回答两个问题：
  - 是否让时间轴更像 SSOT？
  - 是否缩短从音轨到可导出成片的路径？

## 当前最高优先级

- 当前未提交改动已拆成可审查提交边界：Timeline render/export、Codex/ChatGPT provider、IP 内容填充 DeepSeek、主链 readiness 文档。
- 真实 API harness 已通过一次 `Episode -> Timeline -> Render -> Export`：`artifacts/runs/main-chain-e2e-lineage-20260525T040437Z/golden_path.json`。
- timeline delete/restore、render attempt delete/restore、rollback、Timeline Spec schema/import validation、first-class clip asset lineage 后端基础、stable `clip_id` rework API、operator 资产审计读视图、基于已有 media asset 的 rework 控制，以及 provider-backed clip video rework task queue、operator 入口、success lineage 和 rework 后自动 render queue 已落地；下一步进入 legacy 收敛和样片验证。
- 在 10 条窄垂类样片通过前，不把主链标记为商业化可用。

## 状态概览

- P0：Timeline Spec v1 文档、DB/API foundation、`audio_timeline.beats` 导入桥、Timeline readiness 优先级、默认 storyboard support 生成源、dry-run backfill、versioned render/export 回写、delete/rollback、schema/import 校验、clip asset lineage 后端基础和 stable `clip_id` rework API 已落地。
- P0：把对白音轨、beats、占位分镜、渲染导出收成一条可重渲主链。
- P0：优先清理会阻断这条主链的 legacy 和稳定性问题。
- P1：provider-backed video rework task queue 已有后端链路、operator 入口和成功后自动 final render 编排；继续收敛 legacy 稳定性风险。
- P2：用一个窄垂类连续生产 10 条 30-60 秒样片，记录成本、耗时、失败点和人工修正次数。

## 已完成基线

- `timelines`、`render_jobs`、`media_assets` DB/API foundation 已落地。
- `audio_timeline.beats` 已能导入 Timeline Spec v1，生成 dialogue/video/subtitle clips。
- 默认 production/timeline-pipeline 的 storyboard support 已优先消费 Timeline Spec clips。
- render/export worker、`render_jobs.output_asset` 回写、Timeline operator 基础面板和 render/export harness 路径已落地。
- legacy storyboard 视频资产可作为迁移桥导入 Timeline video track，并已跑通一次真实 render/export。

## P0: Main Chain Closure

:link: `docs/timeline-rendering-pipeline.md`, `docs/dialogue-audio-timeline-spec.md`

当前阻塞：

- `audio_timeline`、`scene_beats`、`storyboard.frames` 仍然并存，但 timeline-pipeline、默认生产剧本链路和 deprecated audio-timeline 入口已能把 `audio_timeline.beats` 导入 `Timeline Spec v1`。
- render/export 已能写回稳定的 timeline/versioned jobs；delete/rollback 和更严格的 schema/import 校验已补齐。
- 当前真实 API 的 `Episode -> Timeline -> Render -> Export` 证据已通过；该证据使用 legacy storyboard 视频资产迁移桥，clip asset lineage 后端基础、stable `clip_id` rework API、operator 资产审计读视图、基于已有 media asset 的 rework 控制、provider-backed video rework operator 入口、success lineage 和 rework-triggered final render 编排已补齐。

### 任务（功能→后端→验证）

- [x] 将当前未提交改动拆成可审查的提交边界并完成对应 ledger。
- [x] 补跑真实 `Episode -> Timeline -> Render -> Export`，证据落到 `artifacts/runs/<run_id>/`。
- [x] 补齐 timeline delete/rollback。
- [x] 为 Timeline Spec 增加 schema 校验、导入校验和权限校验。
- [x] 补 first-class clip asset lineage 后端基础：源音频、storyboard 视频和 render 输出按 `clip_id` 关联。
- [x] 补更完整的导出幂等测试，并和 rework 操作联动。

## P1: Production Stability

:link: `docs/exec-plans/active/main-chain-commercial-readiness.md`

当前阻塞：

- 场景音轨、episode 音轨、beats、分镜占位已经收敛到 Timeline Spec 导入；legacy storyboard 视频迁移桥已可生成可渲染 video track，first-class clip asset 关联已有后端基础。
- 重新配音、重新切分、重新导出已有后端 replacement lineage API 挂在稳定 clip identity 上，operator 可以查看选中片段的源/输出/替换资产历史，也可以把已有 `media_asset_id` 记录为重做资产；backend 也能为选中 video clip 排 provider-backed rework task，并在视频任务成功后写回 `provider_rework` replacement lineage；operator 已接入 provider rework API，生成成功后会自动排一个带 rework 指纹的 final render job。
- `scripts_legacy.py`、`dialogue_audio_service.py`、`ai_service_manager.py` 仍是主链旁边的稳定性风险。

### 任务（功能→后端→验证）

- [x] 支持基于稳定 `clip_id` 的 re-dub、re-cut、re-render 后端 replacement lineage API，不允许靠临时 frame index 追踪资产。
- [x] 在 Timeline operator 片段检查器展示选中 clip 的源资产、输出资产和 replacement history。
- [x] 在 Timeline operator 片段检查器提交已有 `media_asset_id` 作为 re-dub / re-cut / re-render replacement lineage。
- [x] 将选中 video clip 的 re-cut / re-render 接入 provider-backed video generation task queue，并在视频任务成功后回写 replacement lineage。
- [x] 将 operator rework 控制接入 provider-backed video generation API。
- [x] 将 provider rework 成功结果接入 render queue / export 自动编排。
- [x] 将首尾帧、分镜图、分镜视频都视为 clip asset，和 timeline clip 显式关联。
- [ ] 继续拆分并下线 `scripts_legacy.py`，让 timeline/audio/storyboard 主链不再依赖 legacy router。
  - [x] 已把 legacy router 和 audio/timeline pipeline endpoints 的任务标题 helper 收敛到
        `services/script/task_titles.py`，并清掉 `scripts_legacy.py` 中已无引用的
        URL/UUID/datetime helper。
  - [x] 已补齐脚本生成测试 mock 对质量闸悬念判断和 repair JSON 的响应，恢复
        `/api/v1/scripts/generate` 真实质量闸路径测试。
  - [x] 已把 `/scripts/formats` 和 `/scripts/languages` 静态 catalog 路由拆到
        `api/v1/endpoints/scripts_catalog.py`，并在 legacy router 内提前挂载，避免被
        `/{script_id}` 动态路由截获。
  - [x] 已把脚本列表、按剧集列表、详情、更新、软删和导出路由拆到
        `api/v1/endpoints/scripts_lists.py` / `scripts_records.py`，共享查询 helper 拆到
        `scripts_route_utils.py`；legacy router 只保留无尾斜杠兼容桥接。
  - [x] 已把按 `script_id` / `script_business_id` 的重新生成排队入口拆到
        `api/v1/endpoints/scripts_regeneration.py`，legacy router 只负责挂载路由。
  - [x] 已把 `/scripts/prompt/preview` 拆到 `api/v1/endpoints/scripts_prompt.py`，
        读取 episode 的 query 收敛到 `repositories/scripts_route_repository.py`。
  - [x] 已把 `/scripts/generate-async` 排队入口拆到
        `api/v1/endpoints/scripts_generation_queue.py`，保留 production 默认参数语义。
  - [x] 已把 `POST /scripts/` 创建入口拆到 `api/v1/endpoints/scripts_create.py`，
        episode 权限查询收敛到 repository。
  - [x] 已把同步 `/scripts/generate` 入口拆到 `api/v1/endpoints/scripts_generation_sync.py`，
        生成业务逻辑迁到 `services/script/sync_generation.py`。
  - [x] 已把重新生成 Celery processor 迁到
        `services/script/regeneration_task_processor.py`，worker 不再从 legacy router 导入。
  - [x] 已把异步剧本生成 Celery processor 迁到
        `services/script/generation_task_processor.py`，上下文、attempt/scoring 和持久化
        helper 拆成 focused service，worker 不再从 legacy router 导入。
- [x] 拆分 `dialogue_audio_service.py`，至少分离 scene audio 生成、episode 拼接、beats 落库、timeline 占位转换。
  - [x] 已把 episode 拼接/写回迁到 `services/audio/episode_audio_builder.py`，并把 episode timeline beat 构造迁到 `services/audio/episode_timeline_beats.py`；旧服务只保留兼容导入。
  - [x] 已把 scene beat 落库、scene audio metadata 写回和单场时长校验迁到 `services/audio/scene_audio_persistence.py`。
  - [x] 已把 timeline 占位转换从 `dialogue_audio_service.py` 迁到 `services/audio/storyboard_from_timeline.py`，旧服务只保留兼容导入。
  - [x] 已把 duration-control 和 deprecated dialogue-audio endpoint 的 scene 音轨生成入口切到 `services/audio/scene_audio_generator.py`。
  - [x] 已把 duration-control 的逐场景生成循环迁到 `services/duration_controlled_scene_runner.py`，并清掉 touched endpoint 的直接 query。
  - [x] 已把历史 `dialogue_audio_service.py` 收成兼容 facade，旧导入转发到 `services/audio/*`，固定段落规划和文本清理兼容逻辑拆到小 helper。
- [x] 拆分 `ai_service_manager.py`，把 provider routing、fallback、model cache、request logging 收成独立模块。
  - [x] 已把 request/response/prompt 日志和截断逻辑迁到 `services/ai_manager_logging.py`，manager 继续保留兼容 wrapper。
  - [x] 已把模型列表 cache key、读取和写入迁到 `services/ai_manager_model_cache.py`。
  - [x] 已把 provider 限流、优先级/权重选择和请求计数迁到 `services/ai_manager_provider_selection.py`。
  - [x] 已把无可用 provider、异常失败和最终失败响应构造迁到 `services/ai_manager_failure_responses.py`。
  - [x] 已把模型列表聚合、provider 启用过滤、capability 匹配和排序迁到 `services/ai_manager_model_listing.py`。
  - [x] 已把文本生成 provider fallback、默认模型解析、日志和 JSON/schema 参数透传迁到 `services/ai_manager_text_generation.py`。
  - [x] 已把 text/image/img2img/video 默认模型解析迁到 `services/ai_manager_model_resolution.py`。
  - [x] 已把生成图片 URL/base64 归一化与 OSS 上传迁到 `services/ai_manager_image_assets.py`。
  - [x] 已把文生图 provider fallback、style spec 解析、OpenAI style 规范化和成功图片 OSS 转换迁到 `services/ai_manager_image_generation.py`。
  - [x] 已把图生图 provider fallback、参考图预载、成功图片 OSS 转换和降级文生图编排迁到 `services/ai_manager_image_to_image.py`。
  - [x] 已把图生图参考图预读取、压缩和 data URL 构造迁到 `services/ai_manager_image_assets.py`。
  - [x] 已把图生图失败后降级文生图的 provider 推断、fallback prompt 和 metadata 构造迁到 `services/ai_manager_image_fallback.py`。
  - [x] 已把文生图/图生图 style spec 解析、prompt 注入和 metadata 回写迁到 `services/ai_manager_image_style.py`。
  - [x] 已把视频生成 provider fallback、默认模型解析、日志和 terminal failure 编排迁到 `services/ai_manager_video_generation.py`。
  - [x] 已把语音合成 provider fallback、日志和 terminal failure 编排迁到 `services/ai_manager_tts_generation.py`。
  - [x] 已把 provider status payload 和 provider config update 迁到 `services/ai_manager_provider_status.py`。
- [x] 修复 story fallback 测试漂移：统一 `ai_fallback` / `ai_fallback_invalid` 语义与断言。
- [x] 修复 AI 初始化中的 `asyncio.run() cannot be called from a running event loop` 警告，避免 warm-cache 逻辑污染任务链。
- [x] 收敛 step-by-step pipeline 的 deprecation 状态，防止 UI 和后端继续沿旧路径分叉。
- [x] 确认独立 storyboard page 不再存在，并将脚本/故事默认生产入口导向 timeline workspace。

## P2: Production Proof

:link: `docs/exec-plans/active/main-chain-commercial-readiness.md`

当前阻塞：

- 工程链路还没有用真实内容证明可重复生产。
- 已固定 2D/3D 卡通样片验证范围、3 个复用角色和 10 条样片记录表：
  `docs/cartoon-sample-production-proof.md`。
- 还没有产出 10 条最终导出样片，也没有完成成本、失败点和人工修正指标记录。

### 任务（内容→生产→复盘）

- [x] 补齐 timeline operator 的选中 clip 资产审计读视图和已有资产 rework 控制。
- [x] 把 storyboard 调整为支持视图：查看占位、关键帧、镜头上下文，不再承担主编排职责。
- [x] 固定一个窄垂类和 2-3 个角色，限定 2D/3D 卡通验证风格。
- [ ] 产出 10 条 30-60 秒竖屏样片。
- [ ] 每条样片记录模型成本、生成耗时、失败点、人工修正次数和最终导出文件。
- [ ] 将可复用的剧作规则、镜头结构、prompt 和资产选择沉淀回主链。

## 6-Week Exit Criteria

- [ ] 至少 1 个 episode 可以从 audio-driven timeline 重建到最终导出。
- [ ] re-dub / re-render 从 operator UI 到真实生成/导出都不会打断 stable `clip_id`。
- [ ] 不再有主要用户路径依赖 `scripts_legacy.py`。
- [ ] storyboard 页面不再是系统主编排入口。
- [x] 真实 `Episode -> Timeline -> Render -> Export` 浏览器/API 证据通过。
- [ ] 10 条窄垂类样片完成并记录生产指标。
