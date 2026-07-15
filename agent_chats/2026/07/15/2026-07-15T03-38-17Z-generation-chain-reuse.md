---
id: 2026-07-15T03-38-17Z-generation-chain-reuse
date: "2026-07-15T03:38:17Z"
participants:
  - user
  - codex
models:
  - gpt-5
tags:
  - generation-chain
  - deepseek
  - timeline
  - provider-fallback
  - runtime-evidence
related_paths:
  - ai-pic-backend/app/api/v1/endpoints/storyboard/image_task_processor.py
  - ai-pic-backend/app/repositories/storyboard_media_repository.py
  - ai-pic-backend/app/repositories/task_repository.py
  - ai-pic-backend/app/services/ai/structured_output.py
  - ai-pic-backend/app/services/ai_manager_text_generation.py
  - ai-pic-backend/app/services/audio/__init__.py
  - ai-pic-backend/app/services/audio/episode_timeline_beats.py
  - ai-pic-backend/app/services/audio/storyboard_from_timeline.py
  - ai-pic-backend/app/services/audio/storyboard_from_timeline_shot_plan.py
  - ai-pic-backend/app/services/audio/timeline_processor.py
  - ai-pic-backend/app/services/production_canvas/media_execution.py
  - ai-pic-backend/app/services/script/timeline_shot_plan_step.py
  - ai-pic-backend/app/services/script/timeline_storyboard_queue.py
  - ai-pic-backend/app/services/storyboard/storyboard_audio_context_enricher.py
  - ai-pic-backend/app/services/storyboard/storyboard_image_autogen.py
  - ai-pic-backend/app/services/storyboard/storyboard_image_queue_inputs.py
  - ai-pic-backend/app/services/storyboard/storyboard_image_task_dispatch.py
  - ai-pic-backend/app/services/storyboard/timeline_image_lineage.py
  - ai-pic-backend/app/services/timeline_clip_video_rework_queue_service.py
  - ai-pic-backend/app/services/timeline_clip_video_rework_images.py
  - ai-pic-backend/tests/test_timeline_clip_video_rework_storyboard_image_api.py
  - ai-pic-backend/tests/integration/test_production_canvas_media_api.py
  - ai-pic-backend/tests/unit/services/audio/test_episode_timeline_beats.py
  - ai-pic-backend/tests/unit/services/audio/test_storyboard_from_timeline_spec.py
  - ai-pic-backend/tests/unit/services/audio/test_timeline_processor_compatibility.py
  - ai-pic-backend/tests/unit/services/ai/test_structured_output.py
  - ai-pic-backend/tests/unit/services/script/test_timeline_shot_plan_step.py
  - ai-pic-backend/tests/unit/services/script/test_timeline_storyboard_queue.py
  - ai-pic-backend/tests/unit/services/storyboard/test_storyboard_audio_context_enricher.py
  - ai-pic-backend/tests/unit/services/storyboard/test_storyboard_image_queue_idempotency.py
  - ai-pic-backend/tests/unit/services/storyboard/test_storyboard_reference_context_hydration.py
  - ai-pic-backend/tests/unit/test_audio_timeline_storyboard.py
  - ai-pic-backend/tests/unit/test_ai_manager_text_generation.py
  - ai-pic-backend/tests/unit/test_storyboard_image_identity_free.py
  - ai-pic-backend/tests/unit/test_storyboard_image_task_checkpointing.py
  - ai-pic-backend/tests/unit/test_storyboard_image_task_image_gen_persistence.py
  - docs/exec-plans/active/timeline-main-chain-optimization.md
  - tasks.md
summary: Reuse complete Timeline shot plans, correct cross-provider text fallback, and preserve provider failures as provider errors with runtime evidence.
---

## User Prompt

进行全链路的生成优化；随后确认 DeepSeek 已经充值。继续要求恢复 Codex 凭证、验证
GPT-img-2 故事板质量，并用一个动作更复杂的镜头检验 2×2 宫格是否有清晰区别；随后
询问是否应让 LLM 自行决定故事板格数，并要求继续稳定整张故事板到视频的链路。

## Goals

- 用真实生成任务确认 DeepSeek 充值后的 provider 状态。
- 避免未要求覆盖时重复生成已有的完整 Timeline shot plan。
- 让文本 fallback 使用目标 provider 支持的模型，并保留真正的 provider 错误。
- 验证 Timeline 生成和已有完整媒体资产的最终导出路径。
- 将故事板固定为选中 Timeline video clip 内的多 Panel 宫格，并让各 Panel 的动作与
  景别在视觉上可区分，而不是退化成近似单帧。
- 让 LLM 负责输出结构化视觉动作节点，由后端确定性映射为 2/4/6/9 格，避免自由文本
  直接决定张数导致同一输入反复漂移。
- 让 Seedance 默认消费整张故事板的完整时序，而不是只读取单个 Panel。

## Changes

- Timeline pipeline 在所有 video clip 都有结构有效且与当前 Timeline 匹配的
  shot plan 时直接复用当前版本，不再重复调用文本模型。
- 非覆盖 pipeline 在现有无素材 storyboard support 已来自同一 Timeline ID/version
  时复用原占位帧；先从当前 Timeline clip 补齐旧帧缺失的 speaker/显式角色语义，
  再以 reference-only 模式补齐角色/环境参考，只在内容变化时落库，不改 prompt、
  frame ID、人工参考或 storyboard version。
- shot-plan storyboard 帧保留 Timeline video clip 的 speaker；角色上下文既消费显式
  characters，也从 plot、prompt 和 `character_anchor` 文本匹配已注册角色别名，
  让动作镜头继续绑定正确 Virtual IP 参考图而不是把外观描述误当成角色名。
- reference-only 重复 enrich 不再从已经编译过的 `prompt_description` / `ai_prompt`
  推断角色，避免“老拐的公寓厨房”这类环境描述把物体空镜误判成老拐出镜。
- 图片自动排队和 worker 使用同一逐帧身份约束：角色帧与未分类的历史帧仍要求
  参考图，Timeline 明确标记 `characters: []` 的物体/环境镜头允许无角色参考生成，
  避免非人物镜头被永久跳过。
- storyboard image worker 把成功生成的支撑图按稳定 `timeline_clip_id` 幂等写入
  `timeline_clip_assets.storyboard_image`；视频 rework 在 Timeline spec 没有内嵌
  首帧时解析当前或历史同 clip lineage，使支撑图真正进入 image-to-video 输入，
  且不改变 Timeline version。
