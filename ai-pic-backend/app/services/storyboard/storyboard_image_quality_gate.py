"""Physical output checks before storyboard images are promoted."""

from __future__ import annotations

import base64
from io import BytesIO
from typing import Any, Awaitable, Callable, Sequence

import httpx

HTTP_IMAGE_TIMEOUT_SECONDS = 20.0


def validate_storyboard_output_aspect_ratio(
    urls: Sequence[str],
    *,
    expected_aspect_ratio: str | None,
    max_relative_error: float = 0.03,
) -> list[dict[str, Any]]:
    """Reject inspectable outputs whose physical ratio misses the request."""

    expected = _parse_ratio(expected_aspect_ratio)
    if expected is None:
        return []
    checks: list[dict[str, Any]] = []
    for url in urls:
        dimensions = _data_image_dimensions(url)
        if dimensions is None:
            checks.append({"status": "not_inspected"})
            continue
        checks.append(
            _validate_dimensions(
                dimensions,
                expected=expected,
                expected_label=expected_aspect_ratio,
                max_relative_error=max_relative_error,
            )
        )
    return checks


async def validate_storyboard_output_aspect_ratio_strict(
    urls: Sequence[str],
    *,
    expected_aspect_ratio: str | None,
    max_relative_error: float = 0.03,
    fetch_bytes: Callable[[str], Awaitable[bytes]] | None = None,
) -> list[dict[str, Any]]:
    """Inspect data URLs and remote provider outputs, failing closed."""

    expected = _parse_ratio(expected_aspect_ratio)
    if expected is None:
        return []
    fetch = fetch_bytes or _fetch_http_image
    checks: list[dict[str, Any]] = []
    for url in urls:
        dimensions = _data_image_dimensions(url)
        if (
            dimensions is None
            and isinstance(url, str)
            and url.startswith(("http://", "https://"))
        ):
            dimensions = _image_dimensions(await fetch(url))
        if dimensions is None:
            raise RuntimeError(
                "Storyboard image aspect ratio quality gate could not inspect output"
            )
        checks.append(
            _validate_dimensions(
                dimensions,
                expected=expected,
                expected_label=expected_aspect_ratio,
                max_relative_error=max_relative_error,
            )
        )
    return checks


def _parse_ratio(value: str | None) -> float | None:
    if not isinstance(value, str) or ":" not in value:
        return None
    left, right = value.split(":", 1)
    try:
        width = float(left)
        height = float(right)
    except (TypeError, ValueError):
        return None
    if width <= 0 or height <= 0:
        return None
    return width / height


def _data_image_dimensions(url: str) -> tuple[int, int] | None:
    if not isinstance(url, str) or not url.startswith("data:image/"):
        return None
    try:
        encoded = url.split(",", 1)[1]
        raw = base64.b64decode(encoded)
        return _image_dimensions(raw)
    except Exception:
        return None


def _image_dimensions(raw: bytes) -> tuple[int, int] | None:
    try:
        from PIL import Image

        with Image.open(BytesIO(raw)) as image:
            image.load()
            return int(image.width), int(image.height)
    except Exception:
        return None


def _validate_dimensions(
    dimensions: tuple[int, int],
    *,
    expected: float,
    expected_label: str | None,
    max_relative_error: float,
) -> dict[str, Any]:
    width, height = dimensions
    relative_error = abs((width / height) - expected) / expected
    if relative_error > max_relative_error:
        raise RuntimeError(
            "Storyboard image aspect ratio quality gate failed: "
            f"expected={expected_label}, actual={width}x{height}"
        )
    return {"width": width, "height": height, "status": "passed"}


async def _fetch_http_image(url: str) -> bytes:
    async with httpx.AsyncClient(
        timeout=HTTP_IMAGE_TIMEOUT_SECONDS,
        follow_redirects=True,
    ) as client:
        response = await client.get(url)
        response.raise_for_status()
        return response.content
