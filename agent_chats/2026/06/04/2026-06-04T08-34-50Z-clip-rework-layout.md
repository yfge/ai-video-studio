## User Prompt

用户要求实现“调整片段生成区布局”计划：将右侧 `片段检查器 -> 资产审计` 中的混合表单拆成“两步卡片”布局，仍保持当前 clip-scoped 定义，不新增整条 Timeline 故事板入口。

## Goals

- 在 `TimelineClipProviderReworkControls` 中拆出 `故事板参考` 和 `片段视频` 两张卡片。
- 将按钮文案改为 `生成故事板参考图` 和 `生成/重做此片段视频`。
- 保留高级生产参数全部可见，不折叠。
- 保持 API 不变：storyboard 仍调用 `generateTimelineClipStoryboard(timelineId, clipId, ...)`，video rework 仍调用 `queueTimelineClipVideoRework(timelineId, clipId, ...)`。
- 更新测试覆盖两张卡片、clip-scoped storyboard payload、video rework payload 和已有 panel 的 `使用故事板 Panel N`。

## Changes

- `TimelineClipProviderReworkControls` 保留状态、submit handler 和 API 调用逻辑，将表单 UI 交给相邻的 `TimelineClipProviderReworkCards`。
- 新增 `TimelineClipProviderReworkCards`，统一卡片、标题、说明和双列字段 class，将原单块混合表单改为两张 `section`。
- `故事板参考` 卡片保留风格、Panel 数、secondary 按钮和参考图预览，按钮文案改为 `生成故事板参考图`。
- `片段视频` 卡片保留动作、提示词、模型、时长、分辨率、比例、原因和 primary 提交按钮，按钮文案改为 `生成/重做此片段视频`。
- `使用故事板 Panel N` checkbox 移到视频卡片顶部，并仍只在当前 clip 有 storyboard panel 时显示。
- `timelineClipReworkControls.test.ts` 新增 JSDOM 组件测试，验证两步 UI 和两个 submit path 的请求 URL/body。

## Validation

- Passed: `cd ai-pic-frontend && ./node_modules/.bin/tsx --test tests/timelineClipReworkControls.test.ts` with 7 tests passing.
- Passed: `cd ai-pic-frontend && npm run test` with 40 tests passing.
- Passed: `cd ai-pic-frontend && npm run lint` with 0 errors and 19 warnings.
- Passed: `git diff --check`.
- Passed: `python3 scripts/check_repo_docs.py`.
- Passed: `/opt/homebrew/Cellar/python@3.12/3.12.11/Frameworks/Python.framework/Versions/3.12/bin/python3.12 scripts/check_repo_contracts.py --mode diff ai-pic-frontend/src/components/features/episode/TimelineClipProviderReworkControls.tsx ai-pic-frontend/src/components/features/episode/TimelineClipProviderReworkCards.tsx ai-pic-frontend/tests/timelineClipReworkControls.test.ts agent_chats/2026/06/04/2026-06-04T08-34-50Z-clip-rework-layout.md`.
- Browser evidence: Chrome validation opened `http://localhost:8089/episodes/0d2c8a2adfb9464b85116ecf8ca68c16/workspace?tab=timeline&scriptId=128`, selected `视频 2`, and confirmed DOM counts for `故事板参考`, `生成故事板参考图`, `片段视频`, and `生成/重做此片段视频` were all `1`; old buttons `生成故事板` and `生成重做视频` were both `0`.
- Browser evidence: final post-split Chrome recheck repeated the same workspace and `视频 2` selection; new text/button counts were all `1`, old button counts were `0`, and console error/warn logs were empty.
- Browser evidence: no generation buttons were clicked; console error/warn logs were empty.
- Artifact: `artifacts/runs/clip-inspector-layout-20260604T0730Z/timeline-clip-inspector-two-step-fullpage.jpg`.
- Note: in-app Browser login was blocked by the browser input/storage sandbox, so validation used Chrome extension fallback.

## Next Steps

- None required for this scoped UI change.

## Linked Commits

None yet.