- 文本 provider 选择优先识别请求模型所属 provider；切到 fallback provider 时，
  解析该 provider 自有的默认文本模型，而不是继续传递外部模型 ID。
- 结构化输出只修复 provider 成功但 JSON/schema 不合格的响应；余额不足、限流、
  上游异常等 provider 失败直接返回 `provider_error`，repair 请求自身发生 provider
  失败时也立即停止。
- 增加 provider fallback、provider failure 与完整 shot-plan 复用的单元测试，并在
  `tasks.md` 记录已验证的性能优化与错误语义。
- 片段故事板 Panel 现在保留完整 motion timeline 作为来源，但生成宫格时每格只输出
  自己的动作锚点；4 格分别使用建立空间、双人互动、道具细节和收束镜头的景别/构图，
  同时保留原 clip 的银幕方向与 blocking，提示词明确禁止近似重复构图。
- 收敛重复的 audio Timeline 构建实现：package 入口直接导出
  `episode_timeline_beats.py` / `storyboard_from_timeline.py` 的 canonical 函数，
  `timeline_processor.py` 从 368 行降为 92 行薄兼容包装器，不再自行构建、优化、
  resegment 或落库 storyboard；source-contract 测试禁止应用层重新导入 legacy 模块。
- storyboard image 自动排队按 user/script、目标帧快照、模型、提示词、参考图、
  canvas branch 和可选 run scope 计算 versioned SHA-256；完全相同的 pending/processing
  Task 直接复用且不再次派发，completed/failed/cancelled 仍可重试。Celery 派发异常会
  把刚创建的 Task 写为 failed，避免 orphan pending 和重复 provider 费用；Production
  Canvas 用 run_id 作为 scope，既隔离不同运行，也合并同一运行的重复提交。
- storyboard image worker 在每个成功帧后立即 checkpoint 累积 storyboard 状态、
  同步该帧的 stable clip lineage 并 commit；后续帧失败仍把父 Task 标为 failed，但
  已经付费成功的图片和 lineage 保留，可只重试缺失帧。
- clip storyboard 的 `panel_count` 改为可选：省略时根据去重后的结构化
  `motion_timeline` 和 clip 时长确定性选择 2/4/6/9 格；显式选择仍保持 operator
  控制并规范化到支持的布局。前端默认显示“智能（按动作节点）”。
- 新增 `clip_storyboard_sheet` 视频参考模式：把整张 sheet 放在参考图首位，按从左到右、
  从上到下写入全部 Panel 的动作时间锚点，固定 clip 目标时长和 Timeline 画幅，并禁止
  成片出现宫格边框、分屏、Panel 编号或文字。旧 `clip_storyboard_panel` 仅保留兼容。
- 视频 readiness 将完整故事板和首尾帧视为两条可替代参考路径；后端最多保留 9 张
  视频参考图，覆盖一张 sheet 加角色/IP/环境图。为满足仓库行数契约，任务 payload
  构建器和前端参考源状态分别拆到独立模块。

## Validation

1. Runtime provider and Timeline generation:

- 充值前 Task `6326` 的持久化错误看起来是 `missing json object`；Celery 日志却显示
  DeepSeek 连续三次返回 `HTTP/1.1 402 Payment Required` 和
  `Insufficient Balance`。初始的 JSON 修复判断与运行时证据冲突，因此按 provider
  failure 与 structured-output validation 两层拆开处理。
- 用户确认充值后，`episode_timeline_generation` Run ID
  `generation-optimization-deepseek-funded-20260715T032700Z` 通过：Task `6327`
  调用 DeepSeek 完成 5 个 shot-plan batch，Celery 用时 `147.251748s`，Timeline
  `69` 更新到 v7。
- 重启 backend/worker 载入修改后，同一 script `30`、同一非覆盖参数的 Run ID
  `generation-optimization-reuse-20260715T033200Z` 通过：Task `6328` 用时
  `0.763842s`，Timeline 保持 `69` v7，Celery 无 LLM request。
- 第二轮幂等优化前，script `30` 的 storyboard 已因重复执行增到 v8；载入占位帧
  复用逻辑后，Run ID
  `generation-optimization-storyboard-reuse-20260715T035127Z` 通过：Task `6331`
  用时 `0.539494s`，Timeline 保持 `69` v7，storyboard 保持 v8，Celery 无
  LLM request。DB 中 storyboard meta 仍指向 Timeline `69` v7。
- script `30` 绑定了“老拐/阿盖儿”及可用头像，但持久化 storyboard 的 36 帧原先
  都没有 reference image。对 Timeline `69` v7 做不写 DB 的重建探针后，speaker
  保留先得到 15/36 帧可绑定参考图，进一步加入 shot-plan 文本别名匹配后达到
  29/36 帧、共 37 个参考；剩余 7 帧是无明确角色的物体/环境镜头。探针未排图片
  或视频 provider 任务，持久化 storyboard 仍保持 v8。

2. Export and asset readiness:

- script `30` 的 `timeline_export_end_to_end` Run ID
  `generation-optimization-export-20260715T033500Z` 按真实状态失败：render job
  `127` 返回 `missing_clip_videos`，36 个 video clip 只解析到 14 个，仍缺 22 个；
  没有为了测试而擅自触发 22 段付费视频生成。
- 已有完整资产的 script `144` 通过 Run ID
  `generation-optimization-export-ready-20260715T034000Z`：Task `6330`、Timeline
  `70` v6、render job `121`、output asset `353` 均成功；输出为 179999ms MP4。

3. Automated tests:

- RED：新增的目标测试最初为 3 failed、1 passed，分别暴露重复 shot-plan、外部模型
  传入 fallback provider、provider 失败继续 repair 三个缺口。
- storyboard 占位帧复用测试第一次被 fixture 中尚未 flush 的 `user.id` 非空约束
  拦住；修正测试持久化顺序后，测试按预期因调用重建函数而失败，再由复用实现转绿。
- speaker 保留和 shot-plan 文本角色匹配都分别先以失败断言确认缺口，再由实现转绿；
  `pytest tests/unit/services/storyboard/test_storyboard_audio_context_enricher.py tests/unit/services/audio/test_storyboard_from_timeline_spec.py -q`
  最终为 7 passed、88 warnings。
