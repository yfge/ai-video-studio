from __future__ import annotations

import base64
from io import BytesIO

import pytest
from app.services.storyboard.storyboard_image_quality_gate import (
    validate_storyboard_output_aspect_ratio,
    validate_storyboard_output_aspect_ratio_strict,
)
from PIL import Image


def _data_image(width: int, height: int) -> str:
    buffer = BytesIO()
    Image.new("RGB", (width, height), "white").save(buffer, format="PNG")
    encoded = base64.b64encode(buffer.getvalue()).decode("ascii")
    return f"data:image/png;base64,{encoded}"


def test_quality_gate_accepts_matching_portrait_output() -> None:
    result = validate_storyboard_output_aspect_ratio(
        [_data_image(900, 1600)],
        expected_aspect_ratio="9:16",
    )

    assert result == [{"width": 900, "height": 1600, "status": "passed"}]


def test_quality_gate_rejects_landscape_output_for_portrait_request() -> None:
    with pytest.raises(RuntimeError, match="aspect ratio quality gate failed"):
        validate_storyboard_output_aspect_ratio(
            [_data_image(1536, 1024)],
            expected_aspect_ratio="9:16",
        )


@pytest.mark.asyncio
async def test_strict_quality_gate_inspects_remote_provider_output() -> None:
    remote_image = _data_image(900, 1600).split(",", 1)[1]

    async def fetch_bytes(_url: str) -> bytes:
        return base64.b64decode(remote_image)

    result = await validate_storyboard_output_aspect_ratio_strict(
        ["https://cdn.example/output.png"],
        expected_aspect_ratio="9:16",
        fetch_bytes=fetch_bytes,
    )

    assert result == [{"width": 900, "height": 1600, "status": "passed"}]
