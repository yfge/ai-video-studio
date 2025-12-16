# 任务看板（AI + 人类超级个体协作版）

> 读取优先：让任何协作者一眼看懂当前优先级、状态和下一步。使用 `[ ]` / `[x]` 标记执行状态，并按“功能 → 后端 → 前端 → 验证”顺序列出。

## 状态概览

- ✅ 稳定/收尾：叙事结构与数据模型对齐（待补迁移验证与权限收口）、对白音轨与声音驱动时间轴（已验证）
- ⏳ 进行中：虚拟 IP 图像生成与模型接入、场景/环境资产与分镜联动
- 🧭 待启动：时间轴/剪辑与渲染导出（首尾帧→视频→拼接）、剧本版本与审校流水线、角色资产与关系图谱、提示词模板组件化、提示词执行评估闭环、提示词权限与发布治理、分镜提示词上下文注入、ReAct Reasoner 实战化、剧本与分镜管理界面重构

## Feature: 叙事结构与数据模型对齐

:information_source: 背景：Story → Episode → Script 当前字段概览 vs 工业级 Treatment / Step Outline / Scene / Shot 要求
:triangular_flag_on_post: 决策点：

- 是否需要单独的 Treatment 表以及与 story 的版本关系
- Scene/Shot 粒度需要保存哪些必填字段（INT/EXT, 时间, 景别, 镜头运动）
- 已有 JSON 字段迁移后如何保证旧数据兼容
  :question: 开放问题：
- 阶段性执行顺序：先建 Treatment → Scene → Shot 还是可以分阶段上线
- 迁移期间老接口是否保持兼容 (可选 query 参数? 版本?)
- 多剧本共享场景/镜头的复用策略

### 进度（功能→后端→前端→验证）

- [x] 功能/需求：梳理 Story → Episode → Script 现状与工业级 Treatment / Step Outline / Scene / Shot 差异，已产出对比文档 `docs/story-structure-gap-analysis.md` 与 Discovery 议程 `docs/story-structure-discovery-session.md`
- [x] 后端：完成 `story_treatments`、`story_step_outlines`、`scenes`、`scene_beats`、`shots` ER 与字段设计及迁移脚本（含回填路径 `alembic upgrade c4a1cbf0d7c2`）
- [x] 前端：剧本详情页已调整为新场景/镜头层级的展示与编辑
- [x] 验证：补齐单元/集成测试与迁移回归用例

### 下一步

- 评审/签收 `docs/story-structure-gap-analysis.md` 中的 ER/字段草案与枚举列表，冻结迁移脚本字段
- 在真实脚本样本上跑 `alembic upgrade c4a1cbf0d7c2`（含回填），并用 `prototype_story_structure_migration.py --mode live --insert-probe --report-path <file>` 生成迁移报告，补充回滚验证文档
- 补足权限/校验（角色鉴权、beat 顺序重排、shot 号冲突处理），向前端开放聚合 CRUD
- 增补端到端/权限链路测试（含分镜帧与 beat/shot 关联），持续跟进迁移回滚演练记录

## Feature: 虚拟 IP 图像生成与模型接入

:information_source: 背景：虚拟 IP 资产需要可靠的文生图 / 图生图流程，并对接多家模型服务（OpenAI、可灵、即梦、火山 Seedream 等）。

### 进度（功能→后端→前端→验证）

- [x] 功能/需求：接入 Seedream 4.5 文生图（`doubao-seedream-4-5-251128`），通过 `/api/v1/virtual-ips/{id}/images/generate` 完成端到端验证（含 Docker）；官方示例为 `POST /api/v3/images/generations` 且 `size: "2K"`，像素需 ≥ 3,686,400
- [ ] 功能/需求：图生图能力完善，梳理 Seedream/其他提供商的单图生图、多图生图参数，对齐 `/api/v1/ai/generate/image-to-image`，覆盖背面照/全身照等变体
- [x] 后端：虚拟 IP 文案注入提示词，聚合 `description` / `background_story` / `biography` / `style_prompt`，确保生成提示词携带完整角色设定
- [ ] 后端：分辨率与规格建模，按模型白名单收敛 `size` / `width` / `height` / `aspect_ratio`，并在统一模型注册表与日志中落盘；当前虚拟 IP 图生图变体接口已透传 `size` 到统一的 `image_to_image` 调用
- [x] 前端：虚拟 IP 图像页支持基于已有图像的变体生成（`/api/v1/virtual-ips/{id}/images/{image_id}/variants`），含模型选择与生成数量，变体会保存为新的虚拟 IP 图像资产
- [x] 前端：虚拟 IP 更新请求类型补齐 `voice_config`，修复 `next build` 类型检查失败
- [ ] 前端：在文生图/图生图表单中按模型动态限制分辨率选项，完善错误与限制提示（目前图生图弹窗复用文生图已选的 `size`）
- [ ] 验证：为不同模型+分辨率补齐端到端用例（含 DALL·E 3 官方三种长宽比、DALL·E 2 三种尺寸、Seedream 2K），在 README / TESTING_GUIDE 记录 Ark 凭证、调试与兼容矩阵

