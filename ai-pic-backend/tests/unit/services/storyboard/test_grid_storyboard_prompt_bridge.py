from app.services.storyboard.grid_storyboard_prompt_bridge import (
    build_clip_storyboard_panels,
    build_grid_storyboard_panels,
    build_grid_storyboard_sheet_prompt,
    build_grid_storyboard_video_prompt,
    grid_layout,
)


def test_grid_layout_clamps_to_supported_panel_counts():
    assert grid_layout(1).panel_count == 2
    assert (grid_layout(1).columns, grid_layout(1).rows) == (2, 1)
    assert grid_layout(4).panel_count == 4
    assert (grid_layout(6).columns, grid_layout(6).rows) == (3, 2)
    assert grid_layout(99).panel_count == 9
    assert (grid_layout(99).columns, grid_layout(99).rows) == (3, 3)


def test_build_grid_storyboard_panels_prefers_timeline_shot_plan_prompts():
    timeline_spec = {
        "tracks": [
            {
                "id": "video-main",
                "kind": "video",
                "clips": [
                    {
                        "id": "clip-1",
                        "scene_id": "scene-1",
                        "beat_id": "beat-1",
                        "start_ms": 0,
                        "end_ms": 2800,
                        "source_refs": {
                            "timeline_shot_plan": {
                                "shot_id": "shot-1",
                                "visual_prompt": "林晚站在雨夜门口，霓虹反光，中景",
                                "video_prompt": "镜头缓慢推近，雨水落在她肩头",
                                "direction_anchor": "朝向雨夜门口的孤独寻找",
                                "aesthetic_reference": "IMAX film, Panavision C lens",
                                "composition_geometry": "林晚在左三分线，门框切分右侧负空间",
                                "motion_timeline": [
                                    {"at_ms": 0, "action": "林晚停在门口"},
                                    {"at_ms": 1400, "action": "雨水落在肩头"},
                                    {"at_ms": 2800, "action": "她抬头看向门内"},
                                ],
                                "emotional_landing": "冷雨中的克制孤独",
                            }
                        },
                        "ai_prompt": "fallback image prompt",
                    }
                ],
            }
        ]
    }

    panels = build_grid_storyboard_panels(timeline_spec, panel_count=2)

    assert len(panels) == 1
    panel = panels[0]
    assert panel["panel_index"] == 1
    assert panel["row"] == 1
    assert panel["column"] == 1
    assert panel["clip_id"] == "clip-1"
    assert panel["visual_prompt"] == "林晚站在雨夜门口，霓虹反光，中景"
    assert panel["video_prompt"] == "镜头缓慢推近，雨水落在她肩头"
    assert panel["direction_anchor"] == "朝向雨夜门口的孤独寻找"
    assert panel["aesthetic_reference"] == "IMAX film, Panavision C lens"
    assert panel["composition_geometry"] == "林晚在左三分线，门框切分右侧负空间"
    assert panel["motion_timeline"][2]["at_ms"] == 2800
    assert panel["emotional_landing"] == "冷雨中的克制孤独"
    assert "fallback image prompt" not in panel["storyboard_panel_prompt"]
    assert "Panel 1" in panel["storyboard_panel_prompt"]
    assert "门框切分右侧负空间" in panel["storyboard_panel_prompt"]


def test_build_grid_storyboard_panels_falls_back_to_clip_text():
    timeline_spec = {
        "tracks": [
            {
                "kind": "video",
                "clips": [
                    {
                        "id": "clip-2",
                        "start_ms": 1000,
                        "end_ms": 4000,
                        "text": "她推开会议室大门，众人回头。",
                    }
                ],
            }
        ]
    }

    panels = build_grid_storyboard_panels(timeline_spec, panel_count=4)

    assert panels[0]["visual_prompt"] == "她推开会议室大门，众人回头。"
    assert panels[0]["video_prompt"] == "她推开会议室大门，众人回头。"
    assert panels[0]["duration_ms"] == 3000


def test_build_clip_storyboard_panels_diversifies_clip_text_fallback():
    clip = {
        "clip_id": "video_scene_91_beat_4003_013",
        "scene_id": 91,
        "beat_id": 4003,
        "start_ms": 36260,
        "end_ms": 45444,
        "text": "厨房与开放式餐厅相连。老拐和阿盖儿站在中岛台旁。",
        "source_refs": {},
    }

    panels = build_clip_storyboard_panels(clip, panel_count=4)

    assert len(panels) == 4
    visual_prompts = [panel["visual_prompt"] for panel in panels]
    assert len(set(visual_prompts)) == 4
    assert all("Key moment" not in prompt for prompt in visual_prompts)
    assert "Opening frame" in visual_prompts[0]
    assert "Interaction frame" in visual_prompts[1]
    assert "Detail frame" in visual_prompts[2]
    assert "Closing frame" in visual_prompts[3]
    assert panels[0]["motion_timeline"][0]["at_ms"] == 36260
    assert panels[3]["motion_timeline"][0]["at_ms"] > panels[0]["motion_timeline"][0]["at_ms"]
    assert len({panel["composition_geometry"] for panel in panels}) == 4


def test_grid_sheet_and_video_prompts_constrain_text_and_panel_scope():
    panels = [
        {
            "panel_index": 1,
            "clip_id": "clip-1",
            "visual_prompt": "林晚站在雨夜门口，霓虹反光，中景",
            "video_prompt": "镜头缓慢推近，雨水落在她肩头",
            "direction_anchor": "朝向雨夜门口的孤独寻找",
            "aesthetic_reference": "IMAX film, Panavision C lens",
            "composition_geometry": "林晚在左三分线，门框切分右侧负空间",
            "motion_timeline": [
                {"at_ms": 0, "action": "林晚停在门口"},
                {"at_ms": 2800, "action": "她抬头看向门内"},
            ],
            "emotional_landing": "冷雨中的克制孤独",
        },
        {
            "panel_index": 2,
            "clip_id": "clip-2",
            "visual_prompt": "陈哲坐在车内，侧脸被手机屏照亮",
            "video_prompt": "镜头保持静止，只捕捉他的犹豫表情",
        },
    ]

    sheet_prompt = build_grid_storyboard_sheet_prompt(
        panels,
        style="vertical short-drama, cinematic realism",
    )
    video_prompt = build_grid_storyboard_video_prompt(panels[1])

    assert "2-panel" in sheet_prompt
    assert "2x1" in sheet_prompt
    assert "panel numbers" in sheet_prompt
    assert "No subtitles" in sheet_prompt
    assert "林晚站在雨夜门口" in sheet_prompt
    assert "IMAX film" in sheet_prompt
    assert "门框切分右侧负空间" in sheet_prompt
    assert "0ms 林晚停在门口" in sheet_prompt
    assert "冷雨中的克制孤独" in sheet_prompt
    assert "Use panel 2 only" in video_prompt
    assert "clip-2" in video_prompt
    assert "Generate only this shot" in video_prompt
    assert "镜头保持静止" in video_prompt