- `cd ai-pic-backend && pytest tests/unit/services/audio/test_storyboard_from_timeline_spec.py tests/unit/services/storyboard/test_storyboard_audio_context_enricher.py tests/unit/services/script/test_timeline_storyboard_queue.py tests/unit/services/script/test_timeline_shot_plan_step.py tests/unit/services/ai/test_structured_output.py tests/unit/test_ai_manager_text_generation.py tests/integration/test_timeline_pipeline_import_api.py tests/integration/test_timeline_pipeline_errors.py tests/test_timeline_shot_plan_api.py -q`
  - passed: 28 tests, 222 warnings.

4. Browser evidence:

- Entry URL: `http://localhost:8089/episodes/174/workspace?tab=timeline`.
- Scenario: `episode_timeline_smoke`; Run ID
  `generation-optimization-browser-20260715T034300Z`.
- Chrome DevTools 在 `http://127.0.0.1:9222` 等待超时；按策略降级后 Playwright
  也在 30 秒超时，Selenium 因 Chrome instance exited 无法建立 session。
- 收尾复查 `http://127.0.0.1:9222/json/version` 仍返回 HTTP `404`，因此没有把
  transport 不可用误记成浏览器验证成功。
- Result: failed，未获得页面 DOM、console 或 network 的成功证据；不能声称 Chrome
  或 fallback 浏览器验证通过。失败尝试与截图占位保存在对应 artifacts 目录。
- 后续 Run ID `generation-optimization-browser-cdp9333-20260714T201853Z` 的 doctor
  在把容器前端入口修正为 nginx `8089` 后通过；专用端口 `9333` 的 Chrome 启动仍
  因当前沙箱中进程 `SIGABRT` 失败，Playwright/Selenium 也未建立 session。
  已安装的浏览器运行时随后明确拒绝访问 `localhost:8089`，因此按安全策略停止，
  未通过其他浏览器或 CDP 绕过该限制。

5. Identity-free storyboard image eligibility:

- RED：显式 `characters: []` 的无角色帧在队列和 worker 测试中均先失败，分别表现
  为只排参考帧 `[0]` 和任务状态 `failed`。
- `cd ai-pic-backend && pytest tests/unit/test_storyboard_image_task_reference_requirement.py -q`
  - passed: 7 tests, 73 warnings.
- Timeline `69` v7 的只读重建探针得到 36 帧：29 帧需要且具备角色参考、7 帧显式
  无角色。新逐帧规则为 `eligible=36`、`skipped=0`，未创建任务或写数据库。

6. Storyboard image to Timeline clip lineage:

- RED：storyboard image worker 完成图片上传后没有任何 `storyboard_image` clip link；
  video rework task 的 `image_url` 仍为 `None`。两个断言均先失败。
- RED 测试最初漏掉 dynamic prompt 的 AI mock，意外向 DeepSeek 发出 2 次请求并收到
  `400 Prompt must contain the word 'json'`；随即补齐 mock 隔离，后续回归没有调用
  真实 provider。
- `cd ai-pic-backend && pytest tests/unit/test_storyboard_image_task_image_gen_persistence.py tests/unit/test_storyboard_image_task_reference_requirement.py tests/test_timeline_clip_video_rework_api.py tests/integration/test_timeline_pipeline_import_api.py tests/unit/services/script/test_production_storyboard_timeline_import.py tests/unit/services/script/test_timeline_storyboard_queue.py tests/unit/services/storyboard/test_storyboard_audio_context_enricher.py tests/unit/services/audio/test_storyboard_from_timeline_spec.py -q`
  - passed: 24 tests, 269 warnings.
- lineage 测试同时证明重复同步返回 0 个新 link、同角色 link 仍只有 1 条，并且
  Timeline version 保持不变。
- 测试文件拆分后恢复了仓库原有的 provider-rework lineage 用例，并把新增
  storyboard-image lineage API 用例放到独立文件；聚焦相邻链路最终为
  `37 passed, 313 warnings`。所有图片持久化用例均显式注入 mock AI service，
  后续运行没有真实 provider TCP 连接。
- 最终审阅把任意非空 `characters` 列表（包括角色对象）保守归为身份绑定帧；
  `pytest tests/unit/test_storyboard_image_identity_free.py tests/unit/test_storyboard_image_task_reference_requirement.py -q`
  为 `8 passed, 73 warnings`。

7. Repository checks:

- `cd ai-pic-backend && python run_tests.py quick` - failed before pytest because its
  dependency setup uses host Python 3.13 and cannot resolve the pinned `pydantic==2.5.0`
  with `langchain-core==0.2.43` on Python 3.12+.
- `cd ai-pic-backend && python run_tests.py quick --no-setup` 的 runner 会捕获全部
  pytest 输出；本轮等待 3 分钟仍无可见进度后主动中断。随后直接运行它内部完全相同
  的 `pytest tests/ -m 'not slow' -vv --tb=short --maxfail=1`，结果为
  `2472 passed, 77 skipped, 20 deselected, 3359 warnings in 503.89s`。
- `python scripts/check_repo_docs.py` - passed.
- `python scripts/check_repo_contracts.py --mode diff <changed files>` - passed.
- `python scripts/check_repo_contracts.py --mode audit` - passed.
- `pre-commit run --files <changed files>` - passed; backend quick gate passed and
  frontend lint correctly skipped because no frontend file changed.
- `git diff --check` - passed.

8. Same-Timeline reference-only hydration:

- RED：同 Timeline 占位帧虽然可被当作 `characters: []` 入队，但持久化帧仍没有角色
  参考；环境-only enrich 也因缺少 reference-only 参数直接报 `TypeError`。
- 第二个 RED 回归证明若继续读取已经编译的 `prompt_description` / `ai_prompt`，环境名
  “老拐的公寓厨房”会把物体空镜错误绑定到老拐；实现改为从当前 Timeline clip 的
  结构化 speaker/characters 和原始 shot-plan 语义补齐身份。
- script `30` / Timeline `69` v7 的最终只读探针：`frames=36`、
  `reference_required=29`、`after_with_refs=29`、`identity_free=7`、
  `required_without_refs=[]`、`eligible=36`；frame ID、`prompt_description`、
  `ai_prompt` 的变化数均为 0，数据库未写入、未创建付费任务。
- `pytest` 受影响链路为 `34 passed, 238 warnings`。
- `cd ai-pic-backend && python run_tests.py quick --no-setup` 最终通过：
  `2475 passed, 77 skipped, 20 deselected, 3382 warnings in 178.47s`。
- diff contract 首次指出 context enricher 测试文件超出大小阈值；把 3 个 reference
  hydration 回归拆到独立测试文件后，`check_repo_docs`、contract audit、contract
  diff 与 `git diff --check` 全部通过。