### 下一步

- 按提供商梳理多图生图参数与约束（Seedream 4.5 / DALL·E / SDXL / 可灵 / 即梦 / DeepSeek），补齐 UI 文案与错误提示
- 固化分辨率白名单：DALL·E 3 仅 `1024x1024` / `1024x1792` / `1792x1024`；DALL·E 2 仅 `256/512/1024` 方图；Seedream 4.5 归一化 `size: 2K` 并校验像素下限；SDXL/其他按官方推荐收敛
- 后端在 `generate_image` / `image_to_image` 中按模型映射规范化参数并记录实际下发规格，前端表单按模型展示受限尺寸
- 增补模型×分辨率测试与 Ark 调试说明，校验文档覆盖背面照/全身照等变体

## Feature: 任务队列与 Agent 执行落库（高优）

:information_source: 背景：已有 Task 表与 Story/Episode/Script 异步生成入口（`/generate-async`）、前端任务管理页 `/tasks`，但任务执行目前依赖 `BackgroundTasks`、散落在各 endpoint 中，LangGraph Agents（故事/剧集/剧本）也未统一落库运行轨迹，难以在任务层面排查与审计。

### 进度（功能→后端→前端→验证）

- [ ] 功能/需求：统一 Story/Episode/Script/图像等任务到 Task 队列，使用 Celery Worker 处理，Agent 每次执行结果在 Task 与目标实体（Story/Episode/Script）上都可追踪
- [ ] 后端：补全 `TaskType` 枚举（如 `story_generation` / `episode_generation` / `script_generation` / `image_generation`），提炼 `task_runner` / `task_worker`，以 Celery 任务消费 Task 表并调用 `AIService` / LangGraph Agents，更新 `Task.status` / `result_file_path` / `error_message`
- [ ] 后端：在 Task 的 `parameters.agent_run` 中落库 agent 输入/输出（prompt、normalized 结构、provider/model、usage、reasoning），保证每次 LangGraph 执行有完整轨迹
- [x] 后端：在 Story/Episode/Script 的 `extra_metadata.agent_run` 中写入 LangGraph/AI 管理器的运行信息，覆盖同步与 `/generate-async` 路径
- [ ] 后端：为虚拟 IP 图像、环境图像、分镜图像等长耗时图像生成操作提供标准 Task 创建 + Celery 异步处理路径（与现有 `/api/v1/tasks` 结构对齐）
- [x] 后端：新增 `app/core/celery_app.py` 与 `app/services/task_worker.py`，并在 `docker/docker-compose.prod.yml` 中增加 `ai-video-celery-worker` 服务（与 backend 共用镜像与配置）
- [ ] 前端：在任务管理页 `/tasks` 中支持按 `task_type` 过滤，并在任务详情中展示 `parameters.agent_run` 的关键信息（provider/model/usage/reasoning）
- [ ] 验证：为 Story/Episode/Script/图像任务增加集成测试（任务创建 → Celery handler 执行 → Task 状态与目标实体写入校验），并在 `TESTING_GUIDE.md` 中记录 Celery 本地运行与调试流程

### 下一步

