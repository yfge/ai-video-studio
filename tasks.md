# 任务看板（AI + 人类超级个体协作版）

> 读取优先：让任何协作者一眼看懂当前优先级、状态和下一步。使用 `[ ]` / `[x]` 标记执行状态，并按“功能 → 后端 → 前端 → 验证”顺序列出。

## 状态概览

- ✅ 稳定/收尾：叙事结构与数据模型对齐（迁移验证/权限收口待补）、对白音轨与声音驱动时间轴（主链路已验证，收尾待补）
- ⏳ 进行中：虚拟 IP 图像生成与模型接入、场景/环境资产与分镜联动、分镜管理规范化对齐、超大文件拆分（backend `scripts_legacy.py` / frontend storyboard page / `src/utils/api.ts`）
- 🔥 **高优新增**：Duration Orchestrator Agent（端到端时长闭环验证）、短剧微类型与投流驱动创作闭环（hook/爽点/素材）
- 🧭 待启动：时间轴/剪辑与渲染导出（首尾帧→视频→拼接）、剧本版本与审校流水线、角色资产与关系图谱、提示词模板组件化、提示词执行评估闭环、提示词权限与发布治理、分镜提示词上下文注入、ReAct Reasoner 实战化、剧本与分镜管理界面重构

## P0: 用户本轮需求（画幅/资产/生成质量）🔥

### 1) 画幅规格（Story/Episode，默认 9:16，可临时覆盖）

- [x] 后端：Episode 增加可选 `aspect_ratio`（`9:16|16:9`），默认继承 Story.`default_aspect_ratio`
- [x] 后端：统一画幅解析优先级 `request override > episode > story > "9:16"`；贯通分镜图/分镜视频生成参数
- [x] 前端：Story/Episode 设置提供画幅选择（仅 9:16/16:9）；分镜视频生成弹窗允许“临时覆盖（仅本次任务，不落库）”
- [x] 验证：Chrome E2E 各生成 1 条 9:16 与 16:9 分镜视频；用 `ffprobe` 校验分辨率/比例与元数据一致

### 2) 生成资产持久化统一抽象（image/video/audio → OSS/CDN）

- [x] 后端：新增 `app/services/media/media_persistence.py`（upload bytes/URL/base64 → OSS/CDN）；已接入分镜视频上传链路
- [x] 后端：SpeechService/语音 OSS 上传改用统一 media persistence（metadata 结构对齐）
- [x] 后端：抽象统一的 media persistence（upload bytes/URL/base64 → OSS/CDN，返回 `url/key/metadata`），图片/视频/音频复用同一入口
- [x] 后端：统一落库的 generation metadata（provider/model/task_id/width/height/duration/mime/sha256 等），减少 provider 分叉与重复字段
- [x] 后端：修复 `video_generation_tasks.provider_task_id` 长度不足导致的 MySQL 1406（Vertex operation name 过长）；补 Alembic 迁移链路与回归测试
- [x] 文档：补充 `docs/` 说明生成资产命名规则、字段含义与 OSS/CDN 路径约定
- [x] 验证：Docker 内跑通视频生成→轮询→上传→回填 URL 的完整链路

### 3) 生成质量闭环（上下文/校验/人物集中管理）

- [x] 后端：人物集中管理：Story 级角色注册表作为 episode/script/timeline/storyboard 单一来源；禁止生成链路引入“未知角色”（可 repair 或阻断）
- [x] 后端：修复脚本对白中“旁白 prose 混入多角色台词”导致 TTS 旁白化：在对白音轨生成阶段自动拆分引号台词并映射到已注册角色（跳过 UI/屏幕文本）
- [x] 后端：audio_timeline → storyboard：分离“对白/屏幕文字”与视觉提示词（ai_prompt），对 dialogue/action/pause 使用不同模板，强制 no subtitles/no readable text，避免模型生成字幕/读屏
- [x] 后端：audio_timeline → storyboard：注入 Story 角色卡简述 + 自动选取 reference_images（<=3：人物锚点+环境）并贯通 Veo 视频提交，提升角色一致性
- [x] 后端：audio_timeline → storyboard：基于 scene 对白集合注入 characters 列表（提升多角色出镜一致性/避免漏人）
- [x] 验证：抽检至少 2 个 dialogue beat：人物嘴型/说话动作明显，且无字幕/无可读文字（见 agent_chats/2026/01/30/2026-01-30T14-19-44Z-validate-dialogue-beats.md）
- [ ] 后端：补齐 readiness 检查（复用下方 `Feature: 故事/剧集生成质量闭环` Phase 3），并输出可读 blocking issues + 一键修复建议
- [ ] 后端：生成后逻辑校验：episode→script→timeline→storyboard 一致性检查（场景数/角色引用/时长/画幅）；报告写入 `Task.parameters.agent_run`
- [x] 验证：全流程 E2E（deepseek 文生文；google banana pro 生图；google veo3 生视频）生成 1 个 Story、1 个 Episode、1 条时间轴/音轨/视频，并抽检图/视频与剧本逻辑一致（Chrome MCP Transport closed，改用 API/curl + 下载抽检，并在 agent_chats 记录）

### 4) 分镜时长 vs 视频模型能力（Veo 4/6/8 等）对齐 🔥

> 目标：Storyboard 仍以音频时间轴为真（start_ms/end_ms），但视频生成必须遵守各模型允许的离散时长；最终产物 MP4 时长要严格回到分镜目标时长，避免“轴与视频不匹配”。

#### Phase 1: 能力抽象 + 生成向上取整 + 后期裁切（P0）

