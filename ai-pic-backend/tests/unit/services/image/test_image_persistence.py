"""Unit tests for image persistence utilities."""

import base64
import os
import pytest
from unittest.mock import AsyncMock, MagicMock, patch, mock_open

from app.services.image.image_persistence import (
    download_image,
    upload_local_image_to_oss,
    persist_local_image,
    persist_generated_image,
    persist_uploaded_image,
    save_base64_image,
)


class TestDownloadImage:
    """Tests for download_image function."""

    @pytest.mark.asyncio
    async def test_download_base64_image(self):
        """Test downloading base64-encoded image."""
        # Create a small test image (1x1 pixel PNG)
        test_image_b64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
        image_data = f"data:image/png;base64,{test_image_b64}"

        with patch("app.services.image.image_persistence.settings") as mock_settings:
            with patch("aiofiles.open", create=True) as mock_aio_open:
                mock_settings.UPLOAD_DIR = "/tmp/test_uploads"
                mock_file = AsyncMock()
                mock_aio_open.return_value.__aenter__.return_value = mock_file

                result = await download_image(image_data, "TestIP", "portrait")

                assert result.startswith("/tmp/test_uploads/")
                assert result.endswith(".png")
                mock_file.write.assert_called_once()

    @pytest.mark.asyncio
    async def test_download_url_image(self):
        """Test downloading image from URL."""
        image_url = "https://example.com/image.png"

        with patch("app.services.image.image_persistence.settings") as mock_settings:
            with patch("httpx.AsyncClient") as mock_client_class:
                with patch("aiofiles.open", create=True) as mock_aio_open:
                    mock_settings.UPLOAD_DIR = "/tmp/test_uploads"

                    mock_response = MagicMock()
                    mock_response.raise_for_status = MagicMock()
                    mock_response.content = b"fake_image_content"

                    mock_client = AsyncMock()
                    mock_client.get.return_value = mock_response
                    mock_client_class.return_value.__aenter__.return_value = mock_client

                    mock_file = AsyncMock()
                    mock_aio_open.return_value.__aenter__.return_value = mock_file

                    result = await download_image(image_url, "TestIP", "portrait")

                    assert result.startswith("/tmp/test_uploads/")
                    mock_client.get.assert_called()

    @pytest.mark.asyncio
    async def test_download_with_retry(self):
        """Test that download retries on failure."""
        image_url = "https://example.com/image.png"

        with patch("app.services.image.image_persistence.settings") as mock_settings:
            with patch("httpx.AsyncClient") as mock_client_class:
                with patch("asyncio.sleep", new_callable=AsyncMock):
                    mock_settings.UPLOAD_DIR = "/tmp/test_uploads"

                    mock_client = AsyncMock()
                    mock_client.get.side_effect = Exception("Network error")
                    mock_client_class.return_value.__aenter__.return_value = mock_client

                    with pytest.raises(RuntimeError, match="Image processing failed"):
                        await download_image(image_url, "TestIP", "portrait")

                    # Should have tried 3 times
                    assert mock_client.get.call_count == 3


class TestUploadLocalImageToOSS:
    """Tests for upload_local_image_to_oss function."""

    @pytest.mark.asyncio
    async def test_upload_success(self):
        """Test successful OSS upload."""
        with patch("app.services.image.image_persistence.oss_service") as mock_oss:
            with patch("builtins.open", mock_open(read_data=b"image_content")):
                mock_oss.upload_file_content = AsyncMock(return_value={
                    "success": True,
                    "file_url": "https://cdn.example.com/image.png",
                    "object_key": "images/image.png",
                })

                result = await upload_local_image_to_oss(
                    "/tmp/image.png",
                    prefix="ai-generated",
                    metadata={"ip_name": "Test"},
                )

                assert result["success"] is True
                assert "file_url" in result
                mock_oss.upload_file_content.assert_called_once()

    @pytest.mark.asyncio
    async def test_upload_without_oss_service(self):
        """Test upload fails when OSS not configured."""
        with patch("app.services.image.image_persistence.oss_service", None):
            with pytest.raises(RuntimeError, match="OSS service not configured"):
                await upload_local_image_to_oss(
                    "/tmp/image.png",
                    prefix="ai-generated",
                )


