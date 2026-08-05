# 任务看板（6 周执行版）

> 本文件只保留未来 6 周内可执行、且直接支撑产品主线的任务。历史完成记录保留在 `agent_chats/`、`docs/` 和 git，不再在这里堆叠。

## 产品定位

- 目标用户：专业短剧制作团队，不是小白一键成片用户。
- 产品模式：ToB 生产工作流系统，不是通用 AI 视频玩具。
- 第一性原理：已审批 canonical 小说是新系列的叙事 SSOT；`Timeline` 是生产时间、
  clip 顺序、资产谱系和交付 SSOT。二者通过 Episode/Script 的固定来源证据衔接。
- 无限画布定位：生产编排、候选评审和执行证据视图；画布布局不改变
  Timeline clip 顺序、时长或版本。
- 默认生产模式：对白/音轨时间轴驱动时长，图像/视频生成只是向时间轴填充 clip 资产。
- 故事板定义：只在选中 Timeline `video` clip（分镜）内生成和使用，作为该
  clip 的视觉参考资产；不再生成整剧/整条 Timeline 的故事板。
- 当前目标：把 `audio -> timeline -> clip -> render -> export` 做成产品核心闭环。
- 当前画布目标：跑通“stable clip → 故事板候选 → 人工选用整张故事板 →
  视频候选 → 人工选片 → `timeline.place` → Timeline”，新链路不使用首尾帧，
  不继续把快捷键和白板工具当作主链完成度。

## 看板规则

- 只记录未来 6 周内的活跃任务，不保留长线愿景和历史清单。
- 任何不直接支撑时间轴第一性的工作，不进入本看板。
- `Storyboard` 是时间轴的支撑视图，不再作为系统主编排入口。
- 新故事板入口必须挂在选中分镜的 clip inspector 内；旧 Timeline-level
  `storyboard_grid` 只读兼容，不再新增生成入口。
- 当前不新增 C 端 APP、通用 SaaS、社交 feed、素材市场等横向平台任务。
- 新任务必须回答两个问题：
  - 是否让时间轴更像 SSOT？
  - 是否缩短从音轨到可导出成片的路径？

## 当前最高优先级

- 当前提交继续围绕 Timeline-first 主链收口，不扩 APP/SaaS/社交方向。
- 真实 API harness 已通过一次 legacy bridge `Episode -> Timeline -> Render -> Export`：`artifacts/runs/main-chain-e2e-lineage-20260525T040437Z/golden_path.json`。
- provider-backed harness 已补成 Timeline-first：先创建含 `dialogue/video/subtitle` tracks 的 Timeline seed，再生图、生视频、回填 video asset，并通过 smoke evidence `artifacts/runs/provider-chain-dialogue-tracks-smoke-20260526T033733Z/provider_chain.json`。
- render worker 已开始消费 Timeline subtitle track 并用 ffmpeg 烧进最终视频；重启 worker 后的系统 API rerender evidence 为 `artifacts/runs/subtitle-render-rerender-20260526T040220Z/subtitle_render.json`。
- render worker 已开始消费 Timeline dialogue audio URL 并替换视频音轨；系统 API rerender evidence 为 `artifacts/runs/dialogue-audio-rerender-20260526T042900Z/dialogue_audio_render.json`，render job `25` 输出 `https://resource.lets-gpt.com/timeline-renders/video/20260526/042743/e73796af.mp4`。
- provider-backed full-30s harness 已按 Timeline-first 跑通：DeepSeek 生成 2 场剧本/对白，先创建 Timeline `19` seed，再逐 dialogue clip 生成 MiniMax TTS，OpenAI `gpt-image-2` 生成角色图，Seedance 2.0 生成 2 段 15 秒视频，回填 Timeline 后按 `start_ms/end_ms` 混音并渲染。证据：`artifacts/runs/provider-chain-dialogue-segments-full-30s-20260526T045229Z/provider_chain.json`；CJK 字体修复后的 rerender evidence：`artifacts/runs/provider-chain-dialogue-segments-full-30s-20260526T045229Z/subtitle_font_rerender.json`，render job `27` 输出 `https://resource.lets-gpt.com/timeline-renders/video/20260526/051434/7849fd70.mp4`，ffprobe 为 video `30.125s` / audio `30.080s`。provider-chain harness 已新增 render media probe，会在后续回归自动写入 `render_ffprobe.json` 并按 Timeline 场景抽帧。
- render media probe 自动门禁已用真实 smoke 链路验证：`artifacts/runs/provider-chain-render-probe-smoke-20260526T071200Z/provider_chain.json`，Timeline `20`、render job `28`、输出 `https://resource.lets-gpt.com/timeline-renders/video/20260526/070808/ada257bc.mp4`，`render_media_probe.ok=true`，expected `4.0s`、video `4.041667s`、audio `4.032s`，并抽出 `frames/render_scene_01_2000ms.jpg`。
- render media probe 自动门禁已用真实 full-30s 链路验证：`artifacts/runs/provider-chain-render-probe-full-30s-20260526T071051Z/provider_chain.json`，Timeline `21`、render job `29`、输出 `https://resource.lets-gpt.com/timeline-renders/video/20260526/072611/d4b917fa.mp4`，`render_media_probe.ok=true`，expected `30.0s`、video `30.125s`、audio `30.08s`，并按场景抽出 `frames/render_scene_01_2000ms.jpg` / `frames/render_scene_02_17000ms.jpg`。本次两段 15 秒 Seedance 同步调用分别耗时约 `402.957s` / `440.514s`，full-30s 只能作为低频付费回归。
- provider-chain harness 已支持独立 video clip 并发生成：`--video-concurrency` 默认 `2`，每条 request_chain 记录 `duration_seconds`，并写入 `video_generation.wall_time_seconds`，用于降低 full-30s 回归墙钟时间和暴露 provider latency。
- 2026-05-27 真实 provider-backed production proof 暂停在 `provider-blocked`：Seedance smoke preflight `artifacts/runs/seedance-billing-preflight-20260527T143214Z/provider_chain.json` 通过并产出 render job `34`，live-3 `artifacts/runs/quality-live-3-20260527T143829Z/quality_report.json` 未出现 billing/quota failure，但正式 live-10 `artifacts/runs/quality-live-10-20260527T155906Z/quality_report.json` 在 `sample-03` 命中 Volcengine `AccountOverdueError`，verdict 为 `provider_blocked_not_evaluable`；后续不得把它计为 trial-ready。
- timeline delete/restore、render attempt delete/restore、rollback、Timeline Spec schema/import validation、first-class clip asset lineage 后端基础、stable `clip_id` rework API、operator 资产审计读视图、基于已有 media asset 的 rework 控制、provider-backed clip video rework task queue、operator 入口、success lineage、rework 后自动 render queue、legacy 收敛和 10 条本地 2D 卡通样片验证已落地。
- 当前结论：主链工程闭环可演示；字幕已能从 Timeline subtitle track 烧进最终成片，source episode audio 或 per-dialogue clip audio 已能替换/按 Timeline timing 混成最终音轨；大规模 provider-backed 内容生产成本、稳定性、角色一致性和内容质量仍需要单独按真实预算复测。