- [ ] 后端：新增 video capabilities 解析层（provider/model/resolution → allowed durations/min/max），并在任务日志中可审计实际命中的能力
- [x] 后端：视频任务提交：按能力把 `target_duration_seconds` 向上取整到 `provider_duration_seconds`（<=max），并把两者写入 `parameters/generation_metadata`
- [x] 后端：视频任务完成后：若 `provider_duration_seconds > target_duration_seconds`，用 ffmpeg trim/copy 裁切到 target 并上传；result 同时保留 original 与 trimmed URL
- [x] 测试：单测覆盖 duration ceil 规则（5→6、7→8、8→8、>max→max+标记需拆分）
- [x] 验证：Docker E2E 选取 1 个 target=5s 的分镜帧生成视频（Veo），抽检最终 MP4 duration≈5s（并保留原始 6s 可追溯）

#### Phase 2: 分镜生成分段/合并（P1）

- [ ] 后端：从 audio_timeline 生成 storyboard 时，按 `max_allowed_duration_seconds` 在 beat 边界拆分长镜头；短于 `min_allowed` 的 pause/action 允许合并相邻 beat
- [ ] 后端：为拆分/合并后的 frame 写入 stable linkage（如 `parent_frame_id` / `beat_range` / `split_index`）便于回溯与 UI 展示
- [ ] 验证：构造 1 个 >8s 的长段（如 12s），确认被拆为 2 段且最终拼接后总时长与原轴一致

## Chore: 工具链升级

- [x] 前端：升级 Node 到 22.20.0（本地/生产镜像一致）
- [x] 前端：升级 Next.js 到 16.1.3（同步调整 eslint/lint 脚本）

## Refactor: 超大文件拆分（AGENTS 规范）🔥

:information_source: 背景：当前仓库仍存在多个超大文件（远超 300/250 行上限），阻碍可维护性与测试；需按领域拆分、抽离服务层与组件/Hook，逐步迁移并保持兼容。

### 进度（后端→前端→验证）

- [x] 后端：已拆出 scripts CRUD/生成到 `ai-pic-backend/app/api/v1/endpoints/scripts/`（legacy 仍需迁移）
- [ ] 后端：拆分 `ai-pic-backend/app/api/v1/endpoints/scripts_legacy.py`（≈4900 行）到 `app/api/v1/endpoints/scripts/*`（按 storyboard/dialogue-audio/timeline 等域拆分），并逐步下线 legacy 路由
- [ ] 后端：拆分 `ai-pic-backend/app/services/dialogue_audio_service.py`（≈1600 行）为 `app/services/audio/*`（tts/mix/timeline/persistence），并补单测
- [ ] 后端：拆分 `ai-pic-backend/app/services/ai_service_manager.py`（≈1480 行）按 provider/domain 拆分，收敛公共重试/鉴权/日志
- [ ] 后端：统一 voice catalog 单一入口（`ai-pic-backend/app/services/voice_catalog.py` 与 `ai-pic-backend/app/services/audio/voice_catalog.py` 去重）
- [x] 前端：已落地 `ai-pic-frontend/src/utils/api/{client,endpoints,types}` 目录（迁移进行中）
- [ ] 前端：迁移并缩减 `ai-pic-frontend/src/utils/api.ts`（≈2750 行），最终仅保留 re-export/兼容层或删除
- [ ] 前端：拆分 `ai-pic-frontend/src/app/episodes/[id]/storyboard/page.tsx`（≈3300 行）为 page + hooks + components（页面 < 200 行）
- [x] 前端：拆分 `ai-pic-frontend/src/app/tasks/page.tsx` 到 `ai-pic-frontend/src/components/features/tasks/*`（页面 < 200 行）
- [ ] 前端：拆分超大 modal（如 `ai-pic-frontend/src/components/shared/modals/StoryboardVideoModal.tsx`），满足 ≤250 行规范
- [ ] 验证：后端 `pytest` + 前端 `npm run lint`；Chrome 跑通 1 条 storyboard 主路径并记录到 `agent_chats`

## Fix: 剧本生成稳定性（避免 mock 回退）

### 进度（后端→测试→验证）

- [x] 后端：episode outline fallback 从 beats 生成 `plot_points/scenes`（上限 12），避免兜底只落 1 场景 summary
- [x] 后端：AI 管理器 direct 剧本生成显式传 `max_tokens` + JSON 修复，缓解 MiniMax 默认 256 tokens 截断导致解析失败→mock 回退
- [x] 后端：LangGraph Script Agent 增加超时保护（120s）；无 `scene_budgets` 时默认禁用 duration 控制，超时后自动回退 direct
- [x] 测试：新增单元测试覆盖 fallback/max_tokens/timeout
- [x] 前端：Episode workspace 再生成剧本轮询 task，完成后自动切换到新 scriptId（URL 同步）
- [x] 前端：Episode workspace 概览“场景数”展示所选剧本的实际场景数（避免 `episode.scene_count` 滞后导致误读）
- [x] 验证：Chrome 端到端在 Episode workspace 重新生成剧本，产出 `v1.1 (Script ID: 83)`，7 场景，`ai_model=ai_manager_minimax`

## Fix: Scripts 列表查询 500（MySQL sort buffer）

- [x] 后端：优化 `/api/v1/scripts` 列表查询（lite 列表项 + `ORDER BY id DESC`），修复 MySQL `Out of sort memory (1038)` 导致的 500
- [x] 后端：进一步加固（先查 `id` 再 `load_only` 拉取列表字段），降低 join/filter 下 MySQL filesort 的 sort buffer 风险
- [x] 验证：Chrome 访问 `/api/v1/scripts?limit=5` 返回 200

## Feature: 短剧微类型与投流驱动创作闭环（故事→剧本→时间线→分镜）🔥

:information_source: 背景：短剧出海的核心是微类型定位与爽点密度，投流素材反向驱动创作与修订。本功能把“市场/类型/节奏/投流素材”前置到故事与剧本生成链路，并形成评分与修订闭环。

### 进度（功能→后端→前端→验证）

- [x] 功能/需求：整理海外短剧/网文出海投流洞察至 `docs/short-drama-overseas-insights.md`
- [x] 功能/需求：定义“市场×微类型”矩阵与 Story Bible（人群、强钩子、禁区、本土化壳），并在 `docs/short-drama-microgenre-framework.md` 建立规范文档
- [x] 功能/需求：制定 hook/反转/卡点节奏规范（含前N集情绪积压与释放节奏、反转密度阈值），输出“投流表/素材清单”标准结构
- [x] 功能/需求：定义脚本评分维度与阈值（冲突强度、角色辨识度、文化适配、素材可剪性、逻辑一致性），明确低分修订流程

