---
id: 2025-12-07T11-30-00Z-model-selector-fallback
date: 2025-12-07T11:30:00Z
participants: [human, codex]
models: [gpt-4o-mini]
tags: [frontend, models]
related_paths:
  - ai-pic-frontend/src/components/ModelSelector.tsx
summary: "Model selector falls back to full list when provider filter empties options"
---

## User Prompt

- 生成剧本时模型列表为空了。

## Goals

- 避免因 provider 过滤导致模型下拉为空。
- 保持首选过滤，但在无结果时回退到全部模型列表。

## Changes

- ModelSelector 先应用过滤，如无结果则自动回退到原始模型列表，确保下拉始终有可选项。

## Validation

- npm --prefix ai-pic-frontend run lint

## Next Steps

- 如仍出现空列表，检查后端 /api/v1/ai/models/available 返回内容及 provider 命名。

## Linked Commits

- (pending)