- 先在后端实现 Celery 应用与通用 `process_task` 处理逻辑，并将 `/stories/episodes/scripts/*/generate-async` 与虚拟 IP 图像生成统一改造为创建 Task → `process_task.delay(task_id)` 调用链
- 为 `StoryLangGraphAgent` / `EpisodeLangGraphAgent` / `ScriptLangGraphAgent` 增加标准化返回结构（明确 `normalized`、`provider_used`、`model_used`、`usage`、`reasoning` 字段），在 `AIService` 层集中写入实体与 Task 的 `agent_run`
- 更新生产 `docker-compose.prod.yml`，增加 `celery_worker` service，并在部署文档中标记任务队列为核心组件；通过 `/tasks` + 诊断 API 验证任务与 Agent 执行轨迹可见

## Feature: 场景/环境资产与分镜联动

:information_source: 背景：需要把环境/场景资产（办公室/学校/商场等）与角色 IP 绑定到分镜帧，支撑“分镜→图像→视频”闭环。

### 进度（功能→后端→前端→验证）

- [x] 功能/需求：定义环境/场景资产与分镜/角色绑定（environments 表、角色锚点），现支持分镜页绑定环境与镜头绑定角色
- [x] 后端：已落地 environments 表与 `scenes.environment_id` / `shots.character_ids` 迁移；环境文生图/图生图已上线用于手动生成参考图
- [ ] 后端：生成链路未闭环——需要在分镜帧结构中携带 `environment_id` 并在生成调用中同时带人物/环境参考图，统一映射到多提供商 API
- [x] 前端：提供环境资产管理页（上传/生成/变体/删除参考图），在 `/stories/[id]` 分镜/剧集界面支持环境选择与标签筛选
- [ ] 验证：待补端到端用例，验证选择环境+角色后分镜帧能稳定生成对应图像；在 `TESTING_GUIDE.md` 记录并为环境表/关联补迁移回归用例

### 下一步

- 在分镜帧结构中显式携带 `environment_id` 并作为条件图选择逻辑输入生成
- 将虚拟 IP 图像（头像/全身/表情）与环境参考图共同注入分镜生成调用，保证人物与场景一致性
- 设计多图条件调用适配层（参考 Seedream/SDXL 等），集中映射“人物/环境参考图 + 文本提示词”到各家 API
- 在真实浏览器路径完成端到端生成验证，补测试与文档

## Feature: 分镜 LangGraph 管线统一（规划+生成）

:information_source: 背景：当前分镜生成同时存在多条路径：直接调用 `generate_storyboard`、基于 `generate_storyboard_plan` 的规划+逐场景生成，以及 `StoryboardReActReasoner` 的 LangGraph ReAct 管线，前端还有“规划/生成”两个操作。希望统一为一条以 LangGraph 为核心的分镜管线，默认走“先规划再生成”，对帧数量不足/JSON 结构不合规能自动 ReAct 修复，这是系统最核心的功能之一。

### 进度（功能→后端→前端→验证）

- [ ] 功能/需求：统一分镜生成模型为“带规划的 LangGraph 管线”，默认每个选定场景至少生成 `frames_per_scene` 帧，帧结构必须满足 `StoryboardModel` JSON Schema
- [ ] 后端：实现 `StoryboardLangGraphAgent`（或扩展现有 `StoryboardReActReasoner`），graph 中包括：场景选择节点 → 帧规划节点（`StoryboardPlanModel`）→ 帧细化节点（`StoryboardModel`）→ 校验/数量检查节点 → 修复节点（在帧数不足或结构不合法时 ReAct 重试）
- [ ] 后端：收敛 `AIService.generate_storyboard*` 接口与 `scripts.py` 中分镜生成逻辑，统一通过 LangGraph agent 入口，保留本地 fallback 作为最后兜底；确保同步/异步（`/storyboard/generate`、`/storyboard/generate-async`）走同一套管线
- [ ] 后端：在分镜生成 Task 与 `script.extra_metadata.storyboard` 中落库完整 agent 运行轨迹（plan、frames、provider/model、usage、reasoning_trace），支持后续审计与问题回溯
- [ ] 前端：分镜工作台按钮统一切换到 `*-async` 路径，默认 `use_plan=true`，不再显式暴露“规划”动作，仅在高级视图中展示 `storyboard_plan` 与 ReAct 轨迹
- [ ] 验证：补充端到端测试（长剧集、多场景、多次生成叠加），重点覆盖：帧数量检查与自动补齐、JSON 结构校验与修复、与环境/角色资产联动后的分镜稳定性

