import pytest
from app.services.providers.base import ProviderConfig
from app.services.providers.minimax_provider import MinimaxProvider


@pytest.mark.asyncio
async def test_minimax_provider_tts_payload_coerces_and_filters(monkeypatch) -> None:
    provider = MinimaxProvider(
        ProviderConfig(
            name="minimax",
            api_key="test-key",
            group_id="test-group",
            base_url="https://example.invalid",
            timeout=10,
        )
    )

    captured: dict[str, object] = {}

    async def fake_post_json(path: str, payload: dict) -> dict:
        captured["path"] = path
        captured["payload"] = payload
        return {"data": {"audio": "https://example.invalid/audio.wav"}, "trace_id": "t"}

    monkeypatch.setattr(provider.client, "post_json", fake_post_json)

    resp = await provider.text_to_speech(
        text="老板，这是我的辞呈。",
        model="speech-2.6-hd",
        voice_id="Chinese (Mandarin)_Lyrical_Voice",
        speed=1.0,
        pitch=0.0,
        emotion=None,
        format="wav",
        output_format="url",
        stream=False,
        voice_type="system",
        sample_rate="24000",
        bitrate="128000",
        channel="1",
    )

    assert resp.success is True
    assert captured["path"] == "/t2a_v2"

    payload = captured["payload"]
    assert isinstance(payload, dict)
    assert "voice_type" not in payload

    voice_setting = payload["voice_setting"]
    assert isinstance(voice_setting, dict)
    assert voice_setting["pitch"] == 0
    assert isinstance(voice_setting["pitch"], int)

    audio_setting = payload["audio_setting"]
    assert isinstance(audio_setting, dict)
    assert audio_setting["sample_rate"] == 24000
    assert audio_setting["bitrate"] == 128000
    assert audio_setting["channel"] == 1


@pytest.mark.asyncio
async def test_minimax_provider_tts_payload_includes_emotion_in_voice_setting(
    monkeypatch,
) -> None:
    provider = MinimaxProvider(
        ProviderConfig(
            name="minimax",
            api_key="test-key",
            group_id="test-group",
            base_url="https://example.invalid",
            timeout=10,
        )
    )

    captured: dict[str, object] = {}

    async def fake_post_json(path: str, payload: dict) -> dict:
        captured["path"] = path
        captured["payload"] = payload
        return {"data": {"audio": "https://example.invalid/audio.wav"}, "trace_id": "t"}

    monkeypatch.setattr(provider.client, "post_json", fake_post_json)

    resp = await provider.text_to_speech(
        text="老板，这是我的辞呈。",
        model="speech-2.6-hd",
        voice_id="Chinese (Mandarin)_Lyrical_Voice",
        speed=1.0,
        pitch=0.0,
        emotion="angry",
        format="wav",
        output_format="url",
        stream=False,
    )

    assert resp.success is True
    assert captured["path"] == "/t2a_v2"

    payload = captured["payload"]
    assert isinstance(payload, dict)
    voice_setting = payload["voice_setting"]
    assert isinstance(voice_setting, dict)
    assert voice_setting["emotion"] == "angry"
