# docs/ Index

This directory holds design notes, API references, and testing guides. Keep this index in sync with additions/removals.

## Harness

- `docs/generated/db-schema.md` — generated schema summary for agent context.
- `docs/exec-plans/active/` — active execution plans that are not product-roadmap items.
- `docs/exec-plans/active/timeline-main-chain-optimization.md` — post-bridge
  review and optimization plan for script -> Timeline Spec -> storyboard
  support.
- `docs/exec-plans/active/script-beat-contract.md` — step-by-step
  implementation plan for script beat contracts and provider-chain quality
  proof.
- `docs/exec-plans/active/commercial-script-quality.md` — deterministic
  commercial-specificity gate for beat-level short-drama scripts.
- `docs/exec-plans/active/grid-storyboard-mode.md` — optional grid-storyboard
  support mode from Timeline clips to storyboard sheet to clip video references.
- `docs/exec-plans/active/storyboard-keyframe-video-generation.md` — implementation
  plan for selected-clip storyboard, start/end keyframe, video generation
  interaction, and shared prompt contract improvements.
- `docs/exec-plans/completed/` — completed execution plans and archived implementation outlines.

## Agent System Of Record

- `docs/architecture/contracts.md` — repository contracts, diff-vs-audit policy, and choke-point rules.
- `docs/architecture/file-size-limits.md` — file-size thresholds, refactor triggers, and layering constraints.
- `docs/architecture/testing-policy.md` — validation matrix, browser policy, and pre-commit expectations.
- `docs/architecture/agent-workflow.md` — ledger format, commit discipline, and evidence recording rules.
- `docs/standards/README.md` — standard engine catalog, standard object shape, and runtime entry points.
- `docs/standards/STD-ARCH-001.md` — source files stay below size limits.
- `docs/standards/STD-ARCH-002.md` — API route handlers stay thin.
- `docs/standards/STD-DATA-001.md` — SQLAlchemy queries stay inside repositories.
- `docs/standards/STD-ARCH-003.md` — legacy choke points are not expansion points.
- `docs/standards/STD-DOCS-001.md` — repository docs and agent mirrors stay synchronized.
- `docs/standards/STD-EVIDENCE-001.md` — agent changes include durable validation evidence.
- `docs/standards/STD-SCRIPT-001.md` — production scripts satisfy beat-level quality gates.
- `docs/standards/STD-TIMELINE-001.md` — Timeline-first provider chains preserve media lineage.

Keep durable engineering rules in repository docs like the files above. Do not treat chat transcripts or temporary notes as authoritative process documentation.

## Product & Architecture

- `docs/media-asset-persistence.md` — generated media persistence plus target `media_assets` contract for timeline clips and render jobs.
- `docs/db-backup-policy.md` — SQL backup handling policy (external storage + restore procedure).
- `docs/soft-delete-business-id.md` — soft delete + business_id design.
- `docs/story-structure-api.md` — normalized story-structure endpoints.
- `docs/story-structure-gap-analysis.md` — historical gap analysis (pre-normalization).
- `docs/storyboard-normalized-toggle.md` — storyboard normalized integration notes.
- `docs/dialogue-audio-timeline-spec.md` — dialogue audio transition spec feeding Timeline Spec v1.
- `docs/timeline-rendering-pipeline.md` — Timeline Spec v1 and render/export main-chain contract.
- `docs/cartoon-sample-production-proof.md` — fixed 2D/3D cartoon sample
  tracker for the 10-sample production proof.
- `docs/agent_graphs/` — generated agent state graphs (Mermaid + PNG).

## Design Documents

- `docs/design/production-canvas.md` — executable short-drama production canvas,
  typed dependency graph, candidate review, and Timeline integration design.
- `docs/design/duration-orchestrator-agent.md` — Duration Orchestrator Agent 设计（端到端时长闭环验证）
- `docs/design/image-generation-unification.md` — 图像生成统一化设计（Virtual IP / Environment / Storyboard）
- `docs/design/story-episode-generation-quality.md` — story/episode generation quality (strict validation + repair, audit trail)
- `docs/design/script-beat-contract.md` — script beat contract design for product generation and provider-chain quality proof.
- `docs/design/storyboard-keyframe-video-generation.md` — selected-clip storyboard, start/end keyframe, video generation interaction and prompt contract design.
- `docs/image-gen-provider-matrix.md` — provider×mode 参数矩阵与提示词语义（provider-aware）

## Market Insights

- `docs/short-drama-overseas-insights.md` — notes from Sanlian Lifeweek PDFs on short‑drama export.
- `docs/short-drama-microgenre-framework.md` — market x micro-genre matrix, Story Bible template, hook cadence, traffic sheet spec, and scoring rules.

## Testing

- `docs/TESTING_GUIDE.md` — browser E2E validation steps.
- `docs/testing/agent-validation-workflow.md` — repo-local validation matrix, MCP minimum checklist, and `agent_chats` Validation template for the testing skills.
- `/.codex/skills/` — repo-versioned Codex skills for backend testing, frontend testing, and MCP E2E validation. Invoke them explicitly by path from this repository.

## Provider Reference

- `docs/api/` — provider API notes (Volcengine, Keling, Minimax, etc.).
