---
id: 2025-12-07T15-06-23Z-environment-image-pipeline
date: 2025-12-07T15:06:23Z
participants: [human, codex]
models: [gpt-4o-mini]
tags: [planning, storyboard, environment, image]
related_paths:
  - task.md
summary: "Plan for using character images + environment images + storyboard prompts as the canonical generation pipeline"
---

## User Prompt

我觉得最终在生成分镜画面的时候，是不是 人物图片+环境图片+分镜提示词才 能保证 最终的一致性？

对，规划进去，而且环境要绑定图像生成功能呢

## Goals

- Reflect in the task board that storyboard image generation should be driven by“人物图片 + 环境图片 + 分镜提示词”.
- Make it explicit that Environment 只做锚点（reference_images）绑定，不强制单独文生图。

## Changes

- Updated `Feature: 场景/环境资产与分镜联动` in `task.md`:
  - Clarified the生成链路为“文本提示 + 角色参考图 + 环境参考图 → 分镜图像；分镜图像 + 提示词 → 短视频”。
  - 新增“环境锚点”子任务：在分镜帧结构中挂 `environment_id`，生成时从 Environment.reference_images 选环境图，用作条件图而非单独生成。
  - 新增“角色锚点”子任务：从虚拟 IP 图像资产中自动选择角色参考图，使分镜生成输入统一为“人物图 + 环境图 + 分镜提示词”。
  - 新增“调用适配”子任务：规划统一的多图条件调用层，对接 Seedream / SDXL 等支持人物/环境图条件的模型。

## Validation

- No runtime behavior change; this is a planning/documentation update only.

## Next Steps

- Implement environment/character anchoring in the storyboard image generation API, then wire the front-end分镜生成弹窗来选择/展示这些锚点。

## Linked Commits

- pending
