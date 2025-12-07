---
id: 2025-12-07T08-50-00Z-story-model-selector
date: 2025-12-07T08:50:00Z
participants: [human, codex]
models: [gpt-4o-mini]
tags: [frontend, stories]
related_paths:
  - ai-pic-frontend/src/components/ModelSelector.tsx
  - ai-pic-frontend/src/app/stories/page.tsx
summary: "Fix story page model selector crash and restrict to OpenAI models"
---

## User Prompt

- 故事生成页模型选择白屏。

## Goals

- 修复故事页模型下拉导致的渲染报错。
- 只展示支持结构化输出的 OpenAI 文本模型，避免返回乱格式。

## Changes

- `ModelSelector` 支持 `filterModels` 解构，避免未定义引用导致渲染崩溃。
- 故事生成表单的模型下拉增加过滤，只展示 provider 为 openai 的文本模型，并补充说明。

## Validation

- 手工打开 `/stories` → “AI生成故事”弹框，模型下拉正常渲染，无白屏；模型列表仅显示 OpenAI 文本模型。

## Next Steps

- 后续如需开放其他 provider，需确保其支持 JSON Schema 结构化输出，再调整过滤条件。

## Linked Commits

- (pending)