## 状态概览

- P0：新系列使用 `Story 合同 → 小说版本 → 分集改编计划 → Episode → Script`
  链路；历史 Story、单条视频和 Script 后 Timeline 主链保持兼容。设计真源见
  `docs/design/story-novel-episode-script.md`，执行计划见
  `docs/exec-plans/active/story-novel-adaptation-chain.md`。无付费浏览器验收见
  `artifacts/runs/story-novel-v1-20260722T170000/summary.json`。
- P0（进行中）：把长篇小说升级为经用户确认的 `story_seed_v2` 结构化章节大纲，
  并把平台长度预设、自定义默认范围和逐章覆盖收归 Novel Revision；章节列表唯一决定
  章数，`generation_plan` v4 自动汇总 min/target/max。StorySeed service 已兼容
  endpoint-dumped dict 并重新做 schema 校验；异步结构化任务使用 Story 已配置模型，
  未配置时固定使用 DeepSeek 默认。设计真源见
  `docs/design/story-novel-episode-script.md`，执行计划见
  `docs/exec-plans/active/structured-outline-platform-lengths.md`。
- P0（已完成基线）：长篇小说已支持 StorySeed 文字大纲动态规划、单任务逐章
  3000–5000 字符生成；
  每章 checkpoint 后抽取 facts/角色记忆并作为修订版内 Canon。实现计划见
  `docs/exec-plans/completed/outline-driven-longform-novel.md`。DeepSeek V4
  Flash 真实验收已生成 48 章/198691 字符，断点恢复、提取覆盖、浏览器路径和
  GPT-5.6 全局审读证据见
  `artifacts/runs/story-novel-longform-real-20260723/`；该样本文本因 65 个
  blocking 连续性问题保持 draft，未提升 Story Canon。该统一长度门禁样本不能替代
  新计划的平台规格、逐章覆盖、双 Revision 隔离和无 blocker 审批验收。
- P0（进行中）：在现有长篇链路上增加生成前唯一 Canon、实际正文 typed state
  gate、人工确认 Canon 修复、最早失效章续写和分层质量报告；严格 Canon 使用
  `gate_version=1` 和 milestone typed outcomes，并在 chapter 0、plan replay 和
  actual body 三层拦截 future outcomes。设计真源见
  `docs/design/story-novel-episode-script.md` 与
  `docs/design/narrative-memory-and-dramatic-state.md`，执行计划见
  `docs/exec-plans/active/canon-gated-longform-quality-loop.md`。
- P0（进行中）：新长篇 Revision 升级为章前规划质量 v3。世界事件和人物记忆只供
  `chapter_brief` 规划，正文只读当前 brief/可见 Canon，服务端 expected delta 与
  sentence proof 审计决定状态和 Narrative 落账；三阶段模型策略、局部 block 返修、
  evidence-only Resume 与 v3-only 下游门禁已进入自动验证。章前 brief 现可把既有
  资源、义务、耗时、因果和关系约束提炼为来源绑定的 continuity watchpoints；正文
  无需复述，只有实际矛盾才由审计阻断。执行计划见
  `docs/exec-plans/active/story-novel-planning-quality-v3.md`。
- P0（进行中）：新建 V5 题材无关一致性内核。每个 Story 自动冻结动态 Schema、
  初始事实图和因果图；正文改为整章连续生成，再做证据绑定的 claim 校验、最小句段
  返修和一次整章重写。V2-V4 保持原样，不新增数据库。设计与验收见
  `docs/design/story-novel-generic-consistency-v5.md` 和
  `docs/exec-plans/active/story-novel-generic-consistency-v5.md`。
- P0：无限画布已有交互、保存恢复、动态节点、类型化端口与边、按图输入解析、
  Run Node、Run Downstream、stale descendants、故事板/视频候选评审和显式
  `timeline.place` 回填。当前缺口是 clip-storyboard v2 的当前环境
  provider-backed 整链复验。
  设计真源见
  `docs/design/production-canvas.md`。
- P0：Timeline Spec v1 文档、DB/API foundation、`audio_timeline.beats` 导入桥、Timeline readiness 优先级、默认 storyboard support 生成源、dry-run backfill、versioned render/export 回写、delete/rollback、schema/import 校验、clip asset lineage 后端基础和 stable `clip_id` rework API 已落地。
- P0：把对白音轨、beats、占位分镜、渲染导出收成一条可重渲主链。
- P0：优先清理会阻断这条主链的 legacy 和稳定性问题。
- P1：provider-backed video rework task queue 已有后端链路、operator 入口和成功后自动 final render 编排；legacy 稳定性风险已收敛。
- P1：clip-scoped storyboard 支持选中 video clip 内生成 2/4/6/9 格参考 sheet；
  默认根据结构化动作节点和片段时长自动定格数，并通过
  `clip_storyboard_sheet` 按从左到右、从上到下的完整时序驱动该 clip rework。
  `clip_storyboard_panel` 和 `storyboard_grid_panel` 仅保留 legacy read path。
- P2：已用一个窄垂类连续生产 10 条 30 秒本地 2D 卡通样片，记录成本、耗时、失败点和人工修正次数。

## P0: Structured Outline And Platform Lengths

:link: `docs/exec-plans/active/structured-outline-platform-lengths.md`

