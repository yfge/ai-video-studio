---
id: 2026-07-03T07-53-41Z-canvas-run-id-input
date: "2026-07-03T07:53:41Z"
participants:
  - user
  - codex
models:
  - GPT-5 Codex
tags:
  - canvas
  - frontend
  - persistence
summary: Normalized infinite canvas run id input.
related_paths:
  - ai-pic-frontend/src/components/features/canvas/useProductionCanvasRunPersistence.ts
  - ai-pic-frontend/tests/productionCanvasRunPersistence.test.ts
---

# Canvas Run ID Input

## User Prompt

继续完善无限画布功能，保持原子化提交。用户随后询问当前完成度，并允许使用 dev_in_docker 和内置浏览器检验。

## Goals

- 让无限画布 Run ID 输入框能够接受直接粘贴的 `/canvas?run_id=...` 链接。
- 保持本次提交只覆盖 Run ID 输入规范化，不合入 URL 同步、自动恢复或 Board 拆分工作。

## Changes

- Added `productionCanvasRunIdFromInput` coverage for raw IDs, absolute canvas URLs, relative canvas URLs, empty run IDs, missing run IDs, and malformed URL-like input.
- Scoped the hook behavior so the returned `setRunId` normalizes pasted input before save/restore resolution.

## Validation

1. Local checks:

- `cd ai-pic-frontend && node --import tsx --test tests/productionCanvasRunPersistence.test.ts` -> pass, 1 test.
- `python scripts/check_repo_contracts.py --mode diff ai-pic-frontend/src/components/features/canvas/useProductionCanvasRunPersistence.ts ai-pic-frontend/tests/productionCanvasRunPersistence.test.ts agent_chats/2026/07/03/2026-07-03T07-53-41Z-canvas-run-id-input.md` -> pass.
- `cd ai-pic-frontend && npm run lint` -> pass, 0 errors and 3 existing warnings in `eslint.config.mjs`, `EnvironmentReferenceImagesField.tsx`, and `VirtualIPReferenceImagesField.tsx`.
- `python scripts/check_repo_docs.py` -> pass.
- `pre-commit run --files ai-pic-frontend/src/components/features/canvas/useProductionCanvasRunPersistence.ts ai-pic-frontend/tests/productionCanvasRunPersistence.test.ts agent_chats/2026/07/03/2026-07-03T07-53-41Z-canvas-run-id-input.md` -> pass.

2. Browser or MCP validation:

- Not run for this helper-only slice; browser validation remains required before declaring the wider canvas flow complete.

3. Conflict signals and corrections:

- Initial assumption: the existing hook-level helper test could be committed as-is.
- Contradicting evidence: `productionCanvasPersistence.test.tsx` contains unrelated canvas restore and Board behavior changes.
- Reproduction and fix: split the Run ID normalization assertion into a dedicated test file and stage only the hook hunk needed for normalization.
- Final verified state: targeted helper tests, repo contracts, docs check, lint, and scoped pre-commit passed.

## Next Steps

- Continue splitting the remaining canvas URL restore, task sync, and Board component extraction into separate commits.
- Run a real browser pass after the user-visible canvas restore path is fully assembled.

## Linked Commits

- Pending.
