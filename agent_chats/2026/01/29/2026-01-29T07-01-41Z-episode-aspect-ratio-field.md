---
id: 2026-01-29T07-01-41Z-episode-aspect-ratio-field
date: "2026-01-29T07:01:41Z"
participants: [human, codex]
models: [gpt-5]
tags: [backend, db, episodes, aspect-ratio]
related_paths:
  - ai-pic-backend/app/models/script.py
  - ai-pic-backend/app/schemas/script.py
  - ai-pic-backend/alembic/versions/f621ea056717_add_episode_aspect_ratio.py
  - tasks.md
summary: "Add optional Episode.aspect_ratio (inherits story default) and expose via API schema."
---

## User Prompt

把“屏幕比/画幅”抽象到 Series/Story/Episode 层面：默认 9:16，仅支持 9:16/16:9，允许临时覆盖，并按 `tasks.md` 推进。

## Goals

- 为 Episode 增加可选画幅字段，作为 story 默认画幅的覆盖层。
- 让该字段在 API schema 中可读可写，为后续“分镜图/视频参数贯通”和前端设置页做准备。

## Changes

- `ai-pic-backend/app/models/script.py`
  - 在 `Episode` 模型新增 `aspect_ratio`（可空），用于覆盖 Story.`default_aspect_ratio`。
- `ai-pic-backend/app/schemas/script.py`
  - 在 `EpisodeBase`/`EpisodeUpdate` 增加 `aspect_ratio?: "9:16" | "16:9"` 字段说明。
- `ai-pic-backend/alembic/versions/f621ea056717_add_episode_aspect_ratio.py`
  - 新增 alembic 迁移：为 `episodes` 表添加 `aspect_ratio` 列（可空）。
- `tasks.md`
  - 将 P0-1 “Episode 增加 `aspect_ratio`”子任务标记为完成。

## Validation

- 单元/服务/脚本测试：
  - `cd ai-pic-backend && pytest tests/unit tests/services tests/scripts`
- Docker 数据库迁移：
  - `docker exec ai-video-backend alembic upgrade head`（已升级到 `f621ea056717`）
  - `docker restart ai-video-backend ai-video-celery-worker`
  - `docker exec ai-video-backend python -c ...` 验证 `Episode.aspect_ratio` 可读取（存量数据为 `NULL`，表示继承 story 默认）
- 生产镜像构建：
  - `./docker/build_prod_images.sh`
- Chrome（MCP）冒烟：
  - 登录 `http://localhost:8089/login`（geyunfei / Gyf@845261）
  - 打开 `http://localhost:8089/episodes/131/storyboard` 页面正常渲染（无 SQL column missing 错误）

## Next Steps

- 统一画幅解析函数（request override > episode > story > 9:16），并贯通到分镜图/分镜视频生成参数与前端弹窗默认值。

## Linked Commits

- (pending)

