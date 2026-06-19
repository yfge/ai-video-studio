## User Prompt

/goal 从 IP ，环境，故事，剧集，时间轴，分镜，成品，进行全链路回归，有问题就修复 ，全部以 AP页面形式操作，直到给出符合商业标准的成品，至少三分钟

## Goals

- Drive the full AP page workflow from virtual IP and environment through story, episode, script, timeline, shot plan, clip media, and final render.
- Fix blocking regressions found during the workflow.
- Produce and verify a commercial-standard final video of at least 3 minutes.
- Record concrete AP/browser/runtime evidence and validation commands.

## Changes

- Produced AP run evidence under `artifacts/runs/ap_full_chain_20260618T164912Z/`.
- Created AP objects:
  - Virtual IP `84`, business id `873528b1cec94b5494678b2e996af70b`.
  - Environment `13`, business id `c2ee1e1985294e1090d61bc298573304`, image task `6081`.
  - Story `61`, task `6088`, business id `cc05f0658ea8494c80676ca074c1adaa`.
  - Episode `174`, task `6091`, business id `88b6d685dc8d400381492e8139ef9891`.
  - Script `144`, task `6122`, business id `9597da5a565847a196ae7c142fcb526d`.
  - Timeline `70`, business id `90dfcc5127a24c409a8856c12ba42063`, final version `6`.
- Fixed AP timeline clip readiness so timeline shot-plan clips can request clip video without storyboard/keyframe-only gating.
- Fixed reference-only video dispatch so Volcengine-capable tasks are not skipped.
- Fixed timeline clip prompt duration conflicts for short clips.
- Added render fallback paths for version-shifted clip media and short-gap neighbor reuse so final render can proceed when a few short clips are blocked by external provider failures.
- Tightened and split production script/story quality helpers, beat contract repair, script scoring, traffic sheet parsing, render missing/short-gap logic, and video reference media helpers to satisfy repository contracts.
- Fixed shot-plan payload coercion and error reporting so invalid motion timelines and missing plot/dialogue fields are rejected with actionable messages.
- Extended story/script character policy for generated story `main_characters` and AP role-name aliases.
- Restored `story_parser.extract_json_block` compatibility export.
- Updated agent graph docs/tests to the current `README.md` / `README_CN.md` entrypoints and explicit graph links.
- Made script-generation test mocks deterministic and story-character-aware to avoid external provider repair calls in unit tests.

## Validation

- AP page E2E:
  - Chrome DevTools MCP attempt failed with `Could not connect to Chrome... http://127.0.0.1:9222/json/version: HTTP Not Found`.
  - Fallback engine: Playwright/system Chrome, evidence recorded under `artifacts/runs/ap_full_chain_20260618T164912Z/`.
  - AP workspace URL: `http://localhost:8089/episodes/88b6d685dc8d400381492e8139ef9891/workspace?tab=timeline&scriptId=144`.
- Final render:
  - Render job `121`, timeline version `6`, status `succeeded`, progress `100`.
  - Remote output: `https://resource.lets-gpt.com/timeline-renders/video/20260618/222733/fc921394.mp4`.
  - Local copy: `artifacts/runs/ap_full_chain_20260618T164912Z/final/render_121_final.mp4`.
  - `ffprobe` duration: `184.291667` seconds.
  - File: H.264 1280x720 with AAC audio, local size `24288824` bytes.
  - Contact sheet: `artifacts/runs/ap_full_chain_20260618T164912Z/final/render_121_contact_sheet.jpg`.
  - Success screenshot: `artifacts/runs/ap_full_chain_20260618T164912Z/155-ap-final-render-succeeded.png`.
- External provider blockers observed during AP run:
  - Volcengine `403 AccountOverdueError`.
  - Keling `Account balance not enough`.
  - Google Veo `404` model unavailable.
  - Final render succeeded via media fallback with `fallbackCount=7`.
- Commands:
  - `python scripts/check_repo_docs.py` passed.
  - `python scripts/check_repo_contracts.py --mode diff $(git diff --name-only) $(git ls-files --others --exclude-standard)` passed.
  - `python scripts/check_repo_contracts.py --mode audit` passed.
  - `git diff --check` passed.
  - `cd ai-pic-frontend && npm run lint` passed with existing warnings.
  - `cd ai-pic-frontend && npm run test` passed.
  - `cd ai-pic-backend && pytest ... -o addopts=''` targeted production/timeline/video/scoring tests passed.
  - `cd ai-pic-backend && python run_tests.py quick --no-setup` passed: `2391 passed, 77 skipped, 20 deselected`.
  - `cd ai-pic-backend && python run_tests.py quick` setup failed before tests because Python 3.13 dependency resolution conflicts: `pydantic==2.5.0` vs `langchain-core==0.2.43` requiring `pydantic>=2.7.4`.

## Next Steps

- Provider account/model remediation is still needed for non-fallback clip generation: replenish/fix Volcengine and Keling balances and update unavailable Google Veo model configuration.
- Consider moving the Python 3.13 dependency conflict into requirements maintenance so `run_tests.py quick` works without `--no-setup`.
- No commit was created in this run.

## Linked Commits

- None.
