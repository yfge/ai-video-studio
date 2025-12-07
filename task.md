# 任务看板（AI + 人类超级个体协作版）

> 读取优先：让任何协作者（包括我）一眼就看懂当前优先级、状态和下一步。使用 `[ ]` / `[x]` 标识执行状态，全部任务按“功能→后端→前端→验证”顺序拆分，保证同一功能的前后端流程保持一致。

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
- [x] 需求澄清：梳理 Story → Episode → Script 现状与工业级 Treatment / Step Outline / Scene / Shot 差异，输出对比文档（见 `docs/story-structure-gap-analysis.md`，Discovery Session 议程详见 `docs/story-structure-discovery-session.md`）
- [x] 后端建模：设计 `story_treatments`、`story_step_outlines`、`scenes`、`scene_beats`、`shots` ER 图与字段说明
  - 下一步行动：评审/签收 `docs/story-structure-gap-analysis.md` 中的 ER/字段草案与枚举列表，冻结迁移脚本所需字段
- [x] 迁移实现：编写 Alembic 脚本迁移现有 JSON 字段到新表，提供回滚方案
  - 下一步行动：在真实脚本样本上跑 `alembic upgrade c4a1cbf0d7c2`（含回填），并用 `prototype_story_structure_migration.py --mode live --insert-probe --report-path <file>` 验证输出；补充端到端回滚验证文档
- [x] 服务层改造：更新生成/查询 Service 与 Repository，提供分层读取与写入接口
  - 下一步行动：完善权限/校验（角色鉴权、beat 顺序重排、shot 号冲突处理），并向前端开放聚合 CRUD
- [x] 前端同步：调整剧本详情页数据结构，支持新场景/镜头层级展示与编辑
  - 下一步行动：补充场景/节拍/镜头编辑的权限提示与错误态提示，并与分镜视图的数据展示保持一致
- [x] 验证闭环：补充单元/集成测试 + 数据迁移回归用例，更新相关文档
  - 下一步行动：补充端到端/权限链路（含分镜帧与 beat/shot 关联）的测试，持续跟进迁移回滚演练记录

## Feature: 虚拟 IP 图像生成与模型接入
:information_source: 背景：虚拟 IP 资产需要可靠的文生图 / 图生图流程，并对接多家模型服务（OpenAI、可灵、即梦、火山 Seedream 等）。
- [x] Seedream 4.5 文生图接入：按火山引擎 Ark 官方文档接入 `doubao-seedream-4-5-251128` 模型，通过 `/api/v1/virtual-ips/{id}/images/generate` 完成端到端验证（含 Docker 开发环境）。
  - 官方示例使用 `POST /api/v3/images/generations` 且 `size: \"2K\"`，并要求像素总数 ≥ 3,686,400。
- [x] 虚拟 IP 文案注入提示词：在虚拟 IP 图像生成接口中聚合 `description` / `background_story` / `biography` / `style_prompt`，确保生成提示词携带完整角色设定。
- [ ] 图生图能力完善：梳理 Seedream / 其他提供商的单图生图、多图生图参数，对齐 `/api/v1/ai/generate/image-to-image`，并补充「背面照、全身照」等变体用例。
  - [x] 在虚拟 IP 图像页接入基于已有图像的图生图变体接口（`/api/v1/virtual-ips/{id}/images/{image_id}/variants`），支持模型选择与生成数量，并将变体保存为新的虚拟 IP 图像资产。
  - [ ] 按提供商梳理多图生图参数与约束（含 Seedream 4.5 / DALL·E / SDXL 等），完善错误提示与 UI 文案。
