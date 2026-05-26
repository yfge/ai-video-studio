## User Prompt

PLEASE IMPLEMENT THIS PLAN: Timeline-First 全链路补齐计划。

## Goals

- Make the provider-chain harness prove Timeline-first behavior instead of reusing script-scene video prompts.
- Require Timeline shot-plan readback before TTS, character image, Seedance generation, asset backfill, and render.
- Persist evidence snapshots for seed, shot plan, asset update, Timeline readback, and clip asset lineage.

## Changes

- Removed video prompt and raw `script_scene` lineage from provider-chain Timeline seed video clips.
- Added `timeline-shot-plan` system API call after Timeline creation and before any media generation.
- Changed Seedance generation to require `source_refs.timeline_shot_plan.video_prompt`; missing shot plan now fails the harness.
- Changed temporary Virtual IP and character image prompts to use Timeline shot-plan character anchors instead of raw script character prompts.
- Added Timeline evidence snapshots under `artifacts/runs/<run_id>/`: `timeline_seed_spec.json`, `timeline_shot_plan_spec.json`, `timeline_assets_spec.json`, `timeline_readback.json`, and `clip_assets.json`.
- Split Timeline asset attachment helpers out of `provider_chain_timeline_payloads.py` to keep contract file-size limits clean.

## Validation

- `cd ai-pic-backend && pytest tests/scripts/test_provider_chain_media.py tests/scripts/test_provider_chain_regression.py tests/scripts/test_provider_chain_api.py tests/scripts/test_provider_chain_render_probe.py -q` passed: `10 passed`.
- `python scripts/check_repo_contracts.py --mode diff <changed files>` passed.
- `git diff --check` passed.
- Live system API smoke/full-30s and browser validation were not run before this commit. They are the next validation step after the atomic harness code change is committed.

## Next Steps

- Run the requested combined targeted test command, repo docs/contracts, and live provider-chain smoke.
- If smoke passes, run the full-30s paid regression and inspect the artifact evidence instead of treating the harness as content-quality proof.

## Linked Commits

Pending
