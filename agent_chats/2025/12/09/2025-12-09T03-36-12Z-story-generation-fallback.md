---
id: 2025-12-09T03-36-12Z-story-generation-fallback
date: 2025-12-09T03:36:12Z
participants: [human, codex]
models: [gpt-4o-mini]
tags: [backend, stories, ai]
related_paths:
  - ai-pic-backend/app/services/ai_service.py
  - ai-pic-backend/app/api/v1/endpoints/stories.py
  - ai-pic-backend/tests/test_story_generation_fallback.py
summary: "Add resilient fallback for AI story generation and normalize async story creation output"
---
## User Prompt
AI 生成故事又不好用了

## Goals
- Diagnose why AI 故事生成返回失败并改进容错
- 确保异步故事生成能落库并附带完整元数据
- 增加回退路径的覆盖测试

## Changes
- ai_service.generate_story_outline 现在在 AI 管理器缺失或返回 failure 时自动退回文本生成链/模拟输出，并在失败时记录 provider 错误
- 异步故事生成流程使用与同步一致的 JSON 规范化和 extra_metadata 处理，避免空内容导致任务失败
- 新增测试覆盖无 AI 提供商场景，验证回退输出含标准字段

## Validation
- `cd ai-pic-backend && pytest`（整体套件在 120s 超时前出现大量既有失败，未能完成）
- `cd ai-pic-backend && pytest tests/test_story_generation_fallback.py`
- Chrome MCP：登录 geyunfei / Gyf@845261，在故事页创建异步故事“回归测试-故事生成fallback”（剧情，现代都市，北京，角色老拐/文闻，额外要求严格 JSON 并允许回退）；前端弹出“故事生成成功！”；列表未立即出现新故事，任务页未显示该标题，可能与运行中的后端/数据库实例不一致，需进一步确认

## Next Steps
- 确认运行中的后端是否加载了最新代码及指向的数据库实例；核对新任务/故事未显现的原因
- 重跑完整 pytest 套件或修复现有环境下的大量既有失败
- 待环境对齐后重新在 UI 检查新故事是否成功落库

## Linked Commits
- (pending)