### 下一步

- 设计 `StoryboardLangGraphAgent` 的 state 结构（包含 script 摘要、选定场景列表、目标帧数、当前 plan 与 frames、reasoning_trace）
- 在 `AIService` 中接入该 agent，作为 `generate_storyboard` 的首选路径，并让 `/scripts/{id}/storyboard/generate(-async)` 统一走这一入口
- 调整 `StoryboardReActReasoner` / `generate_storyboard_plan` / `generate_storyboard_from_plan_for_scene` 的职责，将老的规划/逐场景逻辑收敛到 agent 内部或作为其子节点
- 在浏览器中跑至少一条“真实故事→剧集→剧本→分镜→分镜图像”完整链路，并在 `agent_chats` 中记录验证路径和观察到的问题

## Feature: 对白音轨与声音驱动时间轴（场景→音轨→beats→分镜帧）

:information_source: 背景：剧集生成后，希望在 Episode 内基于剧本为每个场景生成一条“对白混音音轨”，在生成与拼接时记录时间 beats，形成可复用的声音驱动时间轴，并进一步用于生成分镜帧/镜头占位，最终支撑剪辑与导出主线。

:triangular_flag_on_post: 决策点：

- 音轨粒度：MVP 固定为“一个场景一条对白音轨”（混音）；是否需要为后续剪辑保留角色分轨（stems）
- 时长来源：声音优先（TTS 定时长），时间轴以音轨真实时长为准
- Beats 规格：最小字段（scene_id、speaker、start_ms、end_ms、type、text）以及与 `scene_beats` / Timeline Spec 的映射关系；`scene_beats` 存储在 scene 级
- 音色回退：角色未绑定音色时，由 agent 从现有音色库自动挑选并绑定；无需人工确认（需审计可追溯）
- 留白补足：对白缺失/舞台指示/情绪留白的补齐策略（静音/环境音/旁白/自动补台词）及可配置边界
- 衍生角色：指 IP 库中不存在、但在剧本中出现的角色（如“路人”）；由 agent 判断作用域（scene / episode / story）并生成/复用音色绑定策略

### 进度（功能→后端→前端→验证）

- [x] 功能/需求：冻结“场景一条对白音轨”输出规范（输入：剧本/场景/角色；输出：audio + beats），并明确留白补足规则与可配置项（见 `docs/dialogue-audio-timeline-spec.md`）
- [x] 后端：补齐角色音色绑定的查询/落库能力；当角色无绑定时，基于现有音色库运行 agent 自动挑选并绑定（无需人工确认，含审计字段）
- [x] 后端：为衍生角色提供同等的音色绑定与回退策略：agent 判断作用域（scene/episode/story）→ 创建/复用“派生角色”记录 → 绑定音色；保证幂等
- [x] 后端：实现“按场景生成对白混音音轨”：多角色 TTS → 混音为 1 条 scene 音频 → 输出 segment 级 beats（含留白补足的静音/环境段）
- [x] 后端：对白生成传入情绪参数（script.dialogues.emotion/action → provider emotion），并落库到 `scene_beats.extra_metadata.tts_emotion`
- [x] 后端：对白文本中的（动作）不进入朗读；剥离为 action 并用于推导 `tts_emotion`（避免“叹了一口气…说…”被读出来）
- [x] 后端：实现“按 Episode 拼接场景音轨”：拼接生成 episode 级音频，并合并/偏移 beats 形成 episode 时间轴（episode 级落 Timeline Spec；scene 级落 `scene_beats`）
- [x] 后端：基于 beats/时间轴生成分镜帧/镜头占位（或触发分镜 agent），将关键点映射到 frames/shots，支持后续视频/剪辑链路复用
- [x] 后端/运行环境：backend/celery 镜像安装 `ffmpeg`（音频拼接依赖），避免运行时 `No such file or directory: 'ffmpeg'`
- [x] 前端：在 Episode 详情/剧本页新增“生成对白音轨 / 生成时间轴 / 生成分镜帧”入口，展示进度、失败原因、版本与重试/复用
- [x] 前端：修复 Episode 详情页任务轮询参数类型（`taskAPI.getTask(String(taskId))`），确保 `next build` 类型检查通过
- [x] 前端：在 Episode 详情页展示“场景对白音轨（scene）”列表与播放/下载入口（`scene.metadata.dialogue_audio.oss_url`）
- [x] 前端：Episode 详情页默认展开场景音轨列表；存在 episode 级音频时直接提供播放器（避免“生成成功但不知道在哪里听”）
- [x] 前端：分镜管理页接入 episode `audio_timeline`（携带 scriptId 跳转、展示 beats/version 与 episode 音频播放器；帧级展示时间窗 start/end_ms，提供“从时间轴同步分镜占位”入口）
- [x] 验证：浏览器端到端用例（账号 `geyunfei`；Selenium headless Chrome，MCP transport closed）：episodes/10 → 生成对白音轨 → 生成时间轴 → 覆盖生成分镜帧占位，并将路径与结果记录到 `agent_chats`

