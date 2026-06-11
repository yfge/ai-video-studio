"""LLM prompt builders for scene grid sheets and grid-to-video generation."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from app.core.config import settings
from app.core.logging import get_logger
from app.prompts.manager import prompt_manager
from app.prompts.templates import PromptTemplate
from app.schemas.storyboard_scene_grid import (
    SceneGridPromptModel,
    SceneGridVideoPromptModel,
)
from app.services.storyboard.dynamic_prompt.context_builder import (
    build_scene_context,
)
from app.services.storyboard.scene_grid.layout import SceneGridLayout
from app.utils.json_utils import extract_json_block

logger = get_logger("storyboard_scene_grid")

DEFAULT_CELL_DURATION = 1.2
MIN_VIDEO_SECONDS = 4
MAX_VIDEO_SECONDS = 15


async def build_sheet_prompt(
    script: Any,
    scene_number: int,
    frames: List[dict],
    ref_ctx: Any,
    *,
    layout: SceneGridLayout,
    aspect_ratio: str,
    style: Optional[str],
    has_character_refs: bool,
    has_environment_refs: bool,
    ai_manager: Any,
) -> Dict[str, Any]:
    """Build the grid sheet image prompt, preferring LLM with static fallback."""
    scene_context = build_scene_context(
        script,
        scene_number,
        ref_ctx,
        [str(f.get("description") or "") for f in frames],
        style=style,
    )
    frame_inputs = [
        {
            "shot_type": f.get("shot_type") or "",
            "camera_movement": f.get("camera_movement") or "",
            "composition": f.get("composition") or "",
            "duration": f.get("duration_seconds"),
            "description": str(f.get("description") or f.get("ai_prompt") or "")[:200],
        }
        for f in frames
    ]
    variables = {
        **scene_context,
        "frames": frame_inputs,
        "panel_count": layout.panel_count,
        "rows": layout.rows,
        "columns": layout.columns,
        "aspect_ratio": aspect_ratio,
        "has_character_refs": has_character_refs,
        "has_environment_refs": has_environment_refs,
    }
    if ai_manager is not None:
        parsed = await _generate_json(
            ai_manager,
            PromptTemplate.STORYBOARD_SCENE_GRID_PROMPT.value,
            variables,
            SceneGridPromptModel,
            "scene_grid_sheet_prompt",
        )
        if parsed is not None:
            return {
                "sheet_prompt": parsed.sheet_prompt,
                "cells": [cell.model_dump() for cell in parsed.cells],
                "prompt_source": "llm_dynamic",
            }
    return _fallback_sheet_prompt(scene_context, frame_inputs, layout, aspect_ratio)


async def build_video_prompt(
    script: Any,
    scene_number: int,
    cells: List[dict],
    ref_ctx: Any,
    *,
    total_duration: float,
    aspect_ratio: str,
    style: Optional[str],
    ai_manager: Any,
) -> Dict[str, Any]:
    """Build the grid-to-continuous-video prompt with static fallback."""
    scene_context = build_scene_context(
        script,
        scene_number,
        ref_ctx,
        [str(cell.get("caption") or "") for cell in cells],
        style=style,
    )
    variables = {
        **scene_context,
        "cells": cells,
        "total_duration": round(total_duration, 1),
        "aspect_ratio": aspect_ratio,
    }
    if ai_manager is not None:
        parsed = await _generate_json(
            ai_manager,
            PromptTemplate.STORYBOARD_SCENE_GRID_VIDEO_PROMPT.value,
            variables,
            SceneGridVideoPromptModel,
            "scene_grid_video_prompt",
        )
        if parsed is not None:
            return {
                "video_prompt": parsed.video_prompt,
                "prompt_source": "llm_dynamic",
            }
    return _fallback_video_prompt(scene_context, cells, total_duration, aspect_ratio)


def cell_durations(frames: List[dict], panel_count: int) -> List[float]:
    """Per-panel durations from frame durations, padded/cycled to panel_count."""
    durations: List[float] = []
    for frame in frames[:panel_count]:
        try:
            value = float(frame.get("duration_seconds") or DEFAULT_CELL_DURATION)
        except (TypeError, ValueError):
            value = DEFAULT_CELL_DURATION
        durations.append(max(0.5, value))
    while len(durations) < panel_count:
        durations.append(DEFAULT_CELL_DURATION)
    return durations


def clamp_total_duration(durations: List[float]) -> int:
    total = int(round(sum(durations)))
    return max(MIN_VIDEO_SECONDS, min(MAX_VIDEO_SECONDS, total))


async def _generate_json(
    ai_manager: Any,
    template_name: str,
    variables: Dict[str, Any],
    schema_model: Any,
    schema_name: str,
) -> Optional[Any]:
    prompt = prompt_manager.render_prompt(template_name, variables)
    system_prompt = prompt_manager.render_prompt(
        PromptTemplate.SYSTEM_PROMPT_JSON_STRICT.value, {}
    )
    for attempt in range(2):
        try:
            response = await ai_manager.generate_text(
                prompt=prompt,
                temperature=0.5,
                model=settings.STORYBOARD_DYNAMIC_PROMPT_MODEL,
                json_schema={
                    "name": schema_name,
                    "schema": schema_model.model_json_schema(),
                },
                system_prompt=system_prompt,
            )
        except Exception as exc:
            logger.warning("%s LLM call failed (attempt %s): %s", schema_name, attempt + 1, exc)
            continue
        if not getattr(response, "success", False):
            continue
        content = response.data if isinstance(response.data, str) else str(response.data)
        normalized = extract_json_block(content)
        if not normalized:
            continue
        try:
            return schema_model.model_validate(normalized)
        except Exception:
            logger.warning("%s JSON invalid (attempt %s)", schema_name, attempt + 1)
    return None


def _fallback_sheet_prompt(
    scene_context: Dict[str, Any],
    frame_inputs: List[Dict[str, Any]],
    layout: SceneGridLayout,
    aspect_ratio: str,
) -> Dict[str, Any]:
    scene = scene_context.get("scene") or {}
    cells = []
    lines = []
    for index in range(1, layout.panel_count + 1):
        frame = frame_inputs[(index - 1) % max(1, len(frame_inputs))] if frame_inputs else {}
        description = str(frame.get("description") or f"镜头{index}")
        title = description[:6] or f"镜头{index}"
        cells.append({"panel_index": index, "title": title, "caption": title})
        lines.append(
            f"{index:02d}｜{title}：{frame.get('shot_type') or '中景'}，{description}。"
            f"说明栏文字写：“{title}”。"
        )
    characters = scene_context.get("characters") or []
    char_lines = "；".join(f"{c['name']}：{c['appearance']}" for c in characters)
    sheet_prompt = "\n".join(
        [
            f"生成一张横向 {aspect_ratio} 的高完成度中文{layout.panel_count}宫格动作分镜图。",
            "【整体定位】电影级写实分镜板，由真实电影剧照组成，不是素描草图、卡通或插画，适合作为 AI 视频生成参考图。",
            f"【整体版式】{layout.rows} 行 × {layout.columns} 列共 {layout.panel_count} 格；"
            "每格左上角有黑底白字粗体编号；每格下方有白色说明栏写中文镜头名称。",
            f"【场景设定】固定在同一空间：{scene.get('location') or '同一场景'}，"
            f"{scene.get('time') or ''}；{scene.get('description') or ''}；场景不得切换。",
            f"【主角设定】{char_lines or '人物外貌全图保持一致'}。",
            "【镜头内容】",
            *lines,
            "【画面要求】每格只一个镜头瞬间；除编号与说明栏外画面内不得出现其他文字、字幕、水印、logo；"
            "景别机位逐格变化，相邻格保持动作连续感。",
        ]
    )
    return {"sheet_prompt": sheet_prompt, "cells": cells, "prompt_source": "fallback"}


def _fallback_video_prompt(
    scene_context: Dict[str, Any],
    cells: List[dict],
    total_duration: float,
    aspect_ratio: str,
) -> Dict[str, Any]:
    characters = scene_context.get("characters") or []
    char_lines = "；".join(f"{c['name']}：{c['appearance']}" for c in characters)
    shot_lines = [
        f"镜头{cell.get('panel_index')}（约{cell.get('duration') or DEFAULT_CELL_DURATION}秒）："
        f"{cell.get('caption') or cell.get('title') or ''}"
        for cell in cells
    ]
    video_prompt = "\n".join(
        [
            "使用输入的分镜图作为动作分镜参考。严格参考其中的镜头顺序、动作逻辑、人物调度与节奏推进，"
            "但最终输出必须是完整连续的电影画面，不得出现分镜格子、编号、说明栏、文字、边框或纸张背景。",
            f"【整体风格】电影级写实质感，总时长约 {round(total_duration, 1)} 秒，画幅 {aspect_ratio}。",
            f"【主角设定】{char_lines or '全片人物面部、服装、体型保持一致'}。",
            "【镜头与内容设计】",
            *shot_lines,
            "【画面要求】镜头有明显景别与机位变化，动作连贯自然，不得出现任何文字与水印。",
        ]
    )
    return {"video_prompt": video_prompt, "prompt_source": "fallback"}
