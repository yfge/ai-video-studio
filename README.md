# ai-video-studio

中文 | [English](README_EN.md)

面向专业短剧制作团队的 AI 视频生产工作流平台。Timeline-first，harness-tested，
agent-assisted。

ai-video-studio 不是一个视频生成模型。它是面向 AI 短剧/影视生产的工程化工作流
系统：把故事、剧本、音轨、时间轴、分镜、素材、渲染、导出和测试证据纳入同一个
生产链路。

核心定位是让创作团队围绕可播放的 `Timeline` 协作，而不是围绕一次性的模型输出
协作。当前主链路是 `audio -> timeline -> clip -> render -> export`：
`Timeline` 是剧集可播放输出的单一事实来源（SSOT），Storyboard 是视觉支撑视图
和兼容面。

## 能做什么

- 管理短剧/影视生产对象：虚拟 IP、故事、分集、剧本、音轨、Timeline、分镜和素材。
- 将 AI 生成结果沉淀为可追踪的生产资产，而不是停留在 prompt 和临时文件。
- 以 Timeline 为中心组织剪辑、素材替换、渲染、导出和质量验证证据。
- 通过 harness、日志、浏览器证据和 agent ledger 支撑可复现的工程协作。

## 仓库结构

- `ai-pic-backend/`：FastAPI + SQLAlchemy + Alembic + Celery（MySQL/Redis）
- `ai-pic-frontend/`：Next.js 16 App Router + TypeScript + Tailwind
- `docker/`：本地开发/生产 Docker 编排与 Nginx 入口
- `docs/`：设计、接口、测试文档索引
- `tasks.md`：项目任务看板（唯一权威）

## 快速开始：5-10 分钟 Lite 模式

Lite 模式用于快速体验和本地联调：后端使用 SQLite，Celery 任务在进程内 eager 执行，
并默认启用 AI mock 回退，不依赖 MySQL、Redis 或独立 worker。

1. `cd docker`
2. `./init_env.sh lite`
3. `./dev_lite_in_docker.sh`

访问：

- Web（Nginx 入口）：`http://localhost:8089`
- Backend API：`http://localhost:8000`
- Swagger：`http://localhost:8000/docs`

Lite 默认关键配置写在 `docker/.env.lite`：

- `DATABASE_URL=sqlite:////app/ai-pic-backend/uploads/dev_lite.db`
- `CELERY_TASK_ALWAYS_EAGER=true`
- `AI_FORCE_MOCK=true`
- `SQLITE_MIGRATION_FALLBACK_CREATE_ALL=true`

## 完整 Docker 开发栈

需要 MySQL、Redis、Celery worker、Celery beat 和真实 provider 联调时使用完整开发栈。

1. `cd docker`
2. `./init_env.sh dev`，并填写 `DATABASE_URL`、`REDIS_URL`、`SECRET_KEY`
   以及按需填写 AI Key
3. `./dev_in_docker.sh`

主要容器：

- `ai-video-nginx` / `ai-video-frontend` / `ai-video-backend`
- `ai-video-celery-worker` / `ai-video-celery-beat`
- `ai-video-mysql` / `ai-video-redis`

数据库迁移会在后端容器启动时通过 `docker/backend-entrypoint.sh` 自动执行。如果只更新
代码但没有重启后端，可能出现 `Unknown column ...` 这类错误，可运行：

- `cd docker && ./migration_guard.sh check dev`
- `cd docker && ./migration_guard.sh fix dev`

## 本地开发（不使用 Docker）

后端：

```bash
cd ai-pic-backend
cp env.example .env

pip install -r requirements.txt -r requirements-test.txt
alembic upgrade head
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

前端：

```bash
cd ai-pic-frontend
npm install

export NEXT_PUBLIC_API_URL=http://localhost:8000

