"""Canvas sizing and physical ratio checks for Codex image generation."""

from __future__ import annotations

import base64
import io
from typing import Optional

SUPPORTED_SIZES = ("1024x1024", "1536x1024", "1024x1536", "auto")
ASPECT_TOLERANCE = 0.03


def resolve_image_size(
    size: Optional[str],
    width: Optional[int],
    height: Optional[int],
    aspect_ratio: Optional[str],
) -> str:
    """Map arbitrary size hints onto the sizes the image tool accepts."""
    if isinstance(size, str) and size in SUPPORTED_SIZES and size != "auto":
        return size
    ratio = (aspect_ratio or "").strip()
    if not ratio and width and height:
        ratio = "16:9" if width > height else "9:16" if height > width else "1:1"
    if ratio in {"16:9", "4:3", "3:2", "21:9"}:
        return "1536x1024"
    if ratio in {"9:16", "3:4", "2:3"}:
        return "1024x1536"
    if ratio == "1:1":
        return "1024x1024"
    return "auto"


def prompt_with_aspect_contract(prompt: str, aspect_ratio: str | None) -> str:
    ratio = (aspect_ratio or "").strip()
    if not ratio:
        return prompt
    value = _ratio_value(ratio)
    orientation = (
        "VERTICAL PORTRAIT"
        if value is not None and value < 1
        else "HORIZONTAL LANDSCAPE"
    )
    if ratio == "1:1":
        orientation = "SQUARE"
    return (
        f"{prompt.rstrip()}\n\nMANDATORY CANVAS CONTRACT: output exactly one "
        f"{orientation} image at physical aspect ratio {ratio}. Do not rotate, "
        "transpose, letterbox, pillarbox, or return the opposite orientation."
    )


def image_matches_aspect_ratio(
    image_data: str,
    aspect_ratio: str | None,
) -> tuple[bool, tuple[int, int] | None]:
    expected = _ratio_value(aspect_ratio)
    dimensions = _data_image_dimensions(image_data)
    if expected is None or dimensions is None:
        return expected is None, dimensions
    width, height = dimensions
    relative_error = abs((width / height) - expected) / expected
    return relative_error <= ASPECT_TOLERANCE, dimensions


def _ratio_value(value: str | None) -> float | None:
    if not isinstance(value, str) or ":" not in value:
        return None
    left, right = value.split(":", 1)
    try:
        width, height = float(left), float(right)
    except ValueError:
        return None
    return width / height if width > 0 and height > 0 else None


def _data_image_dimensions(value: str) -> tuple[int, int] | None:
    if not isinstance(value, str) or not value.startswith("data:image/"):
        return None
    try:
        raw = base64.b64decode(value.split(",", 1)[1])
        from PIL import Image

        with Image.open(io.BytesIO(raw)) as image:
            image.load()
            return int(image.width), int(image.height)
    except Exception:
        return None
