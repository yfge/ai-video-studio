from types import SimpleNamespace

from app.services.virtual_ip_readiness import compute_virtual_ip_readiness


def _ip(**overrides):
    base = {
        "default_avatar_url": None,
        "images": [],
        "voice_config": None,
    }
    base.update(overrides)
    return SimpleNamespace(**base)


def test_readiness_warns_on_missing_avatar_and_voice():
    readiness = compute_virtual_ip_readiness(_ip())
    assert readiness["has_default_avatar"] is False
    assert readiness["voice_config_valid"] is False
    assert len(readiness["warnings"]) == 2


def test_readiness_accepts_default_avatar_url_and_full_voice_config():
    readiness = compute_virtual_ip_readiness(
        _ip(
            default_avatar_url="https://cdn.example/avatar.png",
            voice_config={"provider": "minimax", "voice_id": "male-qn-qingse"},
        )
    )
    assert readiness == {
        "has_default_avatar": True,
        "voice_config_valid": True,
        "warnings": [],
    }


def test_readiness_accepts_default_image_flag():
    image = SimpleNamespace(is_default=True, is_deleted=False)
    readiness = compute_virtual_ip_readiness(_ip(images=[image]))
    assert readiness["has_default_avatar"] is True


def test_readiness_rejects_partial_voice_config():
    readiness = compute_virtual_ip_readiness(
        _ip(voice_config={"provider": "minimax", "voice_id": "  "})
    )
    assert readiness["voice_config_valid"] is False
    readiness = compute_virtual_ip_readiness(_ip(voice_config={"voice_id": "v1"}))
    assert readiness["voice_config_valid"] is False