- 对所有 tracked/untracked 变更的最终 `pre-commit run --files ...` 通过；backend
  quick gate 通过，frontend lint 因本轮无 frontend 变更按规则跳过。

9. Canonical audio Timeline builder consolidation:

- RED：4 个新契约测试最初全部失败，分别证明旧模块仍自行构建 episode beats、
  storyboard frames、storyboard persistence，且 `app/services/audio/__init__.py` 仍
  import legacy `timeline_processor`。
- 实现后 package 入口解析到
  `app.services.audio.episode_timeline_beats`、
  `app.services.audio.storyboard_from_timeline`、
  `app.services.audio.storyboard_from_timeline`；应用目录中已无 legacy import。
- `timeline_processor.py` 从 368 行降为 92 行，只保留 direct-import 兼容包装；旧的
  storyboard-only duration resegmentation 被移除，避免 support view 独立改变
  Timeline/audio 权威时间窗。
- `pytest tests/unit/services/audio/test_timeline_processor_compatibility.py tests/unit/services/audio/test_episode_timeline_beats.py tests/unit/test_audio_timeline_storyboard.py tests/integration/test_audio_storyboard_task_api.py tests/unit/services/audio/test_storyboard_from_timeline_spec.py -q`
  为 `21 passed, 74 warnings`。
- 扩大到全部 audio service、legacy API 与 Timeline import 相邻链路为
  `176 passed, 7 skipped, 116 warnings`。
- `cd ai-pic-backend && python run_tests.py quick --no-setup` 通过：
  `2460 passed, 77 skipped, 20 deselected, 3392 warnings in 134.37s`。
- `python scripts/check_repo_docs.py`、contract audit、所有变更文件的 contract diff
  与 `git diff --check` 全部通过。
- pre-commit 首轮仅由 isort 调整 `test_audio_timeline_storyboard.py` import 顺序，
  backend quick gate 同轮已通过；对全部 tracked/untracked 变更重跑后所有 hook 通过，
  frontend lint 因无 frontend 文件按规则跳过。
- 本切片没有新增前端行为；当前浏览器运行时对本地 `8089` 的明确禁止仍然有效，
  因此未重复尝试或绕过该策略，沿用第 4 节记录的 browser blocker。

10. Storyboard image active-request idempotency:

- RED：新增契约最初为 `4 failed, 3 passed`；失败分别证明相同 active 请求会创建两个
  Task、queue API 不接受 scope、Celery 派发异常遗留 pending、复用文案仍写“已创建”。
  completed/failed/cancelled 三种终态允许重试的基线从一开始就通过。
- GREEN：幂等契约扩充到模型、提示词、参考图、帧快照和 scope 变化；聚焦测试
  `tests/unit/services/storyboard/test_storyboard_image_queue_idempotency.py` 为
  `8 passed, 76 warnings`，相邻 image queue/worker 与 Production Canvas 链路合计
  `19 passed, 141 warnings`。同一 canvas run 的第二次请求返回同一 Task，fake Celery
  delay 仅调用一次。
- script `30` / Timeline `69` v7 的纯 SELECT + 深拷贝探针得到 `frames=36`、
  `with_references=29`、`identity_free=7`、`eligible=36`；相同输入指纹一致，改变
  model 或 scope 后指纹不同。Task 总数前后均为 `6330`，未写数据库、未调用 provider。
- `cd ai-pic-backend && pytest` 全量通过：
  `2472 passed, 94 skipped, 3444 warnings in 115.33s`。
- contract diff 首次正确拦住两个超线测试文件（312/251 行）；收敛重复 API payload
  后分别降为 298/248 行。最终 `check_repo_docs`、contract audit、全部变更的 contract
  diff、`git diff --check` 均通过。
- 对所有 tracked/untracked 变更运行 `pre-commit run --files ...` 最终全绿；backend
  quick gate 通过，frontend lint 因无 frontend 文件按规则跳过。
- 本切片不触发图片或视频生成；36 张图片和 22 段视频仍保留为需明确付费授权的后续。

11. Paid-media preflight and per-frame checkpoint:

- 用户随后明确授权用 GPT-img-2 生图、Seedance 2 生成视频，并要求注入 Codex auth。
  本机 auth 仅复制到 backend/worker 容器默认路径、权限设为 600；未读取或输出 token，
  未把凭据写入仓库。重启后 provider catalog 确认
  `codex:gpt-image-2:text_to_image` 与
  `volcengine:doubao-seedance-2-0-260128:text_to_video` 均 enabled。
- 正式扣费前的只读 DB 预检：script `30` / Timeline `69` v7 有 36 帧、0 张持久化
  支撑图、0 个 reference frame、0 个 prompt bundle；Timeline video 已解析 14 段、
  缺 22 段，且没有 active media Task。
- RED：两帧 worker 在第 2 帧抛 provider error 后，第 1 帧 URL 未落库。逐帧 checkpoint
  实现后，该 URL 与 `timeline_clip_assets.storyboard_image` 均保留，父 Task 正确 failed。
- `pytest tests/unit/test_storyboard_image_task_checkpointing.py tests/unit/test_storyboard_image_task_image_gen_persistence.py tests/unit/test_storyboard_image_task_reference_requirement.py tests/unit/test_storyboard_image_identity_free.py -q`
  为 `12 passed, 131 warnings`。
- `cd ai-pic-backend && pytest` 在 checkpoint 变更后全量通过：
  `2473 passed, 94 skipped, 3471 warnings in 132.68s`。
- 首个真实图片批次 Task `6332` 仅尝试 scene 1 的 7 帧，但 Codex access token 已
  过期且 refresh token 返回 HTTP 401 `invalid_refresh_token`；Task failed、持久化
  图片仍为 0，保护编排随即停止，没有继续排 scene 2-6。默认 `~/.codex/auth.json`
  与更新的 profile auth 都通过最小 Codex 文本 preflight 证实已失效。
- 已启动隔离 `/private/tmp` Codex home 的 device authorization；必须完成新的官方
  OpenAI device login 后才能继续 `codex:gpt-image-2`。没有用已配置的 OpenAI API
  key 绕过用户指定的 Codex auth，也没有继续触发图片或 Seedance 扣费。

12. Storyboard video active-request idempotency:

- RED：新契约最初为 `8 failed`；现有 video parent queue 每次都创建新 Task，结果也
  不暴露复用状态，Celery transport 异常后 Task 仍停在 pending。
