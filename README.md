# ai-video-studio（AI 短剧/影视剧制作工作流平台）

以**虚拟 IP**为核心的 AI 内容生产平台，覆盖故事（Story）→ 分集（Episode）→ 剧本（Script）的生成与编辑流程，并集成多种图像/文本/视频模型与 OSS 存储。

## 仓库结构

- `ai-pic-backend/`：FastAPI + SQLAlchemy + Alembic + Celery（MySQL/Redis）
- `ai-pic-frontend/`：Next.js 15（App Router）+ TypeScript + Tailwind
- `docker/`：本地开发/生产 Docker 编排与 Nginx 入口
- `docs/`：设计/接口/测试指南索引（见 `docs/README.md`）
- `tasks.md`：项目任务看板（唯一权威）

## 快速开始（推荐：Docker 开发栈）

1. `cd docker`
2. `cp .env.example .env` 并填写必要配置（至少 `DATABASE_URL`、`REDIS_URL`、`SECRET_KEY`；AI Key 按需）
3. `./dev_in_docker.sh`

访问：

- Web（Nginx 入口）：`http://localhost:8089`
- Backend API（直连）：`http://localhost:8000`（Swagger：`http://localhost:8000/docs`）

服务容器名：

- `ai-video-nginx` / `ai-video-frontend` / `ai-video-backend`
- `ai-video-celery-worker` / `ai-video-celery-beat`
- `ai-video-mysql` / `ai-video-redis`

数据库迁移：

- 容器启动时会自动执行 `alembic upgrade head`（见 `docker/backend-entrypoint.sh`）。
- 如果你**只更新了代码但没重启后端**，可能出现 “Unknown column …” 这类 500；此时运行：`docker exec ai-video-backend alembic upgrade head` 然后刷新页面。

## 本地开发（不使用 Docker）

### 后端

```bash
cd ai-pic-backend
cp env.example .env

pip install -r requirements.txt -r requirements-test.txt
alembic upgrade head
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 前端

```bash
cd ai-pic-frontend
npm install

# 指向后端 API（示例：直连 8000）
export NEXT_PUBLIC_API_URL=http://localhost:8000

npm run dev
```

## 提示词与“故事形态”（短剧/电视剧/电影）

系统对不同体裁的提示词支持**按故事形态分流**：

- `story_format`：`short_drama`（默认）、`tv_series`、`film`
- 前端在“AI 生成故事”面板提供“故事形态”下拉，后端会选择对应提示词变体
- 提示词模板目录：`ai-pic-backend/app/prompts/templates/`

命名约定（在不改调用方的前提下分流）：

- 基础模板：`story_outline` / `system_prompt_story` / `system_prompt_script` / `episode_generation` / `script_scenes`
- 变体模板：`<base>_tv_series`、`<base>_film`

解析逻辑位于：

- `ai-pic-backend/app/prompts/template_resolver.py`
- `ai-pic-backend/app/prompts/manager.py`

## 故事导出“知乎体小说”（1–3 万字）

- 入口：故事详情页 → `导出知乎体小说`
- 方式：异步任务 + Celery worker；页面会轮询任务进度，完成后可下载 `.txt`
- 后端接口：
  - `POST /api/v1/stories/business/{story_business_id}/novel/generate-async`
  - `GET /api/v1/stories/novel/tasks/{task_id}/download`
- 提示词模板：`system_prompt_novel_zhihu` / `story_novel_zhihu_plan` / `story_novel_zhihu_chapter`
- 导出落盘：`uploads/exports/novels/`
- 导出入库：`story_novel_exports`（关联 `tasks.id` / `stories.id`，正文存 `content_text`；下载接口在文件缺失时会回退读取数据库）

## 常用验证命令

```bash
# backend
cd ai-pic-backend && pytest

# frontend
cd ai-pic-frontend && npm run lint
```

## 文档入口

- 总索引：`docs/README.md`
- Docker 栈：`docker/README.md`
- 后端说明：`ai-pic-backend/README.md`
- 前端说明：`ai-pic-frontend/README.md`

## Troubleshooting

- `/stories` 等页面显示“空/加载失败”，后端日志出现 `Unknown column 'stories.story_format'`：
  - 说明数据库未升级到最新 schema；运行 `alembic upgrade head`（Docker 用 `docker exec ai-video-backend …`）。
- 小说导出任务一直 `pending/processing`：
  - 确认 Redis/Celery worker 正常运行（Docker 栈中为 `ai-video-celery-worker`），并查看 worker 日志。
- Nginx 入口偶发 `502 Bad Gateway`（Docker 容器 IP 变更导致 upstream 缓存）：
  - 重启 Nginx：`docker restart ai-video-nginx`。
