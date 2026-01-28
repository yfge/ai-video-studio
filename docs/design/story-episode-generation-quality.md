# Story/Episode Generation Quality

This document captures the "strict validation + repair" direction for story/episode generation.

## Goals

- Treat story/episode generation as **structured output**, not free text.
- Fail fast when the model output is invalid instead of persisting heuristic fallbacks.
- Keep an auditable trace of what the model returned and how we repaired it.

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

### Story Outline (Strict Persistence)

- `ai-pic-backend/app/services/story/story_generation_service.py` now requires the story outline to validate against `StoryOutlineModel`.
- We do not persist heuristic parsing from free text as a fallback.

### Audit Trail

We store the structured-output trace in:

- `Story.extra_metadata.agent_run` (for entity-level inspection)
- `Task.parameters.agent_run` (for operator inspection via `/tasks`)

## Notes

- The repair loop is intentionally bounded to avoid runaway retries.
- Context management and readiness checks are tracked separately in `tasks.md` (later phases).
