import hashlib
from types import SimpleNamespace

from app.services.story import story_novel_v4_approval as approval
from app.services.story.story_novel_context_utils import value_hash


def test_call_snapshot_must_bind_exact_persisted_invocation_input(monkeypatch):
    prompt = "冻结的正文输入"
    row = SimpleNamespace(
        id=7,
        call_scene="story_novel.revision-1.prose.1",
        status="succeeded",
        original_prompt=prompt,
        prompt=prompt,
        response="正文结果",
    )
    repo = SimpleNamespace(
        get_by_id=lambda invocation_id: row if invocation_id == 7 else None
    )
    monkeypatch.setattr(approval, "LLMInvocationRepository", lambda _db: repo)
    revision = SimpleNamespace(business_id="revision-1")
    snapshots = {"prose.1": {"input_hash": value_hash(prompt)}}
    metrics = {
        "prose": {
            "attempts": [
                {
                    "invocation_id": 7,
                    "call_scene": row.call_scene,
                    "status": "succeeded",
                    "response_hash": hashlib.sha256("正文结果".encode()).hexdigest(),
                    "raw_response_hash": hashlib.sha256(
                        "正文结果".encode()
                    ).hexdigest(),
                }
            ]
        }
    }

    assert approval._call_snapshots_bound_to_invocations(
        None, revision, snapshots, metrics
    )
    snapshots["prose.1"]["input_hash"] = value_hash("不同输入")
    assert not approval._call_snapshots_bound_to_invocations(
        None, revision, snapshots, metrics
    )


def test_call_snapshot_cannot_bind_a_different_same_scene_invocation(monkeypatch):
    prompt = "同一提示"
    rows = {
        7: SimpleNamespace(
            id=7,
            call_scene="story_novel.revision-1.prose.1",
            status="succeeded",
            original_prompt=prompt,
            prompt=prompt,
            response="旧响应",
        ),
        8: SimpleNamespace(
            id=8,
            call_scene="story_novel.revision-1.prose.1",
            status="succeeded",
            original_prompt=prompt,
            prompt=prompt,
            response="本轮响应",
        ),
    }
    repo = SimpleNamespace(get_by_id=rows.get)
    monkeypatch.setattr(approval, "LLMInvocationRepository", lambda _db: repo)
    metrics = {
        "prose": {
            "attempts": [
                {
                    "invocation_id": 8,
                    "call_scene": rows[8].call_scene,
                    "status": "succeeded",
                    "response_hash": hashlib.sha256("旧响应".encode()).hexdigest(),
                    "raw_response_hash": hashlib.sha256("旧响应".encode()).hexdigest(),
                }
            ]
        }
    }
    assert not approval._call_snapshots_bound_to_invocations(
        None,
        SimpleNamespace(business_id="revision-1"),
        {"prose.1": {"input_hash": value_hash(prompt)}},
        metrics,
    )