- [x] 后端：扩展 Story 生成 schema，支持 `market_region`/`micro_genre`/`hook_plan`/`twist_density`/`cliffhanger_plan`/`ad_snippets`
- [x] 后端：扩展 Episode/Script 生成 schema，支持市场/微类型/钩子/投流素材字段
- [x] 后端：更新 story outline prompt 模板，注入微类型与 hook 规则
- [x] 后端：更新 episode/script/storyboard prompt 模板，注入微类型与 hook 规则
- [x] 后端：新增 `short_drama` prompt 变体（`story_outline`/`episode_generation`/`episode_from_outline`/`episode_duration_reject`/`script_generation`）
- [x] 后端：episode async 生成上下文补齐 `story_format`，确保 Episode Agent 模板分流
- [x] 后端：新增短剧故事模板与剧本模板（每集强爽点/反转/收获点/结尾钩子），并针对 deepseek-chat 做指令优化（优化 system_prompt_story/script_short_drama.txt JSON 输出规范）
- [x] 后端：新增投流素材生成模板（15/30/60 秒素材、标题、字幕钩子）（traffic_sheet_generation.txt/yaml）
- [x] 后端：实现 HookScore/ScriptScore agent 与"投流表生成"service（app/services/scoring/），接入 API 端点（/api/v1/scoring/）
- [x] 后端：修复 `/api/v1/scoring/score/{script_id}` 与 `/api/v1/scoring/traffic-sheet/{script_id}`（从 DB 读取当前字段 + 统一走 `ai_manager.generate_text`），避免运行时报错
- [x] 后端：HookScore/ScriptScore 接入生成链路，生成评分/投流表并输出改写建议（`rewrite_guidance`）
- [x] 后端：故事生成在 `extra_metadata` 落库 hook 计划与投流素材（hook_plan/twist_density/cliffhanger_plan/ad_snippets）
- [x] 后端：在 Task `parameters.agent_run` 中落库评分报告、投流表、素材标签（脚本生成/再生成任务）

- [x] 前端：故事/剧集/剧本生成入口新增“市场/微类型/节奏模板”选择与预览说明
- [x] 前端：新增“爽点评分/风险提示/投流表”视图，支持导出素材清单
- [x] 前端：在分镜/时间线 UI 标注与 hook 节点/投流素材对应的镜头与时间点（HookTagBadge/AdSnippetCard/HookPlanPanel 组件）

- [x] 验证：short_drama prompt 变体单元测试（`template_resolver` + prompt 渲染）
- [x] 验证：Chrome E2E（deepseek 文生文/剧集/剧本；google 文生图；google 文生视频）
- [x] 验证：新增 schema 与 prompt 单元测试，覆盖 hook 计划/评分结构（tests/unit/services/scoring/ 21 tests）
- [x] 验证：E2E 路径（选择微类型→生成故事/剧集/剧本→投流表→分镜/时间线标注），Chrome 记录验证
- [ ] 验证：短剧全流程 E2E（IP→环境→故事→剧本→分镜图→分镜视频），逐张下载抽检并在 `agent_chats` 记录

## Feature: 故事/剧集生成质量闭环（严格校验 + 上下文 + 就绪检查）🔥

:information_source: 背景：当前 story/episode 生成链路仍偏“拼 prompt → 调模型 → 宽松解析 → 落库”，缺少统一的上下文管理与严格校验/验正，容易产生结构不合规、集数不匹配、角色设定漂移等问题；需要建立可追溯、可修复、可阻断的质量闭环。
:triangular_flag_on_post: 决策点：

- 解析/校验失败时是否允许落库（建议：失败不落库，任务标记 FAILED 并保留原始产物用于排查）
- repair 次数与策略（建议：最多 2 次，第二次强制 strict JSON；仍失败则终止）
- 上下文包（Context Pack）字段清单与 token 预算策略（按 story_format/模型差异适配）

### Phase 1: 严格结构化输出 + repair（P0）

- [x] 后端：抽出通用的 JSON 解析/校验/repair 组件（story_outline、episode_plan 共用），标准化 `normalized` 产物与错误结构（validation_errors/repair_attempts）
- [x] 后端：故事生成强制通过 `StoryOutlineModel` 校验后才允许落库；收敛/移除 `extract_outline_from_text` 这类“宽松兜底落库”路径
- [x] 后端：剧集生成强制通过 `EpisodePlanModel` 校验（episodes 数量 == episode_count、必填字段齐全）；失败走 repair；最终失败不创建 Episode
- [x] 后端：把 prompt、raw content、normalized、校验错误与 repair 过程写入 `Task.parameters.agent_run`（便于排障与复现）
- [x] 测试：新增单元测试覆盖（parse fail → repair success/failed、episodes 数量修复、必填字段补齐、错误落库结构）
- [x] 验证：Chrome E2E（生成故事→生成剧集）至少 2 个 case，并在 `agent_chats` 记录（含失败 case 的可追溯性）

### Phase 2: 上下文管理（Context Pack）（P0/P1）

- [x] 功能/需求：定义 `StoryContextPack` / `EpisodeContextPack` 字段清单（角色卡/世界观/关系/禁区/continuity_ledger/最近 N 集摘要/画幅与风格偏好等）
- [x] 后端：实现 context pack builder（从 DB 组装 + token/字符预算裁剪），并补单测
- [x] 后端：新增 context pack preview/debug API（只读接口或内部工具）
- [x] 后端：Episode 生成 prompt/agent 输入改为显式注入 context pack（并把 used_context 写入 agent_run）
- [x] 后端：新增/补齐“每集摘要”产物（episode_summary）用于后续生成连续性（可在 episode 生成后自动回填）
- [x] 前端：在“生成剧集/再生成”弹窗提供上下文预览与开关（如：仅最近 N 集/包含 continuity ledger/包含角色卡）
- [ ] 验证：同一 Story 连续生成/再生成 2 次 episode，抽检关键设定一致性与 ledger 更新是否符合预期（Chrome 记录）

