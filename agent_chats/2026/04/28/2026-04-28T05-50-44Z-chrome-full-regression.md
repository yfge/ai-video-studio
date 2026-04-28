# Chrome Full Regression

## User Prompt

Run the local Chrome full regression plan for AI short-drama generation, use `deepseek:deepseek-v4-flash` for text, `openai:gpt-image-2` for images, `volcengine:seedance-2.0-i2v` with standard-model fallback for video, remove local `OPENAI_BASE_URL`, continue the regression, and handle related issues.

## Goals

- Use local Chrome DevTools/CDP only; do not use Playwright or Selenium.
- Remove the local OpenAI proxy configuration that pointed image generation at an expired TLS certificate.
- Create and verify fresh run-scoped assets: role, voice binding, role image, environment, environment image, story, episode, script, timeline, storyboard, storyboard image, and storyboard video.
- Fix regressions discovered during the flow instead of repeatedly retrying broken endpoints.
- Record browser, network, task, provider, and generated URL evidence under `artifacts/runs/2026-04-28T05-50-44Z-chrome-full-regression-fix/`.

## Changes

- Removed the ignored local `OPENAI_BASE_URL` entry from `docker/.env` and recreated backend/Celery services. Runtime verification showed both process env and `settings.OPENAI_BASE_URL` as `None`.
- Fixed storyboard async task creation in:
  - `ai-pic-backend/app/api/v1/endpoints/storyboard/generation.py`
  - `ai-pic-backend/app/api/v1/endpoints/storyboard/media.py`
- Mounted the extracted storyboard router back under `/api/v1/scripts/{script_id}/storyboard/...` in `ai-pic-backend/app/api/v1/endpoints/scripts/__init__.py`.
- Tightened episode agent validation in `ai-pic-backend/app/services/episode_agent_episode_utils.py` so one-scene or missing-scene episode payloads are rejected and no-beat fallback produces 4 usable scenes.
- Fixed virtual IP image generation parameter parsing in `ai-pic-backend/app/api/v1/endpoints/virtual_ip_images/generation_helpers.py`; `additional_prompts` now accepts both comma-separated strings and JSON arrays.
- Improved Volcengine provider diagnostics in `ai-pic-backend/app/services/providers/base.py` so HTTP status failures include the response body.
- Adjusted Volcengine I2V request content ordering in `ai-pic-backend/app/services/providers/volcengine_provider/video_request.py` so first/last frame media precedes text.
- Added/updated targeted tests:
  - `ai-pic-backend/tests/unit/test_virtual_ip_image_task_normalized_params.py`
  - `ai-pic-backend/tests/unit/test_scripts_storyboard_route_registration.py`
  - `ai-pic-backend/tests/unit/services/test_episode_agent_episode_utils.py`
  - `ai-pic-backend/tests/unit/test_volcengine_provider_video.py`

## Validation

- Doctor:
  - `python scripts/harness/doctor.py --run-id 2026-04-28T05-50-44Z-chrome-full-regression-fix`
  - API `8000`: healthy; frontend `3000`: ok; nginx `8089/login`: still `502`.
  - Evidence: `artifacts/runs/2026-04-28T05-50-44Z-chrome-full-regression-fix/doctor.json`.
- Chrome transport:
  - Main Chrome on `9222` returned `404` for `/json/version`, so a dedicated local Chrome profile was started on CDP `9223`.
  - The flow was driven directly through Chrome DevTools Protocol on `9223`; no Playwright/Selenium fallback was used.
- Runtime config:
  - After removing local `OPENAI_BASE_URL`, backend and Celery reported `OPENAI_BASE_URL=None`.
  - Worker logs showed OpenAI image generation using `https://api.openai.com/v1/images/...` successfully.
- Browser/CDP evidence:
  - `cdp-flow-continued.json`, `network-events-continued.json`, `console-events-continued.json`
  - `cdp-flow-postfix.json`, `network-events-postfix.json`, `console-events-postfix.json`
  - `cdp-flow-video-retry.json`, `network-events-video-retry.json`, `console-events-video-retry.json`
  - Screenshots include login/home, role images, environment detail, storyboard image, storyboard video, and storyboard workspace.
