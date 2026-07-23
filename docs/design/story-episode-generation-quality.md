# Story/Episode Generation Quality

This document captures the "strict validation + repair" direction for story/episode generation.

## Current Design Boundary

`docs/design/narrative-memory-and-dramatic-state.md` narrows new Story generation
to a lightweight, editable `story_seed_v1`. Strict structured output remains,
but the Story schema no longer owns episode pacing, traffic hooks, stage highs,
shootability, character-growth continuity, knowledge state, or subtext.

- Story keeps schema, required-field, Virtual IP ownership, frozen shared-memory
  baseline, direct Canon-conflict, and blocking compliance checks.
- Story uses at most one bounded schema repair and never persists heuristic
  free-text fallback.
- Novel/adaptation planning owns long-form and episode structure.
- Narrative memory owns approved continuity, character knowledge, and growth.
- Episode/Script own commercial pacing, shootability, disclosure, and subtext.
- Existing `structured_story_contract` remains a read-only compatibility format;
  new narrative-series generation uses `story_seed_v1`.

## Goals

- Treat Story Seed and Episode generation as **structured output**, not free text.
- Fail fast when the model output is invalid instead of persisting heuristic fallbacks.
- Keep an auditable trace of what the model returned and how we repaired it.
- Avoid repeating downstream production and continuity validation at Story creation.

## Phase 1: Strict Structured Output + Repair

### Shared Helper

- `ai-pic-backend/app/services/ai/structured_output.py`
  - Extract JSON (`extract_json_block`) from provider output.
  - Validate against a Pydantic schema (`model_validate`).
  - If invalid, run a bounded repair loop (`max_repairs`) using the same JSON schema.

The helper returns structured metadata:

- `content`: last raw provider output (string)
- `normalized`: validated `model_dump()` (dict) or `None`
- `validation_errors`: final Pydantic errors when invalid
- `repair_attempts`: each repair attempt metadata (provider/model/usage + output + errors)
- `first_attempt`: initial attempt metadata

### Story Seed (Strict Persistence)

- Production validates the smaller `StorySeedEnvelope`; fields moved to Novel,
  Episode, Script, or narrative memory are not Story blockers.
- We do not persist heuristic parsing from free text as a fallback.

### Audit Trail

We store the structured-output trace in:

- `Story.extra_metadata.agent_run` (for entity-level inspection)
- `Task.parameters.agent_run` (for operator inspection via `/tasks`)

## Notes

- The repair loop is intentionally bounded to avoid runaway retries.
- Context management and readiness checks are tracked separately in `tasks.md` (later phases).
