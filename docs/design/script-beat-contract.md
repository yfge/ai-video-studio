# Script Beat Contract 设计文档

Date: 2026-05-28

## User Prompt

The current scripts are too weak in quality and structure. Improve both the
product script-generation path and the provider-chain quality proof, with the
first version focused on structured quality plus concrete dramatic quality.

## Goals

- Make script generation produce a stable `scene -> beats -> lines/actions`
  structure before it is rendered into legacy script text.
- Preserve existing public API and database compatibility for
  `scripts.scenes`, `scripts.dialogues`, and `scripts.stage_directions`.
- Reuse existing normalized `scenes` and `scene_beats` tables instead of adding
  a parallel structure or a new migration in the first version.
- Turn hook, escalation, payoff, and cliffhanger from loose text keywords into
  required structured events.
- Align the product production path and provider-chain quality proof around the
  same script-quality semantics.
- Stop fallback code from making incomplete scripts look production-ready.

## Non-Goals

- No frontend changes in the first implementation slice.
- No database migration in the first implementation slice.
- No direct Timeline Spec generation from the script agent in this slice.
- No broad rewrite of `scripts_legacy.py`, `dialogue_audio_service.py`, or
  `ai_service_manager.py`.
- No provider-spend live proof is required to land the contract and local tests.

## Current Context

The repository already has two script surfaces that must converge:

- Product production path: async script generation defaults to `production` and
  runs through `ScriptLangGraphAgent`, quality gates, ScriptScore, persistence,
  and optional Timeline setup.
- Provider-chain quality proof: `scripts/harness/provider_chain_*` calls
  `/api/v1/ai/generate/text` directly and currently uses a thin two-scene,
  one-or-two-lines-per-scene script contract.

The current system can score high on deterministic lint while still producing
thin drama. The quality proof evidence shows examples where `script_lint` passes
but ScriptScore flags weak character recognizability, missing conflict
escalation, weak logic, or low clip yield. This design makes the structured
beat layer the source for both quality checks and downstream formatting.

## Approved Approach

Implement a `StructuredScriptContract v1` internal contract. It complements the
existing `ScriptModel`; it does not replace it.

The contract is generated or normalized before persistence, then flattened into
the existing legacy fields:

- `scripts.scenes`
- `scripts.dialogues`
- `scripts.stage_directions`
- `scripts.content`

It is also synced into normalized story-structure tables:

- `scenes`
- `scene_beats`

More detailed beat metadata lives in `scene_beats.metadata` so the first slice
does not need a database migration.

## Contract Shape

At minimum, the normalized contract contains:

```text
script
  contract_version = "script-beat-v1"
  title
  logline
  scenes[]
    scene_number
    slug_line
    location
    time_of_day
    estimated_duration_seconds
    dramatic_role
    conflict
      question
      stakes
      opposition
      turn
    beats[]
      order_index
      beat_type
      dramatic_purpose
      visible_event
      action_lines[]
      dialogue_lines[]
      duration_seconds
      hook_tag
      payoff_tag
      cliffhanger_tag
```

Required enum values:

- `scene.dramatic_role`: `hook`, `escalation`, `payoff`, `cliffhanger`,
  `transition`
- `beat.beat_type`: `hook`, `setup`, `conflict`, `reveal`, `payoff`,
  `cliffhanger`, `transition`

`dialogue_lines[]` entries include `character`, `content`, optional `emotion`,
and optional `action`. `action_lines[]` entries include `content`, optional
`timing`, and optional `type`.

## Generation Flow

The product production path is the primary integration target.

1. Keep `scene_plan` as the first planning step, but require it to output
   `dramatic_role`, conflict fields, and duration intent.
2. Add or replace a beat-writing step that produces 3 to 5 beats per scene.
3. Assemble the legacy script payload only from the beat contract:
   - `dialogues` is flattened from `beats[*].dialogue_lines`.
   - `stage_directions` is flattened from `beats[*].action_lines`.
   - `content` is rendered through the existing commercial vertical-drama text
     formatter.
4. Run beat-contract validation before existing quality gates persist the
   script.
5. Store the beat contract in script metadata for audit and repair traces.

The direct AI-manager fallback should also return or normalize into the same
contract. If the model returns only the old scene/dialogue shape, the normalizer
may attempt one compatibility conversion, but the converted contract must still
pass the beat gates.

## Provider-Chain Harness Flow

Provider-chain scripts must stop using the current thin script shape as their
quality target.

The harness prompt and parser should require the same beat-level contract while
keeping the existing 30 second proof constraint:

- `full-30s`: exactly 2 scenes, usually 15 seconds each.
- Each scene still has 3 to 5 beats.
- Dialogue stays short enough for subtitles and TTS.
- `video_prompt` and shot planning can be derived from the beat-level visible
  events and action lines.

The quality report should upgrade `structured_script_score` from keyword-based
scoring to beat-contract scoring.

## Persistence And Sync

The first implementation does not change the database schema.

Persistence rules:

- Keep `scripts.scenes` as scene-level summaries, with `beats` optionally
  included inside the JSON payload for compatibility consumers that can use it.
- Keep `scripts.dialogues` and `scripts.stage_directions` as flattened arrays.
- Store the complete normalized beat contract in `script.extra_metadata` under a
  stable key such as `structured_script_contract`.