### Phase 3: 生成前就绪检查（P0/P1）

- [ ] 后端：Story→Episode readiness 检查（必填字段/长度阈值/角色存在与归属/marketing meta 完整性）；输出可读的 blocking issues + 建议修复项
- [ ] 后端：新增 readiness/preview API（用于前端在生成前校验，并支持“一键补齐 story outline 再生成 episode”的流程）
- [ ] 前端：生成按钮前展示 readiness 结果；存在 blocking issues 时阻断生成，并提供一键修复/补齐入口
- [ ] 测试：readiness 规则单测 + API 集成测试（阻断/允许/一键修复）
- [ ] 验证：Chrome E2E 覆盖“story 缺字段被阻断→一键补齐→生成 episode 成功”的完整链路

## Feature: Duration Orchestrator Agent（端到端时长闭环验证）🔥

:information_source: 背景：当前从剧集到时间轴/对白到分镜的时长对不齐。Episode Agent 的 `estimated_duration_seconds` 是 LLM 估算，与 TTS 实际时长差异可达 50%+；Script Agent 不知道场景目标时长，对白长度随机；Timeline Agent 只能通过 GAP 微调，无法拯救大偏差。需要构建端到端闭环验证系统。

:link: 设计文档：`docs/design/duration-orchestrator-agent.md`

:triangular_flag_on_post: 核心思路：

- **场景级闭环验证**：每个场景生成后立即 TTS 测量，不达标则重新生成（最多3次），达标后锁定
- **字数锚定**：根据目标时长计算 `target_word_count`，传递给 Script Agent 约束对白生成
- **预算动态调整**：某场景超时/欠时，从后续场景预算中调整

### Phase 1: 基础框架（P0）✅ 已完成

- [x] 1.1 后端：创建 `app/services/duration_orchestrator/` 目录结构
- [x] 1.2 后端：实现 `OrchestratorState` 数据类（`state.py`）
- [x] 1.3 后端：实现 `allocate_budget` 节点 - 根据场景数量和重要性分配时长预算
- [x] 1.4 后端：实现 `validate_duration` 节点 - 验证场景时长是否在容差范围内
- [x] 1.5 测试：编写 `tests/unit/services/duration_orchestrator/test_budget_allocation.py`（26 tests passing）

### Phase 2: 对白生成改造（P0）✅ 已完成

- [x] 2.1 后端：新增 `SCRIPT_WORD_COUNT_CONSTRAINT` prompt 模板（`prompts/templates/script_word_count_constraint.txt`）
- [x] 2.2 后端：改造 `ScriptLangGraphAgent` 支持 `target_word_count` 约束（`scene_budgets` 参数）
- [x] 2.3 后端：实现 `generate_dialogue` 节点 - 调用改造后的 Script Agent
- [x] 2.4 后端：实现 `compute_adjustment_hint` 函数 - 生成调整建议
- [x] 2.5 测试：编写 `tests/unit/services/duration_orchestrator/test_generate_dialogue.py` 和 `tests/unit/services/test_script_agent_word_count.py`（19 tests passing）

### Phase 3: TTS 估算与验证（P1）✅ 已完成

- [x] 3.1 后端：实现 `tts_trial` 节点 - 支持估算模式和实际 TTS 采样模式
- [x] 3.2 后端：实现 `validate_duration` 节点 - 验证 actual vs target ±15%（Phase 1 已完成）
- [x] 3.3 后端：实现 `prepare_retry` 节点 - 生成调整建议（如"需增加2句对白，约50字"）
- [x] 3.4 后端：实现 `commit_scene` 节点 - 场景验证通过后提交，并触发预算再平衡
- [x] 3.5 测试：编写 `test_tts_trial.py`, `test_commit_scene.py`, `test_prepare_retry.py`（33 tests passing）

### Phase 4: 闭环控制（P1）✅ 已完成

- [x] 4.1 后端：实现 `rebalance_budget` 逻辑（已集成到 `commit_scene` 节点）
- [x] 4.2 后端：组装 LangGraph StateGraph（`agent.py`）
- [x] 4.3 后端：实现条件边路由逻辑（所有节点间的条件边已实现）
- [x] 4.4 测试：编写 `test_agent.py` - 8 tests passing

### Phase 5: 剧集组装与最终验证（P1）✅ 已完成

- [x] 5.1 后端：实现 `assemble_episode` 节点 - 合并所有场景的对白、时长数据
- [x] 5.2 后端：实现 `final_validation` 节点 - 验证总时长 ±10%
- [x] 5.3 后端：集成到 StateGraph（agent.py 已更新）
- [x] 5.4 测试：编写 `test_assemble_episode.py`（10 tests）和 `test_final_validation.py`（15 tests）

### Phase 6: API 集成（P2，预计 1 天）

- [x] 6.1 后端：在 `ScriptDialogueAudioGenerateRequest` 添加 `use_duration_control` 参数
- [x] 6.2 后端：创建 `duration_controlled_dialogue_service.py` 集成服务
- [x] 6.3 后端：修改 `_process_script_dialogue_audio_task` 支持分支逻辑
- [x] 6.4 后端：实现结果持久化（SceneBeat 写入 + scene `extra_metadata.dialogue_audio` 更新）
- [x] 6.5 测试：编写 API 集成测试

### Phase 7: 监控与可观测性（P2，预计 1 天）

- [ ] 7.1 后端：添加结构化日志（各节点日志增强）
- [ ] 7.2 后端：添加进度回调 callbacks
- [ ] 7.3 文档：更新 `docs/duration-orchestrator-guide.md`

### 验收标准