- Run-scoped assets and tasks:
  - Role: id `26`, business id `e29b2b639f5b4c9c965cbb2d5785e791`.
  - Voice binding: `minimax / speech-2.6-hd / male-qn-qingse`.
  - Role image task `5947`: completed, URL `https://resource.lets-gpt.com/ai-generated/virtual-ip/image/20260428/061907/4cf724e1.png`.
  - Environment: id `12`, business id `0e60cd0ea53e40b5b741d4b40e832430`.
  - Environment image task `5948`: completed, URL `https://resource.lets-gpt.com/ai-generated/environments/image/20260428/062031/7f248293.png`.
  - Original generated episode id `137` had `scene_count=1`, reproducing the user issue before the episode-agent fix.
  - Post-fix story task `5953`: completed, story id `46`, business id `cd9760569ce844b59517afe6fa68899d`.
  - Post-fix episode task `5954`: completed, episode id `138`, business id `49994ec3b76d4bbfba65cf48352827e8`, `scene_count=4`.
  - Script task `5955`: completed, script id `130`, business id `af37f4ff1dc84964bd726d14b8f66534`, scenes `4`, dialogues `9`.
  - Timeline pipeline task `5956`: completed, result path `script:130:timeline_pipeline`.
  - Storyboard task `5957`: completed, frame count `4`, generation provider `deepseek`, model `deepseek-v4-flash`.
  - Storyboard image task `5958`: completed, but first video submission rejected by Volcengine privacy safety because the input image was detected as possibly containing a real person.
  - Diagnostic direct provider call confirmed the hidden 400 body: `InputImageSensitiveContentDetected.PrivacyInformation`.
  - No-person storyboard image task `5960`: completed, URL `https://resource.lets-gpt.com/ai-generated/storyboard/image/20260428/070018/514cf8ab.png`; Chrome image load ok at `1024x1024`.
  - Standard Seedance video task `5961`: completed, provider task id `cgt-20260428150035-g46g7`, model `doubao-seedance-2-0-260128`, video URL `https://resource.lets-gpt.com/ai-generated/videos/video/20260428/070617/6b2ca2f7.mp4`.
  - Chrome video metadata load succeeded: duration `5.06195`, dimensions `720x1280`.
- Targeted tests:
  - `python -m py_compile ...`: passed for touched backend modules.
  - `cd ai-pic-backend && pytest tests/unit/test_volcengine_provider_video.py tests/unit/services/test_episode_agent_episode_utils.py tests/unit/test_scripts_storyboard_route_registration.py tests/unit/test_episode_scene_fallback.py tests/unit/test_virtual_ip_image_task_normalized_params.py -v`: 17 passed.
  - `cd ai-pic-backend && ruff check ...`: passed for touched backend modules and tests.
  - `git diff --check`: passed.
- Repository checks:
  - `python scripts/check_repo_docs.py`: passed.
  - `python scripts/check_repo_contracts.py --mode diff ...`: failed on pre-existing hotspot rules for large endpoint/helper files, long route handlers, and direct query usage in touched legacy modules.
  - `cd ai-pic-backend && python run_tests.py quick`: failed before tests during dependency installation on Python 3.13 because pinned `pydantic==2.5.0` conflicts with `langchain-core==0.2.43` requiring `pydantic>=2.7.4`.
  - `pre-commit run --all-files`: failed. It attempted broad end-of-file, ruff, black, isort, and prettier changes across unrelated historical files; those unrelated auto-format changes were reverted. Backend quick gate in the hook initially exposed a stale `ensure_scenes` import after the formatter pass, which was resolved by restoring the unrelated helper file.
  - `BUILD_PUSH=false BUILD_PLATFORMS=linux/amd64 ./docker/build_prod_images.sh`: passed; backend and frontend production images built locally without registry push. Frontend `next build` passed inside the image build.

## Next Steps

- Nginx `8089/login` still returns `502`; direct frontend `3000` and API `8000` were used for the Chrome regression.
- The main Chrome DevTools port `9222` still returned `404`; the verified Chrome run used dedicated local Chrome CDP `9223`.
- Volcengine rejected the first realistic storyboard image for privacy safety; the completed video used an environment-only no-person storyboard image for the same frame.
- Full `run_tests.py quick` remains blocked by the Python 3.13 dependency conflict noted above.
- Repo contract diff still reports pre-existing architectural hotspot rules in touched legacy files.

## Linked Commits

- This commit: `fix: stabilize short-drama regression generation`
