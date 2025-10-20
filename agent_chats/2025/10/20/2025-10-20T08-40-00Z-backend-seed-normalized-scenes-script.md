---
id: 2025-10-20T08-40-00Z-backend-seed-normalized-scenes-script
date: 2025-10-20T08:40:00Z
participants: [human, codex]
models: [gpt-4o-mini]
tags: [backend, scripts]
related_paths:
  - ai-pic-backend/scripts/seed_normalized_scenes.py
  - ai-pic-backend/app/models/story_structure.py
  - ai-pic-backend/app/models/script.py
summary: "Add seeding script to populate normalized scenes from Script.scenes JSON for a given script id."
---

## User Prompt

继续推进，将现有剧本的 JSON 场景迁移为规范化 scenes 表的最小可用脚本，便于演示与验证前端试读。

## Goals

- 对单个 `script_id` 从 `Script.scenes` JSON 生成 `scenes` 表记录；
- 幂等：跳过已存在的 (script_id, scene_number)；支持 `--dry-run`。

## Changes

- 新增 `scripts/seed_normalized_scenes.py`：读取脚本 JSON 场景，构造 `slug_line`，生成递增 `scene_number`（若缺失），插入 `scenes`。

## Validation

- 工具仅在 Alembic 已应用的前提下执行；此变更不触发测试库写入。

## Next Steps

- 可扩展为批量脚本与镜头（shots）导入；后续也可挂接到管理端 API 作为一键导入任务。

## Linked Commits

- pending（本地增量补丁，后续与此台账一并提交）

