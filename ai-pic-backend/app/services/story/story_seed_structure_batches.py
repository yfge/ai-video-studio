"""Bounded hierarchical structure generation for very long StorySeeds."""

from __future__ import annotations

from app.schemas.story_seed import (
    StorySeedProgressionArc,
    StorySeedProgressionPlan,
    StorySeedStructuredChapter,
    StorySeedStructuredOutline,
)
from app.utils.json_utils import extract_json_block

from .story_seed_service import ending_is_covered
from .story_seed_structure_policy import (
    chapter_batch_token_budget,
    progression_token_budget,
    structure_ranges,
)
from .story_seed_structure_prompts import (
    structured_arc_chapters_prompt,
    structured_arc_repair_prompt,
    structured_progression_prompt,
)
from .story_seed_thread_contract import validate_seed_thread_contract


async def generate_hierarchical_outline(
    *,
    db,
    task,
    carrier,
    prompt_seed: dict,
    expected_positions: list[int],
    generate_text,
    ensure_active,
) -> StorySeedStructuredOutline:
    ranges = structure_ranges(expected_positions)
    prompt = structured_progression_prompt(
        story_seed=prompt_seed,
        chapter_ranges=[
            _range_contract(index, rows) for index, rows in enumerate(ranges, 1)
        ],
    )
    arcs = await _generate_progression(
        carrier, prompt, expected_positions, generate_text, ensure_active
    )
    await ensure_active()
    batches, payoffs = [], []
    for index, arc in enumerate(arcs.progression_arcs, start=1):
        positions = list(range(arc.start_position, arc.end_position + 1))
        task.description = f"正在规划第 {positions[0]}–{positions[-1]} 章…"
        db.commit()
        prompt = structured_arc_chapters_prompt(
            story_seed=prompt_seed,
            progression_plan=arcs.model_dump(),
            arc=arc.model_dump(),
            positions=positions,
            is_final=index == len(arcs.progression_arcs),
        )
        chapters, rows = await _generate_chapter_batch(
            carrier,
            prompt,
            arc,
            arcs,
            generate_text,
            ensure_active,
            ending_direction=(
                str(prompt_seed.get("ending_direction") or "")
                if index == len(arcs.progression_arcs)
                else ""
            ),
        )
        batches.extend(chapters)
        payoffs.extend(rows)
        await ensure_active()
    outline = StorySeedStructuredOutline.model_validate(
        {
            "status": "draft",
            "version": 1,
            "requested_chapter_count": len(expected_positions),
            "planning_structure_version": 1,
            "progression_arcs": [item.model_dump() for item in arcs.progression_arcs],
            "chapters": batches,
            "thread_schedule_version": 1,
            "thread_payoffs": payoffs,
        }
    )
    validate_seed_thread_contract(outline, require_version=True)
    return outline


async def _generate_progression(
    carrier, prompt, positions, generate_text, ensure_active
):
    budget = progression_token_budget(positions)
    text = await generate_text(carrier, prompt, max_tokens=budget)
    await ensure_active()
    parsed, error = parse_progression(text, positions)
    if parsed:
        return parsed
    repair = structured_arc_repair_prompt(prompt, text, error or "分卷规划无效")
    text = await generate_text(carrier, repair, max_tokens=budget)
    await ensure_active()
    parsed, error = parse_progression(text, positions)
    if not parsed:
        raise ValueError(f"分卷规划无效: {error}")
    return parsed


async def _generate_chapter_batch(
    carrier,
    prompt,
    arc,
    plan,
    generate_text,
    ensure_active,
    *,
    ending_direction="",
):
    positions = list(range(arc.start_position, arc.end_position + 1))
    budget = chapter_batch_token_budget(positions)
    text = await generate_text(carrier, prompt, max_tokens=budget)
    await ensure_active()
    parsed, error = parse_chapter_batch(
        text, arc, plan, ending_direction=ending_direction
    )
    if parsed:
        return parsed
    repair = structured_arc_repair_prompt(prompt, text, error or "分卷章节无效")
    text = await generate_text(carrier, repair, max_tokens=budget)
    await ensure_active()
    parsed, error = parse_chapter_batch(
        text, arc, plan, ending_direction=ending_direction
    )
    if not parsed:
        raise ValueError(f"第 {positions[0]}–{positions[-1]} 章无效: {error}")
    return parsed


