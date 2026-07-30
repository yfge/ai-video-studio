## User Prompt

长篇网文中的人物、地点、组织和世界范围应当既可提前规划又能依次登场；后续章节因剧情需要产生的持久人物或世界概念也应加入当前世界。认知、能力、资源、活动/时间尺度需要体现长期成长，但不得成为逐章硬性 KPI。目标规模约 200 万字，而不是 20 万字。

## Goals

- 让预规划主要实体按首次出现章逐步可见，并禁止提前泄露。
- 让当前章确需的新持久实体通过门禁后进入 Revision-local 世界与后续规划。
- 将四条成长曲线放在全书/分卷规划和最终吸引力审读，而非逐章升级模板。
- 支持数百章结构化大纲与约 200 万字符规模，不增加总字数字段或应用级上限。
- 保持 Event/Memory 仅进入章前规划、正文未来隔离、确定性状态门禁和旧版本兼容。

## Changes

- 新增稳定的 Revision-local 实体 ID、首次出现顺序校验和 world reveal index；章前 package 可绑定当前 required event 引入人物、地点、组织、物件或概念，状态门禁通过后才写入修订版世界。
- Canon 中提前规划的主要实体按结构化大纲第一次明确引用的位置逐章开放；未来章 ID 或名称在更早合同中出现会 fail closed。
- StorySeed 增加可选的 progression arcs 与 cognition/capability/resources/activity_and_time_scale 四条软曲线；失败、蓄势与有代价回撤明确为合法阶段形态。
- 超过 32 章时，结构化任务先生成固定分卷规划，再按每批最多 32 章细化；每次调用最高 16K token、一次修复、精确连续覆盖。800 章的默认 2,500 字符合同对应约 200 万字符。
- Canon 编译只读取压缩后的分卷规划，不再接收数百章完整明细；当前章 package 只读取所在分卷的软方向，不读取未来分卷事件、实体和伏笔文本。
- 前端超长大纲编辑器按分卷一次只渲染最多 32 个章节卡片，并保留结构化章节数及规划模型选择。
- 硬上下文改为当前章引用与当前状态直接依赖；历史实体只作为“是否已登场”的许可集合，不会全部进入 Prompt。未来关系和未来持有人仍保持隐藏。
- 全局连续性报告增加 progression 与 reader_appeal 评分；不适用曲线不扣分，逐章不检查升级数值。
- 独立 Prompt 审查提出的事件 actor 丢失和审计自由文本回灌风险已在当前 WIP 中确认有防护；章前 package 的 effect manifest、effect refs、稳定 ID 与预算均由服务端编译，模型不再自报 effect coverage。
- 更新小说、Narrative Memory 设计真源、v3 exec plan、任务板和文档索引。

## Validation

- 新增/相关后端 focused：37 passed；Prompt/结构拆分回归：26 passed。
- 用户确认四条成长曲线为正式边界：只做全书/分卷软方向和最终吸引力评价，硬合同只约束大纲已授权升级；蓄势、失败和有代价回撤均合法。
- Docker focused：规划/修复 24 passed，成长/题材中立/世界扩展/长上下文 19 passed；250 行兼容导出复核 17 passed。
- 完整 Story Novel + StorySeed unit 的产品逻辑诊断：867 passed, 1 skipped。容器 FastAPI 版本的 `HTTPException.__str__` 为空，原始运行有 49 条 `pytest.raises(..., match=...)` 展示层假失败；仅在测试进程把异常字符串映射到既有 `detail` 后全部通过，未修改生产异常或门禁。
- 前端大纲/章节数 focused：10 passed。
- 前端 lint：0 errors，3 个既有 warnings。
- 前端完整测试：485 passed，9 个既有 ProductionCanvas failures；失败均位于 canvas planning settings/自动执行，与小说改动路径无关。
- Next.js 默认 Turbopack 因 worktree 的外部 `node_modules` symlink 拒绝构建；同一源码使用 `next build --webpack` 完整通过 TypeScript、静态页与生产构建。
- `python run_tests.py quick` 未进入测试：当前 Python 3.13 环境下锁定的 `pydantic==2.5.0` 与 `langchain-core==0.2.43` 解析冲突；未修改依赖规避环境问题。
- 精确 30 个 Python 路径 black/isort checks：passed。
- 首轮 pre-commit 发现审批模块仍从旧 context 模块隐式再导入 prose input；已改为正式来源并保留兼容再导出，应用 import-safe，审批/执行边界 focused 39 passed。
- 精确 changed-path pre-commit（含 backend unit/services/scripts quick gate 与 frontend lint）、repo contracts、repo docs、`git diff --check`：passed。
- Docker 挂载只读核验：backend、Celery worker 与 frontend 均挂载当前 worktree；Redis `celery` 队列为 0，worker active/reserved/scheduled 均为空。MySQL 仍有一个 2026-07-22 的旧 `#6493` PENDING 记录，但没有 broker 消息，未被本轮重启领取。
- Chrome DevTools 按规则重连一次后仍为 `127.0.0.1:9222/json/version` HTTP 404；改用 Codex 内置浏览器 fallback，并明确不记为 Chrome 通过。
- 浏览器 fallback 路径：`http://localhost:8089/stories/56a749ffed0545c2981c853ae333aaf2#novel-workflow`。页面加载成功且已登录；真实 UI 显示章前规划、正文生成、状态审计三个模型选择器，当前值分别为 `deepseek:deepseek-v4-pro`、`codex:gpt-5.4`、`codex:gpt-5.4`。该 Story 是旧单层 48 章样本，只用于兼容显示检查，未作为 v9 分层规划验收。
- Celery worker 在空队列状态下重启并加载挂载源码，启动后正常 `ready`，未领取旧任务、未产生 provider 调用。
- 本地生产镜像验证明确设置 `BUILD_PUSH=false`，未推送远端。经典构建器停在 728MB 上下文打包，BuildKit 停在读取 `python:3.11-slim` 元数据；两次均主动取消，记录为 Docker 构建环境阻断而非源码通过。

## Next Steps

- 在 Docker Hub 元数据可用时补跑本地生产镜像；保留 ProductionCanvas、Python 3.13 quick 与当前 Docker 元数据阻断证据。
- 通过 Docker dev Compose、正式 UI/API、真实 MySQL 与付费模型创建新的 v9/v3 Revision，先以 48 章完成 cancel/Resume/hash 不变、连续性和 GPT-5.6 验收。
- 48 章样本通过后再执行数百章/约 200 万字符的低频容量验收；结构化分卷任务的跨任务部分进度恢复仍可作为后续可靠性增强，不影响当前有限失败的 fail-closed 语义。

## Linked Commits

- Pending.