- [ ] 分辨率与规格建模（对齐官方文档）：按已接入模型梳理并固化允许的分辨率 / size 组合，在统一模型注册表中声明，并驱动前后端联动：
  - OpenAI 图像 API：根据官方文档，将 DALL·E 3 的 `size` 限定为 `1024x1024` / `1024x1792` / `1792x1024`，DALL·E 2 的 `size` 限定为 `256x256` / `512x512` / `1024x1024`，并在调用时做严格校验。
  - Seedream 4.5（Ark）：根据官方示例和参数约束，将 `size` 选项归一化为 `2K` 等 Ark 支持的值，并在后端做像素下限校验，避免再次触发 `image size must be at least 3686400 pixels` 类错误。
  - 其他提供商（Stable Diffusion XL、可灵、即梦、DeepSeek）：按各自官方 API 文档整理推荐/允许的 `width`/`height` 或 `size` 参数（例如 SDXL 推荐 1024×1024），在后端集中维护白名单，并在前端按模型动态展示。
  - 后端：`generate_image` / `image_to_image` 接口接受规范化的 `size` / `width` / `height` / `aspect_ratio` 参数，按模型映射到具体服务端字段（Ark 用 `size`，OpenAI 用 `size` 字符串，SDXL 用 `width`/`height` 等），并在日志中记录实际下发规格；**当前已在虚拟 IP 图生图变体接口中透传 `size` 到统一的 `image_to_image` 调用，为后续按模型白名单收敛留好扩展点。**
  - 前端：在虚拟 IP 图像页的文生图 / 图生图表单中，根据当前选择的模型动态展示分辨率选项（禁止用户选到该模型不支持的尺寸），并在提示文案中明确当前模型的像素/长宽比限制；**目前图生图弹窗先复用文生图已选的 `size`（如 Seedream 2K / DALL·E 3 官方尺寸），后续再按模型粒度补充独立下拉。**
  - 验证：为不同模型 + 不同分辨率补充最小的端到端用例（含 DALL·E 3 三种长宽比、DALL·E 2 三种尺寸、Seedream 2K），在 `TESTING_GUIDE` 中记录分辨率兼容矩阵和调试方法。
- [ ] 验证与文档：补充虚拟 IP 图像生成与模型选择的端到端测试（含 Seedream 模型），在 README / TESTING_GUIDE 中记录 Ark 凭证与调试说明。

## Feature: 场景/环境资产与分镜联动
:information_source: 背景：需要把环境/场景资产（办公室/学校/商场等）与角色 IP 绑定到分镜帧，支撑“分镜→图像→视频”闭环。
- [x] 数据建模：新增环境/场景资产表（如 `environments`），字段含名称/类型（室内/室外）/标签/参考图/元数据；在 `scenes`（规范化表）中增加 `environment_id` 关联。（已落地 environments 表 + scenes.environment_id / shots.character_ids 迁移）
- [x] 角色与环境绑定：在分镜帧/分镜规划中显式记录 `character_ids`（虚拟 IP）与 `environment_id`，并在分镜编辑视图可选择/覆盖。（当前：分镜页支持场景绑定环境、镜头绑定角色；下一步将绑定信息注入分镜图生成）
- [ ] 生成链路：基于 “文本提示 + 角色参考图 + 环境参考图” 生成分镜图像；再用分镜图像 + 提示词生成短视频（逐场景/逐帧）。
  - [ ] 环境锚点：在分镜帧结构中明确携带 `environment_id`，并在生成分镜图像时从对应 Environment 的 `reference_images` 中选择环境图（或要求手动上传），不对环境本身强制文生图，只作为锚点/条件图使用。（当前环境文生图/图生图已上线，用于手动生成参考图）
  - [ ] 角色锚点：在分镜生成调用中联动虚拟 IP 图像（头像/全身/表情），使 “人物图片 + 环境图片 + 分镜提示词” 成为统一的生成输入，保证角色和场景一致性。
  - [ ] 调用适配：为支持多图条件的图像模型设计统一调用层（参考 Seedream / SDXL 等），在后端集中映射“人物/环境参考图 + 文本提示词”到各家官方 API。
