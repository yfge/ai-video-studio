"""Confirmed structured-outline validation for novel length materialization."""

from fastapi import HTTPException

from .story_seed_thread_contract import (
    outline_has_open_threads,
    validate_seed_thread_contract,
)


def confirmed_outline(story) -> tuple[dict, list[dict], list[int]]:
    seed = dict(story.story_seed or {})
    outline = dict(seed.get("structured_outline") or {})
    chapters = list(outline.get("chapters") or [])
    valid = (
        seed.get("schema") == "story_seed_v2"
        and story.story_seed_status == "confirmed"
        and outline.get("status") in {"confirmed", "frozen"}
        and chapters
    )
    if not valid:
        raise HTTPException(
            status_code=409,
            detail="正文生成需要完整、已确认的 story_seed_v2 结构化大纲",
        )
    positions = [int(item.get("position") or 0) for item in chapters]
    if positions != list(range(1, len(chapters) + 1)):
        raise HTTPException(status_code=409, detail="结构化大纲章节编号不连续")
    try:
        validate_seed_thread_contract(
            outline,
            require_version=outline_has_open_threads(outline),
        )
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return outline, chapters, positions