- GREEN：视频请求现在按 user/script、目标帧快照、已解析首帧、model/video options、
  Timeline rework mapping、canvas branch 与 target run scope 生成版本化 SHA-256 指纹。
  相同 pending/processing 请求复用同一 Task 且只派发一次；model、目标帧或 scope
  改变会新建任务；completed/failed/cancelled 均允许重试。
- Celery 派发异常会把新 Task 持久化为 failed 并记录
  `storyboard_video_dispatch_failed`，避免下次请求复用从未到达 worker 的 orphan row。
- `pytest tests/unit/services/storyboard/test_storyboard_video_queue_idempotency.py tests/unit/test_storyboard_video_queue_version_mapping.py -q`
  为 `10 passed, 107 warnings`；扩大到 Production Canvas media/defaults 相邻链路为
  `14 passed, 132 warnings`。
- `cd ai-pic-backend && pytest` 全量通过：
  `2481 passed, 94 skipped, 3551 warnings in 229.45s`。
- `python scripts/check_repo_docs.py`、contract audit、该切片全部文件的 contract diff
  与 `git diff --check` 均通过；服务/测试文件分别为 115、205、250、192、43、299
  行，没有超过仓库阈值。
- 对该切片全部代码、测试、计划、任务板和 ledger 运行 `pre-commit run --files ...`
  全绿；backend quick gate 通过，frontend lint 因没有前端文件按规则跳过。
- 此切片只使用 fake Celery delay，没有提交 Seedance provider；Codex device auth
  第一轮新设备码等待 15 分钟后超时，未生成 `auth.json`、未注入容器；随后已启动
  新一轮官方 device authorization 等待用户确认。期间没有回退到 OpenAI API key。

13. Storyboard video per-child submission checkpoint:

- 继续审计发现 parent worker 只在整批 frame 提交结束后 commit；后续帧异常会让先前
  已经获得的付费 provider task ID 随 transaction rollback 丢失。活动请求指纹还
  包含 `video_url` / `video_generation` 等结果字段，兄弟帧回填可能让同一请求生成新
  指纹并重复派发。
- RED：3 个回归分别证明视频结果回填后未复用活动 parent、第二帧 transport exception
  直接逃逸且没有 failed child、第二帧失败持久化异常会回滚第一帧 provider task ID；
  初始为 `3 failed, 8 passed`。
- GREEN：每个 submitted/failed child 在下一次 provider 调用前 commit；未知提交异常
  转成 durable failed child。视频 parent 指纹改为只快照 worker 实际消费的 prompt、
  start/end image、reference、duration 等输入，排除可变视频输出字段。
- 第二轮 RED 进一步证明同一 parent 重放会再次提交已有 frame，且只轮询到 1 个成功
  child 时会把显式请求 2 帧的 parent 错标 completed；初始为 `2 failed, 6 passed`。
- 恢复实现按 `(task_id, frame_index)` 复用任何已有非删除 child；失败/超时 child 计入
  parent failure，但不在同 parent 内静默重扣。parent polling 会比较 parameters 中的
  显式 frame indexes 与实际 child coverage，缺 child 时保持 processing。
- `pytest tests/unit/services/storyboard/test_storyboard_video_queue_idempotency.py tests/unit/services/video/test_storyboard_video_submission_checkpoint.py tests/unit/services/video/test_storyboard_video_timeline_submission.py tests/unit/services/video/test_video_task_polling_parent_task.py -q`
  为 `16 passed, 145 warnings`。
- 全部 video service、图片/视频 queue、checkpoint worker 与 Production Canvas 相邻
  链路为 `112 passed, 12 skipped, 348 warnings`。
- 本切片全部 provider submit 均为 mock，没有调用 Seedance；真实媒体生成继续等待
  官方 Codex device authorization 完成后再执行。

14. Storyboard image active-checkpoint and same-task replay safety:

- 视频侧输出字段问题在图片侧同样存在：首帧逐帧 checkpoint 会写入 `image_url`、
  `start_image_urls`、`image_gen`、`storyboard_prompt_v2` 和 candidate lineage，原完整
  frame snapshot 会使仍 active 的 36 帧请求产生新指纹。RED 为 `1 failed, 8 passed`。
- 图片请求现在以完整 frame source 为基础，但移除 worker 自己写入的 image/keyframe、
  compiled prompt、lineage 与 task checkpoint 字段；prompt、角色、环境、reference 等
  实际输入仍参与指纹。相同 active 请求在首帧回填后继续复用原 Task。
- 进一步 RED 证明同一 Celery Task 在 frame 1 成功、frame 2 失败后重放会再次生成
  frame 1（调用序列 `[0, 1, 0, 1]`）。成功帧现在持久化原 Task checkpoint；重放先
  分离 completed/pending indexes，只为 pending frame 构建 dynamic prompt 并调用 provider，
  修复后调用序列为 `[0, 1, 1]`。
- `pytest tests/unit/test_storyboard_image_task_checkpointing.py tests/unit/services/storyboard/test_storyboard_image_queue_checkpoint_idempotency.py tests/unit/services/storyboard/test_storyboard_image_queue_idempotency.py tests/unit/test_storyboard_image_task_image_gen_persistence.py tests/unit/test_storyboard_image_task_reference_requirement.py -q`
  为 `18 passed, 170 warnings`。
- `cd ai-pic-backend && MINIMAX_API_KEY= pytest` 全量通过：
  `2487 passed, 94 skipped, 3597 warnings in 171.01s`。显式清空 MiniMax key 是为了
  避免仓库现有 voice-service import warm-cache 在 pytest collection 阶段访问真实
  MiniMax；本轮 provider 保持完全离线。
- `python scripts/check_repo_docs.py`、contract audit、该切片全部文件的 contract diff
  与 `git diff --check` 均通过。新增/变更服务最大文件为 248 行，测试最大为 218 行，
  均在仓库阈值内。
- 对该切片全部代码、测试、计划、任务板和 ledger 运行 `pre-commit run --files ...`
  全绿；backend quick gate 通过，frontend lint 因无前端变更按规则跳过。
- 浏览器运行时此前已明确禁止访问本地 `8089`，本切片没有绕过或重复尝试；使用后端
  集成、任务状态和 DB 持久化测试证明成本安全语义，但不能声称真实浏览器验证通过。
- 第二轮 Codex device code 也在 15 分钟后超时，隔离目录仍没有 `auth.json`；真实
  GPT-img-2 / Seedance 生成仍需用户在官方页面完成新一轮设备确认。
- 所有图片生成和动态 prompt 均为 mock；没有调用 GPT-img-2 或产生费用。

15. Restored Codex credential injection:

- 用户确认 Codex 已恢复后，使用
  `/Users/geyunfei/.codex-profiles/original/auth.json` 做宿主机真实文本 preflight，
  返回固定结果 `CODEX_AUTH_OK`；未读取或输出 token 内容。
- 凭证同步到 backend/worker 的默认路径 `/root/.codex/auth.json` 后，运行时配置探针
  发现 `CODEX_AUTH_PATH` 实际指向 `/app/ai-pic-backend/.codex/auth.json`；随后把同一
  凭证补同步到真实读取路径。两个容器的 `.codex` 目录权限均为 700、`auth.json`
  权限均为 600，文件大小均为 4714 bytes，并已重启 backend/worker。
- backend `/health` 返回 HTTP 200。项目自身 Codex provider 的底层 responses 请求
  在 backend 和 worker 中均返回 `SUCCESS=True`、`MATCH=True`、
  `USAGE_REPORTED=True`，证明容器实际读取的凭证可用。
- 常规 `generate_text` 探针还暴露当前 Codex endpoint 已拒绝旧的
  `max_output_tokens` 和 `temperature` 参数；图片 provider 使用独立 payload，不携带
  这两个字段，因此该文本兼容性问题不阻塞已授权的 GPT-img-2 图片链路。

16. Paid GPT-img-2 generation and visual quality gate:

- 恢复 auth 后按 scene 串行执行 Task `6333`–`6338`，全部 completed；script `30`
  的 36/36 storyboard frame 均有持久化图片，Timeline `69` v7 有 36/36
  `storyboard_image` links，frame index 无缺失。串行执行避免并发全量 JSON 写回覆盖，
  每帧均通过真实 `codex:gpt-image-2` HTTP 200 和逐帧 checkpoint 落库。
- 使用 `download-images` 技能把 36 张成品下载到
  `/private/tmp/ai-video-studio-quality-review/`，生成 frame `0`–`35` 的三张接触表并
  检查关键人物、手部、构图和尺寸。主角脸部辨识、整体光影、材质和大部分手部质量
  总体良好，但这批没有通过成片质量门禁。
- Story 默认画幅是 `9:16`，实际只有 frame `5,9,21,35` 接近 9:16；其余 32 张为
  3:2、横屏或其他非目标比例。直接排队时未传入已解析的 storyboard aspect ratio，
  Codex image tool 使用 auto size，导致同一批尺寸从 `939x1676` 到 `1731x909` 不等。
- 人物连续性也有明确阻塞：frame `35` 的结构化角色是“阿盖儿”，成品却只出现“老拐”；
  frame `21` 把阿盖儿从贯穿镜头的浅色连衣裙改成灰色 T 恤和牛仔裤；frame `18` 的
  男性手部年龄/皮肤质感与老拐其他镜头明显不一致。当前图片不能直接送入 Seedance。
- Seedance 父任务尚未创建：首次提交在写 Task 前因过长 `target_business_id` 触发
  MySQL `Data too long for column 'target_business_id'`，事务已回滚，没有创建 provider
  子任务或产生视频费用。

17. Complex clip 2×2 storyboard differentiation gate:

- 从 Timeline `69` v9 的 36 个 video clip 中选中
  `video_scene_91_beat_4001_011`（30000–36260ms）：四个动作点依次为老拐递出手机、
  阿盖儿接过、老拐滑动屏幕、两人共同查看，具备人物互动、道具交接与视线转移。
- 只读任务 payload 探针发现旧逻辑虽然动作不同，却把同一
  `over-the-shoulder` 景别、同一构图和完整四点 motion timeline 重复进每个 Panel；
  修正后分别为 wide establishing、medium two-shot、insert detail、held closing，且每格
  只渲染自己的 action anchor。
- 定向回归
  `pytest tests/unit/services/storyboard/test_grid_storyboard_prompt_bridge.py tests/unit/services/storyboard/test_clip_storyboard_panel_sanitizer.py tests/unit/services/storyboard/test_clip_storyboard_prompt_context.py tests/test_timeline_clip_storyboard_context_api.py tests/test_timeline_storyboard_grid_processor.py -q --no-cov`
  为 `19 passed, 147 warnings`；`check_repo_docs`、该切片 contract diff 和
  `git diff --check` 通过。`python run_tests.py quick` 在本机 Python 3.13 的依赖安装阶段
  因仓库 pin `pydantic==2.5.0` 与 `langchain-core==0.2.43` 要求
  `pydantic>=2.7.4` 冲突而未进入测试，属于现有 bootstrap 环境问题。
- 真实 GPT-img-2 Task `6352` 直接使用 `codex:gpt-image-2` 和 3 张参考图完成，未走
  provider fallback；产出 media asset `510`，原图
  `https://resource.lets-gpt.com/ai-generated/clip-storyboard/image/20260715/080727/655da2df.png`，
  实际 `1254×1254` 且 1:1 检查通过，Timeline `69` 从 v9 更新为 v10。
- 原图视觉检查通过：Panel 1 为全景递出、Panel 2 为双人中景交接、Panel 3 为手机与
  手指特写、Panel 4 为共同查看的收束镜头；人物脸、发型、服装和厨房环境连续，无
  多余人物、字幕、水印或格内说明文字。该结果证明此前“两个太相近”主要是共享
  景别/构图和重复 motion prompt 的问题，不是宫格数量参数本身。

18. Adaptive panel count and full-sheet Seedance gate:

- 后端自动格数与整张时序参考定向回归为 `27 passed, 168 warnings`；拆分热点文件后，
  clip storyboard payload 回归为 `15 passed, 137 warnings`。前端相关 `28` 个交互测试
  全绿，目标文件 ESLint 无错误。
- 前端全量 `npm run lint` 为 0 errors、3 个既有 warning；全量 `npm run test` 为
  `348 passed / 349`，唯一失败是 Canvas autosave 的计时型重复保存断言，单独复跑
  `productionCanvasPersistence.test.tsx` 为 `9 passed`。
- 后端全量为 `2516 passed, 88 skipped, 3 failed, 3 errors`；其中共享 `test.db` 的
  readonly/disk-I/O 污染和 Canvas 用例均单独复跑通过。本次相关 context 断言按 canonical
  IP 参考语义更新后通过，相关切片重新全绿。
- `python scripts/check_repo_docs.py` 通过。contract diff 首次发现两个文件超过行数上限；
  拆分后 `grid_storyboard_sheet_service.py` 为 200 行、
  `TimelineClipProviderReworkControls.tsx` 为 247 行，目标 contract diff 通过。