| 指标           | 目标值           |
| -------------- | ---------------- |
| 单场景时长偏差 | ≤ ±15%           |
| 剧集总时长偏差 | ≤ ±10%           |
| 平均重试次数   | ≤ 1.5 次/场景    |
| 端到端生成时间 | ≤ 现有流程 × 1.5 |
| 单元测试覆盖率 | ≥ 80%            |

### 下一步

1. ✅ Phase 1, 2, 3, 4, 5 已完成（108 tests passing）
2. ✅ Phase 6 已完成（`dialogue-audio/generate-async` 支持 `use_duration_control=true`，并落库 scene 音轨 + SceneBeat）
3. 进行 Phase 7：
   - 添加结构化日志和进度回调
   - 更新 `docs/duration-orchestrator-guide.md`

---

## Feature: 全局软删除 + business_id

:information_source: 背景：所有实体需支持软删，默认查询排除已删数据；引入稳定的 `business_id` 作为业务主键，并将关联/唯一性收敛到 `business_id`；再生成改为“新记录 + 旧记录软删”，前端切换到新 ID/business_id。

### 进度（功能→后端→前端→验证）

- [x] 功能/需求：完成全局软删 + business_id 设计稿，落于 `docs/soft-delete-business-id.md`
- [x] 后端：Phase 1 已新增 `business_id`/软删字段与索引并回填（核心表已覆盖）
- [x] 后端：Phase 1 统一查询默认过滤 `is_deleted=false`（stories/episodes/virtual IP/story_structure 全覆盖）
- [x] 后端：Phase 2 已为子表补充 `*_business_id` 并回填（story_structure/virtual_ip_images/tasks 等）
- [x] 后端：Phase 2 唯一约束改为含 `is_deleted` 的复合唯一（迁移 `g3e4f5d6a7b8`），business_id 恢复为全局唯一
- [x] 后端：Phase 3 删除/恢复接口改为软删（scenes/shots/scene_beats/environments 已完成 soft_delete）
- [x] 后端：按 `business_id` 访问的路由/查询参数补全（scenes/shots/scene_beats 已新增 business_id CRUD 端点）
- [x] 前端：stories/episodes/scripts/virtual IP 等核心页面已优先使用 `business_id` 路由（兼容旧 `id` 只读）
- [x] 前端：其余资源与深链路补齐 `business_id` 兜底，regenerate 后跳转到新记录（已验证关键路径均使用 business_id fallback）
- [x] 后端：regenerate 创建新记录并软删旧记录（scripts_legacy + dialogue_audio_service/SceneBeat 已改为 soft-delete）
- [x] 验证：pytest 覆盖软删/重建唯一键/regenerate 新记录链路；前端 `npm run lint` + E2E 检查软删后列表/详情/再生成可用

### 下一步

- 前端：其余资源与深链路补齐 `business_id` 兜底，regenerate 后跳转到新记录
- 验证：E2E 检查软删后列表/详情/再生成可用

## Feature: 叙事结构与数据模型对齐

:information_source: 背景：Story → Episode → Script 当前字段概览 vs 工业级 Treatment / Step Outline / Scene / Shot 要求
:triangular_flag_on_post: 决策点：

- 是否需要单独的 Treatment 表以及与 story 的版本关系
- Scene/Shot 粒度需要保存哪些必填字段（INT/EXT, 时间, 景别, 镜头运动）
- 已有 JSON 字段迁移后如何保证旧数据兼容
- **开放问题**：
  - 阶段性执行顺序：先建 Treatment → Scene → Shot 还是可以分阶段上线
  - 迁移期间老接口是否保持兼容 (可选 query 参数? 版本?)
  - 多剧本共享场景/镜头的复用策略

### 进度（功能→后端→前端→验证）

- [x] 功能/需求：梳理 Story → Episode → Script 现状与工业级 Treatment / Step Outline / Scene / Shot 差异，已产出对比文档 `docs/story-structure-gap-analysis.md` 与接口说明 `docs/story-structure-api.md`
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
- [x] 后端：模型注册表已提供 `size_options` / `aspect_ratio_options`（OpenAI/Seedream 等）
- [x] 后端：引入图像生成参数 `generation_profile`（按 provider+model+mode 默认 `steps/cfg_scale/negative_prompt`），并提供 `GET /api/v1/image-gen/profiles`
- [x] 后端：环境/分镜/图生图落盘 `size` / `width` / `height` / `aspect_ratio`
- [x] 后端：虚拟 IP 文生图落盘 `size` / `width` / `height` / `aspect_ratio`（generation_params/metadata 统一用 normalized 值）
- [x] 前端：虚拟 IP 图像页支持基于已有图像的变体生成（`/api/v1/virtual-ips/{id}/images/{image_id}/variants`），含模型选择与生成数量，变体会保存为新的虚拟 IP 图像资产
- [x] 前端：虚拟 IP 更新请求类型补齐 `voice_config`，修复 `next build` 类型检查失败
- [x] 前端：虚拟 IP 手动上传走统一 OSS（修复上传字段与 FormData 头部）
- [x] 前端：文生图表单按模型动态限制分辨率选项（含 Seedream/DALL·E 白名单）
- [x] 前端：统一 `generation_profile`（质量档位）选择与展示，并贯通虚拟IP/环境/分镜图生图请求
- [x] 前端：图生图弹窗补齐分辨率/比例限制与错误提示（当前复用文生图已选 `size`）
- [ ] 验证：为不同模型+分辨率补齐端到端用例（含 DALL·E 3 官方三种长宽比、DALL·E 2 三种尺寸、Seedream 2K），在 README / TESTING_GUIDE 记录 Ark 凭证、调试与兼容矩阵

### 下一步

