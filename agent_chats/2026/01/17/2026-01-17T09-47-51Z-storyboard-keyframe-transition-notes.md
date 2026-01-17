---
id: 2026-01-17T09-47-51Z-storyboard-keyframe-transition-notes
date: 2026-01-17T09:47:51Z
participants: [human, codex]
models: [gpt-5.2]
tags: [backend, prompts, storyboard]
related_paths:
  - ai-pic-backend/app/prompts/templates/storyboard_keyframe.txt
  - ai-pic-backend/app/prompts/templates/fragments/image_macros.txt
  - ai-pic-backend/tests/unit/test_storyboard_prompt_templates.py
summary: "补齐 storyboard 关键帧提示词的转场语义，并增强 no-collage 约束与单测覆盖"
---

## User Prompt

全局检查文生图/图生图提示词规范，确认模板语义是否合适；如有问题修正。并要求原子化提交与更新 tasks.md。

## Goals

- 检查并修正 storyboard 关键帧（start/end keyframe）提示词在转场/切镜描述上的语义缺口
- 增强通用图像约束（no collage）以减少多宫格/拼贴误生成
- 用单测锁定关键语义，避免回归

## Changes

- 更新 `ai-pic-backend/app/prompts/templates/storyboard_keyframe.txt`：明确“镜头切换/转场/上一镜头”等是剪辑备注，不要在同一画面表现多个镜头
- 更新 `ai-pic-backend/app/prompts/templates/fragments/image_macros.txt`：扩展 `constraint_no_collage()` 到 `no collage, no split-screen, no multi-panel, no contact sheet`
- 更新 `ai-pic-backend/tests/unit/test_storyboard_prompt_templates.py`：断言 `STORYBOARD_KEYFRAME` 渲染结果包含“剪辑备注”语义

## Validation

- Backend pytest：
  - `cd ai-pic-backend && pytest tests/unit/test_storyboard_prompt_templates.py tests/unit/test_image_prompt_templates.py -q`
- 生产镜像构建：
  - `./docker/build_prod_images.sh`（输出包含 `[build_prod_images] Done.`，IMAGE_TAG=ab55ff5）
- Chrome E2E（MCP）：
  - 登录 `http://localhost:8089/login`（geyunfei / Gyf@845261）
  - 进入 `http://localhost:8089/episodes/10/storyboard`
  - 在包含“镜头快速切换 …”的分镜帧点击“选择参考图生成关键帧”，选择 Google `Gemini 2.0 Flash (image exp)`，点击“提交图生图任务”
  - 页面提示“操作成功 / 已创建图像生成任务”，任务列表中新增任务（ID: 595）

## Next Steps

- 继续梳理其它文生图/图生图模板的语义一致性（environment / virtual_ip / storyboard wrapper 等），并对齐各 provider 的参数能力矩阵与前端动态表单

## Linked Commits

- (pending)
