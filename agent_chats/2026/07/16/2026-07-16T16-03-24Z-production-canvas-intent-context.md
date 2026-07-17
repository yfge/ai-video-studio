---
id: 2026-07-16T16-03-24Z-production-canvas-intent-context
date: "2026-07-16T16:03:24Z"
participants:
  - user
  - codex
models:
  - gpt-5
tags:
  - production-canvas
  - intent-parsing
  - content-planning
  - script-quality
related_paths:
  - ai-pic-backend/app/services/production_canvas/production_context_builder.py
  - ai-pic-backend/app/services/production_canvas/script_context_compiler.py
  - ai-pic-backend/app/services/script/beat_contract_auto_repair.py
  - ai-pic-frontend/src/components/features/canvas/useProductionCanvasSkillPlanner.ts
  - docs/design/production-canvas.md
summary: Replace fixed-name Canvas planning with structured model-first production context and preserve it through Script generation.
---

# Production Canvas structured intent and content context

## User Prompt

- Production Canvas Script Skill failed for episode 194 and the generated script did not reflect the prompt.
- Replace fixed-name parsing with model-first structured intent understanding.
- Make every Skill consume structured context for parameters, model choice, video specification, clarification, and existing-asset association.
- Add content planning that decides whether IP and environments should be reused or created, expands one sentence into a story/episode plan, and preserves continuity.
- Keep validation focused instead of relying on excessive file reads and broad commands.

## Goals

- Make Skill IDs routing metadata rather than creative input.
- Preserve the original prompt and model-interpreted intent through Plan, asset/model resolution, and Script generation.
- Ask only when an unanswered decision materially changes execution.
- Prevent deterministic quality repair from replacing provider output with fixed workplace templates.
- Reproduce episode 194 through the real Production Canvas Plan-to-Script path.

## Changes

- Added the versioned `production_context.v1` contract with structured Production Brief and Content Plan.
- Added model-first schema parsing, clarification answers, video specifications, model catalog resolution, and asset reuse/create/ambiguous decisions.
- Added `brief.compose`, `content.plan`, and `asset.select` before `script.generate`; Script compiles the full structured context into the existing production worker request.
- Removed fixed prompt/name parsing and fixed Script repair content.
- Strengthened repair schema/structure preservation and made deterministic repair reuse concrete evidence from the current generated contract.
- Added frontend clarification fields and stopped automatic Script execution while required answers remain unresolved.
- Replaced the false-positive concrete-stakes check with deadline and publication consequence
  recognition, so valid outcomes such as a next-week company-wide playback template are not
  sent through repeated model repair.

## Validation

1. Local checks:

- `cd ai-pic-backend && pytest -q --no-cov tests/unit/services/scoring/test_script_score_service.py tests/unit/services/scoring/test_script_score_service_calibration.py tests/unit/services/script/test_beat_contract_auto_repair.py tests/unit/services/script/test_beat_contract_auto_repair_no_templates.py tests/unit/services/script/test_beat_contract_auto_repair_preservation.py tests/unit/services/script/test_production_script_repair_schema.py tests/unit/services/script/test_quality_gate_repair_guard.py tests/unit/test_production_canvas_prompt_context.py tests/unit/test_production_canvas_context_assets.py tests/unit/test_production_canvas_context_resolution.py tests/unit/test_production_canvas_skill_plan.py tests/integration/test_production_canvas_api.py tests/integration/test_production_canvas_storyboard_api.py`
  passed: `57 passed, 2 skipped`.
- Script contract and repair regression suites passed, including replay of failed episode 194 task payloads.
- Focused conflict-quality regression passed: `6 passed`.
- `cd ai-pic-frontend && npx tsx --test tests/singleVideoCanvasPlanner.test.tsx tests/productionCanvasBoard.test.tsx`
  passed: `15 passed`; this includes required-clarification blocking.
- `cd ai-pic-frontend && npm run lint` passed with 0 errors and 3 pre-existing warnings.
- `python scripts/check_repo_docs.py` passed.
- `python scripts/check_repo_contracts.py --mode audit` passed.
- `python scripts/check_repo_contracts.py --mode diff <staged files>` passed.
- `SKIP=backend-pytest pre-commit run --files <staged files>` passed all remaining
  staged hooks; the duplicate broad backend hook was skipped because the exact 57-test
  backend/API command above had just passed.

2. Browser or MCP validation:

- Entry URL:
  `http://127.0.0.1:8090/canvas?run_id=1d7349af222d48be980144860d60045c`
- User path: load the model-parsed episode 194 Plan run, resume task `6443`, and fetch
  Script `146`.
- Engine: Playwright with local Google Chrome because the Chrome DevTools endpoint was unavailable.
- Plan run: `1d7349af222d48be980144860d60045c`.
- Final task: `6443`, status `completed`, result `script:146`.
- Script quality: score `9.27`; structured beat contract passed all `24` checks.
- Prompt identity retained: 林妹妹, AI 落地, 反转, 60 秒, 9:16, 3D 卡通,
  `gpt-img-2`, and `seedance 2.0`.
- Asset/model resolution retained: Virtual IP `85`, environment `1`,
  `openai:gpt-image-2`, and `volcengine:doubao-seedance-2-0-260128`.
- Browser console errors: none.
- Network failures: none; login, run, task, and Script requests all returned `200`.
- Screenshot:
  `artifacts/runs/episode194-intent-regression-v6/canvas-run.png`.
- Evidence:
  `artifacts/runs/episode194-intent-regression-v6/evidence.json`.

3. Conflict signals and corrections:

- Initial assumption: the remaining failure was still caused by prompt loss.
- Contradicting evidence: failed tasks 6439, 6440, and 6441 all retained 林妹妹, AI 落地, 3D 卡通, gpt-img-2, seedance 2.0, 60 seconds, and the reversal; deterministic keyword gates rejected otherwise valid provider content.
- Reproduction and fix: replayed each persisted provider payload, removed fixed repair templates, accepted visible claim/workload contradiction, and promoted later concrete evidence into a thin opening hook.
- Task `6443` likewise retained the complete prompt but was rejected because the gate did not
  recognize “下周全员播放模板” as a concrete deadline and loss. The persisted model output
  passed after the semantic gate correction and was recovered without regenerating the story.
- The first staged pre-commit run exposed missing compatibility exports after splitting the
  Canvas schema plus an omitted score-schema import. The compatibility surface was restored,
  touched files were kept within repository size limits, and the targeted backend/API suite
  then passed.
- Final verified state: the model-parsed intent reached the worker and the resulting Script;
  deterministic repair no longer replaced the prompt with fixed workplace content.

## Next Steps

- None for this scoped regression.

## Linked Commits

- This commit: `feat(canvas): add structured production context`.