- 按提供商梳理多图生图参数与约束（Seedream 4.5 / DALL·E / SDXL / 可灵 / 即梦 / DeepSeek），补齐 UI 文案与错误提示
- 固化分辨率白名单：DALL·E 3 仅 `1024x1024` / `1024x1792` / `1792x1024`；DALL·E 2 仅 `256/512/1024` 方图；Seedream 4.5 归一化 `size: 2K` 并校验像素下限；SDXL/其他按官方推荐收敛
- 后端在 `generate_image` / `image_to_image` 中按模型映射规范化参数并记录实际下发规格，前端补齐图生图弹窗的尺寸/比例限制
- 增补模型×分辨率测试与 Ark 调试说明，校验文档覆盖背面照/全身照等变体

## Feature: 图像生成提示词/参数规范化（provider-aware）

:information_source: 背景：不同 provider 对文生图/图生图参数差异很大（negative_prompt、reference_images、多图条件等）。需要统一提示词模板语义、参数归一化与 UI 动态表单，避免“输入展示了但提交被丢弃/被忽略”。

### 进度（功能→后端→前端→验证）

- [x] 后端：文生图 `reference_images` → provider-safe 参数透传（Google/Volcengine 等支持者）
- [x] 后端：UI 元数据按能力生成提示（negative_prompt 等）并修正 `supports_reference_images` 判定（避免 OpenAI/DALL·E 误展示）
- [x] 后端：环境文生图支持 `reference_images`（含 task payload 透传与 URL 归一化）
- [x] 后端：虚拟 IP 文生图支持 `reference_images`（含 task payload 透传与 URL 归一化）
- [x] 前端：环境文生图表单按所选模型动态加载 `reference_images` 选择器并随任务提交
- [x] 前端：虚拟 IP 文生图表单按所选模型动态加载 `reference_images` 选择器并随任务提交
- [x] 后端：当 provider 不支持 `negative_prompt`/`reference_images` 时做降级处理（`negative_prompt` 合并进 prompt、`reference_images` 丢弃）并记录 `audit.dropped_fields`
- [x] 后端：可灵文生图支持 `reference_images`（映射到 `image`，仅 1 张）；使用参考图时合并 `negative_prompt` 进 prompt
- [x] 后端：火山图生图 count 参数对齐（img2img `n` → `count`）
- [x] 后端：修正可灵图生图仅支持 1 张基准图（禁用 img2img `extra_images`）并同步 UI 元数据
- [x] 后端：normalize 阶段按 provider+mode(+model) 丢弃不支持参数并写入 `audit_warnings`（避免“填了但静默无效”）
- [x] 后端：即梦图生图透传 `size` 并在 provider 侧映射为 `width/height`（避免 UI 选项被静默丢弃）
- [x] 前端：虚拟 IP 文生图模型列表拉取 `text_to_image`（修复误用 `image_to_image`）
- [x] 后端：环境文生图模板明确单帧语义并补 `no collage` 约束
- [x] 后端：环境图生图变体使用独立提示词模板 `environment_image_variant`（保留空间布局/镜头视角，仅按变体要求调整）
- [x] 后端：Google/Gemini 文生图参考图 413 风险治理（限制张数/压缩/提示）
- [x] 后端：补齐文生图 `max_reference_images` UI 元数据（Google=4、可灵=1）并用于前端动态表单
- [x] 前端：环境/虚拟 IP 文生图参考图选择器按 `max_reference_images` 自动裁剪（超过上限替换最早选择）
- [x] 后端：补齐 `image_gen` UI 元数据：`supports_style_preset_id` / `supports_style_spec`（provider-aware）
- [x] 前端：按模型能力动态隐藏并清理无效的 `style_preset_id` / `style_spec`（避免“选了但不生效”）
- [x] 前端：切换模型/provider 时自动清理不支持的高级参数（seed/steps/cfg/strength 等），避免提交旧值
- [x] 后端：Storyboard refs 在 provider 支持 txt2img `reference_images` 且未显式设置 `strength` 时优先走 `TEXT_TO_IMAGE + reference_images`（否则保持 img2img base+extra_images）
- [x] 后端：补齐 `STORYBOARD_KEYFRAME` 提示词对“转场/镜头切换”等词的语义约束（剪辑备注，不要在一张图里表现多个镜头）
- [x] 后端：增强通用 `no collage` 约束（补充 `no split-screen/multi-panel/contact sheet`）
- [x] 后端：分镜生图强化“禁止 contact sheet/帧号/字幕/标签”等约束，并将 Google 图片生成默认输出改为 image-only（`responseModalities=["IMAGE"]`）
- [x] 前端：分镜图生图弹窗展示「模型提示」（`image_gen` notes）并在不支持多参考图时自动裁剪为 1 张（其余选择替换/忽略）
- [x] 前端：将 `reference_images` 动态输入扩展到分镜文生图等入口（按 model 能力隐藏/显示）
- [x] 验证：补齐 provider×domain 参数兼容矩阵与端到端用例（Chrome 记录关键请求与结果；见 `docs/image-gen-provider-matrix.md`）
- [x] 后端：补齐 `image_gen` UI 元数据 `max_count`（provider-aware；Google/即梦=1，火山/可灵/OpenAI DALL·E2=≤4）
- [x] 前端：文生图/图生图表单按 `max_count` 动态限制生成张数并展示提示（含超限自动裁剪与文案）

## Feature: 任务队列与 Agent 执行落库（高优）

:information_source: 背景：已有 Task 表与 Story/Episode/Script 异步生成入口（`/generate-async`）、前端任务管理页 `/tasks`，但任务执行目前依赖 `BackgroundTasks`、散落在各 endpoint 中，LangGraph Agents（故事/剧集/剧本）也未统一落库运行轨迹，难以在任务层面排查与审计。
:information_source: 背景：已有 Task 表与 Story/Episode/Script 异步生成入口（`/generate-async`）、前端任务管理页 `/tasks`；任务执行已统一走 Celery worker，但 Task 层缺少 `parameters.agent_run` 审计信息，导致排查需跳转到目标实体或日志，审计不直观。

### 进度（功能→后端→前端→验证）

