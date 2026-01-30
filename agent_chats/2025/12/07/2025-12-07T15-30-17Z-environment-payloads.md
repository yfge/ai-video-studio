---
id: 2025-12-07T15-30-17Z-environment-payloads
date: 2025-12-07T15:30:17Z
participants: [human, codex]
models: [gpt-4o-mini]
tags: [backend, environment, docs, testing]
related_paths:
  - ai-pic-backend/app/api/v1/endpoints/story_structure.py
  - task.md
summary: "Make environment image generation endpoints accept JSON payloads, clamp counts, and refresh tasks; verified via Chrome Seedream 4.5 run and pytest"
---

## User Prompt

可以，现在按照tasks.md对环境管理的规划，整体完成环境管理这个功能，注意要保证chrome测试完整 以及提交的原子性。

## Goals

- Fix environment 文生图/图生图接口 so frontend JSON payloads (model/count/size/base_image) are honored instead of being ignored.
- Keep task 看板与环境管理现状同步，并完成一次真实浏览器验证。

## Changes

- Backend (`story_structure.py`): environment image generate/variant endpoints now parse JSON payloads (prompt/model/count/size/base_image), clamp count to 1-4, and infer providers from provided models before calling `ai_manager`.
- Docs (`task.md`): marked环境绑定与管理 UI 完成，补充下一步（环境/角色锚点注入分镜生成、补测试）。

## Validation

- `pytest tests/test_story_structure_endpoints.py -q` (pass; existing deprecation warnings only).
- Chrome manual: 登录 `/environments`，将模型切换为 Seedream 4.5，点击“一键生成参考图”，成功生成并展示 1 张环境参考图（uploads/4449b113dd6a4658a71bd1f7966180f1.png），弹出“操作成功”。

## Next Steps

- 把环境参考图与镜头角色图一并传入分镜图像生成链路；为该链路补充端到端/权限校验测试并记录在 TESTING_GUIDE。
- 提供自定义提示词/尺寸的前端表单，并将结果写回场景/镜头生成参数。

## Linked Commits

- pending