### 下一步

- [ ] 定义 beats→Timeline Spec 的映射与落库方案（scene 级 `scene_beats` + episode 级偏移合并）
- [ ] 输出“音色回退 agent”策略草案（候选集、评分/约束、自动绑定落库与审计字段）
- [ ] 明确衍生角色 scope agent 的输入/输出与幂等规则（scene/episode/story），并与角色/音色绑定数据模型对齐
- [ ] 先用 1 条样例 Episode 跑通数据闭环（scene→audio→beats→timeline→frames），再扩展到批量生成与重试/续跑

## Feature: 时间轴/剪辑与渲染导出（首尾帧→视频→拼接）

:information_source: 背景：当前 Story/Episode/Script/Scene/Shot/Storyboard 更多是“内容与资产分层”，但要实现“首尾帧 → 视频片段 → 拼接剪辑导出”，需要一条可渲染主线（Timeline/Sequence/EDL）来承载片段顺序、时长、多轨音视频、版本与导出作业。单集时长 ≤5分钟适合先做“后端渲染 + Web 编排/预览”的 MVP。

:triangular_flag_on_post: 决策点：

- Timeline 的事实来源：从 `shots`（规范化）生成 vs 从 `storyboard.frames`（JSON）生成
- 时长来源：声音优先（TTS 定时长），时间轴以音轨真实时长为准
- 资产落库：是否引入统一 `media_assets` 表（image/video/audio），以及与现有 `images`/`virtual_ip_images` 的关系
- 导出策略：proxy（HLS/低清）与 final（mp4）是否都需要；转场/字幕 MVP 边界

### 进度（功能→后端→前端→验证）

- [x] 功能/需求：明确需要新增“时间轴管理”承载剪辑与导出主线（详见设计文档 `docs/timeline-rendering-pipeline.md`）
- [ ] 后端：新增 `timelines` / `render_jobs` / `media_assets`（或等价结构）数据模型与迁移；定义 Timeline Spec（EDL JSON）并落库版本号（可重渲/可回放）
- [ ] 后端：实现 Timeline CRUD 与导出 API（创建/更新/版本回滚/触发导出/查询导出结果），统一鉴权到 episode/story 所属用户
- [ ] 后端：实现渲染任务链路（Task/Celery）：关键帧生成（首尾帧）→ 视频片段生成（image-to-video）→ 拼接剪辑（FFmpeg）→ 上传 OSS/CDN → 回填 RenderJob/Timeline
- [ ] 前端：新增时间轴页面（列表 + 编辑器 MVP）：clip 列表编排（排序、时长、绑定 shot/storyboard）、单 clip 预览、导出按钮、proxy 播放器
- [ ] 验证：补 pytest 覆盖（Timeline spec 校验/导出幂等/权限），并在 Chrome 走通端到端用例（创建分镜→生成首尾帧→生成视频片段→导出 proxy/final）

### 下一步（拆分工作项）

