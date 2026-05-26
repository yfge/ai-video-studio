## User Prompt

使用系统 API 回归，重新补齐 Timeline-First 全链路，并用浏览器验证。

## Goals

- 用真实系统 API 跑通 DeepSeek -> Timeline seed -> Timeline shot plan -> TTS -> GPT Image 2 -> Seedance 2.0 -> Timeline asset 回填 -> render。
- 验证 full-30s 不能用单段冒充 30 秒，必须由 Timeline 上的两段 15 秒 clip 驱动。
- 记录浏览器验证和 Chrome DevTools fallback 原因。

## Changes

- 无运行时代码改动。
- 新增本次 live regression 记录；产物保存在 ignored `artifacts/runs/` 下。

## Validation

- `python scripts/harness/provider_chain_regression.py --mode smoke --run-id timeline-first-smoke-20260526T085442Z --api-url http://localhost:8000 --episode-id 133 --script-id 117 --timeout-seconds 900 --poll-interval-seconds 5`
  - Result: passed.
  - Evidence: `artifacts/runs/timeline-first-smoke-20260526T085442Z/provider_chain.json`.
  - Timeline: id `22`, seed version `1`, shot-plan version `2`, asset-backfill version `3`.
  - Image: OpenAI `gpt-image-2`, `https://resource.lets-gpt.com/ai-generated/virtual-ip/image/20260526/085635/60e8bd16.png`.
  - Video: Volcengine `doubao-seedance-2-0-260128`, task `cgt-20260526165637-dwc8r`.
  - Render: `https://resource.lets-gpt.com/timeline-renders/video/20260526/090236/8501b32b.mp4`.
  - Probe: audio/video streams present, duration matches 4s timeline, scene frame extracted.
- `python scripts/harness/provider_chain_regression.py --mode full-30s --run-id timeline-first-full-30s-20260526T090328Z --api-url http://localhost:8000 --episode-id 133 --script-id 117 --timeout-seconds 1200 --poll-interval-seconds 5 --video-concurrency 2`
  - Result: passed.
  - Evidence: `artifacts/runs/timeline-first-full-30s-20260526T090328Z/provider_chain.json`.
  - Timeline: id `23`, seed version `1`, shot-plan version `2`, asset-backfill version `3`.
  - Full duration: two Timeline video clips, `15s + 15s`, no single-clip 30s shortcut.
  - Image: OpenAI `gpt-image-2`, `https://resource.lets-gpt.com/ai-generated/virtual-ip/image/20260526/090510/ac6bb5e6.png`.
  - Videos: Volcengine `doubao-seedance-2-0-260128`, tasks `cgt-20260526170512-7js9w` and `cgt-20260526170512-qkvlx`.
  - Render: `https://resource.lets-gpt.com/timeline-renders/video/20260526/091137/675e22b3.mp4`.
  - Probe: audio/video streams present, duration `30.125s` for expected `30.0s`, both scene frames extracted.
- Browser validation:
  - Chrome DevTools MCP was attempted first and failed to connect to Chrome via `127.0.0.1:9222/json/version` with HTTP Not Found.
  - Fallback: Playwright with local Google Chrome executable.
  - Path: login at `http://localhost:8089/login`, then `http://localhost:8089/episodes/133/workspace?tab=timeline&scriptId=117`.
  - Result: passed; Timeline workspace loaded and Network showed 200 responses for `/api/v1/episodes/133/timelines`, `/api/v1/timelines/23/render-jobs`, and `/api/v1/timelines/23/clip-assets?timeline_version=3`.
  - Evidence: `artifacts/runs/timeline-first-full-30s-20260526T090328Z/browser_validation.json` and `browser_timeline_workspace.png`.
  - Console: only repeated non-material Next.js HMR WebSocket 404 messages from the nginx/dev setup.

## Next Steps

- Review generated full-30s output for subjective production quality; API/lineage/render checks passed, but visual character consistency still needs human acceptance.
- Consider reducing provider wait time by adding async task status polling for Seedance rather than holding synchronous API requests open.

## Linked Commits

- Pending
