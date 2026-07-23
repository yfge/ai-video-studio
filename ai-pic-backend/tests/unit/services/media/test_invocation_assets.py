from __future__ import annotations

import importlib
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from app.services.media import invocation_assets
from app.services.media.invocation_references import (
    collect_input_references,
    safe_media_parameters,
)


@pytest.mark.asyncio
async def test_generated_image_is_persisted_with_storage_descriptor(
    monkeypatch,
) -> None:
    monkeypatch.setattr(invocation_assets, "_owned_oss_descriptor", lambda *_: None)
    upload = AsyncMock(
        return_value={
            "success": True,
            "file_url": "https://cdn.example.com/generated/image.png?signature=secret",
            "object_key": "generated/image.png",
            "file_size": 123,
            "content_type": "image/png",
            "metadata": {"sha256": "abc"},
        }
    )
    monkeypatch.setattr(invocation_assets, "upload_from_url", upload)

    result = await invocation_assets.persist_generated_images(
        ["https://provider.example.com/temporary.png?token=secret"],
        provider="openai",
        model="gpt-image-1",
        prefix="ai-generated/text-to-image",
        logger=None,
    )

    assert result.urls == ["https://cdn.example.com/generated/image.png"]
    assert result.fully_persisted is True
    assert result.assets == [
        {
            "media_type": "image",
            "role": "image_0",
            "source_url": "https://provider.example.com/temporary.png",
            "url": "https://cdn.example.com/generated/image.png",
            "object_key": "generated/image.png",
            "file_size": 123,
            "mime_type": "image/png",
            "sha256": "abc",
            "persisted": True,
        }
    ]


def test_media_parameters_omit_inline_payloads_and_signed_queries() -> None:
    value = safe_media_parameters(
        {
            "reference": "https://example.com/ref.png?token=secret",
            "base64_images": ["data:image/png;base64,secret"],
            "nested": {"image": "data:image/png;base64,secret"},
        }
    )

    assert value == {
        "reference": "https://example.com/ref.png",
        "nested": {"image": "<inline-media-omitted>"},
    }


def test_collects_all_provider_reference_roles() -> None:
    references = collect_input_references(
        image_url="https://example.com/start.png",
        end_image_url="https://example.com/end.png",
        provider_kwargs={
            "reference_image_urls": ["https://example.com/grid.png"],
            "character_reference_images": ["https://example.com/character.png"],
        },
    )

    assert references == [
        ("start_image", "https://example.com/start.png"),
        ("end_image", "https://example.com/end.png"),
        ("reference_image_urls", "https://example.com/grid.png"),
        (
            "character_reference_images",
            "https://example.com/character.png",
        ),
    ]


def test_inline_image_is_not_misclassified_as_owned_storage(monkeypatch) -> None:
    storage_module = importlib.import_module("app.services.storage.oss_service")

    monkeypatch.setattr(
        storage_module,
        "oss_service",
        SimpleNamespace(domain="https://cdn.example.com"),
    )

    assert (
        invocation_assets._owned_oss_descriptor(  # noqa: SLF001
            "data:image/png;base64,abc",
            "reference",
        )
        is None
    )
