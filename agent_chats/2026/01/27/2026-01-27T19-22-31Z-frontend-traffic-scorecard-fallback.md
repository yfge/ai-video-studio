---
id: 2026-01-27T19-22-31Z-frontend-traffic-scorecard-fallback
date: 2026-01-27T19:22:31Z
participants: [human, codex]
models: [gpt-5.2]
tags: [frontend, scoring, microgenre, e2e]
related_paths:
  - ai-pic-frontend/src/components/features/script/ScriptTrafficTab.tsx
  - tasks.md
summary: "Fix Script 投流/评分页读取后端 nested scoring，补齐微类型闭环 E2E 验证。"
---

## User Prompt

- 继续完成 P0/P1 任务；每完成一个用 Chrome 做好测试并原子化提交。
- 本轮聚焦：短剧微类型闭环 E2E（投流/评分可视化 + 分镜侧验证）。

## Goals

- 修复 Script「投流/评分」Tab 不展示评分（后端已将评分写入 `extra_metadata.scoring.script_score`）。
- 在真实浏览器路径验证：脚本页可展示评分 + 分镜生成后可获取 hook_tag 数据。
- 更新 `tasks.md` 对应验证项状态。

## Changes

- 前端：`ScriptTrafficTab` 增加对 `script.extra_metadata.scoring.script_score` 的回退读取，保证总体评分/维度评分/风险与修订建议可展示。
- 看板：勾选 `tasks.md` 中「短剧微类型闭环 E2E 路径」验证项。

## Validation

- `cd ai-pic-frontend && npm run lint`（0 errors，warnings only）
- `./docker/build_prod_images.sh`（backend + frontend prod 镜像 build/push 成功）
- Chrome E2E（账号 `geyunfei`）：
  - 打开 `http://localhost:8089/scripts/113` → 切换到「投流/评分」Tab
    - 总体评分从 `—` 变为 `3.00`，维度评分/风险提示/修订建议正常展示
  - 打开 `http://localhost:8089/episodes/124/storyboard` → 「生成当前场景」
    - 生成任务 `task_id=5854` 完成，页面刷新后场景 1 分镜帧数为 `7`
  - API 侧确认 hook 标注数据存在：`GET /api/v1/scripts/113/storyboard` 返回 frames，包含 `hook_tag`（如“会议室紧张氛围”）

## Next Steps

- 若需要在分镜页直接可视化 `hook_tag` / `ad_snippet` 标注：补 UI（当前该页未展示 hook_tag 字段，数据已存在）。
- 继续推进下一条 P1：`tasks.md` 的「短剧全流程 E2E（IP→环境→故事→剧本→分镜图→分镜视频）」；若 Veo 未配置，先拆成「到分镜图」与「视频」两段验收。

## Linked Commits

- (current) 同提交。
