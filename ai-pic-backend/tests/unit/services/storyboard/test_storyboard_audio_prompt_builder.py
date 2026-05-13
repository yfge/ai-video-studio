from __future__ import annotations

import pytest

from app.services.storyboard.storyboard_audio_prompt_builder import (
    build_visual_prompt_description,
)


def _assert_common_short_drama_shape(prompt: str) -> None:
    assert "画面主体:" in prompt
    assert "表演动作:" in prompt
    assert "场景光线:" in prompt
    assert "构图连续性:" in prompt
    assert "禁止项:" in prompt
    assert "竖屏短剧" in prompt
    assert "单幅画面" in prompt
    assert "无字幕" in prompt
    assert "无可读文字" in prompt
    assert "多格漫画" in prompt


@pytest.mark.parametrize(
    ("text", "expected_intent", "expected_detail"),
    [
        ("你到底想怎么样？", "疑问/追问", "眼神追问"),
        ("我受够了！", "情绪激烈", "情绪外露"),
    ],
)
def test_dialogue_prompt_is_visual_only_and_rich(
    text: str,
    expected_intent: str,
    expected_detail: str,
) -> None:
    prompt = build_visual_prompt_description(
        beat_type="dialogue",
        speaker_name="林晚",
        text=text,
    )

    _assert_common_short_drama_shape(prompt)
    assert "开口说话" in prompt
    assert f"语气{expected_intent}" in prompt
    assert expected_detail in prompt
    assert text not in prompt


def test_voiceover_prompt_uses_silent_reaction() -> None:
    prompt = build_visual_prompt_description(
        beat_type="dialogue",
        speaker_name="林晚",
        text="我不能让他们看出来。",
        dialogue_action="内心独白",
    )

    _assert_common_short_drama_shape(prompt)
    assert "沉默反应" in prompt
    assert "不开口说话" in prompt
    assert "我不能让他们看出来" not in prompt


def test_document_read_prompt_hides_screen_text() -> None:
    prompt = build_visual_prompt_description(
        beat_type="dialogue",
        speaker_name="陈哲",
        text="她看见「离婚协议」四个字，手突然停住。",
    )

    _assert_common_short_drama_shape(prompt)
    assert "屏幕/纸面内容只能模糊呈现" in prompt
    assert "无可读文字" in prompt
    assert "离婚协议" not in prompt


def test_action_prompt_preserves_action_without_dialogue_text() -> None:
    prompt = build_visual_prompt_description(
        beat_type="action",
        speaker_name=None,
        text="推开门冲进客厅，「别动」",
    )

    _assert_common_short_drama_shape(prompt)
    assert "推开门冲进客厅" in prompt
    assert "别动" not in prompt
    assert "动作有明确目的" in prompt


def test_pause_prompt_adds_reaction_rhythm() -> None:
    prompt = build_visual_prompt_description(
        beat_type="pause",
        speaker_name=None,
        text=None,
    )

    _assert_common_short_drama_shape(prompt)
    assert "剧情停顿瞬间" in prompt
    assert "微表情" in prompt