Owner：当前小说生成链路实现流。状态：代码与阶段性 UI 证据已落地，完整验收未完成。

- [x] StorySeed v2、结构化章节编辑、确认与失效边界、平台长度预设/自定义范围、
      逐章覆盖、generation plan v4 和 Revision API/UI 已实现。
- [x] StorySeed service 接受 endpoint dump dictionary 后重新 schema validate；
      结构化任务沿用 Story model，未配置时使用
      `deepseek:<DEEPSEEK_DEFAULT_MODEL>`。
- [x] 最新 StorySeed/Canon/plan/body/resume 定向回归组通过 39 tests。
- [x] Chrome extension fallback 的真实 UI 已确认 Story
      `702dcae4a23c4533ae11f0d2e2a69eda` 的 48 章 StorySeed v2，并创建
      standard-serial Revision `53dee6c31d8d4f0eada05bb0e45eb0b3`；Chrome
      DevTools `127.0.0.1:9222/json/version` 为 HTTP Not Found，不能宣称 DevTools
      验证。
- [ ] 完成逐章 override、两个不同配置 Revision 的隔离、完整 console/network 和
      end-to-end 生成浏览器证据。
- [ ] 完成 profile override 的真实长篇、当前 Revision-only Canon promotion 和
      blocker-free approval 验收。

## P0: Canon-gated Long-form Quality

:link: `docs/exec-plans/active/canon-gated-longform-quality-loop.md`

Owner：当前小说生成链路实现流。状态：进行中。

- [x] 拆分 Canon 编译、章节合同、实际正文 state extraction/gate、v3 ledger、
      v3 continuity 和 Canon edit 服务，避免扩张现有热点文件。
- [x] Canon `gate_version=1`、milestone typed outcomes、chapter-0/plan
      replay/actual-body 三层 future-outcome gate 和 knowledge-grant-only 规则已落地。
- [x] 失败/旧 gate/Canon hash 不匹配的规划 checkpoint 不复用；只有 hash-valid
      gated Canon 可用于章节规划返修，失败章节计划不能复用。
- [x] 新增 Canon 乐观锁编辑、状态进度、质量指标和修复组 UI。
- [x] 最新 milestone/outcome/plan/body/resume、StorySeed boundary/model 定向
      测试通过（39 passed）。
- [ ] 完成剩余 API/审批/失效边界覆盖与 frontend focused tests。
- [ ] 完成 backend quick/full、frontend lint/test、repo docs/contracts、
      pre-commit 和生产镜像构建。
- [x] Chrome DevTools 9222 不可用的原因已记录，并通过 Chrome extension fallback
      使用真实 Story UI 完成 v2 确认、Revision 创建和任务启动阶段。
- [ ] 完成 gate failure、Canon repair、range resume、continuity、approval 的后续
      UI 与 console/network 证据。
- [ ] 用全新 48 章 StorySeed 完成真实模型生成、至少一次断点恢复和 GPT-5.6
      分批/全书审读；七项确定性指标必须为零，未达到 75/100 或仍有 blocker 时
      不得审批。

当前阶段证据：Story `702dcae4a23c4533ae11f0d2e2a69eda`、Revision
`53dee6c31d8d4f0eada05bb0e45eb0b3`、任务 `#6513`–`#6519` 和 invocation
`#372`–`#384`。其中 `#6519` 仍在 `planning/chapters`，正文为 0/48；
provider invocation succeeded 不等于确定性规划或小说验收通过。验收仍以 active exec
plan 和 `artifacts/runs/story-novel-canon-quality-real-<timestamp>/` 为准；不得用
旧 66/100 样本、阶段性 provider 调用或人工接受理由代替。

## P0: Chapter-planning Novel Quality v3

:link: `docs/exec-plans/active/story-novel-planning-quality-v3.md`

Owner：小说生成质量链路。状态：v3 代码与 focused tests 已落地，完整仓库和真实
48 章验收未完成。

- [x] StorySeed 结构化任务支持显式章节数与规划模型；冻结结构仍是唯一章数来源。
- [x] 超过 32 章的 StorySeed 使用“分卷成长规划 + 每批最多 32 章细化”的有界链路；
      例如 800×约 2500 字符形成约 200 万字目标，不增加总字数字段或应用级章数上限。
- [x] 全书成长拆为认知、能力、资源、活动/时间尺度四条可选软曲线；只进入分卷规划
      与最终吸引力审读，不作为逐章升级 KPI，允许蓄势、失败和有代价的回撤。
- [x] Revision 冻结 planning/prose/audit 三阶段模型策略并兼容旧 `model`。
- [x] Event/Memory 只进入章前规划；正文 prompt 不含原始候选、未来目录、evidence
      规则或 expected/state delta；正文仅额外读取经过滤的当前章事件、当前可见
      人物介绍、动机、状态和关系，不读未来人物或关系进展。
- [x] V3 system、结构化大纲及修复、Canon、伏笔调度、批次/完整合同、brief、正文、
      审计/返修与连续性检查全部接入统一 PromptManager；新 plan 冻结 policy v9，
      invocation/ledger 保存 user rendered hash 和 system fingerprint；截断调用同样
      落账，模板变更不会在 Resume 时静默污染旧证据链。
- [x] 章节 brief、正文 blocks、服务端 expected delta、stable sentence spans、proof
      audit、future guard 与确定性 Narrative 落账已接入 v3/v4 checkpoint。
- [x] 正文/ledger 原子 checkpoint、局部 block 返修、candidate-only 与 evidence-only
      Resume、完整 invocation/hash 审批门禁和 canonical-v3 下游门禁已覆盖 focused tests。
- [x] Canon 主要实体可提前规划后依次登场；当前章确需新增的持久人物、地点、组织、
      物件或概念以稳定 Revision-local ID 加入世界，绑定当前事件/初始状态/首次出现章，
      门禁失败不落账且未来章节不得提前引用。
- [x] 数百章上下文只保留当前引用及当前状态直接依赖；历史 Event/Memory 继续走预算
      排序，避免所有已登场实体永久堆进 32K 硬上下文。