- [x] 功能/需求：统一 Story/Episode/Script/图像等任务到 Task 队列，使用 Celery Worker 处理，Agent 每次执行结果在 Task 与目标实体（Story/Episode/Script）上都可追踪
- [x] 后端：补全 `TaskType` 枚举（story/episode/script/dialogue-audio/timeline/storyboard/video/text…），并把 Story/Episode/Script 等生成入口的 `task_type` 从兜底的 `image_generation` 改为正确类型
- [x] 后端：细分 image 相关 `TaskType`（storyboard_image / virtual_ip_image / environment_image + variants），并更新对应生成入口，支持 `/tasks` 按域过滤
- [x] 后端：提供历史任务 `TaskType` 回填脚本 `ai-pic-backend/scripts/backfill_task_types.py`（将 legacy `IMAGE_GENERATION` 按 title/prompt 纠正为正确类型）
- [x] 生产：执行一次历史任务 `TaskType` 回填（先 `--dry-run`，并按 user/时间范围分批）
- [x] 后端：提炼 `task_worker`，改造 `/stories/episodes/scripts/*/generate-async` 统一走 Celery worker（替换 `BackgroundTasks`），并完善 `Task.status` / `result_file_path` / `error_message` 回写
- [x] 后端：在 Task 的 `parameters.agent_run` 中落库 agent 关键信息（prompt、provider/model、usage、reasoning、result_ref），保证每次执行可在 Task 层审计
- [x] 后端：提供历史任务 `parameters.agent_run` 回填脚本 `ai-pic-backend/scripts/backfill_task_agent_runs.py`（默认 dry-run；支持按 user/时间分批；FAILED/CANCELLED 补 error context）
- [x] 后端：扩容 `tasks.parameters` 为 LONGTEXT，避免 agent_run 回填触发 MySQL TEXT 64KB 限制
- [x] 生产：执行一次历史任务 `parameters.agent_run` 回填（先 `--dry-run`，再按 user/时间范围分批 `--apply`）
- [x] 后端：在 Story/Episode/Script 的 `extra_metadata.agent_run` 中写入 LangGraph/AI 管理器的运行信息，覆盖同步与 `/generate-async` 路径
- [x] 后端：为虚拟 IP 图像、环境图像、分镜图像等长耗时图像生成操作提供标准 Task 创建 + Celery 异步处理路径（与现有 `/api/v1/tasks` 结构对齐）
- [x] 后端：新增 `app/core/celery_app.py` 与 `app/services/task_worker.py`，并在 `docker/docker-compose.prod.yml` 中增加 `ai-video-celery-worker` 服务（与 backend 共用镜像与配置）
- [x] 后端：修复 OpenAI `response_format=json_schema` 在 `script_dialogues` 场景的 schema 校验 400（完善 item schema + 非 strict schema 自动回退 `json_object`）
- [x] 前端：在任务管理页 `/tasks` 中支持按 `task_type` 过滤
- [x] 前端：在任务详情中展示 `parameters.agent_run` 的关键信息（provider/model/usage/reasoning/prompt）
- [x] 验证：为 Story/Episode/Script/图像任务增加集成测试（任务创建 → handler 执行 → Task 状态与目标实体写入校验），并在 `TESTING_GUIDE.md` 中记录 Celery 本地运行与调试流程

### 下一步

- [x] 后端：补齐 dialogue-audio/timeline/storyboard/video/text/image 等任务的 `parameters.agent_run` 审计（统一到 Task 层）

## Feature: 场景/环境资产与分镜联动

:information_source: 背景：需要把环境/场景资产（办公室/学校/商场等）与角色 IP 绑定到分镜帧，支撑“分镜→图像→视频”闭环。

### 进度（功能→后端→前端→验证）

- [x] 功能/需求：定义环境/场景资产与分镜/角色绑定（environments 表、角色锚点），现支持分镜页绑定环境与镜头绑定角色
- [x] 后端：已落地 environments 表与 `scenes.environment_id` / `shots.character_ids` 迁移；环境文生图/图生图已上线用于手动生成参考图
- [x] 后端：环境文生图支持 `reference_images`（支持的 provider 才会透传到调用层）
- [x] 后端：`generate_storyboard_images` 已聚合 `scene.environment_id` + `shot.character_ids` 并注入 `image_to_image`
- [x] 后端：修复 Google Veo 分镜视频生成 image-to-video 图像入参（`bytesBase64Encoded`），支持异步轮询并回填可下载链接
- [ ] 后端：Google Veo `429 RESOURCE_EXHAUSTED` 时提供清晰报错与退避策略（避免反复失败/误判为系统异常），并支持可配置 fallback（如临时切换 provider/model）
- [x] 前端：提供环境资产管理页（上传/生成/变体/删除参考图），在 `/stories/[id]` 分镜/剧集界面支持环境选择与标签筛选
- [x] 前端：环境文生图表单按模型动态展示参考图选择器并提交 `reference_images`
- [x] 前端：修复分镜“生成视频”弹窗无尾帧候选时强制勾选尾帧导致无法提交（允许仅首帧生成）
- [x] 验证：Chrome E2E 分镜页生成 Veo 3.1 视频并下载抽帧检查（scriptId=103 frame=0）
- [x] 验证：待补端到端用例，验证选择环境+角色后分镜帧能稳定生成对应图像；在 `TESTING_GUIDE.md` 记录并为环境表/关联补迁移回归用例

### 下一步

- 在分镜帧结构中显式携带 `environment_id` 并作为条件图选择逻辑输入生成
- 将虚拟 IP 图像（头像/全身/表情）与环境参考图共同注入分镜生成调用，保证人物与场景一致性
- 设计多图条件调用适配层（参考 Seedream/SDXL 等），集中映射“人物/环境参考图 + 文本提示词”到各家 API
- 在真实浏览器路径完成端到端生成验证，补测试与文档

## Feature: 分镜 LangGraph 管线统一（规划+生成）

