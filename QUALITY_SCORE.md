# Quality Score

Updated by harness scripts and manual reviews.

## Current Snapshot

- Harness Availability: 0.72
- Structural Compliance: 0.38
- Browser Evidence Coverage: 0.36
- Pipeline Reliability: 0.40

Latest validated run: `local-harness-live`

## Golden Path Status

- `mock_smoke`: passed on `local-harness-live`
- `operator_smoke`: scaffolded, not yet validated in a live authenticated run
- `timeline_export_regression`: partial coverage, currently validates timeline pipeline completion rather than full render/export

## Scenario Coverage

- `login_smoke`
- `virtual_ip_image_generation_smoke`
- `episode_timeline_smoke`
- `task_details_trace_smoke`

## Highest-Risk Debt

- `scripts_legacy.py` remains the primary legacy API choke point.
- `dialogue_audio_service.py` and `ai_service_manager.py` still centralize too much orchestration.
- Storyboard page remains far above the page size target.
- Browser evidence is partially blocked by the local desktop environment: `browser_flow.py` records fallback evidence, but Chrome DevTools MCP could not attach because `127.0.0.1:9222/json/version` returned `404`.
