---
id: 2025-12-17T10-17-22Z-pipeline-visual-cue
date: 2025-12-17T10:17:22Z
participants: [human, codex]
models: [gpt-4o-mini]
tags: [frontend, timeline]
related_paths:
  - ai-pic-frontend/src/app/episodes/[id]/page.tsx
summary: "Add visual pipeline pills/arrows to clarify the dialogue→timeline→storyboard workflow on episode page."
---

## User Prompt
那么现在的工作流具体是什么样的；再把“生成对白音轨/生成时间轴/生成分镜帧占位”加上流程箭头并更明确。

## Goals
- Make the episode page clearly show the three-step flow (对白音轨 → 时间轴 → 分镜占位).
- Provide immediate visual cue on which steps are completed.

## Changes
- Added pipeline pill chips with arrow separators under “对白音轨与时间轴” to show the three steps and completion state (based on scene audio count, timeline presence, storyboard presence).

## Validation
- `npm run lint` (ai-pic-frontend) — pass.

## Next Steps
- When timeline and storyboard are regenerated, ensure the pills turn green to reflect completion; consider tying states to task statuses for finer granularity.

## Linked Commits
- (pending)
