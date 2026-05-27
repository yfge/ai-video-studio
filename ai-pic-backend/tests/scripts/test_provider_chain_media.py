import sys
import threading
from pathlib import Path
from types import SimpleNamespace

import pytest
import requests

REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.append(str(REPO_ROOT))

from scripts.harness.provider_chain_media import (  # noqa: E402
    generate_videos_for_timeline,
)


def test_generate_videos_for_timeline_runs_clips_concurrently(monkeypatch) -> None:
    barrier = threading.Barrier(2, timeout=5)
    timeline = {
        "spec": {
            "tracks": [
                {
                    "track_type": "video",
                    "clips": [
                        {
                            "clip_id": "video_scene1_provider_chain_1_001",
                            "duration_ms": 15000,
                            "source_refs": {
                                "timeline_shot_plan": {
                                    "video_prompt": "robot walks",
                                    "dialogue_source": "Bot: walk",
                                    "plot": "robot starts walking",
                                },
                            },
                        },
                        {
                            "clip_id": "video_scene2_provider_chain_2_002",
                            "duration_ms": 15000,
                            "source_refs": {
                                "timeline_shot_plan": {
                                    "video_prompt": "robot smiles",
                                    "dialogue_source": "Bot: smile",
                                    "plot": "robot smiles",
                                },
                            },
                        },
                    ],
                }
            ]
        }
    }
    args = SimpleNamespace(
        api_url="http://localhost:8000",
        timeout_seconds=30,
        video_concurrency=2,
    )
    session = requests.Session()
    session.headers["Authorization"] = "Bearer token"
    image = {"image_url": "https://example.com/robot.png"}
    payload = {"request_chain": [], "key_artifacts": {}}

    def fake_request_json(
        session,
        method,
        url,
        *,
        chain,
        label,
        timeout,
        **kwargs,
    ):
        barrier.wait()
        chain.append(
            {
                "label": label,
                "method": method,
                "url": url,
                "status_code": 200,
                "duration_seconds": 1.0,
                "auth": session.headers.get("Authorization"),
            }
        )
        return {
            "data": {
                "provider": "volcengine",
                "model": "doubao-seedance-2-0-260128",
                "video_url": f"https://example.com/{label}.mp4",
                "metadata": {"task_id": f"task-{label}"},
            }
        }

    monkeypatch.setattr(
        "scripts.harness.provider_chain_media.request_json",
        fake_request_json,
    )

    clips = generate_videos_for_timeline(session, args, timeline, image, payload)

    assert [item["clip_id"] for item in clips] == [
        "video_scene1_provider_chain_1_001",
        "video_scene2_provider_chain_2_002",
    ]
    assert [item["task_id"] for item in clips] == [
        "task-seedance-video-1",
        "task-seedance-video-2",
    ]
    assert [item["label"] for item in payload["request_chain"]] == [
        "seedance-video-1",
        "seedance-video-2",
    ]
    assert {item["auth"] for item in payload["request_chain"]} == {"Bearer token"}
    assert payload["key_artifacts"]["video_generation"]["clip_count"] == 2
    assert payload["key_artifacts"]["video_generation"]["concurrency"] == 2
    assert "wall_time_seconds" in payload["key_artifacts"]["video_generation"]


def test_generate_videos_for_timeline_requires_timeline_shot_plan() -> None:
    timeline = {
        "spec": {
            "tracks": [
                {
                    "track_type": "video",
                    "clips": [{"clip_id": "video_1", "duration_ms": 4000}],
                }
            ]
        }
    }
    args = SimpleNamespace(
        api_url="http://localhost:8000",
        timeout_seconds=30,
        video_concurrency=1,
    )
    payload = {"request_chain": [], "key_artifacts": {}}

    with pytest.raises(RuntimeError, match="missing_timeline_shot_plan"):
        generate_videos_for_timeline(
            requests.Session(),
            args,
            timeline,
            {"image_url": "https://example.com/robot.png"},
            payload,
        )


def test_generate_videos_for_timeline_normalizes_seedance_prompt(monkeypatch) -> None:
    timeline = {
        "spec": {
            "tracks": [
                {
                    "track_type": "video",
                    "clips": [
                        _video_clip(
                            "video_1",
                            "Plot: robot acts\nDialogue: Bot: hi\nAction: wave",
                        )
                    ],
                }
            ]
        }
    }
    args = SimpleNamespace(
        api_url="http://localhost:8000",
        timeout_seconds=30,
        video_concurrency=1,
    )
    payload = {"request_chain": [], "key_artifacts": {}}
    sent_prompts: list[str] = []

    def fake_request_json(
        session,
        method,
        url,
        *,
        chain,
        label,
        timeout,
        **kwargs,
    ):
        sent_prompts.append(kwargs["json"]["prompt"])
        return {
            "data": {
                "provider": "volcengine",
                "model": "doubao-seedance-2-0-260128",
                "video_url": "https://example.com/video.mp4",
                "metadata": {"task_id": "task-1"},
            }
        }

    monkeypatch.setattr(
        "scripts.harness.provider_chain_media.request_json",
        fake_request_json,
    )

    clips = generate_videos_for_timeline(
        requests.Session(),
        args,
        timeline,
        {"image_url": "https://example.com/robot.png"},
        payload,
    )

    assert sent_prompts == ["Plot: robot acts Dialogue: Bot: hi Action: wave"]
    assert clips[0]["prompt_source"] == "timeline_shot_plan.video_prompt"
    assert clips[0]["raw_timeline_video_prompt"] == (
        "Plot: robot acts\nDialogue: Bot: hi\nAction: wave"
    )


def test_generate_videos_for_timeline_preserves_parallel_failure_chain(
    monkeypatch,
) -> None:
    timeline = {
        "spec": {
            "tracks": [
                {
                    "track_type": "video",
                    "clips": [
                        _video_clip("video_1", "robot walks"),
                        _video_clip("video_2", "robot smiles"),
                    ],
                }
            ]
        }
    }
    args = SimpleNamespace(
        api_url="http://localhost:8000",
        timeout_seconds=30,
        video_concurrency=2,
    )
    payload = {"request_chain": [], "key_artifacts": {}}

    def fake_request_json(
        session,
        method,
        url,
        *,
        chain,
        label,
        timeout,
        **kwargs,
    ):
        chain.append(
            {
                "label": label,
                "method": method,
                "url": url,
                "status_code": 400,
                "response_body": '{"detail":"bad prompt"}',
            }
        )
        raise RuntimeError("400 Client Error")

    monkeypatch.setattr(
        "scripts.harness.provider_chain_media.request_json",
        fake_request_json,
    )

    with pytest.raises(RuntimeError, match="400 Client Error"):
        generate_videos_for_timeline(
            requests.Session(),
            args,
            timeline,
            {"image_url": "https://example.com/robot.png"},
            payload,
        )

    assert payload["request_chain"]
    assert payload["request_chain"][0]["label"].startswith("seedance-video-")
    assert payload["request_chain"][0]["response_body"] == '{"detail":"bad prompt"}'


def _video_clip(clip_id: str, prompt: str) -> dict:
    return {
        "clip_id": clip_id,
        "duration_ms": 15000,
        "source_refs": {
            "timeline_shot_plan": {
                "video_prompt": prompt,
                "dialogue_source": "Bot: line",
                "plot": "robot acts",
            },
        },
    }