- [x] 全局章节规划改为“模型叙事 effect + 服务端状态编译”：持久/场景地点分层、
      全量结构错误向量、字段级 plan patch、复杂度自适应批次，以及 missing/unsupported
      effect 双向语义审计；正文截断可保留完整 blocks 后只续缺失块。
- [x] 每个 required event 冻结 action/time/actor/effort/timeline/knowledge 执行合同；
      仅 Canon、状态、时间、知识和显式世界规则的直接矛盾硬阻断，写实程度、劳动略快、
      戏剧化、节奏和文风仅作网文编辑建议。V3 不再要求逐字日期或独立 timeline/
      milestone/thread proof；日期、未来实体、世界规则字符串只选择审计候选，当前状态与
      相关未来状态边界仅进入 audit。商业网文默认长度为 2000–3000，章前 brief
      使用 4–6 个大 beat；六章窗口输出冲突、爽点、关系、重复和钩子的非阻断读者信号。
      所有 `story_novel_*` 运行模板及动态拼装模块均通过题材中性扫描；Story Novel +
      StorySeed 单测 867 passed、1 skipped。
- [x] 前端支持三个模型选择器、任务冻结、六阶段进度以及逐章 calls/tokens/latency/
      failed blocks。
- [x] 商业网文/超长大纲前端 focused 10 passed，lint 0 errors；全量前端基线为
      485 passed / 9 个无关 ProductionCanvas failures；webpack 生产构建通过。
- [ ] 跑完最终 Story Novel unit、backend quick/full、frontend lint/test/build、repo
      docs/contracts、pre-commit 与生产镜像。
- [ ] 使用 Docker dev Compose、真实 API/MySQL 与付费模型创建新 v3 Revision；48 章
      中至少两章 ready 后正式 cancel，再 Resume 到 48/48 并证明旧正文/hash 不变。
- [ ] 用 GPT-5.6 完成八批六章审读和一次全书综合；达到 75/100、结构/人物/世界观
      各至少 7/10 且无 blocking 后，才审批、提升 canonical 并核验下游/旧版本隔离。

## P0: Frozen-snapshot Long-form Quality v4

:link: `docs/exec-plans/active/story-novel-frozen-snapshot-v4.md`

Owner：小说生成链路。状态：实现中；v3 真实失败作为输入/验证快照漂移证据保留，
不得以证据优先级补丁代替架构修复。

- [ ] 新 Revision 使用 `story_novel_generation_plan.v4`、
      `story_novel_continuity.v5` 和 provider 调用前持久化的 immutable
      `planner_snapshot`；parser/repair/Resume 不得重新查询并重建上下文。
- [ ] Series Bible/Roadmap 支持核心人物路线、分卷角色槽、动态实体提案、题材自定义
      scope taxonomy、包含层级与跨节点连接；未来卷只保存软目标和不可撤销承诺。
- [ ] Event/Memory 只进入章前规划；Chapter Intent 不输出业务 ID/from/to/evidence，
      服务器编译唯一合同和 expected delta，正文仅接收当前可见人物/关系/事件/世界。
- [ ] 完成 800 章结构压力、快照确定性、未来隔离、动态实体回滚、语义时间、局部返修、
      Cancel/Resume hash 和 v2/v3 兼容回归。
- [ ] 完成 backend/frontend/contracts/pre-commit/镜像/真实浏览器；再通过正式 UI/API、
      MySQL 和付费模型完成新 48 章、Cancel/Resume、GPT-5.6 审读、Word 导出与审批。

真实验收状态（2026-08-01）：Task `6948` 已 fail-closed；前 24 章 ready，第 25 章因
长度门禁失败，未完成 48/48。对前 20 章的独立审读约为 58/100，并发现第 13 章在
第 16–18 章权限建立前使用水权的跨章授权漏洞。当前 Revision 不得审批或提升
Canonical；本轮提交仅保存实现与失败证据，后续应先修复跨章语义授权和返修可靠性，
再决定是否启动新的付费验收。

## P0: Generic Consistency And Readability V5

:link: `docs/exec-plans/active/story-novel-generic-consistency-v5.md`

Owner：小说生成链路。状态：实现已落地，灰度/付费验收未完成；默认版本保持 V4，
V5 只在内部开关启用后用于新 Revision。

- [x] 设计文档、active exec plan 和任务板边界已建立。
- [x] 题材无关 Schema、事实图、事件图、Perspective、Evidence、Obligation 内核及
      仓库依赖检查落地。
- [x] V5 自动编译/冻结、全书模拟、整章正文、claim 抽取、可读性门禁、句段返修、
      整章重写和 continuity v6 checkpoint 落地。
- [x] V5 审批/下游门禁、Narrative 投影和只读一致性 UI 落地。
- [x] 完成 V5 聚焦测试、文档/契约、前端 lint/build、本地非推送生产镜像和
      Playwright 页面证据。
- [ ] 清理或豁免仓库既有的 backend `story_parser`、whole-repo Ruff 与 Production
      Canvas 测试失败后，补齐全仓绿灯。
- [ ] 获得明确付费授权后完成多题材 6 章小样、V4/V5 盲测、provider-backed
      返修/恢复浏览器路径与全新 48 章 GPT-5.6 验收；通过前不得切换默认版本。

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
- 当前真实 API 的 `Episode -> Timeline -> Render -> Export` 证据已通过；legacy bridge 证据使用 storyboard 视频资产迁移桥，provider-backed 证据已证明 Timeline seed 先于生图/生视频创建且包含 dialogue/video/subtitle tracks。Timeline render 已能烧入 subtitle track，也能用 Timeline source audio 替换最终音轨，或把 per-dialogue clip audio 按 Timeline timing 混成最终音轨；clip asset lineage 后端基础、stable `clip_id` rework API、operator 资产审计读视图、基于已有 media asset 的 rework 控制、provider-backed video rework operator 入口、success lineage 和 rework-triggered final render 编排已补齐。

### 任务（功能→后端→验证）

- [x] 将当前未提交改动拆成可审查的提交边界并完成对应 ledger。
- [x] 补跑真实 `Episode -> Timeline -> Render -> Export`，证据落到 `artifacts/runs/<run_id>/`。
- [x] 补齐 timeline delete/rollback。
- [x] 为 Timeline Spec 增加 schema 校验、导入校验和权限校验。
- [x] 补 first-class clip asset lineage 后端基础：源音频、storyboard 视频和 render 输出按 `clip_id` 关联。
- [x] 补更完整的导出幂等测试，并和 rework 操作联动。

