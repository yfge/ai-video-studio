## User Prompt

用户要求不要新建独立商用短剧生产包，而是“需要和现有的流式集成，提升现在的生成质量”。

## Goals

- 保持现有脚本生成链路和异步任务入口，接入商用竖屏短剧正文质量。
- 不新增独立生产包/导出流水线。
- 默认生成更接近样本的正文格式：`第N集`、`N-M 内/外. 地点 - 日/夜`、`人物：`、`▲动作/镜头`、`角色(状态)：对白`。
- 保持 provider streaming 主路径，去掉 direct fallback 主生成调用里的强制非流式。

## Changes

- 扩展 `ScriptGenerationRequest`：`template_style`、`target_chars_per_episode`、`quality_threshold`；`EpisodeGenerationRequest.episode_count` 上限提升到 100。
- 在现有 `ScriptGenerator -> ai_service.generate_script -> ScriptLangGraphAgent/AI manager -> quality gate` 链路传递商用正文参数。
- 新增商用正文组装逻辑，保留结构化 `scenes/dialogues/stage_directions`，正文输出改为样本式短剧格式。
- 更新短剧 prompt，强调 1-4 场、目标字数、开场钩子、爽点落点、结尾卡点、可拍动作和角色状态括注。
- 更新 script lint：识别 `第N集`、`N-M 内/外. 地点 - 日/夜`、`人物：`、`▲`、`角色(状态)：对白`；不再要求必须有 `【快/慢】` 标签。
- 修复 `ScriptLintOptions.target_word_min/target_word_max` 分支缺少 `ScriptLintIssue` import 的问题，该问题由真实 DeepSeek 生成结果评分触发。
- 前端剧集工作台的剧本生成表单新增正文模板、目标字数、质量阈值；故事详情页集数输入上限同步为 100。
- 增加商用正文 formatter 和 lint 单元测试。
- 将新增商用正文 formatter 控制在服务层文件大小限制内，避免新增文件自身触发 size violation。

## Validation

- `cd ai-pic-backend && pytest tests/test_script_quality_lint.py tests/unit/services/test_commercial_script_text.py tests/unit/services/test_narrative_quality_gate.py -q`
  - 结果：通过，`11 passed`。
- DeepSeek v4 flash 真实生成测试
  - 配置来源：`docker/.env`，未输出密钥。
  - Full-chain `ai_service.generate_script`：LangGraph 脚本 agent 触发 120 秒超时，随后进入现有 direct fallback；首次结果评分时暴露 lint import bug。
  - Direct fallback `_call_ai_manager_script`：`prefer_provider=deepseek`、`model=deepseek-v4-flash`、`stream=True` 主生成路径，耗时 `33.79s`。
  - 输出：`1264` 字，`2` 场，`31` 条对白，`7` 条舞台指示。
  - Lint：`7.4/10`，未过 `9.0`；主要问题是多条对白超过当前 `15` 字阈值。
- `cd ai-pic-frontend && npm run lint`
  - 结果：通过，`0 errors, 19 warnings`；warnings 为既有 `eslint.config.mjs`、`StoryboardEditor.js`、图片组件等历史告警。
- `cd ai-pic-frontend && npm run test`
  - 结果：通过，`5 pass`。
- `python scripts/check_repo_docs.py`
  - 结果：通过。
- `python -m py_compile ai-pic-backend/app/services/ai/commercial_script_text.py`
  - 结果：通过。
- `git diff --check`
  - 结果：通过。
- `pre-commit run --all-files`
  - 结果：失败。`ruff`/`repo-contracts`/`backend-pytest` 命中仓库既有问题；其中 `backend-pytest` 在导入阶段失败，报 `cannot import name 'ensure_scenes' from app.api.v1.endpoints.episodes.helpers`。pre-commit 对大量历史文件做了自动格式化，已撤回无关工作区改动，仅保留本任务文件。
- `python scripts/check_repo_contracts.py --mode diff ...`
  - 结果：失败。原因是本次需要触达现有生成链路中的若干历史超限文件，检查报告包含 `scripts_legacy.py`、`script_generator.py`、`script_quality/checks.py`、`scripts_ai_manager.py` 等 oversized/direct-query baseline violations；新增 formatter 已控制在限制内。
- `cd ai-pic-backend && python run_tests.py quick`
  - 结果：未进入测试阶段。该脚本先执行依赖安装，当前 Python 3.13 解析到 `langchain-core==0.2.43` 要求 `pydantic>=2.7.4`，而仓库锁定 `pydantic==2.5.0`，pip dependency resolution 失败。
- 真实浏览器验证
  - 未执行。本次没有启动完整前后端栈；剩余风险是表单在真实登录工作台中的视觉布局和任务状态轮询仍需走一次浏览器路径确认。

## Next Steps

- 后续可单独做一次生成链路瘦身，把 `scripts_legacy.py` 和 `script_generator.py` 中的重复 normalize/quality/persist 逻辑迁移到服务层，消除 contract diff 阻断。
- 如需完整 quick gate，需要先调整测试环境 Python 版本或依赖锁定组合，解决 `pydantic` 与 `langchain-core` 的解析冲突。

## Linked Commits

- 本次提交：`feat(scripts): improve streaming commercial script quality`
