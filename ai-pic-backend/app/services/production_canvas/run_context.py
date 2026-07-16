from __future__ import annotations

CONTEXT_KEYS = (
    "virtual_ip_id",
    "environment_id",
    "story_id",
    "episode_id",
    "script_id",
    "timeline_id",
    "timeline_version",
    "clip_id",
    "task_id",
)
INTEGER_CONTEXT_KEYS = set(CONTEXT_KEYS) - {"clip_id"}
PLURAL_CONTEXT_KEYS = {key: f"{key}s" for key in INTEGER_CONTEXT_KEYS}
CLIP_CONTEXT_KEYS = (
    "placed_timeline_clip_id",
    "selected_output_clip_id",
)
CONTEXT_OUTPUT_KEYS = (
    set(CONTEXT_KEYS) | set(PLURAL_CONTEXT_KEYS.values()) | set(CLIP_CONTEXT_KEYS)
)
SCOPED_CONTEXT_KEYS = tuple(key for key in CONTEXT_KEYS if key != "task_id")
SCOPED_CONTEXT_OUTPUT_KEYS = (
    set(SCOPED_CONTEXT_KEYS)
    | set(CLIP_CONTEXT_KEYS)
    | {
        PLURAL_CONTEXT_KEYS[key]
        for key in SCOPED_CONTEXT_KEYS
        if key in PLURAL_CONTEXT_KEYS
    }
)
LINEAGE_DESCENDANTS = {
    "virtual_ip_id": (
        "environment_id",
        "story_id",
        "episode_id",
        "script_id",
        "timeline_id",
        "timeline_version",
        "clip_id",
        "task_id",
    ),
    "environment_id": ("task_id",),
    "story_id": (
        "episode_id",
        "script_id",
        "timeline_id",
        "timeline_version",
        "clip_id",
        "task_id",
    ),
    "episode_id": (
        "script_id",
        "timeline_id",
        "timeline_version",
        "clip_id",
        "task_id",
    ),
    "script_id": ("timeline_id", "timeline_version", "clip_id", "task_id"),
    "timeline_id": ("timeline_version", "clip_id", "task_id"),
    "timeline_version": ("clip_id", "task_id"),
    "clip_id": ("task_id",),
}


def _positive_integer(value):
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        normalized = value
    elif isinstance(value, str) and value.strip().isdigit():
        normalized = int(value.strip())
    else:
        return None
    return normalized if normalized > 0 else None


def _normalized_context_value(key: str, source: dict):
    if key == "clip_id":
        direct = source.get("clip_id")
        if isinstance(direct, str) and direct.strip():
            return direct.strip()
        for alias in CLIP_CONTEXT_KEYS:
            value = source.get(alias)
            if isinstance(value, str) and value.strip():
                return value.strip()
        return None
    if key not in INTEGER_CONTEXT_KEYS:
        return None
    value = _positive_integer(source.get(key))
    if value is not None:
        return value
    plural = source.get(PLURAL_CONTEXT_KEYS[key])
    if not isinstance(plural, list):
        return None
    return next(
        (value for item in plural if (value := _positive_integer(item)) is not None),
        None,
    )


def _merge_context(context: dict, source: dict) -> None:
    incoming = {}
    for key in INTEGER_CONTEXT_KEYS:
        value = _normalized_context_value(key, source)
        if value is not None:
            incoming[key] = value
    clip_id = _normalized_context_value("clip_id", source)
    if clip_id is not None and ("timeline_id" in incoming or "timeline_id" in context):
        incoming["clip_id"] = clip_id
    for key in CONTEXT_KEYS:
        if key not in incoming or key not in context or context[key] == incoming[key]:
            continue
        for descendant in LINEAGE_DESCENDANTS.get(key, ()):
            if descendant not in incoming:
                context.pop(descendant, None)
    context.update(incoming)


