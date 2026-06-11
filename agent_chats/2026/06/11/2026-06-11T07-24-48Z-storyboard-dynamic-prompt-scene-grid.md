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

## 追加（同日第二轮）：真实 provider 链路接入

用户指定：DeepSeek v4-flash 跑提示词、用 Codex token 调 gpt-image-2 出图、Seedance 出成片，且必须带入 IP/环境参考图。

- Codex 生图 provider：新增 `app/services/providers/codex_image.py`（Responses API `image_generation` 工具 payload/SSE 解析/尺寸映射/参考图下载内联为 base64——ChatGPT 端无法访问内网 uploads URL）与 `codex_models.py`；`codex_provider.py` 实现 `generate_image`（含 server_error 延迟重试与错误透传），声明 TEXT_TO_IMAGE 支持
- `provider_params.py` 拆出 `provider_param_tables.py`（文件大小限制）并新增 codex t2i 参数白名单（reference_images 走 t2i 路径）
- scene_grid LLM 调用读取 `STORYBOARD_DYNAMIC_PROMPT_MODEL`（.env 配 `deepseek:deepseek-v4-flash`，provider 前缀 pin 路由）
- 前端：宫格面板新增生图模型选择（默认 `codex:gpt-image-2`）；剧集角色为空时回退加载故事角色（解决人物勾选列表为空）
- 实测：DeepSeek 成功产出逐格分节宫格提示词（2192 tokens）；Codex 生图实测通过（含 1536x1024 + 参考图）；发现 ChatGPT 图像工具有约 10 分钟级冷却限流（连续调用 server_error），单张/低频可用
- 新增 `tests/unit/test_codex_image.py`（5 例：尺寸映射/payload/SSE 解析/错误透传）
- `.gitignore` 增加 `.codex/`（auth token 永不入库）；`ai-pic-backend/.codex/auth.json` 为本机复制，不提交

## 追加（同日第三轮）：端到端真实出图结论

- **宫格图全链路成功**（task 6050）：DeepSeek v4-flash 动态分节提示词（prompt_source=llm_dynamic）→ Codex token 调 gpt-image-2 → 12 宫格电影级写实大图落 OSS（`ai-generated/scene-grid/.../d8645f49.png`），老拐/文闻/环境三张参考图全部带入（refs_used 含 character×2 + environment），编号与中文说明栏渲染清晰、人物形象贯穿一致。证据：`artifacts/runs/2026-06-11-scene-grid-dynamic-prompt/05-scene2-grid-sheet-codex.png`
- 排障结论一（已修复）：ChatGPT 图像工具对 **base64 内联 input_image 必然 server_error**，公网 URL 透传即成功 → `inline_reference_images` 改为公网 URL 透传、仅内网 uploads 才内联兜底
- 排障结论二（已修复）：normalize 层把 aspect_ratio 16:9 吞成 1024x1024 → `compute_image_ui` 增加 codex 分支（auto 优先 + 比例选项），`resolve_image_size` 对 auto 继续走比例映射，16:9→1536x1024 验证通过
- 排障结论三（平台限制）：火山 Seedance 2.0 图生视频对含写实人脸的宫格图返回 `InputImageSensitiveContentDetected.PrivacyInformation`（疑似真人审核）拒绝生成；用无人物环境图验证 Seedance i2v 链路本身正常（4s 成片成功）。成片环节被平台内容策略阻断，需向火山申请真人内容权限或改用对真人审核宽松的 i2v 渠道

## Next Steps

- 在配置了可用 LLM 文本模型与生图余额的环境开启 `STORYBOARD_DYNAMIC_PROMPT_ENABLED=true` 做真实出图对比与灰度
- 宫格图生成建议配置中文文字渲染较强的生图模型（如 jimeng/seedream 系），验证编号与说明栏渲染质量
- 场景帧时长合计 >15s 的多段成片拆分（当前 clamp 15s 单段）
- 前端人物参考可进一步升级为按角色选择具体参考图（复用 TimelineClipStoryboardReferenceImages 选择器）

## Linked Commits

- feat(storyboard): LLM dynamic frame prompts and scene grid sheet-to-video mode（本 ledger 与代码同 commit）