:information_source: 背景：当前分镜生成同时存在多条路径：直接调用 `generate_storyboard`、基于 `generate_storyboard_plan` 的规划+逐场景生成，以及 `StoryboardReActReasoner` 的 LangGraph ReAct 管线，前端还有“规划/生成”两个操作。希望统一为一条以 LangGraph 为核心的分镜管线，默认走“先规划再生成”，对帧数量不足/JSON 结构不合规能自动 ReAct 修复，这是系统最核心的功能之一。

### 进度（功能→后端→前端→验证）

- [x] 功能/需求：统一分镜生成模型为“带规划的 LangGraph 管线”，默认每个选定场景至少生成 `frames_per_scene` 帧，帧结构必须满足 `StoryboardModel` JSON Schema
- [x] 后端：实现 `StoryboardLangGraphAgent`（或扩展现有 `StoryboardReActReasoner`），graph 中包括：场景选择节点 → 帧规划节点（`StoryboardPlanModel`）→ 帧细化节点（`StoryboardModel`）→ 校验/数量检查节点 → 修复节点（在帧数不足或结构不合法时 ReAct 重试）
- [x] 后端：收敛 `AIService.generate_storyboard*` 接口与 `scripts_legacy.py`/`app/api/v1/endpoints/scripts/*` 中分镜生成逻辑，统一通过 LangGraph agent 入口，保留本地 fallback 作为最后兜底；确保同步/异步（`/storyboard/generate`、`/storyboard/generate-async`）走同一套管线
- [x] 后端：在分镜生成 Task 与 `script.extra_metadata.storyboard` 中落库完整 agent 运行轨迹（plan、frames、provider/model、usage、reasoning_trace），支持后续审计与问题回溯
- [x] 前端：分镜工作台按钮统一切换到 `*-async` 路径，默认 `use_plan=true`，不再显式暴露“规划”动作，仅在高级视图中展示 `storyboard_plan` 与 ReAct 轨迹
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
- [x] 后端：分镜占位生成合并短 pause beats（停顿/留白），保证 scene 内分镜总时长与音轨一致（声音优先）
- [x] 后端/运行环境：backend/celery 镜像安装 `ffmpeg`（音频拼接依赖），避免运行时 `No such file or directory: 'ffmpeg'`
- [x] 前端：在 Episode 详情/剧本页新增“生成对白音轨 / 生成时间轴 / 生成分镜帧”入口，展示进度、失败原因、版本与重试/复用
- [x] 前端：修复 Episode 详情页任务轮询参数类型（`taskAPI.getTask(String(taskId))`），确保 `next build` 类型检查通过
- [x] 前端：在 Episode 详情页展示“场景对白音轨（scene）”列表与播放/下载入口（`scene.metadata.dialogue_audio.oss_url`）
- [x] 前端：Episode 详情页默认展开场景音轨列表；存在 episode 级音频时直接提供播放器（避免“生成成功但不知道在哪里听”）
- [x] 前端：分镜管理页接入 episode `audio_timeline`（携带 scriptId 跳转、展示 beats/version 与 episode 音频播放器；帧级展示时间窗 start/end_ms，提供“从时间轴同步分镜占位”入口）
- [x] 验证：浏览器端到端用例（账号 `geyunfei`；Selenium headless Chrome，MCP transport closed）：episodes/10 → 生成对白音轨 → 生成时间轴 → 覆盖生成分镜帧占位，并将路径与结果记录到 `agent_chats`

### 下一步

- [ ] 补齐 beats→Timeline Spec 映射说明与测试覆盖（scene 级 `scene_beats` + episode 级偏移合并）
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
- [x] 验证：单集样例基于 `storyboard.frames` 生成全帧分镜视频并用 FFmpeg concat 导出 2 版 MP4（Veo 自带音频 / Episode TTS 音轨），产物上传 OSS（episode_id=133, script_id=117）

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
- **开放问题**：
  - 版本比较粒度：按场景/镜头/台词是否需要细化
  - 人工修改与 AI 生成如何合并成单一版本历史
  - 是否需要与 Git 等外部版本工具同步

### 进度（功能→后端→前端→验证）

- [x] 后端：新增 deterministic 剧本质检（lint 规则+评分）与同步/异步 API（`/api/v1/scripts/{id}/quality-check(-async)`）
- [x] 后端：扩展 TaskType `script_review`，新增 Celery 任务 `tasks.script_quality_check`，结果落库到 `Task.parameters.result` 与 `Script.extra_metadata.script_quality`
- [x] 前端：/tasks 支持 `script_review` 类型筛选与展示
- [x] 测试：新增 `ai-pic-backend/tests/test_script_quality_lint.py`
- [x] 验证：Chrome E2E 跑通“触发 script_review → 任务完成 → 拉取 result / script_quality”路径并记录到 `agent_chats`

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
- **开放问题**：
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
- **开放问题**：
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
- **开放问题**：
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
- **开放问题**：
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
- **开放问题**：
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
- **开放问题**：
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
- **开放问题**：
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

### 当前进展

- [x] 后端：规范化结构已落地（`scenes.environment_id` / `shots.character_ids`），剧本生成/更新时同步 `story_structure.scenes`（best effort）
- [x] 后端：`generate_storyboard_images` 已聚合环境/角色参考图进行图生图生成
- [x] 前端：storyboard 页面读取 normalized scenes/shots，支持环境选择与镜头角色绑定

### 待补（功能→后端→前端→验证）

- [ ] 功能/需求：明确分镜生成/更新的上下文字段清单（场景摘要、beat/shot 描述、角色、环境、模板版本），并对外暴露
- [ ] 后端：`generate_storyboard` / plan / update 路径写入 normalized scene/shot id、`environment_id`、`character_ids`，并回填 `scene_scope`/`shot_scope`/`context_text`
- [ ] 后端：将 `environment_id/character_ids` 持久化到 storyboard frames/meta，作为图像/视频生成的默认锚点
- [ ] 前端：阻断未选择规范化场景/镜头的生成操作，并展示上下文提示词预览
- [ ] 验证：在 http://localhost:8089/episodes/8/storyboard 走通“选环境+镜头角色→生成首尾帧→回填 meta→触发视频生成”路径并记录结果
