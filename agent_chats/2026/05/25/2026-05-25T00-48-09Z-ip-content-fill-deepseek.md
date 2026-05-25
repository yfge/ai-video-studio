## User Prompt

IP 角色时的内容填充使用deepseek-v4-flash

## Goals

- Pin virtual IP role content fill text generation to `deepseek-v4-flash`.
- Keep the change scoped to the virtual IP content generation path.
- Add targeted regression coverage for the selected provider/model.

## Changes

- Updated `VirtualIPAIService` so virtual IP profile completion and style prompt generation call the AI manager with `prefer_provider="deepseek"` and `model="deepseek-v4-flash"`.
- Moved generated-profile-to-form-field mapping into `virtual_ip/ai_prompt_helpers.py` so `virtual_ip_ai_service.py` stays under the backend service file-size limit.
- Added a unit test that records both virtual IP content fill AI calls and asserts they use the DeepSeek V4 Flash model.

## Validation

1. Local checks:

- `cd ai-pic-backend && pytest tests/unit/services/virtual_ip/test_virtual_ip_ai_service.py tests/unit/test_virtual_ip_prompt_templates.py -v` -> passed, 4 tests.
- `python scripts/check_repo_docs.py` -> passed.
- `python scripts/check_repo_contracts.py --mode diff ai-pic-backend/app/services/virtual_ip_ai_service.py ai-pic-backend/app/services/virtual_ip/ai_prompt_helpers.py ai-pic-backend/tests/unit/services/virtual_ip/test_virtual_ip_ai_service.py agent_chats/2026/05/25/2026-05-25T00-48-09Z-ip-content-fill-deepseek.md` -> passed.
- `pre-commit run --all-files` -> failed outside this change's surface. Formatter hooks modified unrelated historical files and the backend quick gate failed while importing `tests.fixtures.client` because `app.services.script_quality.checks` does not export `check_cliffhanger`; the unrelated formatter mutations were reverted to preserve atomic commits.
- `BUILD_PUSH=false ./docker/build_prod_images.sh` -> passed for the whole dirty worktree before final commits; backend and frontend images were built locally without push with `IMAGE_TAG=f6cc4461`.

2. Browser or MCP validation:

- Entry URL: `http://localhost:8089/login`.
- User path: logged in as `geyunfei`, opened `/virtual-ip`, opened `创建 IP`, filled name `测试IP-DeepSeek补全-0525` and overall introduction, clicked `AI 生成草稿`.
- Engine: Chrome DevTools MCP attempted first but `http://127.0.0.1:9222/json/version` returned 404 / Not Found; fallback used Playwright with system Google Chrome.
- Network: `POST http://localhost:8000/api/v1/virtual-ips/generate-ai-content` returned 200 in 19.123s. Response fields were populated: description 142 chars, background_story 216 chars, biography 1157 chars, style_prompt 89 chars, tags 10.
- Backend logs: both LLM calls for the request used `provider=deepseek model=deepseek-v4-flash` with `status=success`.
- Console: only existing dev/runtime noise observed during the path: Next HMR websocket 404 through nginx, one resource 404, and existing Next image aspect-ratio warnings for pre-existing list thumbnails.
- Evidence: `artifacts/runs/ip-content-fill-deepseek-20260525T005503Z/summary.json` and `artifacts/runs/ip-content-fill-deepseek-20260525T005503Z/virtual-ip-content-fill.png`.

3. Conflict signals and corrections:

- Initial browser assumption: Chrome DevTools MCP would attach to port 9222.
- Contradicting evidence: Chrome DevTools MCP reported Not Found from `127.0.0.1:9222/json/version`.
- Correction: used Playwright fallback with system Chrome and recorded the fallback explicitly.
- Final verified state: the virtual IP content fill request completes from the real UI and the backend logs show `deepseek-v4-flash` for both profile and style prompt generation.

## Next Steps

- None.

## Linked Commits

- Pending.
