# 分镜提示词动态化 + 场景宫格分镜模式

## User Prompt

> 现在分镜的故事板生成的还是太糙了，是否可以考虑在故事板生成时根据分镜信息和剧本动态生成故事板的提示词？
>
> （补充）先上网搜索典型的分镜故事板提示词（十二宫格动作分镜图范例）以及故事板到 Seedance 2.0 的提示词范例，再进行生成链路的优化，结合现有的流程。注意宫格生成时要能带入选择的人物/环境图片。

## Goals

- 阶段一：分镜图生成任务内，按场景批量调用 LLM，结合剧本上下文（场景描述、对白、舞台提示、角色外貌、相邻镜头）动态生成 image/start/end 三种提示词，替代固定模板拼接；后端透明、失败降级到 compiler、指纹缓存、配置开关灰度。
- 阶段二：新增"场景宫格分镜"模式（与逐帧链路共存）——按场景 LLM 生成分节式宫格提示词出一张 N 格大图（支持用户选择人物/环境参考图，未选则按场景绑定自动带入），再 LLM 生成 Seedance 时间轴提示词引用宫格图生成连续多镜头成片。

## Changes

阶段一（逐帧动态提示词，默认关闭，`STORYBOARD_DYNAMIC_PROMPT_ENABLED` 灰度）：
- `app/core/config.py`：新增 `STORYBOARD_DYNAMIC_PROMPT_ENABLED/_MAX_FRAMES_PER_CALL/_MODEL`
- `app/prompts/templates/storyboard_dynamic_image_prompt.txt/.yaml` + `PromptTemplate.STORYBOARD_DYNAMIC_IMAGE_PROMPT` 注册
- `app/schemas/storyboard_dynamic_prompt.py`：LLM 输出 Pydantic schema
- 新包 `app/services/storyboard/dynamic_prompt/`：`context_builder.py`（ORM Script → 场景级上下文）、`cache.py`（输入指纹 + frame["llm_prompt_bundle"] 缓存）、`generator.py`（LLM JSON 调用 + 重试一次）、`service.py`（编排 + `apply_dynamic_prompt_bundle` 覆写 compiled 三字段，i2v 不变）
- 接线：`image_task_processor.py` 帧循环前批量构建 bundles；`image_task_frame_generation.py` compile 后 apply（角色锚图匹配仍用原 base_prompt，顺序不变）

阶段二（场景宫格模式）：
- 模板 `storyboard_scene_grid_prompt.txt/.yaml`（分节式：整体定位/版式/风格/场景设定/主角设定/逐格内容/画面要求）、`storyboard_scene_grid_video_prompt.txt/.yaml`（Seedance 时间轴分节提示词）+ 枚举注册
- `app/schemas/storyboard_scene_grid.py`：请求/LLM 输出 schema
- 新包 `app/services/storyboard/scene_grid/`：`layout.py`（4/6/9/12/16 格）、`prompt_builder.py`（LLM + 静态 fallback）、`refs.py`（用户显式人物/环境参考图优先，否则按 ImageRefContext 场景绑定自动带入）、`processor.py`（宫格图生成+落库 scene_grids）、`video_processor.py`（Seedance 成片，时长 clamp 4-15s）、`shared.py`
- `app/repositories/storyboard_media_repository.py`：`load_scene_grids` / `save_scene_grid`（持久化到 `script.extra_metadata.storyboard.scene_grids`）
- `app/services/task_worker_scene_grid.py`：Celery `tasks.scene_grid_sheet_generate` / `tasks.scene_grid_video_generate`（celery_app include 注册）
- API `app/api/v1/endpoints/storyboard/scene_grid.py`：POST `/scripts/{id}/storyboard/scene-grid/generate`、POST `.../scene-grid/video`、GET `.../scene-grid`
- 前端：`storyboard-scene-grid.endpoints.ts`（API client）、`WorkspaceStoryboardSceneGridPanel.tsx` + `WorkspaceStoryboardSceneGridParts.tsx` + `useWorkspaceSceneGridGeneration.ts`（场景/宫格数选择、人物参考勾选、环境参考 URL、任务轮询、宫格图与成片展示），挂载到 `WorkspaceStoryboardTabContent.tsx`（默认折叠）

测试：
- `tests/unit/services/storyboard/test_dynamic_prompt_context.py` / `test_dynamic_prompt_service.py` / `dynamic_prompt_fixtures.py`
- `tests/unit/test_storyboard_image_task_dynamic_prompt.py`（任务级集成：bundle 覆写 + 落库）
- `tests/unit/services/storyboard/test_scene_grid.py`、`tests/unit/test_scene_grid_task_processor.py`

## Validation

- 后端：`pytest`（跳过基线既有损坏模块）→ 2238 passed / 3 failed（三个失败在干净基线同样失败，已用 `git stash` 比对确认与本次改动无关；11 个 collection error 同为基线 `scripts/harness/production_quality_script` 缺符号问题）
- 新增测试：dynamic_prompt 18 个 + scene_grid 11 个 + processor 集成 3 个 + 任务集成 1 个，全部通过
- 前端：`npm run lint`（0 error）、`npm run test`（71/71）、`npm run build` 成功
- `python scripts/check_repo_docs.py` ok；`python scripts/check_repo_contracts.py --mode diff` ok（拆分超限文件后）
- `pre-commit run --all-files`：本次改动文件 ruff/black/isort/prettier 全过；ruff 全仓 72 处与 pytest 快速门失败均为基线既有问题（干净基线复现确认）；whitespace 钩子对旧文档的自动修改已 `git restore` 还原，不混入本次提交
- 真实浏览器验证（Chrome DevTools，证据 `artifacts/runs/2026-06-11-scene-grid-dynamic-prompt/`）：
  - 登录 → 第1集工作区分镜 Tab → "场景宫格分镜"面板渲染并展开（场景 1/2/3 选择器、宫格数、成片按钮在无宫格图时正确禁用），截图 `01-scene-grid-panel-expanded.png`
  - 网络证据：GET `/scripts/142/storyboard/scene-grid` 200、GET 剧集角色 200、POST `/scene-grid/generate` 200 → task #6044，前端开始轮询
  - Celery（重启 worker 后注册 `tasks.scene_grid_sheet_generate/video_generate`）接收任务并执行：LLM（doubao-lite-4k 该环境不可用→走静态 fallback 提示词路径，符合降级设计）→ 生图 provider 链（keling 余额不足 429，环境问题非代码问题）
  - 阶段一动态提示词开关默认关闭，生图链路行为与现状一致（compiled dict 无覆写、无额外 warning）
- 跳过说明：`./docker/build_prod_images.sh` 未运行（本机 dev 容器以源码挂载方式运行并已验证；如需发布请在发布前执行）

## Next Steps

- 在配置了可用 LLM 文本模型与生图余额的环境开启 `STORYBOARD_DYNAMIC_PROMPT_ENABLED=true` 做真实出图对比与灰度
- 宫格图生成建议配置中文文字渲染较强的生图模型（如 jimeng/seedream 系），验证编号与说明栏渲染质量
- 场景帧时长合计 >15s 的多段成片拆分（当前 clamp 15s 单段）
- 前端人物参考可进一步升级为按角色选择具体参考图（复用 TimelineClipStoryboardReferenceImages 选择器）

## Linked Commits

- feat(storyboard): LLM dynamic frame prompts and scene grid sheet-to-video mode（本 ledger 与代码同 commit）
