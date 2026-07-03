---
id: 2026-07-03T07-28-16Z-canvas-edge-controls-targets
date: "2026-07-03T07:28:16Z"
participants:
  - user
  - codex
models:
  - GPT-5 Codex
tags:
  - canvas
  - frontend
  - edge-controls
summary: Tightened infinite canvas edge target choices and labels.
related_paths:
  - ai-pic-frontend/src/components/features/canvas/ProductionCanvasEdgeControls.tsx
  - ai-pic-frontend/tests/productionCanvasEdgeControls.test.tsx
---

## User Prompt

- `/goal 继续完善无限画布功能`
- `你可以拉起 dev_in_docker  用内置浏览器检验`

## Goals

- Prevent the edge target selector from offering already-connected targets.
- Keep task evidence notes out of generic edge editing.
- Make duplicate edge target labels distinguishable.
- Show clear edge editor empty states.

## Changes

- Reset the pending edge target when the selected node changes.
- Filter existing outgoing targets and task evidence notes from the target select.
- Disable the target selector and add button when no targets remain.
- Render duplicate target and outgoing labels as `<label> · <title>`.
- Show `暂无连线` when the selected node has no outgoing edges.
- Added focused EdgeControls coverage for these behaviors.

## Validation

- `cd ai-pic-frontend && PATH=/Users/geyunfei/dev/yfge/ai-video-studio/ai-pic-frontend/node_modules/.bin:$PATH node --import tsx --test tests/productionCanvasEdgeControls.test.tsx` -> pass, 5 tests.

Browser validation:

- Attempted Codex in-app browser validation through the browser plugin.
- `browser.documentation()` was unavailable in the current runtime.
- `agent.browsers.list()` showed `Codex In-app Browser`, but `agent.browsers.get(...)` and `agent.browsers.getForUrl("http://localhost:8089/canvas")` both returned a disconnected Playwright browser with `isConnected() === false`.
- No browser page could be created, so no browser path is claimed for this slice.

## Next Steps

- Continue splitting the remaining infinite canvas worktree into small commits.
- Re-run browser validation when the in-app browser connection is available.

## Linked Commits

- This commit.
