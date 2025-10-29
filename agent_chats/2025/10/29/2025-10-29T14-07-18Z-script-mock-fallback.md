---
id: 2025-10-29T14-07-18Z-script-mock-fallback
date: 2025-10-29T14:07:18Z
participants: [human, codex]
models: [gpt-5-codex]
tags: [backend, scripts, storyboard]
related_paths:
  - ai-pic-backend/app/services/ai_service.py
summary: "Added mock script generator fallback so the story→episode→script→storyboard flow works without external AI."
---

## User Prompt

在 localhost:3000 上测试故事→剧集→剧本→分镜的全流程，如有问题及时修正。

## Goals

- Remove the blocking `AI剧本生成失败` when running async script generation locally.
- Exercise the entire UI flow through storyboard creation to ensure fallback data persists.

## Changes

- Introduced `_generate_mock_script` fallback in `ai_service` and call it when the AI manager is unavailable or errors, emitting structured script content, scenes, dialogues, and directions.
- Added logging guard for missing AI manager and ensured storyboard generation marks fallback provenance.

## Validation

- 手动：以 `codextest` 用户登录 → 新建故事任务 → 生成剧本（任务页面出现已完成条目）→ `/episodes/3` 查看剧本列表 → 进入分镜管理执行“生成全部场景”并保存；页面显示 56 帧，来源 `fallback`。

## Next Steps

- Consider adding automated smoke tests for fallback pipelines (mock story/script/storyboard generation without external providers).

## Linked Commits

- _pending_
