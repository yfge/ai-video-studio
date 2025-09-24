import uuid

from app.api.v1.endpoints.scripts import _augment_frames, _merge_frames, _enforce_storyboard_variety


def test_merge_frames_preserves_other_scenes():
    existing = [
        {
            "frame_id": str(uuid.uuid4()),
            "scene_number": 1,
            "frame_number": 1,
            "description": "existing scene 1",
            "generation_source": "legacy",
            "generation_method": "ai",
        },
        {
            "frame_id": str(uuid.uuid4()),
            "scene_number": 2,
            "frame_number": 2,
            "description": "existing scene 2",
            "generation_source": "legacy",
            "generation_method": "ai",
        },
    ]
    new_raw = [
        {"scene_number": 2, "description": "new frame A", "shot_type": "中景"},
        {"scene_number": 2, "description": "new frame B", "shot_type": "近景"},
    ]
    scene_map = {1: {}, 2: {}}

    augmented = _augment_frames(
        new_raw,
        scene_map=scene_map,
        generation_source="ai:test",
        generation_method="direct",
        generation_model="gpt-test",
    )
    merged = _merge_frames(existing, augmented, [2])

    assert len(merged) == 3
    assert merged[0]["scene_number"] == 1
    assert merged[0]["description"] == "existing scene 1"
    assert merged[1]["scene_number"] == 2
    assert merged[2]["scene_number"] == 2
    assert merged[1]["frame_number"] == 2
    assert merged[2]["frame_number"] == 3
    assert merged[1]["generation_source"] == "ai:test"
    assert merged[1]["frame_id"] != merged[2]["frame_id"]
    assert merged[1]["generation_model"] == "gpt-test"


def test_enforce_storyboard_variety_changes_duplicates():
    frames = [
        {
            "scene_number": 1,
            "description": "角色对话",
            "shot_type": "中景",
            "camera_movement": "固定",
            "composition": "三分法",
            "duration_seconds": 3,
            "ai_prompt": "角色对话",
        },
        {
            "scene_number": 1,
            "description": "角色对话",
            "shot_type": "中景",
            "camera_movement": "固定",
            "composition": "三分法",
            "duration_seconds": 3,
            "ai_prompt": "角色对话",
        },
    ]

    diversified = _enforce_storyboard_variety(frames)

    assert diversified[0]["shot_type"] == "中景"
    assert diversified[1]["shot_type"] != diversified[0]["shot_type"]
    assert "变体" in diversified[1]["description"]
    assert diversified[1]["ai_prompt"].startswith(diversified[1]["description"])