- [ ] 冻结 Timeline MVP 需求与 UI 草图：clip 列表编排、proxy 预览、final 导出（≤5分钟）
- [ ] 定义 Timeline Spec（EDL）Pydantic schema（tracks/clips/assets），并写入 `docs/timeline-rendering-pipeline.md` 的最终字段表
- [ ] 后端：建表与迁移（timelines/render_jobs/media_assets），补 Alembic 与回填策略（如从现有 storyboard JSON 生成初始 timeline）
- [ ] 后端：实现 `timeline_service`（CRUD + 版本）与 `render_service`（导出/复用/幂等）
- [ ] 后端：实现 3 类任务：`keyframe_generate`、`clip_video_generate`、`timeline_render_export`（含失败重试与可续跑）
- [ ] 后端：FFmpeg 渲染方案落地（concat + audio mix + subtitle 可选），并为 proxy/final 预设出厂配置
- [ ] 前端：实现 Episode → Timeline 入口与编辑页；复用现有大图预览组件做关键帧查看
- [ ] 前端：实现导出进度展示（poll `render_jobs` / `tasks`），并提供下载/播放入口（proxy HLS、final mp4）
- [ ] 验证：写一条标准 E2E 用例脚本（账号 `geyunfei`），并把实际路径记录到 `agent_chats`

## Feature: 剧本版本与审校流水线

:information_source: 背景：工业剧本版本色彩流程 (Draft/Blue/Pink...) 与现有 `scripts` 单版本结构
:triangular_flag_on_post: 决策点：

- 版本颜色/状态集与审批角色的对应关系
- 版本切换时需要记录的提示词快照和差异数据
- 审批与回滚的权限边界（谁能回滚、需要审计吗）
  :question: 开放问题：
- 版本比较粒度：按场景/镜头/台词是否需要细化
- 人工修改与 AI 生成如何合并成单一版本历史
- 是否需要与 Git 等外部版本工具同步

### 进度（功能→后端→前端→验证）

- [ ] 功能/需求：定义 Draft / Blue / Pink 等版本流程与审批角色
- [ ] 后端：实现 `script_versions`、`scene_revisions`、`review_notes` 表及关联
- [ ] 前端：构建版本时间线、差异对比、审批与回滚视图
- [ ] 验证：新增端到端测试覆盖版本切换与审批流程，撰写使用指南

### 下一步

- 明确版本颜色/审批角色矩阵，定义版本切换所需的快照/差异数据与审计要求

## Feature: 角色资产与关系图谱

:information_source: 背景：角色档案、造型、情绪弧线在提示词与生成中的角色
:triangular_flag_on_post: 决策点：

- 角色档案结构如何拆分 (基础信息/造型/性格/弧线)
- 关系图谱是否需要时间轴或事件颗粒度
- 造型锚点同虚拟 IP 资产如何联动
  :question: 开放问题：
- 多语言/多文化角色设定是否需要特殊处理
- 角色共享与复用：同一角色在不同剧本如何引用
- 是否要引入角色一致性校验的自动化阈值

### 进度（功能→后端→前端→验证）

- [ ] 功能/需求：整理角色档案的身份、造型、情感、弧线节点
- [ ] 后端：拆分角色档案表，新增 `character_profiles`、`character_relations`、`relation_history`
- [ ] 前端：实现角色档案页与关系图谱可视化，支持编辑与版本记录
- [ ] 验证：补充分镜/剧本生成前的角色一致性校验测试，更新文档

### 下一步

- 先产出角色档案分层方案与关系图谱时间轴设计，明确与虚拟 IP 造型锚点的联动方式

## Feature: 提示词模板组件化

:information_source: 背景：shared conversation 中的工业级提示词段落结构
:triangular_flag_on_post: 决策点：

- 模板段落最小粒度 (项目/场景/镜头/风格/声音/锚点)
- 变量命名规范与占位格式
- 模板版本管理策略
  :question: 开放问题：
- 模板是否按项目类型/题材分类
- 人工自定义片段如何与系统模板共存
- 模板覆盖率 KPI（多少生成调用要使用模板）

### 进度（功能→后端→前端→验证）

- [ ] 功能/需求：提炼工业级提示词模板段落（项目、场景、镜头、视觉、声音、锚点）
- [ ] 后端：设计 `prompt_templates`、`prompt_sections`、`prompt_variables` 表结构与模板渲染器（按 Story / Episode / Scene / Shot 注入上下文，可覆写变量）
- [ ] 前端：提供模板选择、片段库、变量编辑与预览功能
- [ ] 验证：建立模板单测 + 快照测试，撰写模板编写指南

### 下一步

- 先确定模板粒度与占位格式，再落地数据模型与渲染器接口

## Feature: 提示词执行评估闭环