- Extend `sync_script_scenes_to_story_structure` so generated beat data creates
  `scene_beats` rows.
- Put fields without first-class columns into `SceneBeat.extra_metadata`, such
  as `dramatic_purpose`, `visible_event`, `hook_tag`, `payoff_tag`,
  `cliffhanger_tag`, and raw line arrays.

Compatibility rule:

Existing frontend and API consumers should continue to work against the old
fields. New downstream code can opt into the contract from metadata or
normalized `scene_beats`.

## Validation Gates

Validation has three layers.

### Structure Gate

Fail if:

- A scene has fewer than 3 beats, except for explicitly configured ultra-short
  smoke mode.
- Beat order indexes are missing, duplicated, or non-contiguous.
- Any beat lacks `visible_event`.
- A scene has neither action coverage nor dialogue coverage.
- Required scene roles are missing from the episode-level contract.
- Dialogue or action lines reference a scene or beat outside the contract.

### Drama Gate

Fail if:

- The first scene does not contain a first-beat hook.
- There is no clear escalation after the opening hook.
- No payoff beat names what the protagonist concretely gains, reveals, prevents,
  wins, or loses.
- The final beat fully resolves the situation instead of leaving an unresolved
  question, new threat, or irreversible reveal.
- Conflict fields do not name stakes or opposition.

Most checks should be deterministic. LLM judgement may be used narrowly for
whether a payoff or cliffhanger is genuine, but deterministic failures should
not require an LLM call.

### Production Gate

Fail if:

- Duration totals are outside configured tolerance.
- Dialogue lines exceed the configured short-line limit.
- Registered-character policy fails.
- Action lines are abstract or unfilmable.
- Beat duration and scene duration cannot map into Timeline or storyboard
  planning.

## Repair Behavior

Repair operates on the beat contract, not on formatted text.

Failure details should become structured repair input:

- failed check id
- scene number
- beat order index when available
- evidence
- fix guidance

The repair step regenerates only the invalid contract pieces when practical.
After repair, the formatter re-flattens `content`, `dialogues`, and
`stage_directions`.

Fallback narration should no longer make a script pass quality. If
`populate_dialogues_and_stage_if_missing` creates narration or synthetic stage
directions, those entries must be marked as fallback evidence and the beat gate
must fail unless a real repair replaces them.

## Rollout Plan

### Slice 1: Contract And Local Gates

- Add Pydantic schemas or typed dataclasses for `StructuredScriptContract v1`.
- Add normalizer and flatten helpers.
- Add deterministic contract checks.
- Add unit tests for pass/fail cases.
- Add tests proving flatten output remains compatible with existing
  `ScriptModel`.

### Slice 2: Product Production Path

- Update `ScriptLangGraphAgent` prompts and schemas to produce scene beats.
- Update direct AI-manager fallback prompts and schemas.
- Wire contract normalization before existing script quality gates.
- Extend story-structure sync to create `scene_beats`.
- Persist the contract in `extra_metadata`.

### Slice 3: Provider-Chain Proof Alignment

- Update provider-chain script prompt and parser to require beats.
- Update `provider_chain_script_text` and Timeline payload derivation to use the
  beat contract.
- Replace keyword-heavy `structured_script_score` with beat-contract scoring.
- Keep paid provider-chain smoke separate from the implementation commit unless
  explicitly requested.

## Test Plan

Local tests:

- New contract schema and normalizer tests.
- New structure/drama/production gate tests.
- Existing `test_script_quality_lint.py` coverage for rendered text.
- Story-structure sync tests proving `scene_beats` are created from script
  beats.
- Harness parser and quality-gate tests for provider-chain beat scripts.

Repo checks:

- `python scripts/check_repo_docs.py`
- `python scripts/check_repo_contracts.py --mode diff <changed files>`

Runtime validation for implementation, not for this design document:

- Backend quick or targeted pytest for changed services.
- Provider-chain smoke only when the implementation reaches harness integration
  and provider state is available.
- Browser evidence only if frontend/backend workflow behavior changes.

## Acceptance Criteria

The implementation is acceptable when:

- A valid beat-contract script can be flattened into the old script fields.
- Invalid thin scripts fail local beat gates even when old lint would pass.
- Product async production generation stores the beat contract and still creates
  normal script records.
- Normalized `scene_beats` are created from generated script beats.
- Provider-chain quality tests reject two-scene scripts that only have one or
  two loose dialogue lines per scene.
- No new database migration is required for the first slice.

## Risks

- The model may return overlarge beat JSON. Mitigation: cap scenes and beats,
  keep dialogue lines short, and use repair on specific failed pieces.
- Beat validation may initially be stricter than current live generation.
  Mitigation: land deterministic tests first and gate provider spend separately.
- Existing fallback code can hide missing script structure. Mitigation: treat
  fallback narration as repair evidence, not production-quality content.
- Provider-chain prompt changes may increase text-generation latency. Mitigation:
  keep the 30 second proof to 2 scenes and 3 to 5 beats per scene.

## Open Decisions

- The exact Python module names for the new contract helpers should follow the
  implementation plan after checking file-size limits.
- The final threshold values for beat counts and line lengths can start with
  conservative defaults and be tuned after one local regression pass.