## P0: Production Canvas Vertical Slice

:link: `docs/design/production-canvas.md`

当前阻塞：

- 类型化端口、边、输入映射、Ready 评估、Run Downstream 和 stale descendants
  已接入真实请求。
- 故事板/视频候选预览、历史恢复、人工选用、拒绝原因和下游 stale 传播已接入
  持久化资产与真实画布请求。
- approved video 已能通过独立 `timeline.place` 节点写入 stable `clip_id` 和当前
  Timeline version，并回写新版本与 media lineage；Phase 1-3 主链不再阻塞。
- 大规模画布的性能预算、视口虚拟化和规模回归证据已经补齐；发布前仍需在
  当前环境做一次 provider-backed 整链集中复验。
- 新建 v2 画布按 clip 时长自动生成 2/4/6/9 格完整故事板，并用
  `clip_storyboard_sheet` 驱动视频；旧 v1 图片候选首帧行为只保留给历史 Run。
- 已有 Timeline 的 assembly checkpoint 会直接从稳定 `video` clip 重建分镜支撑
  映射，不再因重复调用 provider 规划而阻断视频候选执行。

### 任务（可执行图→候选评审→Timeline）

- [x] 定义并持久化版本化节点端口与类型化边；后端校验兼容类型、重复边、
      自环、环路和恢复数据。
- [x] 让后端按图依赖计算 Ready、Run Node 和 Run Downstream；边变化必须改变
      真实 Skill 请求输入。
- [x] 定义、边或 selected output 变化时计算 stale descendants，并阻止过期结果
      被静默当作当前输入继续执行。
- [x] 故事板候选节点展示真实持久化资产、生成历史和人工选用状态，并输出
      `approved_storyboard`；格数按 stable clip 的时长和动作结构自动选择
      2/4/6/9。
- [x] 故事板和视频候选支持显式拒绝、可选拒绝原因、评审人和时间持久化；拒绝
      当前选用项会清空输出并将下游标记为 stale，恢复 Run ID 后评审状态一致。
- [x] 视频候选节点通过
      `approved_storyboard -> approved_storyboard` 消费整张故事板，使用
      `reference_mode=clip_storyboard_sheet`；新 v2 图不包含 `start_frame` 或
      `end_frame` binding。
- [x] approved video 通过独立 `timeline.place` 节点写入 stable `clip_id` 和当前
      Timeline version，回写新 Timeline version 与 media lineage；上游选用变化时
      标记下游 stale，不得静默覆盖 Timeline。
- [x] 用真实浏览器完成 v2 结构与候选交互的非付费确定性回归；证据见
      `artifacts/runs/canvas-v2-storyboard-20260716T1320Z/canvas_storyboard_e2e.json`。
      Chrome DevTools transport 超时后按政策使用 Playwright fallback；结果包含
      Phase 9 合并前的 10 个 clip-storyboard 节点、11 条唯一 typed edges、0 个
      首帧/尾帧 binding、2/4/6/9 格提示、独立 `timeline.place`、0 page error 和
      0 API failure。生成接口被拦截，
      未冒充 provider-backed 验收。
- [ ] 在当前环境完成 v2 provider-backed 全链：真实故事板生成/选用、视频请求中的
      `reference_mode=clip_storyboard_sheet`、视频生成/选用、显式
      `timeline.place` 和 Timeline 资产 lineage 断言，证据落到
      `artifacts/runs/<run_id>/`。
- [x] 旧 v1 provider-backed 图片候选→选图→视频候选→选片→Timeline 回填已完成
      当前环境集中验证。Run
      `9a4bbfdb95f846e4be216beb1b09ad88` 使用图片候选 `#442`、MiniMax 视频
      候选 `#443` 和 Task `6325`，将 stable clip
      `video_scene_90_beat_3991_001` 从 Timeline `69` v5 显式回填到 v6；证据见
      `artifacts/runs/9a4bbfdb95f846e4be216beb1b09ad88/canvas-provider-chain.json`。

退出标准：操作员不复制 URL 或业务 ID，即可在画布中完成一个真实镜头的
故事板生成、人工选用整张故事板、视频生成、人工选片和显式 Timeline 回填；
刷新并通过 Run ID 恢复后，图定义、选用状态、执行证据和 Timeline 绑定保持一致。

### Production Canvas Phase 3（生产组织与恢复）

- [x] 增加端口直接拖拽连线和空白画布兼容节点发现。
- [x] 将原始后端输出和复用目标收纳到显式高级诊断视图。
- [x] 增加节点搜索以及场景、节点类型、状态、负责人和 stale 筛选。
- [x] 增加小地图和跳转到选中节点。
- [x] 增加多选、组移动、对齐、分布和生产节点复制。
- [x] 增加场景/集分区及其持久化定义。
- [x] 增加图定义变更的撤销和重做。
- [x] 补齐 Run Ready、Resume、Cancel 和 original/current definition retry。

### Production Canvas Phase 4（协作、复用与规模化）

- [x] 增加基于既有图片/视频候选的再生成与分支，复用真实媒体 worker，并把
      parent candidate、分支 Task 和指令 lineage 持久化到生成资产；恢复 Run ID
      后保持可见且不静默替换当前选用项。
- [x] 增加节点、候选、边和分区评论，以及 Viewer、Commenter、Editor、Approver
      权限与可审计活动历史。
- [x] 增加不暴露 provider 实现图的领域模板和可复用子流程。
- [x] 定义大规模画布性能预算，接入视口虚拟化和规模回归证据。

### Production Canvas Phase 5（领域实体层级）

- [x] 完成 `IP / 环境 / 故事 / 剧集 / 分镜 / 视频` 六列业务实体视图；原始
      无 Run 首屏全量 IP 行为已由 Phase 7 的 prompt-first 入口替代，Run deep link
      仍直接打开现有执行 DAG。
- [x] 复用现有 API 渐进加载真实
      `IP -> Story -> Episode -> Timeline clip -> current-version asset` 主链，并把 IP
      环境明确展示为可用资源/引用关系，不伪造 `Environment -> Story` 所有权。
