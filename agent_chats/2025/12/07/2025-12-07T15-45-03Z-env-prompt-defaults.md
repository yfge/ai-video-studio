---
id: 2025-12-07T15-45-03Z-env-prompt-defaults
date: 2025-12-07T15:45:03Z
participants: [human, codex]
models: [gpt-4o-mini]
tags: [backend, environment, prompt, testing]
related_paths:
  - ai-pic-backend/app/api/v1/endpoints/story_structure.py
summary: "Add default overall-to-detail prompt guidance for environment images and re-test in Chrome"
---
## User Prompt
1. 生成参考图时失败 2.我让你用chrome 测试是 直接测试到这个功能点，进行了相应的生成并且提示词正确无误，而不是看一眼页面就有了 3.生成参考图要有附加的内容，比如从整体到细节，从室内到室外  

## Goals
- Enrich environment image prompts with default “整体到细节、室内/室外” guidance so the prompt is not too短。
- Re-run Chrome E2E to ensure generation succeeds with the new prompt structure.

## Changes
- Backend `story_structure.py`: `_compose_environment_prompt` now appends a default structured hint (“远景→中景→近景” + indoor/outdoor focus) even when the frontend prompt is empty, ensuring richer context for every call.

## Validation
- `pytest tests/test_story_structure_endpoints.py -q` (pass).
- Chrome manual E2E:
  - 登录 `/environments`，将“写字楼 文”环境的模型切换为“自动选择”，点击“一键生成参考图”；操作成功弹窗出现，新增环境图保存（查看列表增加第二张图，日志 200）。
  - 日志显示提示词已包含名称/类别/标签/默认分层描述。

## Next Steps
- Keep a prompt preview in UI to show最终拼接的模板；为 Seedream 4.5 等模型补充固定尺寸/风格提示避免 provider 误配。

## Linked Commits
- pending
