---
id: 2025-10-29T07-05-00Z-story-structure-er-draft
date: 2025-10-29T07:05:00Z
participants: [human, codex]
models: [gpt-5-codex]
tags: [backend, docs]
related_paths:
  - docs/story-structure-gap-analysis.md
summary: "Added mermaid ER diagram aligning Story→Episode→Script with Treatment-to-Shot normalization"
---

## User Prompt
检查tasks.md 规划下一步的工作；完成 Feature “叙事结构与数据模型对齐” 的下一行动项，准备 ER 草图并补充字段草案。

## Goals
- Translate discovery output into a visual ER draft covering treatments, step outlines, scenes, beats, and shots.
- Capture relationships between normalized tables and existing entities for upcoming migrations.
- Keep documentation in `docs/story-structure-gap-analysis.md` as the authoritative reference.

## Changes
- Embedded a Mermaid ER diagram illustrating relationships among stories, treatments, step outlines, scripts, scenes, beats, shots, and storyboard assets inside `docs/story-structure-gap-analysis.md`.

## Validation
- Documentation-only change; manual review of rendered Markdown diagram.

## Next Steps
- Share ER draft during discovery session for stakeholder validation.
- Refine column enumerations after aligning on approval/version workflows.

## Linked Commits
N/A