- [x] 增加固定列布局、展开/折叠与已加载后代数量、语义边标签、画布与大纲同步
      定位；层级状态不得进入 Run saved state 或执行边校验。
- [x] 覆盖关系真相、稳定 `clip_id`、同版本视频 ready/generating/missing、视图切换
      和 Run deep-link 回归；Run action、候选审核与候选加载的迟到响应按 Run
      identity/epoch 丢弃，不能覆盖新路由恢复的画布。真实浏览器证据见
      `artifacts/runs/canvas-domain-hierarchy-20260715/`。Chrome DevTools 传输返回
      HTTP 404，验收明确使用 Playwright fallback 且未冒充 Chrome 验证。

### Production Canvas Phase 6（一句话生成与业务层级闭环）

- [x] 将 Plan/Execute、Run 持久化、Task 结果和层级选择统一到
      `IP / Environment / Story / Episode / Script / Timeline / version /
stable clip / Task` 上下文；旧 `agent_run.result_ref` 与结果路径继续兼容。
- [x] 一句话规划先校验显式业务 ID 和 lineage，再按可访问 Story 标题/标签及明确
      `第 N 集` 做保守解析；歧义时不猜、不隐式创建 Story/Episode。
- [x] 生成任务完成后把 Script/Timeline/clip 回写执行节点和 Board revision；业务
      层级自动刷新、逐级展开并定位最深的真实节点，旧 revision 不得覆盖新结果。
- [x] Run/Task/前端部分上下文按 lineage 合并：上游实体变化时清除未随新结果提供的
      旧后代；Plan、Execute、Task 与 Render 的迟到响应按 Run/operation identity
      丢弃，不能把旧 Run 的节点或上下文写入新画布。
- [x] 层级节点反向写回完整规划上下文；同 IP 内保留已选 Environment，但不把它
      伪装成 Story 父实体。有 IP 时 Environment 必须进入真实关联资源池；prompt
      可明确复用或创建并建立真实关联，但显式冲突 ID 必须拒绝。图片/视频审核和
      Timeline 回填仍保持人工显式门槛。
- [x] 当前环境真实浏览器验收：一句话首先解析到 Story `61` / Episode `174`；
      选择真实分镜后，下一次 `/plan` 和 Execute 请求携带 Script `144`、Timeline
      `70` v6 与 stable clip `video_scene_584_beat_4176_001`，层级自动定位到视频
      资产 `#353`。Task `6357` 的 `result_context` 可完整恢复九字段上下文；干净
      reload 无 console error 或失败 API。证据见
      `artifacts/runs/canvas-one-sentence-hierarchy-closure-20260715/`。Chrome DevTools
      传输在 `/json/version` 返回 HTTP 404，因此按政策使用 Playwright fallback；
      最终 Execute 被显式 stub，未产生 provider 费用，Plan、Run、Task 与层级读取
      均为真实请求。

### Production Canvas Phase 7（Prompt-first 资产选择与创建）

- [x] 新建 `/canvas` 默认进入执行 prompt，用户输入前不请求或展示账号资产列表。
- [x] prompt 优先复用同名可访问 IP/Environment；明确缺失时只创建最小资产，并把
      Environment 持久化到 IP 的真实资源池关联。
- [x] 歧义 prompt 不猜测、不创建 Story/Episode；显式不兼容业务 ID 直接拒绝，
      校验失败不得遗留新资产。
- [x] 业务层级只精确加载本次解析出的 IP/Environment/Story/Episode/Timeline
      clip/video 分支，不再预取前 100 个 IP 或 Story 根节点。
- [x] 执行图明确标记资产是“已选择/复用”还是“已创建”，方便 provider 调用前复核。

### Production Canvas Phase 8（受约束自主 Planner）

- [x] Planner 根据生产目标和已解析业务上下文自主选择最小 Skill 子集与依赖，不再由
      前端固定拼装完整执行链。
- [x] 后端将提案编译为白名单类型化 DAG，并复用 Graph v2 校验未知 Skill、端口类型、
      重复绑定、缺失前置和环路；模型不得直接调用 worker。
- [x] 结构化提案最多修复一次；provider 或可行性校验失败时回退确定性完整方案，并
      持久化 planner mode、provider/model、修复次数、错误和回退原因。
- [x] Run 恢复必须保留 Planner 选择的节点子集和动态边；前端创建与无 saved state
      恢复均消费服务端返回的类型化边。
- [x] 补齐自主方案、修复成功、确定性回退、动态边创建/恢复的后端与前端回归，并完成
      当前环境真实浏览器验证。
- [x] 将新建画布的规范图切换为 Brief、Content Planning、Assets、Script、
      Timeline、Storyboard Candidates、Video Candidates、Timeline Place、Render、
      Export 和 Report 十一个 Skill；旧 v1 Skill 和首帧端口只用于历史 Run 恢复。

### Production Canvas Phase 9（结构化生产上下文与内容规划）

- [x] 将 Skill 名称降为展示/路由元数据，建立
      `brief.compose -> content.plan -> asset.select -> script.generate`
      类型化合同；下游统一消费版本化 `production_context.v1`，不再各自只解析原始
      prompt。
- [x] Production Brief 结构化保存原始目标、创意意图、时长/集数/画幅/分辨率/FPS、
      视觉风格、模型请求与选用、资产策略、冲突证据和必须回答的问题；明确 prompt
      的本次生产规格优先于历史默认值。
- [x] 意图理解改为模型优先：上下文模型一次性输出 schema 校验后的 Brief/Content
      Plan；删除角色、环境、模型、风格和目标集数的固定词表/正则解析以及模型结果
      反向覆盖。fallback 只保留原始 prompt 和显式参数，不再猜名称。
- [x] Content Planning Skill 将一句话扩展为 premise、主冲突、角色弧、可复用场景、
      跨集持续机制、逐集合同、连续性规则和未来线索；结合现有 IP/Environment/
      Story/Episode 判断复用、歧义待选或缺失后创建。
