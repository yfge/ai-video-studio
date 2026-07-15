from typing import Any, Sequence


def normalize_frame_indexes(
    frame_indexes: Sequence[int] | None,
    frame_count: int,
) -> list[int]:
    if frame_count <= 0:
        return []
    if frame_indexes is None:
        return list(range(frame_count))
    normalized: list[int] = []
    for raw in frame_indexes:
        try:
            index = int(raw)
        except (TypeError, ValueError):
            continue
        if 0 <= index < frame_count and index not in normalized:
            normalized.append(index)
    return normalized


def frame_has_reference_images(frame: dict[str, Any]) -> bool:
    for key in (
        "reference_images",
        "reference_image_urls",
        "start_reference_images",
        "end_reference_images",
    ):
        value = frame.get(key)
        if isinstance(value, list) and any(_has_non_empty_url(item) for item in value):
            return True
    return any(
        _has_non_empty_url(frame.get(key))
        for key in ("reference_image", "environment_reference_image")
    )


def frame_requires_reference_images(frame: dict[str, Any]) -> bool:
    """Keep legacy frames safe while allowing explicit identity-free shots."""

    explicit = frame.get("requires_reference_images")
    if isinstance(explicit, bool):
        return explicit
    characters = frame.get("characters")
    if isinstance(characters, list):
        return bool(characters)
    return True


def _has_non_empty_url(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())
