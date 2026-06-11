"""Unit tests: dynamic prompt service orchestration and bundle apply."""

from __future__ import annotations

from types import SimpleNamespace

from app.core.config import settings
from app.services.storyboard.dynamic_prompt.service import (
    apply_dynamic_prompt_bundle,
    build_dynamic_prompt_bundles,
)
from tests.unit.services.storyboard.dynamic_prompt_fixtures import (
    FakeAIManager,
    llm_payload,
    make_frames,
    make_ref_ctx,
    make_script,
)


def enable_feature(monkeypatch):
    monkeypatch.setattr(settings, "STORYBOARD_DYNAMIC_PROMPT_ENABLED", True)




def test_disabled_feature_returns_empty(monkeypatch):
    monkeypatch.setattr(settings, "STORYBOARD_DYNAMIC_PROMPT_ENABLED", False)
    result = build_dynamic_prompt_bundles(
        make_script(),
        make_frames(),
        [0, 1],
        make_ref_ctx(),
        ai_service=SimpleNamespace(ai_manager=FakeAIManager([])),
    )
    assert result == {}


def test_prompt_override_skips_generation(monkeypatch):
    enable_feature(monkeypatch)
    manager = FakeAIManager([llm_payload([0, 1])])
    result = build_dynamic_prompt_bundles(
        make_script(),
        make_frames(),
        [0, 1],
        make_ref_ctx(),
        prompt_override="用户自定义提示词",
        ai_service=SimpleNamespace(ai_manager=manager),
    )
    assert result == {}
    assert manager.calls == 0


def test_generates_bundles_and_writes_cache(monkeypatch):
    enable_feature(monkeypatch)
    frames = make_frames()
    manager = FakeAIManager([llm_payload([0, 1])])
    result = build_dynamic_prompt_bundles(
        make_script(),
        frames,
        [0, 1],
        make_ref_ctx(),
        style="写实",
        ai_service=SimpleNamespace(ai_manager=manager),
    )
    assert set(result) == {0, 1}
    assert result[0]["image_prompt"] == "image prompt 0"
    assert frames[0]["llm_prompt_bundle"]["input_sha"]
    assert frames[1]["llm_prompt_bundle"]["provider_used"] == "fake"
    assert manager.calls == 1


def test_cache_hit_skips_llm_call(monkeypatch):
    enable_feature(monkeypatch)
    frames = make_frames()
    manager = FakeAIManager([llm_payload([0, 1])])
    args = dict(style="写实", ai_service=SimpleNamespace(ai_manager=manager))
    build_dynamic_prompt_bundles(make_script(), frames, [0, 1], make_ref_ctx(), **args)
    assert manager.calls == 1
    second = build_dynamic_prompt_bundles(
        make_script(), frames, [0, 1], make_ref_ctx(), **args
    )
    assert manager.calls == 1
    assert set(second) == {0, 1}


def test_changed_input_invalidates_cache(monkeypatch):
    enable_feature(monkeypatch)
    frames = make_frames()
    manager = FakeAIManager([llm_payload([0, 1]), llm_payload([0])])
    args = dict(ai_service=SimpleNamespace(ai_manager=manager))
    build_dynamic_prompt_bundles(make_script(), frames, [0, 1], make_ref_ctx(), **args)
    frames[0]["description"] = "改写后的画面"
    build_dynamic_prompt_bundles(make_script(), frames, [0], make_ref_ctx(), **args)
    assert manager.calls == 2


def test_bad_json_retries_once_then_falls_back(monkeypatch):
    enable_feature(monkeypatch)

    class BadManager:
        def __init__(self):
            self.calls = 0

        async def generate_text(self, **kwargs):
            self.calls += 1
            return SimpleNamespace(success=True, data="not json at all {", provider="f", model="m")

    manager = BadManager()
    result = build_dynamic_prompt_bundles(
        make_script(),
        make_frames(),
        [0, 1],
        make_ref_ctx(),
        ai_service=SimpleNamespace(ai_manager=manager),
    )
    assert result == {}
    assert manager.calls == 2


def test_exception_is_swallowed(monkeypatch):
    enable_feature(monkeypatch)

    class BoomManager:
        async def generate_text(self, **kwargs):
            raise RuntimeError("boom")

    result = build_dynamic_prompt_bundles(
        make_script(),
        make_frames(),
        [0, 1],
        make_ref_ctx(),
        ai_service=SimpleNamespace(ai_manager=BoomManager()),
    )
    assert result == {}


# ---------------------------------------------------------------- apply


def compiled_stub():
    return {
        "image_prompt": "compiler image",
        "start_keyframe_prompt": "compiler start",
        "end_keyframe_prompt": "compiler end",
        "i2v_motion_prompt": "compiler i2v",
        "prompt_sha256": "old",
        "warnings": [],
    }


def test_apply_bundle_overwrites_three_fields_keeps_i2v():
    bundle = {
        "image_prompt": "llm image",
        "start_keyframe_prompt": "llm start",
        "end_keyframe_prompt": "llm end",
    }
    compiled = apply_dynamic_prompt_bundle(compiled_stub(), bundle)
    assert compiled["image_prompt"] == "llm image"
    assert compiled["start_keyframe_prompt"] == "llm start"
    assert compiled["end_keyframe_prompt"] == "llm end"
    assert compiled["i2v_motion_prompt"] == "compiler i2v"
    assert compiled["prompt_source"] == "llm_dynamic"
    assert compiled["prompt_sha256"] != "old"


def test_apply_bundle_truncates_long_prompts():
    bundle = {
        "image_prompt": "x" * 3000,
        "start_keyframe_prompt": "y" * 2000,
        "end_keyframe_prompt": "z",
    }
    compiled = apply_dynamic_prompt_bundle(compiled_stub(), bundle)
    assert len(compiled["image_prompt"]) <= 2200
    assert "image_prompt_truncated" in compiled["warnings"]
    assert "start_keyframe_prompt_truncated" in compiled["warnings"]


def test_apply_without_bundle_keeps_compiler_output(monkeypatch):
    monkeypatch.setattr(settings, "STORYBOARD_DYNAMIC_PROMPT_ENABLED", False)
    compiled = apply_dynamic_prompt_bundle(compiled_stub(), None)
    assert compiled["image_prompt"] == "compiler image"
    assert compiled["warnings"] == []


def test_apply_without_bundle_records_fallback_when_enabled(monkeypatch):
    monkeypatch.setattr(settings, "STORYBOARD_DYNAMIC_PROMPT_ENABLED", True)
    compiled = apply_dynamic_prompt_bundle(compiled_stub(), None)
    assert "dynamic_prompt_fallback" in compiled["warnings"]
