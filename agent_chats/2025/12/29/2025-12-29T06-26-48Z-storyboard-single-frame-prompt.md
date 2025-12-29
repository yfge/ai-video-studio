---
id: 2025-12-29T06-26-48Z-storyboard-single-frame-prompt
date: 2025-12-29T06:26:48Z
participants: [human, codex]
models: [gpt-5.2]
tags: [backend, storyboard, prompt, image]
related_paths:
  - ai-pic-backend/app/prompts/templates/storyboard_image_prompt.txt
  - ai-pic-backend/app/prompts/templates/storyboard_image_prompt.yaml
  - ai-pic-backend/app/prompts/templates/storyboard_image_fallback.txt
  - ai-pic-backend/app/prompts/templates/storyboard_image_fallback.yaml
  - ai-pic-backend/app/prompts/templates/storyboard_keyframe.txt
  - ai-pic-backend/app/prompts/templates/storyboard_keyframe.yaml
  - ai-pic-backend/tests/unit/test_storyboard_prompt_templates.py
summary: "Prevent storyboard image prompts from producing multi-panel/collage outputs."
---

## User Prompt

分镜生成的提示词容易生成宫格/分屏图片（不可用）。需要调整分镜图片生成提示词，避免这种多格合成输出。

## Goals

- 在分镜图像生成提示词中明确要求“单幅画面”，并显式禁止拼接/分屏/多格漫画。
- 增加回归测试，避免后续模板调整时回退。
- 通过 Chrome 跑一次真实分镜图像生成验证。

## Changes

- 强化 `storyboard_image_prompt`：追加“只生成单幅画面/禁止拼接分屏/禁止文字UI水印”等硬约束。
- 强化 `storyboard_image_fallback` 与 `storyboard_keyframe`：同样追加单幅画面与禁用拼接等约束，覆盖缺省与首尾关键帧模式。
- 新增单测 `ai-pic-backend/tests/unit/test_storyboard_prompt_templates.py`，确保关键约束文本存在。

## Validation

- Backend: `cd ai-pic-backend && pytest -q tests/unit/test_storyboard_prompt_templates.py`
- Chrome (MCP):
  - 登录后打开 `http://localhost:8089/episodes/cd378417b7f143eab5bc6d063cd7f6e7/storyboard?scriptId=58`
  - 在“选择参考图生成关键帧”中使用提示词 `老拐, 执行最终压力测试...` 提交任务
  - 任务完成后页面出现新候选图（例如 `.../20251229/062241/c61ad9b6.png`），结果为单幅画面而非多格拼接
- Docker: `./docker/build_prod_images.sh`

## Next Steps

- 若仍出现多格：为支持 `negative_prompt` 的 provider 补充统一的“anti-collage”负向提示并在分镜生成链路传入。
- 继续把分镜帧 `ai_prompt` 从“剪辑备注+镜头语言”拆分为结构化字段，避免模型把“镜头切换”等误当成多镜头合成指令。

## Linked Commits

- (pending)