def merge_canvas_context_outputs(outputs: dict, incoming: dict) -> dict:
    context = {}
    _merge_context(context, outputs)
    _merge_context(context, incoming)
    aliases = {}
    for key, plural in PLURAL_CONTEXT_KEYS.items():
        if plural in outputs or plural in incoming:
            value = context.get(key)
            if value is not None:
                aliases[plural] = [value]
    clip_markers = {}
    for key in CLIP_CONTEXT_KEYS:
        value = incoming.get(key) if key in incoming else outputs.get(key)
        if (
            isinstance(value, str)
            and value.strip()
            and value.strip() == context.get("clip_id")
        ):
            clip_markers[key] = value.strip()
    return {
        **{
            key: value
            for key, value in outputs.items()
            if key not in CONTEXT_OUTPUT_KEYS
        },
        **{
            key: value
            for key, value in incoming.items()
            if key not in CONTEXT_OUTPUT_KEYS
        },
        **aliases,
        **clip_markers,
        **context,
    }


def replace_canvas_context_outputs(outputs: dict, incoming: dict) -> dict:
    shell = {
        key: value for key, value in outputs.items() if key not in CONTEXT_OUTPUT_KEYS
    }
    shell.update(
        {plural: [] for plural in PLURAL_CONTEXT_KEYS.values() if plural in outputs}
    )
    shell.update({key: outputs[key] for key in CLIP_CONTEXT_KEYS if key in outputs})
    return merge_canvas_context_outputs(shell, incoming)


def is_scoped_canvas_media(source: dict) -> bool:
    outputs = source.get("outputs")
    return (
        source.get("skill") in {"image.candidates", "video.candidates"}
        and isinstance(outputs, dict)
        and any(
            isinstance(outputs.get(key), list)
            for key in ("frame_indexes", "queued_frame_indexes")
        )
    )


def merge_canvas_node_context_outputs(
    source: dict,
    incoming: dict,
    *,
    authoritative: bool = False,
) -> dict:
    outputs = source.get("outputs") if isinstance(source.get("outputs"), dict) else {}
    merged = (
        replace_canvas_context_outputs(outputs, incoming)
        if authoritative
        else merge_canvas_context_outputs(outputs, incoming)
    )
    if not is_scoped_canvas_media(source):
        return merged
    scoped = {}
    _merge_context(scoped, outputs)
    for key in SCOPED_CONTEXT_KEYS:
        if key in scoped:
            merged[key] = scoped[key]
    canonical = merge_canvas_context_outputs({}, outputs)
    for key in SCOPED_CONTEXT_OUTPUT_KEYS:
        if key in canonical:
            merged[key] = canonical[key]
    own_task_id = next(
        (
            value
            for key in ("dispatched_task_id",)
            if (value := _positive_integer(outputs.get(key))) is not None
        ),
        None,
    )
    if own_task_id is not None:
        merged["task_id"] = own_task_id
    return merged


def is_authoritative_canvas_context(context) -> bool:
    return set(CONTEXT_KEYS).issubset(context.model_fields_set)


def canvas_run_context(payload: dict) -> dict:
    context = {}
    requested = payload.get("requested_asset_ids")
    if isinstance(requested, dict):
        _merge_context(context, requested)
    sources = list(payload.get("skill_results") or [])
    saved_state = payload.get("saved_state") or {}
    sources.extend(
        node
        for node in saved_state.get("nodes") or []
        if not isinstance(node, dict) or node.get("kind") != "note"
    )
    for source in sources:
        outputs = source.get("outputs") if isinstance(source, dict) else None
        if isinstance(outputs, dict):
            if is_scoped_canvas_media(source):
                outputs = {
                    key: value
                    for key, value in outputs.items()
                    if key not in CONTEXT_OUTPUT_KEYS
                }
            _merge_context(context, outputs)
    resolved = payload.get("resolved_context")
    if isinstance(resolved, dict):
        context = {}
        _merge_context(context, resolved)
    return context
