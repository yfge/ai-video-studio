## User Prompt

`http://localhost:8089/episodes/ecd5d5d0b87a485ebfbc9275f1ae6ff3/workspace?tab=timeline&scriptId=125 还是把动作场景生成了音频`

## Goals

- Diagnose why `scriptId=125` still showed action beats as audio on the Timeline tab.
- Keep action beats available as video timing, but prevent them from appearing on `dialogue` / `subtitle` tracks.
- Repair the local bad Timeline data for episode `ecd5d5d0b87a485ebfbc9275f1ae6ff3`.

## Changes

- Added `timeline_import_repair.existing_timeline_needs_audio_track_repair()` to detect legacy Timeline specs where action or pause beats are present on `dialogue` / `subtitle` tracks for the same `source_audio_timeline_version`.
- Updated `import_audio_timeline_to_timeline_spec()` so `overwrite=false` still rebuilds malformed legacy specs instead of returning `skipped`.
- Added an audio dialogue prose filter so generic narrator fallback blocks such as `冲突升级：` / `爽点：` / `卡点：` are treated as silent action timing rather than spoken dialogue.
- Wired the same filter into scene audio generation, Timeline Spec import, legacy repair detection, and Timeline Spec validation.
- Added regression coverage in `test_timeline_import_repair.py`, `test_timeline_spec_validation.py`, `test_timeline_import_service.py`, and `test_prose_dialogue_splitter.py`.
- Updated `docs/timeline-rendering-pipeline.md` to state that only spoken dialogue beats create `dialogue` / `subtitle` clips, while action/fallback prose remains on the `video` track.

## Validation

1. Local checks:

- `ai-pic-backend/.venv/bin/python -m pytest ai-pic-backend/tests/test_timeline_import_service.py ai-pic-backend/tests/test_timeline_import_repair.py ai-pic-backend/tests/test_timeline_spec_validation.py ai-pic-backend/tests/unit/services/audio/test_prose_dialogue_splitter.py -q` -> pass, `18 passed`.
- `python scripts/check_repo_docs.py` -> pass.
- `python scripts/check_repo_contracts.py --mode diff ai-pic-backend/app/services/audio/dialogue_processing/audio_dialogue_filter.py ai-pic-backend/app/services/audio/dialogue_processing/prose_dialogue_splitter.py ai-pic-backend/app/services/audio/scene_audio_generator.py ai-pic-backend/app/services/timeline_import_service.py ai-pic-backend/app/services/timeline_import_repair.py ai-pic-backend/app/services/timeline_spec_builder.py ai-pic-backend/app/services/timeline_spec_validation.py ai-pic-backend/tests/test_timeline_import_service.py ai-pic-backend/tests/test_timeline_import_repair.py ai-pic-backend/tests/test_timeline_spec_validation.py ai-pic-backend/tests/unit/services/audio/test_prose_dialogue_splitter.py docs/timeline-rendering-pipeline.md agent_chats/2026/06/09/2026-06-09T07-51-56Z-timeline-action-audio-repair.md` -> pass.
- `SKIP=backend-pytest pre-commit run --files ai-pic-backend/app/services/audio/dialogue_processing/audio_dialogue_filter.py ai-pic-backend/app/services/audio/dialogue_processing/prose_dialogue_splitter.py ai-pic-backend/app/services/audio/scene_audio_generator.py ai-pic-backend/app/services/timeline_import_service.py ai-pic-backend/app/services/timeline_import_repair.py ai-pic-backend/app/services/timeline_spec_builder.py ai-pic-backend/app/services/timeline_spec_validation.py ai-pic-backend/tests/test_timeline_import_service.py ai-pic-backend/tests/test_timeline_import_repair.py ai-pic-backend/tests/test_timeline_spec_validation.py ai-pic-backend/tests/unit/services/audio/test_prose_dialogue_splitter.py docs/timeline-rendering-pipeline.md agent_chats/2026/06/09/2026-06-09T07-51-56Z-timeline-action-audio-repair.md` -> pass; `backend-pytest` skipped because the repo quick hook performs broad collection that currently hits unrelated baseline/import errors.
- `git diff --check` -> pass.

2. Runtime data evidence:

- Before repair, `timeline_id=65` had `dialogue` and `subtitle` clips with `beat_type=action`, and action clips had `asset_ref.url` pointing at the episode mp3.
- Browser/API evidence then showed a second issue: four fallback narrator prose beats (`冲突升级` / `爽点` / `卡点`) were still marked as `dialogue` in `episode.extra_metadata.audio_timeline.beats`, so the UI still showed them under `对白`.
- Ran the import repair against episode `136`, script `125`, business id `ecd5d5d0b87a485ebfbc9275f1ae6ff3`.
- Repair result: `{'action': 'updated', 'timeline_id': 65, 'version': 2, 'source_audio_timeline_version': 2}`.
- After repair, `timeline_id=65` v2 counts are `dialogue/dialogue=12`, `subtitle/dialogue=12`, `video/dialogue=12`, `video/action=8`.
- After repair, `timeline_clip_assets` v2 `source_audio` links exist only for the 12 `dialogue_*` clips.
- After adding the fallback prose filter, reran import repair.
- Final repair result: `{'action': 'updated', 'timeline_id': 65, 'version': 3, 'source_audio_timeline_version': 2}`.
- Final DB/API counts for `timeline_id=65` v3 are `dialogue/dialogue=8`, `subtitle/dialogue=8`, `video/dialogue=8`, `video/action=12`.
- Final v3 `timeline_clip_assets` `source_audio` links exist only for 8 true dialogue clips.

3. Conflict signals and corrections:

- Initial code inspection showed the current builder already filters dialogue beats correctly.
- DB evidence contradicted the current-code expectation: the existing Timeline v1 was a legacy malformed spec and import had been returning `skipped`.
- Page evidence contradicted the first fix: the `对白` track still contained four long fallback narrator prose blocks even though their `beat_type` was `dialogue`.
- Final fix targets both the skip path and the spoken-dialogue filter used by audio generation / Timeline import.

4. Browser evidence:

- Chrome DevTools transport failed twice with `http://127.0.0.1:9222/json/version` returning HTTP Not Found, so verification used the in-app Browser Playwright fallback.
- Logged into `http://localhost:8089/login` with the repo test account and opened `http://localhost:8089/episodes/ecd5d5d0b87a485ebfbc9275f1ae6ff3/workspace?tab=timeline&scriptId=125`.
- After reload, the Timeline `对白` section had no `冲突升级` / `爽点` / `卡点` matches; the `视频` section still contained those action prose blocks.
- Browser console logs for the target page were empty for `error` / `warn`.

## Next Steps

- Reload the Timeline tab so the frontend fetches `timeline_id=65` v3.
- If any future old Timeline shows the same shape, rerunning the import path with the same `audio_timeline.version` will repair instead of skipping.

## Linked Commits

- Pending commit.
