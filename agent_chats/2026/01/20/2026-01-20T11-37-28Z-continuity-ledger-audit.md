---
id: 2026-01-20T11-37-28Z-continuity-ledger-audit
date: "2026-01-20T11:37:28Z"
participants: [human, codex]
models: [gpt-5.2]
tags: [backend, prompts, continuity]
related_paths:
  - ai-pic-backend/app/api/v1/endpoints/episodes/generation.py
  - ai-pic-backend/app/schemas/continuity.py
  - ai-pic-backend/app/services/continuity/__init__.py
  - ai-pic-backend/app/services/continuity/episode_continuity.py
  - ai-pic-backend/app/services/continuity/episode_generation_flow.py
  - ai-pic-backend/app/services/continuity/episode_plan_postprocess.py
  - ai-pic-backend/app/services/continuity/script_continuity.py
  - ai-pic-backend/app/services/ai/episodes.py
  - ai-pic-backend/app/services/ai/scripts.py
  - ai-pic-backend/app/services/episode/episode_generation_service.py
  - ai-pic-backend/app/services/script/script_utils.py
  - ai-pic-backend/app/services/episode_agent.py
  - ai-pic-backend/app/services/episode_agent_episode.py
  - ai-pic-backend/app/prompts/templates/episode_from_outline.txt
  - ai-pic-backend/app/prompts/templates/episode_from_outline_short_drama.txt
  - ai-pic-backend/app/prompts/templates/episode_duration_reject.txt
  - ai-pic-backend/app/prompts/templates/episode_duration_reject_short_drama.txt
  - ai-pic-backend/app/prompts/templates/episode_generation.txt
  - ai-pic-backend/app/prompts/templates/episode_continuity_audit.txt
  - ai-pic-backend/app/prompts/templates/episode_rewrite_with_audit.txt
  - ai-pic-backend/app/prompts/templates/episode_continuity_ledger_update.txt
  - ai-pic-backend/app/prompts/templates/script_scenes.txt
  - ai-pic-backend/app/prompts/templates/script_scenes_tv_series.txt
  - ai-pic-backend/app/prompts/templates/script_scenes_film.txt
  - ai-pic-backend/app/prompts/templates/script_scenes_short_drama.txt
  - ai-pic-backend/app/prompts/templates/script_dialogues.txt
  - ai-pic-backend/app/prompts/templates/script_dialogues_short_drama.txt
  - ai-pic-backend/app/prompts/templates/script_generation.txt
  - ai-pic-backend/app/prompts/templates/script_continuity_audit.txt
  - ai-pic-backend/app/prompts/templates/script_dialogues_rewrite_with_audit.txt
  - ai-pic-backend/app/prompts/templates/story_novel_zhihu_ledger_update.txt
  - ai-pic-backend/app/services/story/story_novel_export_continuity.py
  - ai-pic-backend/tests/unit/test_episode_agent_callbacks.py
  - ai-pic-backend/tests/unit/test_episode_step_outline_light.py
summary: "Add rolling continuity ledger + audit/rewrite passes for episodes and scripts; strengthen time/knowledge consistency prompts."
---

## User Prompt
- “按你的修改建议进行调整… 给分集/剧本补 continuity_ledger、加 continuity_audit + rewrite_with_audit、增强上下文注入与信息揭示规则、扩展 REACT 机制，并注意时间轴一致性；小说 ledger_update 也补充时间/地点锚点与信息获得事件。”

## Goals
- Provide a rolling `continuity_ledger` across episodes with knowledge gating + time/location anchors.
- Add separate audit + rewrite passes (not schema repair) for episodes and scripts.
- Improve prompt context injection (previous episodes end state / reveals / relationships).
- Keep novel export ledger richer on time/location anchors and info-acquisition events.

## Changes
- Added continuity schemas (`ContinuityLedger`, `ContinuityAuditResult`, etc.) and new prompt templates for audit/rewrite/ledger-update.
- Episode generation:
  - LangGraph path: per-episode REACT now includes continuity audit + rewrite and writes `continuity_snapshot`; updates `continuity_ledger` incrementally.
  - Direct plan path: postprocesses episode list with audit/rewrite and rolling ledger updates.
  - Persists the latest `continuity_ledger` into `Story.extra_metadata`.
- Script generation:
  - Adds audit + rewrite pass for dialogues/stage directions (both LangGraph and direct generation results).
  - Injects continuity constraints into script prompts (knowledge gating + time/transition rules).
- Novel export:
  - Extends ledger update prompt and ledger compaction/init to track time/location anchors and info-acquisition events.

## Validation
- `cd ai-pic-backend && pytest tests/unit tests/services tests/scripts`
- Chrome e2e (Chrome DevTools MCP):
  - Login as `geyunfei`.
  - Open story `E2E-ShortDrama-2026-01-18-21-49-06` (`/stories/d4b832fc1ff4498383737772183b055e`).
  - Generate episodes (1 episode, 5 minutes). Refresh story page and confirm episode list shows `第1集 · 复仇序幕` and `进入工作台` works.
  - In episode workspace (`/episodes/d2a55afbef4c4c9a8460d651b0475ba2/workspace`), click `生成剧本` → task created (`task_id=5838`) → task completed → script visible under `查看剧本` with scenes + dialogues.
- `./docker/build_prod_images.sh` (success; image tag printed as `7155a32`)

## Next Steps
- Consider adding format-aware variants for audit/rewrite prompts if short_drama needs stricter enforcement.
- Add unit tests for continuity postprocessing (audit/rewrite mocked) to prevent regressions.

## Linked Commits
- (to be filled after commit)
