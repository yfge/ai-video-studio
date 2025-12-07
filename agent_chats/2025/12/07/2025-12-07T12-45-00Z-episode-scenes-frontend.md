---
id: 2025-12-07T12-45-00Z-episode-scenes-frontend
date: 2025-12-07T12:45:00Z
participants: [human, codex]
models: [gpt-4o-mini]
tags: [frontend, episodes]
related_paths:
  - ai-pic-frontend/src/app/episodes/[id]/page.tsx
summary: "Render AI-generated scene list on episode detail and fallback scene counts"
---

## User Prompt

- 继续完成场景相关的功能。

## Goals

- 在剧集详情页展示 AI 返回的场景信息，并用其回填场景数。

## Changes

- 从 episode.extra_metadata/metadata 中提取 scenes，场景数缺失时用列表长度回填显示。
- 新增“场景列表”区块，展示编号、标题、地点/时间等，兼容多种字段名。

## Validation

- npm --prefix ai-pic-frontend run lint

## Next Steps

- 若需要展示 beats/镜头，进一步解析 scenes 内嵌结构或直接对接规范化 scenes 表。

## Linked Commits

- (pending)