- 重启 backend/worker 后，Timeline `69` 仍为 v10、180000ms、1080x1920。真实 Task
  `6353` 的提交 payload 正确命中 `clip_storyboard_sheet`、`sheet_sequence`、4 个按序
  Panel、asset `510`、6.26 秒、9:16，以及 sheet + 两个 canonical IP + 环境共 4 张参考图；
  prompt 的动作锚点为 0.0s 递出、2.0s 接过、4.0s 滑动、6.0s 共同查看。
- 火山 Ark 在创建 provider 任务前返回 HTTP 403：`AccountOverdueError`，request id
  `021784105426127e7a0e121a78287261e362ecd929ed85342f035`。父 Task `6353` 和 child
  `267` 已持久化 failed；没有生成视频、没有 Timeline replacement 或 render 更新。
  运行时没有第二条 Seedance 2 provider 路由，因此不能用别的账户静默替代。

19. Recharged Volcengine retry, privacy-safe fallback, and frame-aligned trim:

- 充值后原样重试 Task `6354`，欠费 403 已消失，但 Ark 改为返回
  `InputImageSensitiveContentDetected.PrivacyInformation`，request id
  `021784105950940e4fd4c285bd49f804239cddc30345c48d176ee`。只保留 asset `510`
  的隔离 Task `6355` 仍被拒绝，request id
  `021784106049088f952b6c252d6ae62c15909f77d85597eae4b37`，证明触发源是高度写实
  宫格本身，不是余额、额外参考图数量或参数。
- 火山官方 Seedance 2.0 可信素材文档要求写实真人走授权素材库并以
  `asset://<asset_id>` 引用；当前外链 AI 写实角色不具备该资产身份。链路新增受限降级：
  仅 `clip_storyboard_sheet` 命中该真人隐私错误时，使用同一内置 panel sequence prompt
  和文字版人物/环境连续性做 `text_to_video`，不对普通用户图片泛化绕过，并在 child
  metadata 中保留原 request id、from/to reference mode 与降级原因。
- 真实 Task `6358` 首次图片请求被拦截，request id
  `02178410642272026c44c94e78e1636b22d696d555dc11eb2a83e`；同一父任务自动文本降级后
  成功获得 Volcengine provider task `cgt-20260715170721-54bw8`，child `270`
  succeeded。Timeline `69` v10 绑定 `generated_video` link `1621`、media asset `511`，
  `reference_mode=clip_storyboard_prompt_fallback`；自动 final render job `128` 正确解析到
  15 段视频后因其余 21 段缺失而 failed，没有伪造完整成片。
- 0.3s、2.1s、4.1s、6.0s 抽帧证明镜头依次完成递出/交接、手机特写滑动、共同查看，
  没有宫格、边框、编号或分屏泄露；但文本降级没有严格复刻故事板角色身份，发型、服装、
  年龄感存在偏移。这是当前外链写实图不能进入 Seedance 的明确质量折损。
- 旧 stream-copy 裁切把标称 6.26s 的成片保留为 153 帧 / 6.375s。裁切改为按 Timeline
  fps 重编码并向下对齐完整帧；6.26s @ 24fps 现在为 150 帧 / 6.250s，音视频流一致，
  误差 10ms、小于 1 帧。media asset `511` 已无重新生成费用地从保存的 7 秒原片重处理为
  `https://resource.lets-gpt.com/ai-generated/videos/video/20260715/092235/e8c7f572.mp4`。
- 裁切后末帧现在从成片最后一帧重新提取，而不是复用 provider 7 秒末帧；Task `6358`
  当前 last-frame 为
  `https://resource.lets-gpt.com/ai-generated/video-last-frames/image/20260715/092742/e3e5ef49.png`，
  source `trimmed_video_frame_149`，原 provider 末帧仍单独保留用于审计。
- 提交失败、隐私降级、逐 child checkpoint、帧对齐裁切、裁切末帧与上传服务定向回归为
  `11 passed, 63 warnings`；相关 contract diff 与 `git diff --check` 通过。提交服务拆分后
  235 行，trim/upload/generation service 均在仓库 hard limit 内。
- `python run_tests.py quick --no-setup` 运行到 `2403 passed, 77 skipped`，随后出现
  `23 failed, 101 errors`；失败面从 Canvas、readiness、Workbench 扩散到基础 CRUD，
  共同根因是共享 `test.db` 的 `sqlite3.OperationalError: disk I/O error` /
  `attempt to write a readonly database`。删除 `test.db` 并用独立 pytest 进程复跑，仍在
  `Base.metadata.create_all` 阶段同样失败，未进入本次业务断言，因此 quick gate 不能记为
  通过，也没有把它归因于本次视频变更。
- 最终 `python scripts/check_repo_docs.py`、目标 contract diff 与全工作树
  `git diff --check` 通过。浏览器对本地 `8089`
  的既有禁止仍未解除，本节证据来自真实 API、Worker、Ark、DB、ffprobe 和抽帧，不声称
  Chrome 验证。

20. Restored direct storyboard-grid submission:

- 用户根据 Task `6358` 的实际成片确认纯文本降级会损失人物身份、发型和服装连续性，明确
  要求恢复“之前的宫格传入”。Timeline clip 视频提交因此恢复为单次
  `clip_storyboard_sheet` / `sheet_sequence` 图片参考请求，整张宫格继续通过
  `reference_images` 原样传给 Seedance。
- 删除仅针对 Ark 真人隐私错误的自动 `text_to_video` 二次提交模块；宫格被拒绝时不再静默
  清空图片参考或更换 `reference_mode`。失败 child 仍持久化 provider、model、完整宫格引用、
  `reference_privacy_rejected`、`retryable=false` 和 provider request id，父任务明确 failed。
- 新回归断言隐私拒绝只发生一次 provider 调用，调用仍包含宫格 URL，child 维持
  `image_to_video`，且不存在 `visual_reference_fallback`。提交、时长帧对齐、裁切后末帧和
  checkpoint 定向测试为 `11 passed, 61 warnings`。
- `python scripts/check_repo_docs.py`、目标 contract diff 和 `git diff --check` 通过。
  backend/worker 已重启；容器内代码探针确认宫格引用转发开启、文本重试不存在，backend
  `/health` 返回 healthy。本次没有重新提交已知会被 Ark 拒绝的 asset `510`，因此没有新增
  Seedance 费用。

21. Full direct-grid generation, visual rework, and exact final render:

