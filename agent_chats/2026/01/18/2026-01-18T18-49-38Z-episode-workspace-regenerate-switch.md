---
id: 2026-01-18T18-49-38Z-episode-workspace-regenerate-switch
date: 2026-01-18T18:49:38Z
participants: [human, codex]
models: [gpt-5.2]
tags: [frontend, fix, episode, workspace]
related_paths:
  - ai-pic-frontend/src/app/episodes/[id]/workspace/page.tsx
  - ai-pic-frontend/src/components/features/episode/WorkspaceScriptSelector.tsx
  - ai-pic-frontend/src/components/features/episode/index.ts
  - ai-pic-frontend/src/hooks/useEpisodeDetail.ts
  - ai-pic-frontend/src/hooks/episode/episodeWorkspaceScriptActions.types.ts
  - ai-pic-frontend/src/hooks/episode/scriptSort.ts
  - ai-pic-frontend/src/hooks/episode/useEpisodeWorkspaceController.ts
  - ai-pic-frontend/src/hooks/episode/useEpisodeWorkspaceGenerateScript.ts
  - ai-pic-frontend/src/hooks/episode/useEpisodeWorkspaceRegenerateScript.ts
  - ai-pic-frontend/src/hooks/episode/useEpisodeWorkspaceScriptActions.ts
  - ai-pic-frontend/src/utils/api/endpoints/script/core.endpoints.ts
  - tasks.md
summary: "Fix episode workspace so regenerated scripts auto-select and URL stays in sync."
---

## User Prompt

- 全局检查提示词规范，并按 provider 优化（后续拆分原子提交）。
- 当前优先：修复 `http://localhost:8089/episodes/.../workspace` 再生成剧本后仍停留旧剧本、内容不及格的问题排查。
- 要求：原子化分布提交、更新 `tasks.md`。

## Goals

- 修复 Episode workspace：点击“重新生成剧本”后，能自动切换到新生成的 script（并同步 `scriptId` 到 URL）。
- 保持页面组件/Hook 文件大小在规范范围内（TS/TSX ≤ 250 行，hooks ≤ 200 行）。
- 补充 `tasks.md` 记录。

## Changes

- 新增 `sortScriptsNewestFirst`，确保默认展示最新版本脚本（按 `version`/`created_at`/`id` 排序）。
- 提取 Episode workspace 的脚本选择器为独立组件，避免页面臃肿并复用选择逻辑。
- 将“生成/再生成剧本”动作拆分为独立 hooks：
  - `useEpisodeWorkspaceGenerateScript`：处理（同步/异步）生成流程。
  - `useEpisodeWorkspaceRegenerateScript`：处理再生成 + task 轮询 + 完成后自动选中。
  - `useEpisodeWorkspaceScriptActions`：聚合两个 hooks 给 workspace controller 使用。
- 再生成时写入 `sessionStorage` 的 pending task 信息，页面重载/中断后可自动续跑并最终切换到新 script。
- 同步更新脚本 regenerate 的 endpoint 类型签名（返回 task 响应）。
- 更新 `tasks.md` 增加前端修复记录。

## Validation

- Chrome E2E（MCP/DevTools）：
  - 登录：`geyunfei / Gyf@845261`
  - 打开：`/episodes/1cca3cc61d7740b4b5f73bccf8fe4d32/workspace?tab=script&scriptId=100`
  - 点击“重新生成剧本”→“确认重新生成”
  - 观察提示：`task_id=615`
  - 任务完成后自动切换到新脚本：`scriptId=101`，下拉框选中 `ID: 101`，URL 更新为 `...?scriptId=101`，并弹出“已生成新剧本（v1.6 / ID: 101）”
- `cd ai-pic-frontend && npm run lint`：0 errors（7 warnings）
- `./docker/build_prod_images.sh`：success（`[build_prod_images] Done.`，`IMAGE_TAG=b74388f`）

## Next Steps

- 继续拆分原子提交：全局检查文生图/图生图提示词模板与 provider 参数一致性，并按 provider 动态加载/补齐输入项。
- 排查“剧本内容不及格”的根因：后端剧本生成 prompt/约束、角色设定注入、结构化输出格式与 token/temperature 配置。

## Linked Commits

- fix(frontend): auto-select regenerated script in workspace
