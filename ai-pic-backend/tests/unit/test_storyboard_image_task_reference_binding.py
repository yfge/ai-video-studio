from __future__ import annotations

from types import SimpleNamespace

from app.api.v1.endpoints.storyboard.image_task_refs import (
    ImageRefContext,
    build_frame_references,
)


def test_explicit_single_character_filters_other_character_anchor() -> None:
    ctx = ImageRefContext()
    ctx.vip_map = {
        1: SimpleNamespace(name="阿盖儿"),
        2: SimpleNamespace(name="老拐"),
    }
    ctx.name_to_vip_id = {"阿盖儿": 1, "老拐": 2}
    ctx.char_image_map = {
        1: "https://cdn.example/agaier.png",
        2: "https://cdn.example/laoguai.png",
    }
    frame = {
        "characters": ["阿盖儿"],
        "reference_images": [
            "https://cdn.example/agaier.png",
            "https://cdn.example/laoguai.png",
        ],
    }

    refs, notes, character_refs = build_frame_references(
        frame,
        35,
        ctx,
        prompt="阿盖儿按下手机屏幕。",
        reference_images=None,
        labeled_references=None,
    )

    assert refs == ["https://cdn.example/agaier.png"]
    assert character_refs == ["https://cdn.example/agaier.png"]
    assert notes == [{"type": "character", "name": "阿盖儿", "source": "frame"}]


def test_explicit_empty_character_list_does_not_use_scene_cast() -> None:
    ctx = ImageRefContext()
    scene = SimpleNamespace(id=8)
    ctx.scene_by_number[1] = scene
    ctx.scene_char_ids[8] = {2}
    ctx.vip_map = {2: SimpleNamespace(name="老拐")}
    ctx.name_to_vip_id = {"老拐": 2}
    ctx.char_image_map = {2: "https://cdn.example/laoguai.png"}

    refs, notes, character_refs = build_frame_references(
        {"scene_number": 1, "characters": []},
        0,
        ctx,
        prompt="An empty room.",
        reference_images=None,
        labeled_references=None,
    )

    assert refs == []
    assert character_refs == []
    assert notes == []