- 先以复杂四动作镜头 `video_scene_91_beat_4001_011` 做质量门禁：Task `6359` 的首张宫格因
  景别差异不足被人工退回，Task `6360` / asset `513` 重抽后通过；Task `6361` / child `271`
  直接把整张宫格作为唯一时序参考提交 Seedance 并成功，证明合规 3D 宫格链路可用。
- 随后为 Timeline `69` 批量补齐：并发 storyboard Tasks `6362`–`6372` 在 MySQL 上完成
  v16→v20 的无丢失 rebase，Tasks `6373`–`6385` 继续推进到 v33。共覆盖 22 个本轮新生成
  3D clip；任务账面为 33 次 storyboard（比基准多 11 次）和 29 次 video submission（比
  基准多 7 次）。其中 5 次视频在 Ark 创建 provider task 前因隐私输入 400 被拒绝，没有
  实际生成费用；真正多产出的 Seedance 视频为 2 条，均用于最后一个分屏缺陷的视觉返工。
- 21 个批量视频提交中，5 个隐私拒绝镜头改用同一 3D 风格锚点重新生成合规宫格，仍坚持
  `clip_storyboard_sheet` / `sheet_sequence` 直接传图，不使用 text fallback。approved style
  anchor 自动继承已通过的 3D 资产；2-panel 布局改为 `2:1`，并由物理宽高门禁验证。真实
  Task `6416` 产出 2-panel 宫格，Task `6417` / child `297` 补齐最后一个缺失 clip 后，
  Timeline `69` v38 达到 36/36 video clips resolved。
- 所有生成视频按 Timeline 目标时长向下对齐完整帧。实际 ffprobe 发现旧最终 renderer
  仍输出 `768×768 / 181.333s`（Render `129`），因此新增统一 canvas/fps/codec 归一化、
  累计帧预算和渲染后硬探针；每个输出现在必须匹配 Timeline 的宽高、fps、总帧数和时长，
  否则 render job 明确失败。
- 修复后的 Render `130` 首次达到 `1080×1920 / 24fps / 4320 frames / 180.000s`，但全片
  60 点抽帧在 96.852–102.961s 的 `video_scene_93_beat_4021_031` 发现 4 宫格被 Seedance
  解释为上下分屏。Task `6418` 用更强单画面提示重抽后，开头两秒仍残留分屏，未通过视觉门禁。
- 内置 full-sheet sequence prompt 现明确要求任意时刻只能有一个铺满画布的 camera view，
  禁止 stack/tile/duplicate/divider；2-panel 动作采样改为首尾锚点。Task `6419` / asset `572`
  生成真实 `1774×887` 横向 2 宫格；Task `6420` / child `299` / provider
  `cgt-20260715194137-9xrrn` 将 asset `572` 作为唯一参考生成 146 帧 / 6.083333s 视频。逐秒
  6 点抽帧均为单一全屏画面，无宫格、边框、编号或分屏泄露。
- Timeline `69` v39 的最终 Render `132` / asset `574` 成功：
  `https://resource.lets-gpt.com/timeline-renders/video/20260715/114957/0a71a8c1.mp4`。
  远端下载后 ffprobe 为 H.264 `1080×1920`、24fps、4320 帧、视频和容器均精确
  `180.000000s`，AAC 音频 `179.968s`；全片每 3 秒共 60 点抽帧及 96–104s 逐秒复查通过，
  最终镜头没有分屏回归。
- render/storyboard/provider 定向回归为 `42 passed, 187 warnings`；真实 1 秒 FFmpeg
  contract smoke、`check_repo_docs`、目标 contract diff、ruff、black/isort 和
  `git diff --check` 通过。浏览器对本地 `8089` 仍不可用，本节只声明 API、Worker、DB、
  provider、ffprobe 和本地抽帧证据，不声明 Chrome 验证。

22. Commit packaging validation:

- 为避免把尚未收敛的 Production Canvas 领域层级工作混入本次提交，只暂存故事板、
  Timeline 视频、provider、裁切和最终渲染主链；Canvas 代码、测试、设计文档及其 ledger
  继续保留在工作树。
- 仅把 index 中 154 个暂存路径应用到独立 worktree 后，生成链路定向后端回归为
  `190 passed, 1067 warnings`，前端 Timeline 生成交互为 `68 passed`，默认 Turbopack
  `npm run build` 通过；证明未提交 Canvas 改动没有为本次提交提供隐式依赖。
- 原混合工作树的 `npm run build` 完成 Next.js 编译后，被未提交 Canvas 切片中的
  `ProductionCanvasNodeExecutionResponse.input_fingerprint` 类型缺口阻断；全量前端测试的
  确定性失败也集中在同一未提交 Canvas 上下文恢复切片，未作为生成链路通过证据。全量
  frontend lint 为 0 errors、3 个既有 warnings。
- `pre-commit run --all-files` 首轮触发历史文件格式化并暴露 69 个既有 Ruff 问题；所有
  hook 引入的范围外改动均已恢复，工作树回到运行前的 177 个 tracked 变更。提交改用精确
  文件集检查，避免把历史清理混入功能提交。
- 精确文件集的 merge、whitespace、EOF、YAML、Ruff、Black、isort、repo docs 和 repo
  contracts 全部通过；直接 ORM 查询已下沉到 repository，超限测试已拆到独立文件，
  `TimelineClipProviderReworkControls.tsx` 保持 250 行。因 `tasks.md` 同时含未提交 Canvas
  hunk，prettier hook 对 partial stage 无法无损 stash/reapply，已跳过该 hook；工作树文件
  本身已由 prettier 格式化，暂存 hunk 经 `git diff --cached --check` 验证；generation
  ledger 的独立 `agent-chats-ledger` hook 通过。
- `./docker/build_prod_images.sh` 在 Docker Hub `python:3.11-slim` 元数据解析阶段持续无响应，
  等待约 7 分钟后取消；未产出或推送镜像。该外部 registry 阻塞与前述 Canvas build 缺口
  均作为交付例外保留，不伪记为通过。

## Next Steps

- 生成主链当前无缺失镜头，直接宫格传入、2/4 格动作提示、视频裁切和最终 180 秒渲染均已有
  真实运行时证据。后续新剧集继续保留 storyboard visual gate；若模型仍把 4 宫格解释为
  分屏，优先降为首尾 2 宫格，不允许退化为纯文本或单首帧。
- 恢复可用的 Chrome DevTools transport，并允许浏览器运行时访问本地 `8089` 后，重跑
  `episode_timeline_smoke`，补齐页面、console 和 network 证据。

## Linked Commits

- This commit (generation chain).
