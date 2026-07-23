"""Outline-driven chapter planning for prose novel revisions."""

from __future__ import annotations

import re
from typing import Awaitable, Callable

from app.schemas.story_novel_longform import StoryNovelGenerationPlan
from app.utils.json_utils import extract_json_block
from fastapi import HTTPException
from pydantic import ValidationError

from .story_novel_ai_prompts import planning_prompt

GenerateText = Callable[..., Awaitable[str]]
_CHAPTER_MARKER = re.compile(r"第\s*(\d+|[零〇一二两三四五六七八九十百千]+)\s*章")
_CN_DIGITS = {
    "零": 0,
    "〇": 0,
    "一": 1,
    "二": 2,
    "两": 2,
    "三": 3,
    "四": 4,
    "五": 5,
    "六": 6,
    "七": 7,
    "八": 8,
    "九": 9,
}
_CN_UNITS = {"十": 10, "百": 100, "千": 1000}


def planning_contract(snapshot: dict) -> dict:
    """Expose only the frozen seed, characters, and world constraints."""
    return {
        "story_seed": snapshot.get("story_seed"),
        "main_characters": snapshot.get("main_characters"),
        "character_relationships": snapshot.get("character_relationships"),
        "world_building": snapshot.get("world_building"),
        "setting_time": snapshot.get("setting_time"),
        "setting_location": snapshot.get("setting_location"),
    }


def _chapter_number(raw: str) -> int:
    if raw.isdigit():
        return int(raw)
    total = 0
    current = 0
    for char in raw:
        if char in _CN_DIGITS:
            current = _CN_DIGITS[char]
        else:
            unit = _CN_UNITS[char]
            total += (current or 1) * unit
            current = 0
    return total + current


def explicit_outline_positions(snapshot: dict) -> list[int]:
    """Return a complete explicit chapter sequence when the outline provides one."""
    outline = str(((snapshot.get("story_seed") or {}).get("outline") or ""))
    positions = list(
        dict.fromkeys(
            _chapter_number(match) for match in _CHAPTER_MARKER.findall(outline)
        )
    )
    if len(positions) >= 2 and positions == list(range(1, positions[-1] + 1)):
        return positions
    return []


def _parse_plan(
    text: str, *, expected_positions: list[int]
) -> tuple[dict | None, str | None]:
    payload = extract_json_block(text)
    try:
        if not payload:
            raise ValueError("missing JSON object")
        parsed = StoryNovelGenerationPlan.model_validate(payload)
        positions = [item.position for item in parsed.chapters]
        if expected_positions and positions != expected_positions:
            raise ValueError(
                "explicit outline chapter coverage mismatch: "
                f"expected 1-{expected_positions[-1]}, got {len(positions)} chapters"
            )
        return parsed.model_dump(), None
    except (ValidationError, ValueError) as exc:
        return None, str(exc)


async def ensure_generation_plan(
    service,
    revision,
    task,
    generate_text: GenerateText,
) -> dict:
    current = dict(revision.generation_plan or {})
    if current.get("status") == "ready" and current.get("chapters"):
        return current

    task.description = "正在根据 StorySeed 大纲规划章节…"
    revision.generation_plan = {
        "version": int(current.get("version") or 0) + 1,
        "status": "planning",
        "chapters": [],
    }
    service.db.commit()
    snapshot = revision.story_snapshot or {}
    expected_positions = explicit_outline_positions(snapshot)
    base = planning_prompt(planning_contract=planning_contract(snapshot))
    text = await generate_text(revision, base, max_tokens=16000)
    normalized, error = _parse_plan(text, expected_positions=expected_positions)
    if not normalized:
        coverage = (
            f"\n大纲显式列出第1章至第{expected_positions[-1]}章；"
            "修复结果必须逐章完整覆盖，不能合并、省略或新增。"
            if expected_positions
            else ""
        )
        repair = (
            base
            + "\n\n上一次规划无效或被截断，请只修复并完整重输一次。"
            + coverage
            + "\n为避免再次截断，每个字符串字段保持一句话，数组只保留必要条目。"
            + f"\n校验错误：{error}\n上一次输出：{text[:12000]}"
        )
        text = await generate_text(revision, repair, max_tokens=16000)
        normalized, error = _parse_plan(text, expected_positions=expected_positions)
    if not normalized:
        revision.generation_plan = {
            **dict(revision.generation_plan or {}),
            "status": "failed",
            "error": error or "invalid generation plan",
        }
        service.db.commit()
        raise HTTPException(status_code=500, detail="章节规划无效，正文尚未生成")

    chapters = normalized["chapters"]
    plan = {
        "version": int((revision.generation_plan or {}).get("version") or 1),
        "status": "ready",
        "chapter_count": len(chapters),
        "target_chars": sum(int(item["target_chars"]) for item in chapters),
        "chapters": chapters,
    }
    revision.generation_plan = plan
    revision.chapter_count = len(chapters)
    revision.target_words = plan["target_chars"]
    task.description = f"规划完成，共 {len(chapters)} 章"
    service.db.commit()
    return plan
