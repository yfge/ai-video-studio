from __future__ import annotations

import re
from typing import Any

_TIMELINE_PATH = re.compile(r"^(?:timeline|timeline_videos):(\d+):v(\d+)(?::.*)?$")

_INTEGER_FIELDS = (
    "virtual_ip_id",
    "environment_id",
    "story_id",
    "episode_id",
    "script_id",
    "timeline_id",
    "timeline_version",
)
_PLURAL_FIELDS = {field: f"{field}s" for field in _INTEGER_FIELDS}
_CLIP_FIELDS = (
    "placed_timeline_clip_id",
    "selected_output_clip_id",
)
_LINEAGE_DESCENDANTS = {
    "virtual_ip_id": (
        "environment_id",
        "story_id",
        "episode_id",
        "script_id",
        "timeline_id",
        "timeline_version",
        "clip_id",
    ),
    "story_id": (
        "episode_id",
        "script_id",
        "timeline_id",
        "timeline_version",
        "clip_id",
    ),
    "episode_id": ("script_id", "timeline_id", "timeline_version", "clip_id"),
    "script_id": ("timeline_id", "timeline_version", "clip_id"),
    "timeline_id": ("timeline_version", "clip_id"),
    "timeline_version": ("clip_id",),
}


def _integer(value: Any) -> int | None:
    if value is None or isinstance(value, bool):
        return None
    if isinstance(value, int):
        normalized = value
    elif isinstance(value, str) and value.strip().isdigit():
        normalized = int(value.strip())
    else:
        return None
    return normalized if normalized > 0 else None


def _text(value: Any) -> str | None:
    if not isinstance(value, str):
        return None
    normalized = value.strip()
    return normalized or None


def _source_integer(source: dict[str, Any], field: str) -> int | None:
    value = _integer(source.get(field))
    if value is not None:
        return value
    plural = source.get(_PLURAL_FIELDS[field])
    if not isinstance(plural, list):
        return None
    return next(
        (value for item in plural if (value := _integer(item)) is not None),
        None,
    )


def _merge_source(context: dict[str, Any], source: Any) -> None:
    if not isinstance(source, dict):
        return
    incoming: dict[str, Any] = {}
    for field in _INTEGER_FIELDS:
        value = _source_integer(source, field)
        if value is not None:
            incoming[field] = value
    if "environment_id" not in incoming:
        environment_id = _integer(source.get("env_id"))
        if environment_id is not None:
            incoming["environment_id"] = environment_id
    has_timeline = "timeline_id" in incoming or "timeline_id" in context
    clip_id = None
    if has_timeline:
        clip_id = _text(source.get("clip_id"))
    if clip_id is None and has_timeline:
        for field in _CLIP_FIELDS:
            clip_id = _text(source.get(field))
            if clip_id is not None:
                break
    if clip_id is not None:
        incoming["clip_id"] = clip_id
    clip_ids = source.get("clip_ids")
    if (
        "timeline_id" in incoming
        and "clip_id" not in incoming
        and isinstance(clip_ids, list)
        and len(clip_ids) == 1
    ):
        clip_id = _text(clip_ids[0])
        if clip_id is not None:
            incoming["clip_id"] = clip_id
    for field in _INTEGER_FIELDS:
        if (
            field not in incoming
            or field not in context
            or context[field] == incoming[field]
        ):
            continue
        for descendant in _LINEAGE_DESCENDANTS.get(field, ()):
            if descendant not in incoming:
                context.pop(descendant, None)
    context.update(incoming)


def _merge_result_path(context: dict[str, Any], result_file_path: str | None) -> None:
    path = _text(result_file_path)
    if path is None:
        return
    timeline_match = _TIMELINE_PATH.match(path)
    if timeline_match:
        context.setdefault("timeline_id", int(timeline_match.group(1)))
        context.setdefault("timeline_version", int(timeline_match.group(2)))
        return
    prefix, separator, rest = path.partition(":")
    if not separator:
        return
    token = rest.split(":", 1)[0]
    if prefix == "story":
        story_id = _integer(token)
        if story_id is not None:
            context.setdefault("story_id", story_id)
    elif prefix == "episodes":
        episode_tokens = [item.strip() for item in rest.split(",") if item.strip()]
        if len(episode_tokens) == 1:
            episode_id = _integer(episode_tokens[0])
            if episode_id is not None:
                context.setdefault("episode_id", episode_id)
    elif prefix in {"script", "storyboard_videos"}:
        script_id = _integer(token)
        if script_id is not None:
            context.setdefault("script_id", script_id)


def build_task_result_context(
    *,
    task_id: int,
    parameters: Any,
    result_file_path: str | None,
) -> dict[str, Any]:
    """Normalize old and new task result shapes into one canvas-safe context."""

    params = parameters if isinstance(parameters, dict) else {}
    context: dict[str, Any] = {"task_id": int(task_id)}
    resolved = params.get("resolved_context")
    if params.get("kind") == "production_canvas_run" and isinstance(resolved, dict):
        _merge_source(context, resolved)
        return context
    _merge_source(context, params)
    _merge_source(context, params.get("requested_asset_ids"))
    _merge_source(context, resolved)
    agent_run = params.get("agent_run")
    if isinstance(agent_run, dict):
        _merge_source(context, agent_run.get("result_ref"))
    _merge_result_path(context, result_file_path)
    return context
