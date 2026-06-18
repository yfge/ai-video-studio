import json
import re
from types import SimpleNamespace

from app.models.script import Episode, Script
from app.services.timeline_shot_plan_payloads import clips_for_track


class _BatchAIManager:
    def __init__(self, spec: dict, *, invalid_attempts: int = 0):
        self.spec = spec
        self.invalid_attempts = invalid_attempts
        self.calls: list[dict] = []
        self.video_by_id = {
            str(clip.get("clip_id")): clip for clip in clips_for_track(spec, "video")
        }

    async def generate_text(self, **kwargs):
        self.calls.append(kwargs)
        if self.invalid_attempts > 0:
            self.invalid_attempts -= 1
            return SimpleNamespace(
                success=True,
                data=json.dumps({"shots": []}, ensure_ascii=False),
                provider="deepseek",
                model="deepseek-v4-flash",
                usage={"completion_tokens": 18},
                metadata={"finish_reason": "stop"},
                error=None,
            )

        clip_ids = _clip_ids_from_prompt(kwargs["prompt"])
        return SimpleNamespace(
            success=True,
            data=json.dumps(
                {
                    "shots": [
                        _valid_shot_for_clip(self.video_by_id[clip_id])
                        for clip_id in clip_ids
                    ]
                },
                ensure_ascii=False,
            ),
            provider="deepseek",
            model="deepseek-v4-flash",
            usage={"completion_tokens": len(clip_ids) * 100},
            metadata={"finish_reason": "stop"},
            error=None,
        )


def _clip_ids_from_prompt(prompt: str) -> list[str]:
    return re.findall(r"'clip_id': '([^']+)'", prompt)


def _large_timeline_spec(episode: Episode, script: Script, *, clip_count: int) -> dict:
    dialogue_clips = []
    video_clips = []
    subtitle_clips = []
    for index in range(clip_count):
        ordinal = index + 1
        start_ms = index * 1000
        end_ms = start_ms + 1000
        scene_id = f"scene_{ordinal:03d}"
        beat_id = f"beat_{ordinal:03d}"
        common = {
            "scene_id": scene_id,
            "beat_id": beat_id,
            "ordinal": ordinal,
            "start_ms": start_ms,
            "end_ms": end_ms,
            "duration_ms": 1000,
            "source": {
                "kind": "audio_timeline_beat",
                "scene_id": scene_id,
                "beat_id": beat_id,
                "audio_timeline_version": 1,
            },
            "source_refs": {
                "scene_beat_id": beat_id,
                "audio_timeline_version": 1,
            },
        }
        dialogue_text = f"机器人: 第 {ordinal} 个时间轴节点。"
        dialogue_clips.append(
            {
                **common,
                "clip_id": f"dialogue_clip_{ordinal:03d}",
                "track_type": "dialogue",
                "text": dialogue_text,
                "speaker_name": "机器人",
            }
        )
        video_clips.append(
            {
                **common,
                "clip_id": f"video_clip_{ordinal:03d}",
                "track_type": "video",
                "text": f"机器人检查第 {ordinal} 个发光节点。",
                "beat_type": "dialogue",
                "placeholder": True,
                "asset_ref": None,
            }
        )
        subtitle_clips.append(
            {
                **common,
                "clip_id": f"subtitle_clip_{ordinal:03d}",
                "track_type": "subtitle",
                "text": dialogue_text,
            }
        )

    return {
        "spec_version": "timeline.v1",
        "episode_id": episode.id,
        "script_id": script.id,
        "version": 1,
        "source_audio_timeline_version": 1,
        "fps": 24,
        "resolution": "1080x1920",
        "duration_ms": clip_count * 1000,
        "source": {"type": "api_test"},
        "tracks": [
            {"track_type": "dialogue", "clips": dialogue_clips},
            {"track_type": "video", "clips": video_clips},
            {"track_type": "subtitle", "clips": subtitle_clips},
        ],
    }


def _create_timeline_with_spec(client, episode: Episode, script: Script, spec: dict):
    response = client.post(
        f"/api/v1/episodes/{episode.id}/timelines",
        json={
            "script_id": script.id,
            "title": "Large Shot Plan Timeline",
            "spec": spec,
            "source_audio_timeline_version": 1,
        },
    )
    assert response.status_code == 200
    return response.json()


def _valid_shot_for_clip(clip: dict) -> dict:
    clip_id = str(clip["clip_id"])
    duration_ms = int(clip["duration_ms"])
    return {
        "clip_id": clip_id,
        "duration_ms": duration_ms,
        "plot": str(clip.get("text") or f"plot for {clip_id}"),
        "dialogue_source": f"机器人: {clip_id}",
        "visual_prompt": f"3D cartoon robot studies {clip_id}",
        "video_prompt": (
            f"Plot: robot studies {clip_id}. Dialogue: 机器人: {clip_id}. "
            "Character: non-real blue robot with LED eyes. Camera: medium shot. "
            "Action: points at a glowing node. Style: 3D cartoon. "
            f"Duration: {duration_ms}ms. Composition: robot center. "
            "Motion timeline: at 0ms robot enters, at 800ms robot points. "
            "Emotional landing: focused discovery."
        ),
        "character_anchor": "non-real blue robot with LED eyes",
        "camera": "medium shot",
        "action": "points at a glowing node",
        "direction_anchor": "clear discovery beat",
        "aesthetic_reference": "stylized 3D animation, soft studio light",
        "shot_type": "medium shot",
        "camera_movement": "subtle push-in",
        "composition_geometry": "robot centered, glowing node lower third",
        "motion_timeline": [
            {"at_ms": 0, "action": "robot enters frame"},
            {"at_ms": min(800, duration_ms), "action": "robot points at node"},
        ],
        "emotional_landing": "focused discovery with warm light",
        "prompt_method": "direction_reference_geometry_timeline_emotion_v1",
    }