:information_source: 背景：提示词质量指标与评估流程缺失
:triangular_flag_on_post: 决策点：

- 评分指标权重与公式
- 人工与自动评分如何结合
- A/B 测试触发条件和样本量
  :question: 开放问题：
- 需要哪些外部信号 (用户反馈/播放数据) 纳入评分
- 生成失败或部分成功的定义标准
- 评估周期与指标更新频率

### 进度（功能→后端→前端→验证）

- [ ] 功能/需求：确定提示词质量指标（准确度、一致性、镜头合规、锚点保持）
- [ ] 后端：新增 `prompt_runs`、`generation_feedback`、`comparison_jobs`
- [ ] 前端/分析：实现 A/B 对比、评分聚合、健康度展示
- [ ] 验证：接入真实生成案例，补充自动/人工评分流程文档

### 下一步

- 定义评分指标与公式，确认需要的外部信号，规划 A/B 触发条件

## Feature: 提示词权限与发布治理

:information_source: 背景：模板草稿/审核/发布机制缺失
:triangular_flag_on_post: 决策点：

- 角色权限矩阵 (作者/审阅/发布者)
- 灰度发布流程（按团队/项目/百分比）
- 变更日志与通知机制
  :question: 开放问题：
- 是否需要外部审批集成 (例如企业流程)
- 模板撤回与紧急下线策略
- 权限模型与现有用户体系如何合并

### 进度（功能→后端→前端→验证）

- [ ] 功能/需求：划定模板草稿/审核/发布角色与灰度策略
- [ ] 后端：实现模板状态机、审批日志、权限控制
- [ ] 前端：提供审批队列、版本对比、灰度发布开关
- [ ] 验证：新增权限/灰度相关测试与操作手册

### 下一步

- 输出权限矩阵与灰度策略草案，锁定状态流转与审计字段后再开工

## Feature: 分镜提示词上下文注入

:information_source: 背景：当前分镜提示词缺乏场景/角色上下文
:triangular_flag_on_post: 决策点：

- 每个镜头需要注入的上下文字段列表
- 不同生成模型是否需要不同上下文格式
- 上下文获取方式 (实时查询 vs 缓存)
  :question: 开放问题：
- 大场景分镜是否需要拆分多级摘要
- 上下文注入对性能的影响需要如何评估
- 与 ReAct Reasoner 的信息共享方式

### 进度（功能→后端→前端→验证）

- [ ] 功能/需求：列出分镜生成所需上下文（场景编号、地点、角色、对白、舞台指示）
- [ ] 后端：调整 `ai_service.generate_storyboard`，按场景注入真实摘要与角色信息
- [ ] 前端：更新分镜结果展示，突出差异化帧并显示引用上下文
- [ ] 验证：编写快照测试与人工对比用例，确保 frames 与场景一一对应

### 下一步

- 先冻结上下文字段清单与获取方式，再按模型适配注入格式与缓存策略

## Feature: ReAct Reasoner 实战化

:information_source: 背景：现有 reasoner 仅提示词约束，缺少持久化推理
:triangular_flag_on_post: 决策点：

- 推理节点要求的输入/输出格式
- 自动修复规则与优先级
- 推理日志存储位置与展示方式
  :question: 开放问题：
- 推理失败的恢复策略
- 多人协作时如何合并推理结果
- 是否需要可视化调试工具的导出功能

### 进度（功能→后端→前端→验证）

- [ ] 功能/需求：定义 plan → critique → finalize 流程输出的必备字段
- [ ] 后端：扩展 `StoryboardReActReasoner`，持久化推理轨迹与自动修复逻辑
- [ ] 前端：提供推理步骤、修复记录的可视化面板
- [ ] 验证：补充集成测试覆盖计划/细化/回退路径

### 下一步

- 先敲定推理节点输入/输出结构与存储格式，再实现持久化与可视化

## Feature: 剧本与分镜管理界面重构

:information_source: 背景：现有 UI 不能满足多版本、多视图需求
:triangular_flag_on_post: 决策点：

- 信息架构模块顺序与布局
- 前端状态管理方案 (Zustand, Redux, Query)
- 交互模式（实时协作、批量操作）
  :question: 开放问题：
- 与任务队列/后台服务的同步机制
- 移动端/平板适配需求
- 用户权限差异对 UI 的影响

