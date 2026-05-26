import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.append(str(REPO_ROOT))

from scripts.harness.provider_chain_payloads import (  # noqa: E402
    extract_structured_script,
    scene_durations,
)
from scripts.harness.provider_chain_timeline_payloads import (  # noqa: E402
    attach_timeline_video_assets,
    build_timeline_seed_spec,
)


def test_extract_structured_script_requires_dialogue() -> None:
    content = """
    ```json
    {
      "title": "机甲便利店",
      "logline": "机器人在夜班找回遗失的订单。",
      "characters": [
        {
          "name": "小蓝",
          "role": "主角",
          "appearance_prompt": "圆润蓝色机器人",
          "consistency_anchor": "blue robot, visor eyes, orange scarf"
        }
      ],
      "scenes": [
        {
          "scene_id": "s1",
          "duration_seconds": 4,
          "plot": "小蓝发现订单会自己移动。",
          "dialogue": [{"speaker": "小蓝", "line": "别跑，我还没扫码。"}],
          "image_prompt": "3D cartoon robot in store",
          "video_prompt": "blue robot catches a glowing order ticket"
        }
      ]
    }
    ```
    """

    script = extract_structured_script(content, expected_scene_count=1)

    assert script["title"] == "机甲便利店"
    assert script["scenes"][0]["dialogue"][0]["line"] == "别跑，我还没扫码。"


def test_scene_durations_split_modes() -> None:
    assert scene_durations("smoke") == [4]
    assert scene_durations("full-30s") == [15, 15]


def test_timeline_seed_precedes_video_assets_and_preserves_lineage() -> None:
    script = {
        "title": "机甲便利店",
        "characters": [
            {
                "name": "小蓝",
                "appearance_prompt": "圆润蓝色机器人",
                "consistency_anchor": "blue robot, visor eyes, orange scarf",
            }
        ],
        "scenes": [
            {
                "scene_id": "s1",
                "duration_seconds": 15,
                "plot": "机器人进门。",
                "dialogue": [{"speaker": "小蓝", "line": "我到了。"}],
                "video_prompt": "robot enters",
            },
            {
                "scene_id": "s2",
                "duration_seconds": 15,
                "plot": "机器人解决问题。",
                "dialogue": [{"speaker": "小蓝", "line": "订单归位。"}],
                "video_prompt": "robot solves",
            },
        ],
    }
    clips = [
        {
            "ordinal": 1,
            "clip_id": "video_s1_provider_chain_1_001",
            "duration_seconds": 15,
            "video_url": "https://example.com/a.mp4",
            "image_url": "https://example.com/robot.png",
            "provider": "volcengine",
            "model": "doubao-seedance-2-0-260128",
            "task_id": "task-a",
            "prompt": "robot enters",
            "scene": {
                "scene_id": "s1",
                "plot": "机器人进门。",
                "dialogue": [{"speaker": "小蓝", "line": "我到了。"}],
            },
        },
        {
            "ordinal": 2,
            "clip_id": "video_s2_provider_chain_2_002",
            "duration_seconds": 15,
            "video_url": "https://example.com/b.mp4",
            "image_url": "https://example.com/robot.png",
            "provider": "volcengine",
            "model": "doubao-seedance-2-0-260128",
            "task_id": "task-b",
            "prompt": "robot solves",
            "scene": {
                "scene_id": "s2",
                "plot": "机器人解决问题。",
                "dialogue": [{"speaker": "小蓝", "line": "订单归位。"}],
            },
        },
    ]

    seed = build_timeline_seed_spec(
        "run-1", episode_id=133, script_id=117, script=script
    )
    seed_tracks = {track["track_type"]: track for track in seed["tracks"]}
    seed_video_clips = seed_tracks["video"]["clips"]
    seed_dialogue_clips = seed_tracks["dialogue"]["clips"]
    seed_subtitle_clips = seed_tracks["subtitle"]["clips"]
    spec = attach_timeline_video_assets(seed, clips, "run-1")
    tracks = {track["track_type"]: track for track in spec["tracks"]}
    video_clips = tracks["video"]["clips"]

    assert seed["duration_ms"] == 30000
    assert set(seed_tracks) == {"dialogue", "video", "subtitle"}
    assert seed_dialogue_clips[0]["text"] == "小蓝: 我到了。"
    assert seed_subtitle_clips[0]["text"] == "小蓝: 我到了。"
    assert seed_video_clips[0]["placeholder"] is True
    assert "asset_ref" not in seed_video_clips[0]
    assert video_clips[0]["asset_ref"]["url"] == "https://example.com/a.mp4"
    assert video_clips[0]["placeholder"] is False
    assert video_clips[1]["start_ms"] == 15000
    assert video_clips[0]["source_refs"]["dialogue"][0]["line"] == "我到了。"
    assert video_clips[0]["source_refs"]["provider_chain_stage"] == "video_generated"


def test_timeline_asset_attach_fails_on_clip_id_mismatch() -> None:
    script = {
        "characters": [
            {
                "name": "小蓝",
                "appearance_prompt": "圆润蓝色机器人",
                "consistency_anchor": "blue robot",
            }
        ],
        "scenes": [
            {
                "scene_id": "s1",
                "duration_seconds": 4,
                "plot": "机器人进门。",
                "dialogue": [{"speaker": "小蓝", "line": "我到了。"}],
                "video_prompt": "robot enters",
            }
        ],
    }
    seed = build_timeline_seed_spec(
        "run-1", episode_id=133, script_id=117, script=script
    )
    clips = [
        {
            "clip_id": "wrong_clip",
            "video_url": "https://example.com/a.mp4",
            "image_url": "https://example.com/robot.png",
            "provider": "volcengine",
            "model": "doubao-seedance-2-0-260128",
        }
    ]

    with pytest.raises(RuntimeError, match="timeline_asset_lineage_mismatch"):
        attach_timeline_video_assets(seed, clips, "run-1")