- [x] 前端 UI：新增“环境资产管理”页（类似虚拟 IP 管理），支持上传/生成/变体/删除环境参考图；在 `/stories/[id]` 的分镜/剧集界面增加环境选择器，按标签筛选。（下一步：将环境参考图/角色选择显式传入分镜图生成与视频生成入口）
- [ ] 校验与测试：补充端到端用例，验证在选择环境 + 角色后，分镜帧能稳定生成对应图像；记录在 `TESTING_GUIDE.md`，并为环境表/关联新增迁移回归用例。（当前已在 Chrome 中用 Seedream 4.5 生成环境图）

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
- [ ] 需求澄清：定义 Draft / Blue / Pink 等版本流程与审批角色
- [ ] 后端建模：实现 `script_versions`、`scene_revisions`、`review_notes` 表及关联
- [ ] 服务层实现：记录版本切换、审批动作、回滚逻辑，保存提示词快照
- [ ] 前端版本视图：构建版本时间线、差异对比界面，支持审批与回滚操作
- [ ] 验证闭环：新增端到端测试覆盖版本切换与审批流程，撰写使用指南

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
- [ ] 需求澄清：整理角色档案应包含的身份、造型、情感、弧线节点
- [ ] 后端建模：拆分角色档案表，新增 `character_profiles`、`character_relations`、`relation_history`
- [ ] 服务层实现：提供角色查询、关系图谱 API，暴露造型锚点给提示词生成
- [ ] 前端角色面板：实现角色档案页与关系图谱可视化，支持编辑和版本记录
- [ ] 验证闭环：补充分镜/剧本生成前的角色一致性校验测试，更新文档

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
- [ ] 需求澄清：提炼工业级提示词模板段落（项目、场景、镜头、视觉、声音、锚点）
- [ ] 模板建模：设计 `prompt_templates`、`prompt_sections`、`prompt_variables` 表结构
- [ ] 生成引擎：实现模板渲染器，按 Story / Episode / Scene / Shot 注入上下文，可覆写变量
- [ ] 前端提示词工作台：提供模板选择、片段库、变量编辑与预览功能
- [ ] 验证闭环：建立模板单测 + 快照测试，撰写模板编写指南

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
- [ ] 需求澄清：确定提示词质量指标（准确度、一致性、镜头合规、锚点保持）
- [ ] 后端建模：新增 `prompt_runs`、`generation_feedback`、`comparison_jobs`
- [ ] 分析服务：实现 A/B 对比、评分聚合、健康度计算
- [ ] 前端仪表盘：展示提示词成功率、问题分布、改进建议
- [ ] 验证闭环：接入真实生成案例，补充自动/人工评分流程文档

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
- [ ] 需求澄清：划定模板草稿/审核/发布角色与灰度策略
- [ ] 后端状态机：实现模板状态流转、审批日志、权限控制
- [ ] 前端治理面板：提供审批队列、版本对比、灰度发布开关
- [ ] 验证闭环：新增权限/灰度相关测试与操作手册

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
- [ ] 需求澄清：列出分镜生成所需上下文（场景编号、地点、角色、对白、舞台指示）
- [ ] 后端提示词拼装：调整 `ai_service.generate_storyboard`，按场景注入真实摘要与角色信息
- [ ] 前端渲染：更新分镜结果展示，突出差异化帧并显示引用上下文
- [ ] 验证闭环：编写快照测试与人工对比用例，确保 frames 与场景一一对应

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
- [ ] 需求澄清：定义 plan → critique → finalize 流程输出的必备字段
- [ ] 推理实现：扩展 `StoryboardReActReasoner`，持久化推理轨迹与自动修复逻辑
- [ ] 前端调试视图：提供推理步骤、修复记录的可视化面板
- [ ] 验证闭环：补充集成测试覆盖三条路径（计划/细化/回退）

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
- [ ] 需求澄清：设计信息架构（顶部摘要、剧本预览、分镜版本、任务状态）
- [ ] 前端组件：实现场景树、镜头列表、版本历史、任务队列组件
- [ ] 后端接口：提供所需 meta / plan / 版本 API，确保前后端契合
- [ ] 验证闭环：编写关键交互单测 + E2E，更新用户操作说明