### 进度（功能→后端→前端→验证）

- [ ] 功能/需求：设计信息架构（顶部摘要、剧本预览、分镜版本、任务状态）
- [ ] 前端：实现场景树、镜头列表、版本历史、任务队列组件
- [ ] 后端：提供所需 meta / plan / 版本 API，确保前后端契合
- [ ] 验证：编写关键交互单测 + E2E，更新用户操作说明

### 下一步

- 先出信息架构草图和状态管理方案，再分解组件与接口交付节奏

## 专项：分镜管理任务拆解（/episodes/[id]/storyboard）

> 场景： http://localhost:8089/episodes/8/storyboard，目标是让分镜生成/编辑对齐规范化场景/镜头，并能携带角色与环境参考图完成闭环。

### 里程碑 0：现状梳理与阻断收集

- [ ] 功能/需求：梳理当前分镜生成入口、规范化场景/镜头数据与环境/角色资产的绑定现状，列出阻断清单。
- [ ] 后端：盘点 `/scripts/{id}/storyboard` / `generate_storyboard*` 返回体与 story_structure 模型的缺口（环境/角色/镜头 id），确认是否存在版本或 JSON 兼容分支。
- [ ] 前端：在 storyboard 页面确认哪些 UI 依赖未打通（镜头角色选择、环境选择、参考图载入、生成按钮状态），记录具体交互缺口。
- [ ] 验证：用 episode 8 复现“生成分镜→生成图像/视频→保存”路径，截图/日志记录当前失败点。

### 里程碑 1：数据与上下文对齐

- [ ] 功能/需求：确定生成/更新分镜的上下文字段清单（场景摘要、beat/shot 描述、角色、环境、提示词模板版本），并对外暴露；**剧本生成时即抽象出场景列表写入 `story_structure.scenes`，必要时生成 beats/shots 占位，保证新剧本可直接用于分镜。**
- [ ] 后端：`ai_service.generate_storyboard` / plan / update 路径统一携带 normalized scene/shot id、environment_id、character_ids，并将 `scene_scope`、`shot_scope`、context_text 反写 meta；剧本生成落地时同步 scenes→story_structure.scenes（含 beats/shots 占位）；确保 partial regenerate merge 策略。
- [ ] 前端：storyboard 页面请求参数与展示层对齐新字段（场景/镜头 id、上下文提示词预览、scope 提示），阻断未选择规范化场景/镜头的生成操作；确认加载的场景列表来自 story_structure 而非文本解析。
- [ ] 验证：补充/更新 storyboard prompt 单测覆盖上下文注入；本地调用 `/scripts/{id}/storyboard/preview` 确认字段生效；生成新剧本后直接打开分镜页，确认场景列表、beats/shots 占位已自动可用。

### 里程碑 2：参考图锚点与生成闭环

- [ ] 功能/需求：规定“角色图片 + 环境图片 + 分镜提示词”作为生成锚点，首尾帧/单帧/整场景皆可调用。
- [ ] 后端：`generate_storyboard_images` 支持 environment + character 参考图的自动聚合，写回帧级 metadata（reference_images、environment_id、character_ids、asset_id）；视频生成入口复用同一锚点。
- [ ] 前端：在分镜列表提供参考图选择/默认选中逻辑、首尾帧快速生成按钮，将选中的 env/role 透传给生成接口并在 UI 标记锚点；保存/刷新后保持选择状态。
- [ ] 验证：在 http://localhost:8089/episodes/8/storyboard 走一遍“选环境+镜头角色→生成首尾帧图像→查看回填 meta→触发视频生成”流程并记录结果。

### 里程碑 3：版本化与可见性

- [ ] 功能/需求：明确分镜版本号、来源（生成/手工）、模型/模板标签的展示与回滚需求。
- [ ] 后端：在 storyboard meta 中记录 version、updated_at、generation_method/source/model、scene_scope、template_version；提供回滚或只读快照接口（若可行）。
- [ ] 前端：在顶部信息区突出版本/来源/模板信息，支持选择特定版本查看，保存/生成后显示版本号递增。
- [ ] 验证：手工/自动生成后检查 meta 落盘与 UI 展示一致，补充 README/TESTING_GUIDE 对应字段说明。
