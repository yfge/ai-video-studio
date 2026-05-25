# docs/ Index

This directory holds design notes, API references, and testing guides. Keep this index in sync with additions/removals.

## Harness

- `docs/generated/db-schema.md` — generated schema summary for agent context.
- `docs/exec-plans/active/` — active execution plans that are not product-roadmap items.
- `docs/exec-plans/active/timeline-main-chain-optimization.md` — post-bridge
  review and optimization plan for script -> Timeline Spec -> storyboard
  support.
- `docs/exec-plans/completed/` — completed execution plans and archived implementation outlines.

## Agent System Of Record

- `docs/architecture/contracts.md` — repository contracts, diff-vs-audit policy, and choke-point rules.
- `docs/architecture/file-size-limits.md` — file-size thresholds, refactor triggers, and layering constraints.
- `docs/architecture/testing-policy.md` — validation matrix, browser policy, and pre-commit expectations.
- `docs/architecture/agent-workflow.md` — ledger format, commit discipline, and evidence recording rules.

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

- `docs/design/duration-orchestrator-agent.md` — Duration Orchestrator Agent 设计（端到端时长闭环验证）
- `docs/design/image-generation-unification.md` — 图像生成统一化设计（Virtual IP / Environment / Storyboard）
- `docs/design/story-episode-generation-quality.md` — story/episode generation quality (strict validation + repair, audit trail)
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
