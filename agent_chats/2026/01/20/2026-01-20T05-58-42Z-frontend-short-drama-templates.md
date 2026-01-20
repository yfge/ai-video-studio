---
id: 2026-01-20T05-58-42Z-frontend-short-drama-templates
date: 2026-01-20T05:58:42Z
participants: [human, codex]
models: [gpt-5.2]
tags: [frontend, templates, short-drama]
related_paths:
  - ai-pic-frontend/src/utils/shortDramaTemplates.ts
  - ai-pic-frontend/src/components/features/stories/StoryBasicsSection.tsx
  - ai-pic-frontend/src/components/features/episode/ScriptGenerationForm.tsx
  - ai-pic-frontend/src/components/features/episode/ShortDramaScriptTemplateSelector.tsx
summary: "Add selectable short-drama story/script templates to guide爽点/卡点结构 during generation."
---

## User Prompt

添加一个短剧故事模板和剧本模板，要求每一集都有爽点；并在选择不同 provider 时可动态加载输入以得到额外信息；要求原子化分布提交。

## Goals

- 为“短剧故事生成”提供可选模板，快速填充市场/微类型/节奏与额外要求（爽点/卡点约束）。
- 为“剧本生成”提供可选短剧模板，将爆款结构要求自动合并到额外要求中。
- 在 UI 上可见且可用，便于全流程测试与运营复用。

## Changes

- 新增短剧模板定义 `ai-pic-frontend/src/utils/shortDramaTemplates.ts`（故事模板 + 剧本模板）。
- 故事生成弹窗：当 `story_format=short_drama` 时显示“短剧故事模板（可选）”，选择后自动填充表单及节奏模板字段：`ai-pic-frontend/src/components/features/stories/StoryBasicsSection.tsx`。
- 剧本生成表单：新增“短剧剧本模板（可选）”选择器，选择后将模板 `additional_requirements` 合并进当前输入：`ai-pic-frontend/src/components/features/episode/ScriptGenerationForm.tsx`、`ai-pic-frontend/src/components/features/episode/ShortDramaScriptTemplateSelector.tsx`。

## Validation

- `cd ai-pic-frontend && npm run lint`（0 errors）。
- Chrome (MCP) 手动路径验证：
  - `http://localhost:8089/stories` → 点击“AI生成故事” → 选择“故事形态=短剧”后可见“短剧故事模板（可选）”下拉框。
  - 进入任一剧集工作台的“剧本”tab，在生成表单中可见“短剧剧本模板（可选）”并包含“爆款结构（HOOK→升级→PAYOFF→CLIFFHANGER）”选项。

## Next Steps

- 将 Google Veo 视频生成调用对齐 Vertex 文档（`predictLongRunning` + 新响应结构），并补齐 OSS 上传链路对 `bytesBase64Encoded` 的支持。

## Linked Commits

- (this commit) feat(frontend): add short-drama story/script templates