def parse_progression(text, expected_positions):
    try:
        payload = extract_json_block(text) or {}
        raw = payload.get("progression_plan") or payload
        plan = StorySeedProgressionPlan.model_validate(raw)
        expected = [
            (f"arc-{index:03d}", rows[0], rows[-1])
            for index, rows in enumerate(structure_ranges(expected_positions), 1)
        ]
        actual = [
            (item.arc_id, item.start_position, item.end_position)
            for item in plan.progression_arcs
        ]
        if (
            plan.requested_chapter_count != len(expected_positions)
            or actual != expected
        ):
            raise ValueError(f"分卷覆盖不匹配: expected={expected}, actual={actual}")
        return plan, None
    except (KeyError, TypeError, ValueError) as exc:
        return None, str(exc)


def parse_chapter_batch(
    text, arc: StorySeedProgressionArc, plan, *, ending_direction=""
):
    try:
        payload = extract_json_block(text) or {}
        if not isinstance(payload, dict):
            raise ValueError("分卷章节必须是 JSON 对象")
        raw_chapters = payload.get("chapters")
        raw_payoffs = payload.get("thread_payoffs")
        if set(payload) != {"chapters", "thread_payoffs"}:
            raise ValueError("分卷章节必须且只返回 chapters/thread_payoffs")
        if not isinstance(raw_chapters, list) or not isinstance(raw_payoffs, list):
            raise ValueError("chapters/thread_payoffs 必须是数组")
        chapters = [
            StorySeedStructuredChapter.model_validate(item).model_dump()
            for item in raw_chapters or []
        ]
        positions = list(range(arc.start_position, arc.end_position + 1))
        if [item["position"] for item in chapters] != positions:
            raise ValueError("分卷章节位置不连续或覆盖不完整")
        if ending_direction.strip():
            last = chapters[-1]
            ending_contract = "\n".join(
                [
                    last["title"],
                    last["goal"],
                    *last["key_events"],
                    last["end_state"],
                ]
            )
            if not ending_is_covered(ending_direction, ending_contract):
                raise ValueError("final chapter does not cover ending_direction")
        directives = [item for row in plan.progression_arcs for item in row.threads]
        _validate_openings(chapters, directives)
        payoffs = _validate_payoffs(chapters, raw_payoffs, directives)
        return (chapters, payoffs), None
    except (KeyError, TypeError, ValueError) as exc:
        return None, str(exc)


def _validate_openings(chapters, directives) -> None:
    expected = {
        position: [
            item.thread_id for item in directives if item.open_position == position
        ]
        for position in [item["position"] for item in chapters]
    }
    for chapter in chapters:
        if chapter.get("open_threads") != expected[chapter["position"]]:
            raise ValueError(f"第 {chapter['position']} 章伏笔开启与分卷规划不一致")


def _validate_payoffs(chapters, rows, directives) -> list[dict]:
    positions = {item["position"] for item in chapters}
    expected = {
        item.thread_id: item.payoff_position
        for item in directives
        if item.payoff_position in positions
    }
    if [item.get("thread_id") for item in rows] != list(expected):
        raise ValueError("分卷伏笔回收未按规划完整返回")
    events = {item["position"]: item["key_events"] for item in chapters}
    for item in rows:
        position = item.get("payoff_position")
        if position != expected[item["thread_id"]]:
            raise ValueError(f"伏笔回收章节不匹配: {item['thread_id']}")
        if item.get("evidence_key_event") not in events[position]:
            raise ValueError(f"伏笔证据不属于第 {position} 章 key_events")
    return rows


def _range_contract(index: int, positions: list[int]) -> dict:
    return {
        "arc_id": f"arc-{index:03d}",
        "start_position": positions[0],
        "end_position": positions[-1],
    }
