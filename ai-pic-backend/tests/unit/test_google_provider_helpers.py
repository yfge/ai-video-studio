import os
from io import BytesIO

import pytest
from app.services.providers.google_provider.helpers import maybe_compress_inline_image
from PIL import Image


@pytest.mark.unit
def test_maybe_compress_inline_image_downscales_and_reencodes():
    img = Image.frombytes("RGB", (1024, 1024), os.urandom(1024 * 1024 * 3))
    buf = BytesIO()
    img.save(buf, format="PNG")
    raw = buf.getvalue()

    out, mime = maybe_compress_inline_image(
        raw,
        content_type="image/png",
        target_max_bytes=150_000,
        max_side=512,
    )

    assert mime == "image/jpeg"
    assert len(out) < len(raw)

    decoded = Image.open(BytesIO(out))
    assert max(decoded.size) <= 512
