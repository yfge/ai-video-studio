## User Prompt

现在剧集和故事的 IP 都显示未命名

## Goals

- Find why story and episode IP labels fall back to "未命名".
- Return the linked VirtualIP name in backend responses when a story or episode character has no custom display alias.
- Update frontend display fallbacks so story cards, story detail chips, episode character rows, and clip storyboard IP selectors use backend display fields.
- Validate with focused backend, frontend, contract, and browser evidence.

## Changes

- Added `virtual_ip_name`, `name`, and `display_name` properties to `StoryCharacter` and `EpisodeCharacter`.
- Added those display fields to story-character and episode-character API response schemas.
- Split story-character schemas into `app/schemas/story_character.py` so `app/schemas/script.py` stays below the Python hard line limit after the response contract change.
- Added backend regression coverage for story-character and episode-character responses with missing `character_name`.
- Added frontend display-name tests and a small `episodeCharacterDisplayName()` helper.
- Updated story IP chips, story detail chips, episode character rows, and clip storyboard IP selector labels to prefer `character_name`, then backend `display_name`, `name`, and `virtual_ip_name`.

## Validation

1. Local checks:

- `ai-pic-backend/.venv/bin/python -m pytest tests/integration/api/test_character_display_names_api.py tests/unit/test_episode_character_service.py -q` -> pass, 10 tests.
- `ai-pic-backend/.venv/bin/python -m pytest tests/test_api.py::TestStoryAPI tests/integration/api/test_episode_characters_api.py::TestEpisodeCharacterCRUD tests/integration/api/test_character_display_names_api.py tests/unit/test_episode_character_service.py -q` -> pass, 22 tests.
- `cd ai-pic-frontend && npm run test` -> pass, 48 tests.
- `cd ai-pic-frontend && npm run lint` -> pass with 3 existing warnings: anonymous default export in `eslint.config.mjs`, and two existing `<img>` warnings in environment / virtual-IP reference image fields.
- `python scripts/check_repo_docs.py` -> pass.
- `python scripts/check_repo_contracts.py --mode diff <changed files>` -> pass after moving new tests/schema out of existing oversized files.
- `git diff --check` -> pass.
- `pre-commit run --files <changed files>` -> formatting hooks updated touched files, then backend quick gate failed on existing baseline import drift.
- `SKIP=backend-pytest pre-commit run --files <changed files>` -> pass; backend quick gate intentionally skipped because the same baseline collection errors were already reproduced with direct pytest.
- `cd ai-pic-backend && .venv/bin/python -m pytest` -> failed during collection on existing baseline import drift before running tests: missing `structured_script_score`, `STRUCTURED_SCORE_PASS`, and `_BEAT_CONTRACT_MAX_TOKENS`.

2. Browser or MCP validation:

- Chrome DevTools attempt: failed before navigation because `http://127.0.0.1:9222/json/version` returned HTTP Not Found.
- Fallback engine: Playwright driving system Chrome.
- Story evidence: `artifacts/runs/ip-display-2026-06-09T11-49-43-714Z/browser_flow.json`.
- Story path: login as `geyunfei`, open `http://localhost:8089/stories`, then first story detail `/stories/be3f0a9a256e430b8e3ce24a8022da1f`.
- Story result: story list and detail showed IP labels such as `IP: 老拐`, `IP: 文闻`, `IP: 阿飞`; no "未命名" text found.
- Episode evidence: `artifacts/runs/ip-display-episode-2026-06-09T11-51-46-243Z/browser_flow.json`.
- Episode path: login token set in browser context, query episode characters, then open `/episodes/cb25bff3f2394368bc6482ceec94c5a3/workspace?tab=characters`.
- Episode result: API returned sample `character_name=医生`, `virtual_ip_name=老拐`, `name=医生`, `display_name=医生`; workspace had no "未命名" text.
- Console: only local Next HMR websocket 404 errors were observed during fallback browser runs.

3. Conflict signals and corrections:

- Initial assumption: adding relationship preloading in endpoint/service files would be harmless.
- Contradicting evidence: `check_repo_contracts.py --mode diff` flagged touched direct-query files and existing oversized files.
- Correction: removed nonessential preloading changes, moved tests into new files, and split story-character schemas out of `script.py`.
- Final verified state: contracts diff passes and focused backend/frontend/browser checks prove story and episode IP labels no longer fall back to "未命名".

## Next Steps

- Full backend pytest still needs the existing baseline import drift fixed outside this change.
- No commit has been created yet.

## Linked Commits

- None.
