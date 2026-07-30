"""Parse and validate one bounded chapter-contract batch."""

from __future__ import annotations

from app.schemas.story_novel_longform import StoryNovelGenerationPlan
from app.utils.json_utils import extract_json_block
from pydantic import ValidationError

from .story_novel_canon_service import canonical_json, validate_generation_plan
from .story_novel_outline_merge import merge_frozen_chapters
from .story_novel_plan_normalizer import normalize_plan_payload
from .story_novel_plan_state_compiler import compile_plan_state
from .story_novel_planning_batches import validated_prefix_context

_FROZEN_LENGTH_KEYS = ("min_chars", "target_chars", "max_chars", "length_source")


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
    payload = normalize_plan_payload(
        extract_json_block(text), canon, thread_payoffs=thread_payoffs
    )
    try:
        if not payload:
            raise ValueError("missing JSON object")
        prior = list(prior_chapters or [])
        batch_rows = _inject_frozen_lengths(
            list(payload.get("chapters") or []), frozen_spec
        )
        parsed = StoryNovelGenerationPlan.model_validate(
            {**payload, "chapters": [*prior, *batch_rows]}
        )
        positions = [item.position for item in parsed.chapters[len(prior) :]]
        if expected_positions and positions != expected_positions:
            raise ValueError(
                "explicit outline chapter coverage mismatch: "
                f"expected {expected_positions}, got {positions}"
            )
        machine_rows = compile_plan_state(canon, parsed.model_dump()["chapters"])[
            len(prior) :
        ]
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
    except ValidationError as exc:
        chapter_rows = [
            *list(prior_chapters or []),
            *list((payload or {}).get("chapters") or []),
        ]
        return None, canonical_json(
            {
                "kind": "schema",
                "issues": [_schema_issue(item, chapter_rows) for item in exc.errors()],
            }
        )
    except ValueError as exc:
        return None, str(exc)


def _inject_frozen_lengths(rows: list[dict], frozen_spec: dict | None) -> list[dict]:
    """Make deterministic length contracts authoritative before strict parsing."""
    if not frozen_spec:
        return rows
    frozen = {
        int(item["position"]): item
        for item in frozen_spec.get("chapters") or []
        if isinstance(item, dict) and item.get("position") is not None
    }
    return [
        (
            {
                **row,
                **{
                    key: frozen[int(row["position"])][key]
                    for key in _FROZEN_LENGTH_KEYS
                    if row.get("position") is not None
                    and int(row["position"]) in frozen
                    and key in frozen[int(row["position"])]
                },
            }
            if isinstance(row, dict)
            else row
        )
        for row in rows
    ]


def _schema_issue(item: dict, chapter_rows: list[dict]) -> dict:
    location = list(item["loc"])
    chapter_position = None
    if (
        len(location) > 1
        and location[0] == "chapters"
        and isinstance(location[1], int)
        and 0 <= location[1] < len(chapter_rows)
    ):
        chapter_position = chapter_rows[location[1]].get("position")
    return {
        "path": ".".join(str(value) for value in location),
        "chapter_position": chapter_position,
        "code": item["type"],
        "message": item["msg"],
    }