- [x] 对多 Story/多资产匹配、系列缺少主角、请求模型不可用、仅复用策略下资产缺失
      等关键歧义先反问；回答进入同一 Brief 并重新规划，不允许系统擅自猜测或重复
      创建业务实体。
- [x] Script Skill 将完整 Production Context 编译进现有 production script worker；
      删除 AP/张总/小陈/陈默/撤单/篡改固定职场模板注入和固定短语分数校准，质量修复
      只能从当前 prompt/provider 内容推导冲突、升级和兑现。
- [x] 前端支持生产规格、模型、风格、澄清答案和结构化上下文摘要；单条视频先规划，
      仅在必答澄清完成后由后端统一复用/创建兼容 Story/Episode，再自动执行
      `script.generate`。
- [x] 用 `episode_id=194`（实际 `episode_number=1`）和原始目标完成真实浏览器重跑，
      确认请求包含林妹妹、gpt-img-2、seedance 2.0、60 秒、3D 卡通、AI 落地与反转，
      且新剧本不再被固定职场模板替换。

### 单条视频快捷生产（Story 列表与 Production Canvas 共享）

- [x] 新增共享后端创建能力：只要求标题/描述、3 或 5 分钟、画幅与可选风格；IP 和
      Environment 均可不选，同时保留显式资产归属与资源池关系校验。
- [x] 内部创建一个带 `creation_mode=single_video` 的 Story/Episode 兼容结构，
      前端统一展示为 `视频项目 -> 主视频`，不要求用户先完成系列故事建模。
- [x] `/stories` 提供“创建单条视频”主入口，创建后直接跟踪现有剧本生成 Task 并进入
      Script/Timeline 工作区；系列故事入口继续保留。
- [x] `/canvas` 提供“单条视频 / 系列制作”模式切换；单条视频模式先解析结构化
      Brief/Content Plan，并在必答澄清完成后由后端统一复用或创建兼容项目，再只自动
      执行 `script.generate`，不得自动触发图片、视频或渲染费用。
- [x] 无 IP 的单条视频层级以真实 Story 为根；Run 节点和执行请求保留
      `planning_mode=single_video`，恢复后也不得重新按 prompt 猜测或创建资产。
- [x] 补齐后端 API/资产安全、前端入口/工作区、Canvas 编排与无 IP 层级回归，并通过
      lint、生产构建和真实浏览器验证。

## P1: Production Stability

:link: `docs/exec-plans/active/main-chain-commercial-readiness.md`

当前阻塞：

- 场景音轨、episode 音轨、beats、分镜占位已经收敛到 Timeline Spec 导入；legacy storyboard 视频迁移桥已可生成可渲染 video track，first-class clip asset 关联已有后端基础。
- 重新配音、重新切分、重新导出已有后端 replacement lineage API 挂在稳定 clip identity 上，operator 可以查看选中片段的源/输出/替换资产历史，也可以把已有 `media_asset_id` 记录为重做资产；backend 也能为选中 video clip 排 provider-backed rework task，并在视频任务成功后写回 `provider_rework` replacement lineage；operator 已接入 provider rework API，生成成功后会自动排一个带 rework 指纹的 final render job。
- 老 script compatibility wrapper 与旧 dialogue-audio facade 已下线；剩余主链旁边的稳定性风险集中在
  `ai_service_manager.py` 和 `script_agent.py`。

### 任务（功能→后端→验证）

- [x] GPT-img 多帧 active/replay 防重：请求指纹排除 worker 写入的 image/keyframe、
      compiled prompt、candidate lineage 和 checkpoint 输出但保留真实生成输入；成功帧
      记录同 Task checkpoint，同一 Celery Task 重放时在 dynamic prompt/provider 前
      过滤已完成帧，只处理缺失帧。两个 RED 分别证明 checkpoint 会改变 active 指纹、
      同 Task 会重复生成首帧；修复后图片 queue/worker 相邻链路 `18 passed`。
- [x] storyboard video 多帧提交按 child 逐帧 checkpoint provider task ID；后续帧
      transport/DB 异常不会回滚已付费提交，未知提交异常会形成 failed child 并参与
      parent 终态汇总；同一 parent 重放只提交缺失 frame，parent 只有在显式目标帧均有
      child 后才允许完成。活动请求指纹只采集视频 worker 实际输入，排除 `video_url`、
      `video_generation` 等回填输出，避免兄弟帧完成时误建第二批 Seedance 任务。首轮
      RED 为 `3 failed`，恢复完整性补充 RED 为 `2 failed`；submission、polling、
      Timeline mapping 与 Production Canvas 扩展链路已通过。
- [x] 为 storyboard video parent queue 增加 active-request 幂等：按目标帧快照、
      已解析首帧、model/video options、Timeline rework mapping 与 canvas run scope
      生成版本化指纹；相同 pending/processing 请求复用同一 Task 且不重复派发，终态
      仍允许重试，Celery dispatch 失败会持久化为 failed。RED 为 `8 failed`，实现后
      新契约与相邻 Timeline mapping 为 `10 passed`。
- [x] storyboard image worker 对每个成功帧立即 checkpoint storyboard 与稳定 clip
      lineage；后续帧 provider 失败时保留已付费结果，只重试缺失帧，避免整批 36 帧在
      尾部失败后全部丢失。RED 先证明第 2 帧异常会丢掉第 1 帧，修复后相邻链路
      `12 passed`。
- [x] 为 storyboard image 自动排队增加 active-request 幂等：按 script、目标帧快照、
      model/prompt/reference/canvas scope 生成版本化指纹；相同 pending/processing task
      直接复用且不重复 dispatch，终态任务仍允许重试，Celery dispatch 失败必须把新
      task 标记为 failed，避免 orphan pending 与重复 provider 费用。
- [x] 收敛 legacy audio storyboard builder：`episode_timeline_beats.py` 与
      `storyboard_from_timeline.py` 为唯一实现，`timeline_processor.py` 仅保留薄兼容
      包装；移除会独立改变 Timeline/audio 时间窗的旧 duration resegmentation，并用
      source-contract 测试禁止应用层新增 legacy import；旧服务从 368 行降至 92 行，
      audio 相邻链路 `176 passed, 7 skipped`，backend quick `2460 passed`。
