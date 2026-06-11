"""Shared fakes/factories for dynamic prompt tests."""

from __future__ import annotations

import json
from types import SimpleNamespace


class FakeRefContext:
    def __init__(self):
        self.scene_by_number = {}
        self.scene_char_ids = {}
        self.vip_map = {}
        self.name_to_vip_id = {}


def make_script(**overrides):
    story = SimpleNamespace(
        title="醉拳",
        genre="武侠",
        theme="醉中藏劲",
        world_building="旧港风酒肆江湖",
    )
    episode = SimpleNamespace(story=story, title="酒馆夜斗", episode_number=1)
    defaults = {
        "episode": episode,
        "scenes": [
            {
                "scene_number": 1,
                "location": "酒馆外",
                "time": "夜",
                "description": "主角醉态迎敌",
            }
        ],
        "dialogues": [
            {"scene_number": 1, "content": "你喝多了吧"},
            {"scene_number": 2, "content": "别的场景的话"},
        ],
        "stage_directions": [{"scene_number": 1, "content": "敌人从两侧逼近"}],
    }
    defaults.update(overrides)
    return SimpleNamespace(**defaults)


def make_frames():
    return [
        {
            "scene_number": 1,
            "shot_type": "中远景",
            "camera_movement": "推",
            "composition": "三分法",
            "duration_seconds": 1.0,
            "description": "醉步入场",
        },
        {
            "scene_number": 1,
            "shot_type": "特写",
            "camera_movement": "固定",
            "composition": "中心",
            "duration_seconds": 0.9,
            "description": "仰头喝酒",
        },
    ]


def make_ref_ctx():
    ctx = FakeRefContext()
    scene = SimpleNamespace(id=11)
    ctx.scene_by_number[1] = scene
    ctx.scene_char_ids[11] = {7}
    ctx.vip_map[7] = SimpleNamespace(
        name="阿龙", description="30岁武者，旧布衣短打", style_prompt=None
    )
    ctx.name_to_vip_id["阿龙"] = 7
    return ctx


class FakeAIManager:
    def __init__(self, payloads):
        self.payloads = list(payloads)
        self.calls = 0

    async def generate_text(self, **kwargs):
        self.calls += 1
        payload = self.payloads.pop(0) if self.payloads else None
        if payload is None:
            return SimpleNamespace(success=False, data=None, error="empty")
        return SimpleNamespace(
            success=True,
            data=json.dumps(payload, ensure_ascii=False),
            provider="fake",
            model="fake-model",
        )


def llm_payload(indexes):
    return {
        "frames": [
            {
                "frame_index": idx,
                "image_prompt": f"image prompt {idx}",
                "start_keyframe_prompt": f"start prompt {idx}",
                "end_keyframe_prompt": f"end prompt {idx}",
            }
            for idx in indexes
        ]
    }
