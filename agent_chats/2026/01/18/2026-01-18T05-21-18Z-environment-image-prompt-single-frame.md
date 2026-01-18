---
id: 2026-01-18T05-21-18Z-environment-image-prompt-single-frame
date: 2026-01-18T05:21:18Z
participants: [human, codex]
models: [gpt-5.2]
tags: [backend, prompts, image_gen, environment]
related_paths:
  - ai-pic-backend/app/prompts/templates/environment_image.txt
summary: "Clarify environment prompt as single-frame and add no-collage constraint"
---

## User Prompt

全局检查文生图/图生图提示词规范，确认模板语义是否合适，并按 provider 可进一步优化。

## Goals

- 环境图提示词明确“单幅画面”，避免被“远景->中景->近景”误解成多格/拼图
- 统一与分镜模板一致的“no collage”约束语义

## Changes

- `environment_image.txt`：
  - 明确单帧构图（远景/中景/近景层次仍在同一张图内）
  - Constraints 追加 `no collage / no split-screen / no multi-panel`

## Validation

- `cd ai-pic-backend && pytest tests/unit/test_image_prompt_templates.py`
- `./docker/build_prod_images.sh`
- Chrome (MCP): 打开 `http://localhost:8089/environments/aab17f172446462a97e738772337d272`，确认页面可正常加载（环境 AI 生成入口可用）

## Next Steps

- 梳理各域（虚拟 IP / 环境 / 分镜）模板中中英混用与“标签式字段”对文字伪影的影响，必要时按 provider 做分支优化
- 继续对齐各 provider 的 negative_prompt / reference_images 行为，并在 UI 元数据中提示限制

## Linked Commits

- (pending)