- [x] 完整 shot-plan 的重复 Timeline pipeline 直接复用当前版本，不再重复调用
      文本 provider 或产生无意义的 Timeline version；script `30` 的真实任务从
      Task `6327` 的 `147.2517s`、Timeline `69` v7，降到 Task `6328` 的
      `0.7638s`、仍为 v7。
- [x] 同一 Timeline version 的无素材 storyboard support 占位帧在非覆盖执行时
      直接复用，不再增加 legacy `storyboard_version`；Task `6331` 用时
      `0.5395s`，Timeline `69` 保持 v7，storyboard 保持 v8。
- [x] shot-plan 转 storyboard 时保留 video clip speaker，并从 plot、角色锚点和
      prompt 文本匹配已注册角色别名；script `30` 的只读重建探针把可绑定角色
      参考图的帧从 0/36 提升到 29/36，剩余 7 帧均为无明确角色的物体/环境镜头。
- [x] 图片自动排队按帧区分角色身份约束：角色/旧帧继续强制参考图，显式
      `characters: []` 的物体或环境镜头允许无角色参考生成，避免 7 个镜头永久跳过。
- [x] 同一 Timeline placeholder 复用时，以 reference-only 模式补齐缺失的角色/环境
      参考并按内容变化落库；保持 frame ID、人工参考、prompt 与 storyboard version，
      避免旧持久化帧绕过新 enrich 后继续被排图过滤；script `30` 只读探针确认
      Timeline `69` v7 的 29 个角色约束帧均有参考、7 个明确无角色帧可直接生成，
      `eligible=36`，且 36 个 frame ID / prompt 均未变化。
- [x] storyboard image worker 按稳定 `timeline_clip_id` 把生成图写入
      `timeline_clip_assets.storyboard_image`，视频任务从该 lineage 解析首帧，避免
      已生成支撑图无法进入 image-to-video 链路。
- [x] 文本 provider fallback 改为使用候选 provider 自有模型，并把 provider
      请求失败与成功响应的 JSON/schema repair 分开，避免余额、限流或上游错误
      被重复请求并伪装成 `missing json object`。
- [x] 支持基于稳定 `clip_id` 的 re-dub、re-cut、re-render 后端 replacement lineage API，不允许靠临时 frame index 追踪资产。
- [x] 在 Timeline operator 片段检查器展示选中 clip 的源资产、输出资产和 replacement history。
- [x] 在 Timeline operator 片段检查器提交已有 `media_asset_id` 作为 re-dub / re-cut / re-render replacement lineage。
- [x] 将选中 video clip 的 re-cut / re-render 接入 provider-backed video generation task queue，并在视频任务成功后回写 replacement lineage。
- [x] 将 operator rework 控制接入 provider-backed video generation API。
- [x] 将 provider rework 成功结果接入 render queue / export 自动编排。
- [x] 将首尾帧、分镜图、分镜视频都视为 clip asset，和 timeline clip 显式关联。
- [x] 继续拆分并下线老 script compatibility wrapper，让 timeline/audio/storyboard 主链不再依赖 legacy router。
  - [x] 已把 legacy router 和 audio/timeline pipeline endpoints 的任务标题 helper 收敛到
        `services/script/task_titles.py`，并清掉旧 router 中已无引用的
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
  - [x] 已把主 `/scripts` router 组装迁到 `api/v1/endpoints/scripts/__init__.py`，
        并删除老导入兼容 wrapper。
- [x] 拆分旧 dialogue-audio facade，至少分离 scene audio 生成、episode 拼接、beats 落库、timeline 占位转换。
  - [x] 已把 episode 拼接/写回迁到 `services/audio/episode_audio_builder.py`，并把 episode timeline beat 构造迁到 `services/audio/episode_timeline_beats.py`。
  - [x] 已把 scene beat 落库、scene audio metadata 写回和单场时长校验迁到 `services/audio/scene_audio_persistence.py`。
  - [x] 已把 timeline 占位转换迁到 `services/audio/storyboard_from_timeline.py`。
  - [x] 已把 duration-control 和 deprecated dialogue-audio endpoint 的 scene 音轨生成入口切到 `services/audio/scene_audio_generator.py`。
  - [x] 已把 duration-control 的逐场景生成循环迁到 `services/duration_controlled_scene_runner.py`，并清掉 touched endpoint 的直接 query。
  - [x] 已删除历史 dialogue-audio 兼容 facade，固定段落规划和文本清理兼容逻辑也已下线。
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

- 工程链路已用 10 条本地 2D 卡通样片证明可重复走通。
- 已固定 2D/3D 卡通样片验证范围、3 个复用角色和 10 条样片记录表：
  `docs/cartoon-sample-production-proof.md`。
- 已产出 10 条最终导出样片，并完成成本、失败点和人工修正指标记录。
- 真实 provider-backed production proof 当前是 `provider-blocked`，不是
  `trial-ready`：`quality-live-10-20260527T155906Z` 在 `sample-03` 收到
  Volcengine `AccountOverdueError` 后停止，避免继续付费样片。

### 任务（内容→生产→复盘）

- [x] 补齐 timeline operator 的选中 clip 资产审计读视图和已有资产 rework 控制。
- [x] 把 storyboard 调整为支持视图：查看占位、关键帧、镜头上下文，不再承担主编排职责。
- [x] 固定一个窄垂类和 2-3 个角色，限定 2D/3D 卡通验证风格。
- [x] 产出 10 条 30-60 秒竖屏样片。
- [x] 每条样片记录模型成本、生成耗时、失败点、人工修正次数和最终导出文件。
- [x] 将可复用的剧作规则、镜头结构、prompt 和资产选择沉淀回主链。

## 6-Week Exit Criteria

- [x] 至少 1 个 episode 可以从 audio-driven timeline 重建到最终导出。
- [x] re-dub / re-render 从 operator UI 到真实生成/导出都不会打断 stable `clip_id`。
- [x] 老 script compatibility wrapper 已删除，主要用户路径统一挂载在
      `api/v1/endpoints/scripts/__init__.py`。
- [x] storyboard 页面不再是系统主编排入口。
- [x] 真实 `Episode -> Timeline -> Render -> Export` 浏览器/API 证据通过。
- [x] 10 条窄垂类样片完成并记录生产指标。
