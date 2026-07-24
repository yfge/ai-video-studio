"""One-repair conversion from a plain StorySeed outline to v2 chapters."""

from __future__ import annotations

from app.models.task import TaskStatus
from app.repositories.narrative_memory_repository import NarrativeMemoryRepository
from app.schemas.story_seed import StorySeedModel, StorySeedStructuredOutline
from app.utils.json_utils import extract_json_block
from fastapi import HTTPException
from pydantic import ValidationError

from .story_novel_ai_prompts import structured_outline_prompt
from .story_outline_positions import explicit_outline_positions
from .story_seed_service import StorySeedService, ending_is_covered
from .story_seed_thread_contract import (
    merge_payoff_evidence,
    validate_seed_thread_contract,
)
from .story_seed_thread_repair import (
    apply_seed_thread_repairs,
    repair_conflict_ids,
    seed_thread_repair_prompt,
)


async def structure_story_seed(
    db,
    story,
    task,
    carrier,
    generate_text,
    *,
    expected_version: int,
) -> StorySeedModel:
    seed = dict(story.story_seed or {})
    expected_positions = explicit_outline_positions({"story_seed": seed})
    prompt_seed = {
        key: value for key, value in seed.items() if key != "structured_outline"
    }
    prompt = structured_outline_prompt(
        story_seed=prompt_seed, expected_positions=expected_positions
    )
    task.description = "正在把文字大纲转换为结构化章节…"
    db.commit()
    text = await generate_text(carrier, prompt, max_tokens=_planning_tokens(seed))
    ending_direction = str(seed.get("ending_direction") or "")
    outline, error = _parse(text, expected_positions, ending_direction)
    if not outline:
        shape, _ = _parse_outline_shape(text, expected_positions, ending_direction)
        conflicts = _targeted_conflicts(shape)
        if shape and conflicts:
            try:
                repair = seed_thread_repair_prompt(shape, conflicts, error)
            except ValueError:
                conflicts = []
        if shape and conflicts:
            task.description = "章节结构完成，正在修复伏笔回收合同…"
            db.commit()
        else:
            repair = (
                prompt
                + "\n\n上一次结果无效或被截断，只允许完整修复并重输一次。"
                + f"\n校验错误：{error}\n上一次输出：{text[:12000]}"
            )
        text = await generate_text(carrier, repair, max_tokens=_planning_tokens(seed))
        if shape and conflicts:
            try:
                outline = apply_seed_thread_repairs(shape, text, conflicts)
                error = None
            except (KeyError, TypeError, ValueError) as exc:
                outline, error = None, str(exc)
        else:
            outline, error = _parse(text, expected_positions, ending_direction)
    if not outline:
        raise HTTPException(status_code=500, detail=f"结构化大纲无效: {error}")
    db.refresh(task)
    if task.status == TaskStatus.CANCELLED:
        raise HTTPException(status_code=409, detail="任务已取消")
    source_outline = seed.get("outline_text") or seed.get("outline")
    upgraded = StorySeedModel.model_validate(
        {
            **seed,
            "schema": "story_seed_v2",
            "outline_text": source_outline,
            "structured_outline": {
                **outline.model_dump(),
                "status": "draft",
                "version": int(
                    ((seed.get("structured_outline") or {}).get("version") or 0)
                )
                + 1,
            },
        }
    )
    StorySeedService(NarrativeMemoryRepository(db)).apply_local_update(
        story,
        upgraded,
        requested_status="draft",
        expected_version=expected_version,
        allow_task_id=task.id,
    )
    db.commit()
    return upgraded


def _parse(
    text: str, expected_positions: list[int], ending_direction: str = ""
) -> tuple[StorySeedStructuredOutline | None, str | None]:
    outline, error = _parse_outline_shape(text, expected_positions, ending_direction)
    if not outline:
        return None, error
    try:
        validate_seed_thread_contract(outline, require_version=True)
        return outline, None
    except (ValueError, TypeError) as exc:
        return None, str(exc)


def _parse_outline_shape(
    text: str, expected_positions: list[int], ending_direction: str = ""
) -> tuple[StorySeedStructuredOutline | None, str | None]:
    try:
        payload = extract_json_block(text) or {}
        raw = payload.get("structured_outline") or payload
        outline = StorySeedStructuredOutline.model_validate(raw)
        outline = merge_payoff_evidence(outline)
        positions = [item.position for item in outline.chapters]
        if expected_positions and positions != expected_positions:
            raise ValueError(
                "explicit outline chapter coverage mismatch: "
                f"expected 1-{expected_positions[-1]}, got {len(positions)} chapters"
            )
        last = outline.chapters[-1]
        ending_contract = "\n".join(
            [last.title, last.goal, *last.key_events, last.end_state]
        )
        if ending_direction.strip() and not ending_is_covered(
            ending_direction, ending_contract
        ):
            raise ValueError("final chapter does not cover ending_direction")
        return outline, None
    except (ValidationError, ValueError, TypeError) as exc:
        return None, str(exc)


def _targeted_conflicts(
    outline: StorySeedStructuredOutline | None,
) -> list[str]:
    if not outline:
        return []
    try:
        return repair_conflict_ids(outline)
    except (KeyError, TypeError, ValueError):
        return []


def _planning_tokens(seed: dict) -> int:
    expected = explicit_outline_positions({"story_seed": seed})
    return max(6000, (len(expected) or 12) * 700)
