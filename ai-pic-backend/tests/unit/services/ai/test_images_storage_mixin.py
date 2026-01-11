from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from app.services.ai.images_storage import ImageStorageMixin


class _DummyService(ImageStorageMixin):
    def __init__(self) -> None:
        self.logger = MagicMock()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_download_image_accepts_dict_url():
    service = _DummyService()
    test_image_b64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
    image_data = f"data:image/png;base64,{test_image_b64}"

    with patch("app.services.ai.images_storage.settings") as mock_settings:
        with patch("aiofiles.open", create=True) as mock_aio_open:
            with patch("os.makedirs"):
                mock_settings.UPLOAD_DIR = "/tmp/test_uploads"

                mock_file = AsyncMock()
                mock_aio_open.return_value.__aenter__.return_value = mock_file

                result = await service._download_image(
                    {"index": 0, "url": image_data},
                    "TestIP",
                    "environment",
                )

                assert result.startswith("/tmp/test_uploads/")
                assert result.endswith(".png")
                mock_file.write.assert_called_once()
