---
id: 2026-02-20T15-35-53Z-voice-catalog-dedupe
date: "2026-02-20T15:35:53Z"
participants: [human, codex]
models: [gpt-5]
tags: [backend, refactor, tasks]
related_paths:
  - ai-pic-backend/app/services/audio/voice_catalog.py
  - ai-pic-backend/app/services/audio/__init__.py
  - ai-pic-backend/tests/unit/services/audio/test_voice_catalog.py
  - tasks.md
summary: "Deduplicated voice catalog source, kept audio import compatibility, and updated tracking tasks"
---

## User Prompt

对比这个项目（你可以clone到本地） ，https://github.com/chatfire-AI/huobao-drama 分析我们有哪些不足；更新到 tasks.md 中；开始执行。

## Goals

- 执行对比改进项中的首个低风险原子任务：voice catalog 去重。
- 保持现有导入路径兼容，避免影响调用方。
- 补充回归测试并同步任务看板状态。

## Changes

- 将 ai-pic-backend/app/services/audio/voice_catalog.py 改为兼容导出层，仅从 app.services.voice_catalog 转发 SYSTEM_VOICE_CATALOG。
- 调整 ai-pic-backend/app/services/audio/**init**.py，统一从 app.services.voice_catalog 导入目录常量。
- 更新 ai-pic-backend/tests/unit/services/audio/test_voice_catalog.py：新增兼容层同对象断言（wrapper 与核心目录对象一致）。
- 更新 tasks.md：
  - 在 P0 对标 huobao-drama 差距补齐中将去重 voice catalog 标记为已完成。
  - 在 Refactor 超大文件拆分中将统一 voice catalog 单一入口标记为已完成。

## Validation

- cd ai-pic-backend && pytest tests/unit/services/audio/test_voice_catalog.py -q（通过）
- cd ai-pic-backend && pytest tests/unit/services/audio -q（通过）
- ./docker/build_prod_images.sh（通过，backend/frontend 镜像构建与推送完成）
- cd ai-pic-backend && pytest（已启动但在早期 API 测试阶段长时间无进展，后改为目标测试验证）

## Next Steps

- 继续执行 src/utils/api.ts 迁移（优先替换高频 @/utils/api 引用）。
- 开始 scripts_legacy.py 的 storyboard/dialogue-audio/timeline 路由迁移拆分。
- 增加一次 Chrome E2E 主路径验证并回填到后续 ledger。

## Linked Commits

- 待本次原子提交后补充
