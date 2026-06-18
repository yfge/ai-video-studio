## User Prompt

在现有基础上加一个无限画布的入口，是不是可以考虑？实现这个目标。

## Goals

- 在当前短剧制作台侧边栏增加“创作画布”入口。
- 增加 `/canvas` 页面，作为现有生产系统旁路入口。
- 第一版画布展示 Brief -> Script -> Storyboard -> Image Candidates -> Video Candidates -> Timeline -> Report 的可操作生产链路，不替代现有业务数据。
- 让画布具备最低可用能力：选择节点、拖拽节点、平移、缩放、适配视图、重置布局、添加临时便签，并在本地保存布局。
- 保持改动集中在前端入口、页面和测试，不改动现有后端生产链路。

## Changes

- Added the production navigation item `创作画布` at `/canvas`.
- Added a `canvas` navigation icon.
- Added `ProductionCanvasBoard` and `ProductionCanvasContent` for the first usable infinite canvas view.
- Added a canvas node and edge model for the current short-drama production chain.
- Added reusable canvas state helpers for node movement, viewport panning, zoom clamping, and note creation.
- Added canvas toolbar controls for note creation, zoom, fit, and reset.
- Added a node inspector and local layout persistence through `localStorage`.
- Split canvas rendering, controller state, and storage/geometry helpers so each TS/TSX file stays under the repository hard line limit.
- Added a Next.js route at `/canvas`.
- Added frontend tests for the navigation model, canvas icon, interactive canvas content, inspector behavior, and reusable canvas state helpers.
- Tightened canvas node positions so the whole chain is visible in the desktop first viewport and kept the mobile header action from wrapping.
- Fixed type safety in the current `useTimelineProductionCharacters.ts` worktree file so the frontend production build can complete: episode data is captured before `await`, and nullable story-character appearance is normalized to `undefined`.

## Validation

1. Local checks:

- `cd ai-pic-frontend && npx tsx --test tests/productionCanvasBoard.test.tsx` -> pass, 4 tests.
- `cd ai-pic-frontend && npx tsx --test $(find tests -type f \( -name '*.test.tsx' -o -name '*.test.ts' -o -name '*.test.js' \) ! -name 'toastProvider.test.tsx')` -> pass, 125 tests across 20 suites.
- `cd ai-pic-frontend && npm run test` -> attempted, but the process does not exit in the current worktree because `tests/toastProvider.test.tsx` hangs; single-running `npx tsx --test tests/toastProvider.test.tsx` also hangs after the first toast test output and was interrupted. The non-toast suite passed separately.
- `cd ai-pic-frontend && npm run lint` -> pass with 3 pre-existing warnings in `eslint.config.mjs`, `EnvironmentReferenceImagesField.tsx`, and `VirtualIPReferenceImagesField.tsx`.
- `cd ai-pic-frontend && npm run build` -> pass; route manifest includes `/canvas`.
- `python scripts/check_repo_docs.py` -> pass.
- `python scripts/check_repo_contracts.py --mode diff <canvas-entry changed files>` -> pass.
- `git diff --check -- <canvas-entry changed files>` -> pass.

2. Browser or MCP validation:

- Existing Next dev server on `http://127.0.0.1:3100` was reused because `.next/dev/lock` was held by an existing `next dev --port 3100` process.
- Playwright bundled Chromium was unavailable, so rendered validation used system Chrome at `/Applications/Google Chrome.app/Contents/MacOS/Google Chrome`.
- Desktop path: `http://127.0.0.1:3100/canvas` with local auth token seeded -> rendered the canvas, selected `Script`, showed the inspector, dragged `Script` by 88px, zoomed to `110%`, panned the canvas with a changed world transform, and added a `便签` node.
- Mobile path: `http://127.0.0.1:3100/canvas` at 390x844 -> rendered nonblank canvas content and visible canvas controls.
- Dev-server screenshot refresh saw transient `page.goto: net::ERR_ABORTED` during hot reload; retrying the same route succeeded.
- Screenshots:
  - `artifacts/runs/canvas-entry-20260618T0854Z/canvas.png`
  - `artifacts/runs/canvas-entry-20260618T0854Z/canvas-mobile.png`
  - `artifacts/runs/canvas-usable-20260618T0915Z/canvas-usable-desktop.png`
  - `artifacts/runs/canvas-usable-20260618T0915Z/canvas-usable-mobile.png`

3. Conflict signals and corrections:

- Initial unit test rendering `ProductionCanvasBoard` directly failed because `OperatorShell` requires Next router context. The canvas body was split into `ProductionCanvasContent` so unit tests cover the pure canvas view while route/build/browser validation covers the shell integration.
- Initial mobile screenshot showed the header action wrapping into a vertical label. The action was moved behind a responsive wrapper and revalidated on mobile.
- Initial desktop screenshot clipped the terminal nodes. Node positions were tightened and revalidated on desktop.
- Initial `npm run build` failed on `src/components/features/episode/useTimelineProductionCharacters.ts` because `episodeResponse.data` was possibly undefined after an `await`, then because `StoryCharacter.appearance` could be `null`. Both were normalized without changing the fallback character merge behavior, and the build then passed.
- The first interactive canvas implementation exceeded the repository TS/TSX line limit. It was split into `ProductionCanvasElements.tsx`, `useProductionCanvasController.ts`, and `productionCanvasViewModel.ts`.
- The first split used a single `canvas` object in render, which triggered `react-hooks/refs` false-positive errors because the object also contained a ref. The component now destructures the hook return before rendering.

## Next Steps

- Wire node actions to existing generation APIs after the canvas interaction model proves useful.

## Linked Commits

- Pending.
