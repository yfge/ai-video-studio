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
- timeline delete/restore、render attempt delete/restore、rollback 已落地；下一步补更严格的 Timeline Spec schema/import validation。
- 在 10 条窄垂类样片通过前，不把主链标记为商业化可用。

## 状态概览

- P0：Timeline Spec v1 文档、DB/API foundation、`audio_timeline.beats` 导入桥、Timeline readiness 优先级、默认 storyboard support 生成源、dry-run backfill、versioned render/export 回写和 delete/rollback 已落地，下一步补更完整的 schema/import 校验。
- P0：把对白音轨、beats、占位分镜、渲染导出收成一条可重渲主链。
- P0：优先清理会阻断这条主链的 legacy 和稳定性问题。
- P1：补齐可生产的资产审计、clip lineage、re-dub/re-render 操作闭环。
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
- render/export 已能写回稳定的 timeline/versioned jobs；delete/rollback 已补齐，更严格的 schema/import 校验仍未补齐。
- 当前真实 API 的 `Episode -> Timeline -> Render -> Export` 证据已通过；该证据使用 legacy storyboard 视频资产迁移桥，后续仍需补 first-class clip asset lineage。

### 任务（功能→后端→验证）

- [x] 将当前未提交改动拆成可审查的提交边界并完成对应 ledger。
- [x] 补跑真实 `Episode -> Timeline -> Render -> Export`，证据落到 `artifacts/runs/<run_id>/`。
- [x] 补齐 timeline delete/rollback。
- [ ] 为 Timeline Spec 增加 schema 校验、导入校验、权限校验和更完整的导出幂等测试。

## P1: Production Stability

:link: `docs/exec-plans/active/main-chain-commercial-readiness.md`

当前阻塞：

- 场景音轨、episode 音轨、beats、分镜占位已经收敛到 Timeline Spec 导入；legacy storyboard 视频迁移桥已可生成可渲染 video track，first-class clip asset 关联仍未完成。
- 重新配音、重新切分、重新导出还没有统一挂在稳定 clip identity 上。
- `scripts_legacy.py`、`dialogue_audio_service.py`、`ai_service_manager.py` 仍是主链旁边的稳定性风险。

### 任务（功能→后端→验证）

- [ ] 支持基于稳定 `clip_id` 的 re-dub、re-cut、re-render，不允许靠临时 frame index 追踪资产。
- [ ] 将首尾帧、分镜图、分镜视频都视为 clip asset，和 timeline clip 显式关联。
- [ ] 继续拆分并下线 `scripts_legacy.py`，让 timeline/audio/storyboard 主链不再依赖 legacy router。
- [ ] 拆分 `dialogue_audio_service.py`，至少分离 scene audio 生成、episode 拼接、beats 落库、timeline 占位转换。
- [ ] 拆分 `ai_service_manager.py`，把 provider routing、fallback、model cache、request logging 收成独立模块。
- [ ] 修复 story fallback 测试漂移：统一 `ai_fallback` / `ai_fallback_invalid` 语义与断言。
- [ ] 修复 AI 初始化中的 `asyncio.run() cannot be called from a running event loop` 警告，避免 warm-cache 逻辑污染任务链。
- [ ] 收敛 step-by-step pipeline 的 deprecation 状态，防止 UI 和后端继续沿旧路径分叉。
- [ ] 拆分 `ai-pic-frontend/src/app/episodes/[id]/storyboard/page.tsx`，并将默认操作导向 timeline workspace。

## P2: Production Proof

:link: `docs/exec-plans/active/main-chain-commercial-readiness.md`

当前阻塞：

- 工程链路还没有用真实内容证明可重复生产。
- 还没有固定垂类、镜头模板、成本记录、失败点记录和人工修正指标。

### 任务（内容→生产→复盘）

- [ ] 补齐 timeline operator 的源音轨/源帧完整资产审计视图。
- [ ] 把 storyboard 调整为支持视图：查看占位、关键帧、镜头上下文，不再承担主编排职责。
- [ ] 固定一个窄垂类和 2-3 个角色，产出 10 条 30-60 秒竖屏样片。
- [ ] 每条样片记录模型成本、生成耗时、失败点、人工修正次数和最终导出文件。
- [ ] 将可复用的剧作规则、镜头结构、prompt 和资产选择沉淀回主链。

## 6-Week Exit Criteria

- [ ] 至少 1 个 episode 可以从 audio-driven timeline 重建到最终导出。
- [ ] re-dub / re-render 不会打断 stable `clip_id`。
- [ ] 不再有主要用户路径依赖 `scripts_legacy.py`。
- [ ] storyboard 页面不再是系统主编排入口。
- [x] 真实 `Episode -> Timeline -> Render -> Export` 浏览器/API 证据通过。
- [ ] 10 条窄垂类样片完成并记录生产指标。
