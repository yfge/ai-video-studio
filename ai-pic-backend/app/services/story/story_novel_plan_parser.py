"""Parse and validate one bounded chapter-contract batch."""

from __future__ import annotations

from app.schemas.story_novel_longform import StoryNovelGenerationPlan
from app.utils.json_utils import extract_json_block
from pydantic import ValidationError

from .story_novel_canon_service import validate_generation_plan
from .story_novel_outline_merge import merge_frozen_chapters
from .story_novel_plan_normalizer import (
    normalize_plan_payload,
    normalize_redundant_location_state,
)
from .story_novel_planning_batches import validated_prefix_context


def parse_plan(
    text,
    expected_positions,
    canon,
    frozen_spec,
    thread_payoffs=None,
    *,
    prior_chapters=None,
    require_complete=True,
) -> tuple[dict | None, str | None]:
    payload = normalize_plan_payload(extract_json_block(text), canon)
    try:
        if not payload:
            raise ValueError("missing JSON object")
        prior = list(prior_chapters or [])
        batch_rows = list(payload.get("chapters") or [])
        parsed = StoryNovelGenerationPlan.model_validate(
            {**payload, "chapters": [*prior, *batch_rows]}
        )
        positions = [item.position for item in parsed.chapters[len(prior) :]]
        if expected_positions and positions != expected_positions:
            raise ValueError(
                "explicit outline chapter coverage mismatch: "
                f"expected {expected_positions}, got {positions}"
            )
        machine_rows = normalize_redundant_location_state(
            canon, parsed.model_dump()["chapters"]
        )[len(prior) :]
        rows = merge_frozen_chapters(
            machine_rows,
            frozen_spec,
            canon,
            thread_payoffs,
            validate=False,
        )
        candidate = [*prior, *rows]
        if require_complete:
            validate_generation_plan(canon, candidate)
        else:
            validated_prefix_context(canon, candidate)
        return {"chapters": rows}, None
    except (ValidationError, ValueError) as exc:
        return None, str(exc)