npm run dev
```

## Harness 工作流

默认 harness 入口：

- `scripts/harness/bootstrap_worktree.sh --mode lite`
- `python scripts/harness/doctor.py --run-id <run_id>`
- `python scripts/harness/browser_flow.py --scenario login_smoke --run-id <run_id>`
- `python scripts/harness/run_golden_path.py --scenario mock_smoke --run-id <run_id>`
- `python scripts/harness/query_logs.py --run-id <run_id>`
- `python scripts/harness/query_metrics.py --run-id <run_id>`
- `python scripts/harness/trace_run.py --run-id <run_id>`
- `python scripts/harness/trace_task.py --task-id <task_id>`
- `python scripts/harness/score_quality.py --run-id <run_id> --write-quality-score`

所有 harness 证据写入 `artifacts/runs/<run_id>/`，包含 manifest、summary、console、
network、DOM snapshot、截图和具体场景的浏览器证据。Contract audit 会写入
`artifacts/repo_audit/latest/`。

## 提示词与故事形态

系统支持按故事形态分流提示词：

- `story_format`：默认 `short_drama`，另有 `tv_series`、`film`
- 前端“AI 生成故事”表单提供故事形态选择
- 提示词模板目录：`ai-pic-backend/app/prompts/templates/`

命名约定：

- 基础模板：`story_outline`、`system_prompt_story`、`system_prompt_script`、
  `episode_generation`、`script_scenes`
- 变体模板：`<base>_tv_series`、`<base>_film`

解析逻辑位于：

- `ai-pic-backend/app/prompts/template_resolver.py`
- `ai-pic-backend/app/prompts/manager.py`

## 导出知乎体小说

- 入口：故事详情页，`导出知乎体小说`
- 方式：异步任务 + Celery worker；页面轮询任务进度，完成后下载 `.txt`
- 后端接口：
  - `POST /api/v1/stories/business/{story_business_id}/novel/generate-async`
  - `GET /api/v1/stories/novel/tasks/{task_id}/download`
- 提示词模板：`system_prompt_novel_zhihu`、`story_novel_zhihu_plan`、
  `story_novel_zhihu_chapter`
- 导出落盘：`uploads/exports/novels/`
- 导出入库：`story_novel_exports`

## Agent 状态图

LangGraph 支持将状态机导出为 Mermaid 和 PNG。仓库内只为实际构建 `StateGraph` 的
生成链路生成快照。`StoryLangGraphAgent` 和 `EpisodeLangGraphAgent` 当前是
structured repair loop，类名保留用于兼容，不作为 LangGraph 图列出。

- 生成脚本：`python scripts/generate_agent_graphs.py`
- 输出目录：`docs/agent_graphs/`

当前包含的状态图：

- `ScriptLangGraphAgent`：剧本生成
- `StoryboardPipeline`：显式分镜管线
- `StoryboardReActReasoner`：分镜规划、评审和生成
- `TimelineLangGraphAgent`：legacy 对白节奏/间隔计算
- `DurationOrchestratorAgent`：experimental 端到端时长闭环验证

## 验证

常用验证命令：

```bash
cd ai-pic-backend && pytest
cd ai-pic-frontend && npm run lint
python scripts/check_repo_docs.py
python scripts/check_repo_contracts.py --mode audit
```

## 文档入口

- 总索引：`docs/README.md`
- 架构约束：`ARCHITECTURE.md`
- 前端规则：`FRONTEND.md`
- 可靠性与 trace：`RELIABILITY.md`
- 安全约束：`SECURITY.md`
- 质量面板：`QUALITY_SCORE.md`
- Docker 栈：`docker/README.md`
- 后端说明：`ai-pic-backend/README.md`
- 前端说明：`ai-pic-frontend/README.md`

## 故障排查

- `/stories` 等页面显示为空或加载失败，后端日志出现
  `Unknown column 'stories.story_format'`：说明数据库 schema 落后，运行
  `alembic upgrade head`，Docker 环境可用 `docker exec ai-video-backend ...`。
- 小说导出任务一直 `pending` 或 `processing`：确认 Redis 和
  `ai-video-celery-worker` 正常运行，并查看 worker 日志。
- Nginx 入口偶发 `502 Bad Gateway`：通常是容器 IP 变更导致 upstream 缓存，
  运行 `docker restart ai-video-nginx`。

## 许可证

本项目使用 MIT License，详见 [LICENSE](LICENSE)。
