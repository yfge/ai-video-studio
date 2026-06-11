"""Unit tests for the scene grid storyboard package."""

from __future__ import annotations

import json
from types import SimpleNamespace

import anyio

from app.services.storyboard.scene_grid.layout import scene_grid_layout
from app.services.storyboard.scene_grid.prompt_builder import (
    build_sheet_prompt,
    build_video_prompt,
    cell_durations,
    clamp_total_duration,
)
from app.services.storyboard.scene_grid.refs import resolve_reference_images


class FakeRefContext:
    def __init__(self):
        self.scene_by_number = {}
        self.scene_char_ids = {}
        self.vip_map = {}
        self.char_image_map = {}
        self.name_to_vip_id = {}
        self.env_images_by_scene = {}


def make_ref_ctx():
    ctx = FakeRefContext()
    scene = SimpleNamespace(id=11)
    ctx.scene_by_number[1] = scene
    ctx.scene_char_ids[11] = {7}
    ctx.vip_map[7] = SimpleNamespace(
        name="阿龙", description="30岁武者", style_prompt=None
    )
    ctx.char_image_map[7] = "https://example.com/along.png"
    ctx.env_images_by_scene[1] = [
        "https://example.com/env1.png",
        "https://example.com/env2.png",
        "https://example.com/env3.png",
    ]
    return ctx


def make_script():
    story = SimpleNamespace(title="醉拳", genre="武侠", theme=None, world_building=None)
    episode = SimpleNamespace(story=story, title="酒馆夜斗", episode_number=1)
    return SimpleNamespace(
        episode=episode,
        scenes=[{"scene_number": 1, "location": "酒馆外", "description": "醉态迎敌"}],
        dialogues=[],
        stage_directions=[],
    )


def make_frames(count=2):
    return [
        {
            "scene_number": 1,
            "shot_type": "中远景",
            "camera_movement": "推",
            "composition": "三分法",
            "duration_seconds": 1.0,
            "description": f"镜头动作{i}",
        }
        for i in range(count)
    ]


# ---------------------------------------------------------------- layout


def test_layout_defaults_to_twelve():
    layout = scene_grid_layout(None)
    assert (layout.panel_count, layout.rows, layout.columns) == (12, 3, 4)


def test_layout_rounds_up_and_caps():
    assert scene_grid_layout(5).panel_count == 6
    assert scene_grid_layout(13).panel_count == 16
    assert scene_grid_layout(99).panel_count == 16


# ---------------------------------------------------------------- refs


def test_user_character_refs_take_priority():
    ctx = make_ref_ctx()
    refs, used = resolve_reference_images(
        1,
        ctx,
        character_refs=[{"url": "https://example.com/custom.png", "name": "自选"}],
        environment_refs=[],
    )
    char_used = [u for u in used if u["type"] == "character"]
    assert refs[0] == "https://example.com/custom.png"
    assert char_used[0]["source"] == "user"
    assert "https://example.com/along.png" not in refs


def test_character_ref_resolved_from_virtual_ip_id():
    ctx = make_ref_ctx()
    refs, used = resolve_reference_images(
        1,
        ctx,
        character_refs=[{"virtual_ip_id": 7}],
        environment_refs=[],
    )
    assert "https://example.com/along.png" in refs
    assert used[0]["name"] == "阿龙"


def test_auto_refs_from_scene_bindings_and_env_limit():
    ctx = make_ref_ctx()
    refs, used = resolve_reference_images(1, ctx, character_refs=[], environment_refs=[])
    assert "https://example.com/along.png" in refs
    env_used = [u for u in used if u["type"] == "environment"]
    assert len(env_used) == 2
    assert all(u["source"] == "scene" for u in used)


def test_user_environment_refs_override_auto():
    ctx = make_ref_ctx()
    refs, used = resolve_reference_images(
        1,
        ctx,
        character_refs=[],
        environment_refs=["https://example.com/myenv.png"],
    )
    env_used = [u for u in used if u["type"] == "environment"]
    assert len(env_used) == 1
    assert env_used[0]["source"] == "user"


# ---------------------------------------------------------------- durations


def test_cell_durations_pad_to_panel_count():
    durations = cell_durations(make_frames(2), 4)
    assert len(durations) == 4
    assert durations[0] == 1.0


def test_clamp_total_duration_bounds():
    assert clamp_total_duration([1.0] * 30) == 15
    assert clamp_total_duration([1.0]) == 4
    assert clamp_total_duration([1.0] * 10) == 10


# ---------------------------------------------------------------- prompts


def test_sheet_prompt_fallback_without_ai_manager():
    layout = scene_grid_layout(12)
    result = anyio.run(
        lambda: build_sheet_prompt(
            make_script(),
            1,
            make_frames(2),
            make_ref_ctx(),
            layout=layout,
            aspect_ratio="16:9",
            style="写实",
            has_character_refs=True,
            has_environment_refs=False,
            ai_manager=None,
        )
    )
    assert result["prompt_source"] == "fallback"
    assert "【整体版式】" in result["sheet_prompt"]
    assert len(result["cells"]) == 12
    assert result["cells"][0]["panel_index"] == 1


def test_sheet_prompt_uses_llm_output():
    payload = {
        "sheet_prompt": "【整体定位】LLM 宫格提示词",
        "cells": [
            {"panel_index": i, "title": f"镜头{i}", "caption": f"说明{i}"}
            for i in range(1, 13)
        ],
    }

    class Manager:
        async def generate_text(self, **kwargs):
            return SimpleNamespace(
                success=True,
                data=json.dumps(payload, ensure_ascii=False),
                provider="fake",
                model="fake",
            )

    result = anyio.run(
        lambda: build_sheet_prompt(
            make_script(),
            1,
            make_frames(2),
            make_ref_ctx(),
            layout=scene_grid_layout(12),
            aspect_ratio="16:9",
            style=None,
            has_character_refs=False,
            has_environment_refs=False,
            ai_manager=Manager(),
        )
    )
    assert result["prompt_source"] == "llm_dynamic"
    assert result["sheet_prompt"].startswith("【整体定位】")
    assert len(result["cells"]) == 12


def test_video_prompt_fallback_contains_timeline():
    cells = [
        {"panel_index": 1, "title": "醉步入场", "caption": "醉步入场", "duration": 1.0},
        {"panel_index": 2, "title": "饮酒定神", "caption": "饮酒定神", "duration": 0.9},
    ]
    result = anyio.run(
        lambda: build_video_prompt(
            make_script(),
            1,
            cells,
            make_ref_ctx(),
            total_duration=12,
            aspect_ratio="16:9",
            style=None,
            ai_manager=None,
        )
    )
    assert result["prompt_source"] == "fallback"
    assert "镜头1" in result["video_prompt"]
    assert "不得出现分镜格子" in result["video_prompt"]
