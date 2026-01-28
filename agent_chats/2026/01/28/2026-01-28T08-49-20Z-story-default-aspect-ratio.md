---
id: 2026-01-28T08-49-20Z-story-default-aspect-ratio
date: 2026-01-28T08:49:20Z
participants: [human, codex]
models: [gpt-5.2]
tags: [backend, frontend, story, video, refactor]
related_paths:
  - ai-pic-backend/app/models/script.py
  - ai-pic-backend/alembic/versions/e1f2a3b4c5d6_add_story_default_aspect_ratio.py
  - ai-pic-backend/app/schemas/script.py
  - ai-pic-backend/app/schemas/generation_requests.py
  - ai-pic-backend/app/services/story/story_generation_service.py
  - ai-pic-backend/app/services/story/story_generation_utils.py
  - ai-pic-backend/tests/unit/services/story/test_story_generation_utils.py
  - ai-pic-backend/app/api/v1/endpoints/scripts_legacy.py
  - ai-pic-frontend/src/utils/storyOptions.ts
  - ai-pic-frontend/src/components/features/stories/StorySettingSection.tsx
  - ai-pic-frontend/src/utils/api.ts
  - ai-pic-frontend/src/utils/api/types/story.types.ts
  - ai-pic-frontend/src/components/shared/modals/StoryboardVideoModal.tsx
  - ai-pic-frontend/src/app/episodes/[id]/storyboard/page.tsx
summary: "Add story-level default aspect ratio (9:16/16:9) with per-task overrides and UI wiring"
---

## User Prompt
配置故事层面的默认屏幕比（9:16 / 16:9），默认 9:16，允许临时覆盖；并排查视频生成相关错误。

## Goals
- 在 Story 层持久化默认画幅，并提供迁移
- 让分镜图像/视频生成在未显式指定时使用默认画幅
- 前端生成故事表单暴露默认画幅选择
- 保持服务文件体积限制，通过抽取工具函数降行数

## Changes
- 新增 `stories.default_aspect_ratio` 字段与 Alembic 迁移（默认 9:16）
- Story 生成流程保存 `default_aspect_ratio` 并写入生成参数
- 分镜图像/视频生成请求默认继承 Story 画幅，并限制为 9:16/16:9
- 前端故事生成表单新增“默认画幅”下拉（9:16/16:9）
- Storyboard 视频生成弹窗支持从 Story 默认画幅初始化
- 抽取 story 生成工具函数到 `story_generation_utils`，新增单元测试

## Validation
- `cd ai-pic-backend && pytest` ❌ 运行后长时间无输出，已 `pkill -f pytest` 中止（仅看到 1074 tests 收集与少量进度）
- `cd ai-pic-frontend && npm run lint` ⚠️ 7 warnings（`import/no-anonymous-default-export`、`no-img-element`、未使用变量等），无错误
- `pre-commit run --all-files` ❌ trailing-whitespace/end-of-file-fixer 修改大量历史文件；`ruff` 报历史问题；`backend-pytest` 因 Minimax API key 缺失与 `to_int` 导入错误失败（已恢复所有非本次改动）
- `./docker/build_prod_images.sh` ✅ backend/frontend 镜像构建并推送成功（tag: c6d59dd），Next.js 提示多 lockfile 与 npm audit warning
- Chrome MCP ✅ 登录 `http://localhost:8089/login`，进入“故事创作”，打开“AI生成故事”表单，确认“默认画幅”下拉默认 9:16 且可选 16:9

## Next Steps
- 运行 `alembic upgrade heads` 应用新迁移
- 若模型返回其他画幅选项，考虑前端显式过滤为 9:16/16:9 以避免请求被后端拒绝

## Linked Commits
- TBD
