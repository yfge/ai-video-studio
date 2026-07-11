## User Prompt

继续完善无限画布功能；先提交现有变更。

## Goals

- Close the Production Canvas collaboration slice as one atomic commit.
- Enforce Viewer, Commenter, Editor, Approver, and Owner capabilities in the real canvas UI.
- Persist comments and auditable activity against stable canvas identities.
- Prove Owner and Approver behavior in the in-app browser.

## Changes

- Added the collaboration panel for node, candidate, edge, and section comments, activity history, and Owner-managed members.
- Propagated role capabilities through canvas editing, keyboard, connection, candidate review, execution, save, and autosave controls.
- Recorded definition saves, node execution, run controls, candidate review and branching, Timeline placement, comments, and membership changes in persistent activity history.
- Split collaboration, access-gate, URL-sync, candidate-activity, and definition-activity responsibilities to keep touched production files within repository size contracts.
- Updated the Production Canvas design and task board to mark the collaboration slice complete while leaving templates and scale work open.

## Validation

1. Local checks:

- `python scripts/check_repo_contracts.py --mode diff <changed files>` -> pass.
- `python scripts/check_repo_docs.py` -> pass.
- `cd ai-pic-backend && pytest tests/integration/test_production_canvas_collaboration_api.py tests/integration/test_production_canvas_candidate_branch_api.py tests/integration/test_production_canvas_candidate_rejection_api.py tests/integration/test_production_canvas_run_control_api.py -q` -> 11 passed.
- `cd ai-pic-backend && pytest -q` -> 2466 passed, 88 skipped.
- `cd ai-pic-frontend && npm run lint` -> 0 errors; 3 pre-existing warnings.
- `cd ai-pic-frontend && npm run test` -> 315 passed.
- `cd ai-pic-frontend && npm run build` -> pass; `/canvas` generated successfully.

2. Browser validation:

- Entry URL: `http://localhost:8089/canvas?run_id=aa6e7886ed874556bcfd8490eaecfb8e`.
- Owner path: added the dedicated reviewer as Approver, created a scene section, and commented on node, candidate, edge, and section targets.
- Approver path: approval and rejection remained available; graph edits, save, run, branch, edge, and media controls were absent or disabled. Pressing `n` left the manual-note count unchanged.
- Console: no errors or warnings after the Approver flow.
- Network: collaborator update `req-1783791308585-d5hlek2k`; Owner comments `req-1783791371823-7njph8bd`, `req-1783791372456-xb21yxyt`, `req-1783791373087-87rksfb6`, `req-1783791404059-3n0apr51`; Approver comment `req-1783791522300-arx3vw5f`; all returned 200.
- Database: one Approver collaborator, five comments, eight activity entries, one section, and latest action `comment.added` for the validated run.
- Evidence: `artifacts/runs/canvas-collaboration-20260712T013500Z/owner-activity.jpg` and `approver-review.jpg`.

3. Conflict signals and corrections:

- Initial panel and several touched legacy files crossed repository size limits.
- The diff contract identified every oversized file; responsibilities were split or compacted without changing behavior.
- The final diff contract and complete frontend/backend suites passed.

## Next Steps

- Add provider-agnostic domain templates and reusable subflows.
- Define a large-canvas performance budget, viewport virtualization, and scale regression evidence.
- Run one consolidated provider-backed image-to-video-to-Timeline release validation.

## Linked Commits

- `feat(canvas): add collaborative review workspace`