class TestPersistLocalImage:
    """Tests for persist_local_image function."""

    @pytest.mark.asyncio
    async def test_persist_with_oss(self):
        """Test persisting local image with OSS upload."""
        with patch("app.services.image.image_persistence.oss_service") as mock_oss:
            with patch("os.path.getsize", return_value=1024):
                with patch("builtins.open", mock_open(read_data=b"image_content")):
                    mock_oss.upload_file_content = AsyncMock(return_value={
                        "success": True,
                        "file_url": "https://cdn.example.com/image.png",
                        "object_key": "images/image.png",
                    })

                    result = await persist_local_image(
                        "/tmp/test_image.png",
                        prefix="ai-generated",
                    )

                    assert result["local_file_path"] == "/tmp/test_image.png"
                    assert result["relative_path"] == "/uploads/test_image.png"
                    assert result["file_size"] == 1024
                    assert result["oss_url"] == "https://cdn.example.com/image.png"

    @pytest.mark.asyncio
    async def test_persist_without_oss(self):
        """Test persisting local image without OSS."""
        with patch("app.services.image.image_persistence.oss_service", None):
            with patch("os.path.getsize", return_value=1024):
                result = await persist_local_image(
                    "/tmp/test_image.png",
                    prefix="ai-generated",
                )

                assert result["local_file_path"] == "/tmp/test_image.png"
                assert result["oss_url"] is None

    @pytest.mark.asyncio
    async def test_persist_require_upload_fails_without_oss(self):
        """Test that require_upload fails when OSS not configured."""
        with patch("app.services.image.image_persistence.oss_service", None):
            with patch("os.path.getsize", return_value=1024):
                with pytest.raises(RuntimeError, match="OSS not configured"):
                    await persist_local_image(
                        "/tmp/test_image.png",
                        prefix="ai-generated",
                        require_upload=True,
                    )


class TestPersistGeneratedImage:
    """Tests for persist_generated_image function."""

    @pytest.mark.asyncio
    async def test_persist_generated_image(self):
        """Test persisting generated image from URL."""
        with patch(
            "app.services.image.image_persistence.download_image"
        ) as mock_download:
            with patch(
                "app.services.image.image_persistence.persist_local_image"
            ) as mock_persist:
                mock_download.return_value = "/tmp/downloaded.png"
                mock_persist.return_value = {
                    "local_file_path": "/tmp/downloaded.png",
                    "relative_path": "/uploads/downloaded.png",
                    "file_size": 2048,
                    "oss_url": "https://cdn.example.com/downloaded.png",
                }

                result = await persist_generated_image(
                    "https://example.com/image.png",
                    ip_name="TestIP",
                    category="portrait",
                    prefix="ai-generated",
                )

                assert result["local_file_path"] == "/tmp/downloaded.png"
                mock_download.assert_called_once()
                mock_persist.assert_called_once()


class TestPersistUploadedImage:
    """Tests for persist_uploaded_image function."""

    @pytest.mark.asyncio
    async def test_persist_uploaded_image(self):
        """Test persisting user-uploaded image."""
        with patch("app.services.image.image_persistence.settings") as mock_settings:
            with patch("aiofiles.open", create=True) as mock_aio_open:
                with patch(
                    "app.services.image.image_persistence.persist_local_image"
                ) as mock_persist:
                    mock_settings.UPLOAD_DIR = "/tmp/uploads"
                    mock_file = AsyncMock()
                    mock_aio_open.return_value.__aenter__.return_value = mock_file
                    mock_persist.return_value = {
                        "local_file_path": "/tmp/uploads/abc123.png",
                        "relative_path": "/uploads/abc123.png",
                        "file_size": 4096,
                    }

                    result = await persist_uploaded_image(
                        b"image_bytes",
                        "user_upload.png",
                        prefix="user-uploads",
                    )

                    assert "local_file_path" in result
                    mock_file.write.assert_called_once_with(b"image_bytes")


class TestSaveBase64Image:
    """Tests for save_base64_image function."""

    @pytest.mark.asyncio
    async def test_save_base64_image(self):
        """Test saving base64-encoded image."""
        test_b64 = base64.b64encode(b"test_image_data").decode()

        with patch("app.services.image.image_persistence.settings") as mock_settings:
            with patch("builtins.open", mock_open()) as mock_file:
                mock_settings.UPLOAD_DIR = "/tmp/uploads"

                result = await save_base64_image(test_b64, "stability")

                assert result.startswith("/uploads/")
                assert "stability" in result
                assert result.endswith(".png")
