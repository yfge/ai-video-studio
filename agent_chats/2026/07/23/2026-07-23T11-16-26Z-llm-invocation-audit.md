---
id: 2026-07-23T11-16-26Z-llm-invocation-audit
date: "2026-07-23T11:16:26Z"
participants: [user, codex]
models: [gpt-5]
tags: [backend, llm, media, audit, persistence, tokens, oss]
related_paths:
  - ai-pic-backend/app/models/llm_invocation.py
  - ai-pic-backend/app/models/video_generation_task.py
  - ai-pic-backend/app/repositories/llm_invocation_repository.py
  - ai-pic-backend/app/services/llm_invocation.py
  - ai-pic-backend/app/services/ai_manager_text_generation.py
  - ai-pic-backend/app/services/ai_manager_image_generation.py
  - ai-pic-backend/app/services/ai_manager_image_to_image.py
  - ai-pic-backend/app/services/ai_manager_video_generation.py
  - ai-pic-backend/app/services/video/video_task_polling_service.py
  - ai-pic-backend/alembic/versions/b6c7d8e9f0a1_add_llm_invocations.py
summary: Persist complete per-attempt text and media AI inputs, outputs, OSS assets, token usage, provider lifecycle, and call scene.
---

## User Prompt

新增统一的 `llm_invocations`，确保每次 LLM 调用都记录完整 prompt
和 response，以及 input token、cache token、output token、model 和调用场景。
生图和生视频调用还需记录原始 prompt、相关 reference，并将输出记录为
OSS 资产；异步视频需关联提交与最终轮询结果。

## Goals

- Record every product text-provider attempt, including failure and fallback attempts.
- Preserve complete user prompt, system prompt, response, and error without truncation.
- Normalize provider-specific input, cached, and output token usage.
- Record actual provider/model, call scene, attempt number, status, and latency.
- Record image/video invocation type, original/effective prompt, stable input
  reference copies, and normalized OSS output descriptors without DB binary blobs.
- Link async video submission attempts to their final polling result.
- Keep observability persistence failures from breaking the user-facing LLM call.

## Changes

- Added the `llm_invocations` SQLAlchemy model, repository, and Alembic migration.
- Used MySQL `LONGTEXT` variants for complete prompt, system prompt, response, and
  error storage while retaining SQLite `Text` compatibility.
- Added two-phase persistence around each provider attempt in the shared text
  fallback loop, leaving interrupted calls visible as `processing`.
- Added automatic call-scene inference with an explicit `call_scene` override.
- Routed the legacy OpenAI fallback through the audited manager and added
  equivalent persistence for the configured custom text service.
- Added token normalization for OpenAI/Codex, DeepSeek, and Google usage shapes.
- Extended the same table to `text_to_image`, `image_to_image`,
  `text_to_video`, and `image_to_video` attempts with `original_prompt`,
  `input_references`, `output_assets`, and `provider_task_id`.
- Reused the existing media persistence layer to copy image outputs and input
  references to OSS. Signed query strings and inline base64 payloads are not
  persisted in JSON audit fields.
- Added per-attempt image/video recording across manager fallback loops and the
  separate async video task dispatcher path.
- Added `video_generation_tasks.llm_invocation_id` so polling completes the
  exact submitted invocation with final video, thumbnail, and last-frame OSS
  descriptors; terminal failure and timeout also finalize the audit row.
- Added `output_persist_failed` to distinguish provider success from failed
  product-owned media persistence.
- Updated the compact generated database schema summary.

## Validation

- Focused text, image, media persistence, video submission, dispatcher, and
  polling matrix — 33 passed; all newly added invocation/media tests executed
  and passed.
- Timeline clip rework compatibility regression reproduced from the full suite,
  updated its provider double for the explicit call-scene contract, and reran
  the file — 2 passed.
- An isolated full-suite run from the exact staged snapshot completed without
  shared-database interference — 2699 passed, 96 skipped, 6 failed. Two failures
  were the call-scene test-double mismatch fixed above. The remaining four are
  pre-existing Timeline lifecycle, single-video context, and concurrent Story
  Novel behavior outside this slice.
- Isolated migration validation stamped SQLite to `a8b9c0d1e2f3`, upgraded to
  `b6c7d8e9f0a1`, inspected the schema, then downgraded cleanly — the table,
  eight indexes, and `video_generation_tasks` column/index/foreign key were
  created and removed as expected.
- Full SQLite migration from base did not reach this migration because existing
  revision `e5f3948ee82e` executes unsupported SQLite `ALTER COLUMN` syntax.
- `ruff check <changed Python files>` — pass.
- `black --check <25 changed Python files>` and
  `isort --check-only --profile=black <25 changed Python files>` — pass.
- MySQL offline DDL renders `prompt`, `system_prompt`, `response`, and `error`
  as `LONGTEXT`, with three token counters as `BIGINT`.
- `python scripts/check_repo_docs.py` — pass.
- `python scripts/check_repo_contracts.py --mode diff <changed files>` — pass
  after replacing a literal legacy-manager module name in scene inference.
- Browser/provider validation was not run because it would require paid
  external LLM/image/video generation; persistence behavior is covered with
  provider and storage doubles.
- `pre-commit run --all-files` was not run because the shared checkout contains
  two unrelated active Story Novel slices; the equivalent changed-file
  formatting, repository checks, and focused tests above were run directly.
- `docker/build_prod_images.sh` was not run because its default behavior pushes
  images to the external registry, which is outside this commit-and-migrate
  request.

## Next Steps

- Apply migration `b6c7d8e9f0a1` in each deployment before enabling the code.
- Add retention/access policy before exposing full prompts and responses in an
  operator API because they may contain private production content.

## Linked Commits

- This commit.
