## User Prompt

检查miniMax 的 API  在语音合成的时候接入人物情绪  https://platform.minimaxi.com/docs/mcp

## Goals

- Verify the current MiniMax T2A API contract for speech emotion support.
- Check whether ai-video-studio already passes character/dialogue emotion into speech synthesis.
- Add narrow regression coverage for the MiniMax TTS emotion payload path.

## Changes

- Confirmed from the official MiniMax T2A HTTP docs that `voice_setting.emotion` accepts `happy`, `sad`, `angry`, `fearful`, `disgusted`, `surprised`, `calm`, `fluent`, and `whisper`.
- Confirmed the current backend already normalizes dialogue `emotion`/`action` through `normalize_tts_emotion()` and passes it into `tts_to_wav_file()`.
- Added a MiniMax provider payload regression test proving non-empty `emotion` is placed under `voice_setting`.
- Added an audio generator regression test proving `tts_to_wav_file()` forwards normalized emotion to `ai_manager.text_to_speech()`.
- No production code change was needed because the implementation already connected the field.

## Validation

1. Local checks:

- `cd ai-pic-backend && pytest tests/unit/test_minimax_provider_tts_payload.py tests/unit/services/audio/test_audio_generator.py tests/unit/services/audio/test_audio_emotions.py -v` -> passed, 30 tests.
- `python scripts/check_repo_docs.py` -> passed.
- `python scripts/check_repo_contracts.py --mode diff ai-pic-backend/tests/unit/test_minimax_provider_tts_payload.py ai-pic-backend/tests/unit/services/audio/test_audio_generator.py agent_chats/2026/06/04/2026-06-04T01-11-53Z-minimax-tts-emotion.md` -> passed.
- `pre-commit run --all-files` -> skipped because the worktree contains broad unrelated backend/frontend/storyboard changes; running all-file hooks could modify or fail on user-owned files outside this commit scope.
- `./docker/build_prod_images.sh` -> skipped because this commit only adds scoped backend regression tests/ledger and the worktree contains unrelated in-progress changes outside the commit scope.

2. Browser or MCP validation:

- Not run. This was a backend payload/contract inspection with no UI or live provider call.

3. Conflict signals and corrections:

- Initial assumption: MiniMax emotion support might need a production implementation.
- Contradicting evidence: `ai-pic-backend/app/services/providers/minimax_provider/tts.py` already writes `emotion` into `voice_setting`; `scene_tts_phase.py` already normalizes dialogue emotion/action before TTS.
- Reproduction and fix: added regression tests around the provider payload and production TTS helper.
- Final verified state: character/dialogue emotion is already connected to MiniMax TTS, with new tests guarding the path.

## Next Steps

- If the frontend/operator flow should expose per-dialogue emotion editing, validate that separately with a browser path.
- If switching the default model to `speech-2.8-*`, account for MiniMax's documented restrictions on `fluent` and `whisper`.

## Linked Commits

- None yet.
