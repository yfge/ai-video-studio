import json

import anyio
from app.services.story.story_novel_canon_service import (
    parse_model_canon,
    validate_generation_plan,
)
from app.services.story.story_novel_planning_phases import (
    checkpoint_canon,
    compile_canon,
    complete_plan,
)
from tests.unit.test_story_novel_longform import _canon, _plan_row, _setup


def _contract() -> dict:
    return {
        "story_seed": {
            "structured_outline": {
                "chapters": [
                    {
                        "position": 1,
                        "key_events": [
                            "第一日，发现线索",
                            "褚蓝公开移交零号风钥",
                            "裴衡宣布九月二十日后季风窗口永久关闭",
                        ],
                        "end_state": "8月3日傍晚，风钥由黎雁保管。",
                    },
                    {
                        "position": 2,
                        "key_events": ["8月10日清晨货列离开澄砂港"],
                    },
                ]
            }
        }
    }


def _filter_payload() -> dict:
    payload = _canon()
    payload["timeline"] = [
        payload["timeline"][0],
        {
            "id": "time-end-state-only",
            "label": "8月3日傍晚的概括标签",
            "order": 2,
            "story_time": "8月3日傍晚",
            "immutable": True,
            "source_chapter_position": 1,
            "source_key_event": "褚蓝公开移交零号风钥",
        },
        {
            "id": "time-departure",
            "label": "改写标签",
            "order": 3,
            "story_time": "8月10日清晨",
            "immutable": True,
            "source_chapter_position": 2,
            "source_key_event": "8月10日清晨货列离开澄砂港",
        },
        {
            "id": "time-deadline-object",
            "label": "未来截止日",
            "order": 4,
            "story_time": "九月二十日",
            "immutable": True,
            "source_chapter_position": 1,
            "source_key_event": "裴衡宣布九月二十日后季风窗口永久关闭",
        },
    ]
    return payload


def test_filter_drops_borrowed_time_but_keeps_event_literal_times():
    canon, error, diagnostics = parse_model_canon(
        json.dumps(_filter_payload(), ensure_ascii=False), _contract()
    )

    assert error is None
    assert [item["id"] for item in canon["timeline"]] == [
        "time-1",
        "time-departure",
        "time-deadline-object",
    ]
    assert canon["timeline"][1]["label"] == "8月10日清晨货列离开澄砂港"
    assert diagnostics == [
        {"id": "time-end-state-only", "reason": "time_not_source_literal"},
    ]


def test_filter_drops_unknown_or_duplicate_source_without_fuzzy_match():
    payload = _canon()
    payload["timeline"][0]["source_chapter_position"] = "not-a-position"
    canon, error, diagnostics = parse_model_canon(
        json.dumps(payload, ensure_ascii=False), _contract()
    )
    assert error is None
    assert canon["timeline"] == []
    assert diagnostics == [{"id": "time-1", "reason": "unknown_source_chapter"}]

    duplicate = _contract()
    duplicate["story_seed"]["structured_outline"]["chapters"][0]["key_events"].append(
        "第一日，发现线索"
    )
    canon, error, diagnostics = parse_model_canon(
        json.dumps(_canon(), ensure_ascii=False), duplicate
    )
    assert error is None
    assert canon["timeline"] == []
    assert diagnostics == [{"id": "time-1", "reason": "source_event_not_exact_unique"}]


def test_planning_filters_model_timelines_once_and_checkpoints_diagnostics(db_session):
    _user, _story, service, revision, task, *_ = _setup(db_session)
    calls = []

    async def generate(_revision, _prompt, **kwargs):
        calls.append(kwargs["max_tokens"])
        return json.dumps(_filter_payload(), ensure_ascii=False)

    canon, diagnostics = anyio.run(
        compile_canon,
        service,
        revision,
        task,
        generate,
        _contract(),
        None,
    )

    assert calls == [16000]
    assert [item["id"] for item in canon["timeline"]] == [
        "time-1",
        "time-departure",
        "time-deadline-object",
    ]
    checkpoint_canon(service, revision, task, canon, diagnostics)
    first = _plan_row(1)
    first.update(
        key_events=[
            "第一日，发现线索",
            "褚蓝公开移交零号风钥",
            "裴衡宣布九月二十日后季风窗口永久关闭",
        ],
        required_event_ids=["event-1", "event-transfer", "event-deadline"],
        canon_refs=["char-a", "time-1", "time-deadline-object"],
        timeline_event_bindings={
            "time-1": "event-1",
            "time-deadline-object": "event-deadline",
        },
    )
    second = _plan_row(2)
    second.update(
        key_events=["8月10日清晨货列离开澄砂港"],
        required_event_ids=["event-2"],
        canon_refs=["char-a", "time-departure"],
        timeline_event_bindings={"time-departure": "event-2"},
    )
    chapters = [first, second]
    validate_generation_plan(canon, chapters)
    plan = complete_plan(service, revision, task, None, canon, chapters)
    assert plan["canon_timeline_filter"] == {
        "dropped": diagnostics,
        "kept_count": 3,
    }
    db_session.expire(revision, ["generation_plan"])
    assert (
        revision.generation_plan["canon_timeline_filter"]
        == plan["canon_timeline_filter"]
    )


def test_planning_drops_all_unsourced_times_without_canon_repair(db_session):
    _user, _story, service, revision, task, *_ = _setup(db_session)
    payload = _filter_payload()
    payload["timeline"] = [payload["timeline"][1]]
    calls = 0

    async def generate(_revision, _prompt, **_kwargs):
        nonlocal calls
        calls += 1
        return json.dumps(payload, ensure_ascii=False)

    canon, diagnostics = anyio.run(
        compile_canon,
        service,
        revision,
        task,
        generate,
        _contract(),
        None,
    )

    assert calls == 1
    assert canon["timeline"] == []
    assert [item["reason"] for item in diagnostics] == ["time_not_source_literal"]


def test_resumed_canon_preserves_existing_filter_diagnostics(db_session):
    _user, _story, service, revision, task, *_ = _setup(db_session)
    canon, error, diagnostics = parse_model_canon(
        json.dumps(_filter_payload(), ensure_ascii=False), _contract()
    )
    assert error is None
    checkpoint_canon(service, revision, task, canon, diagnostics)

    async def must_not_generate(*_args, **_kwargs):
        raise AssertionError("validated Canon must be resumed")

    resumed, resumed_diagnostics = anyio.run(
        compile_canon,
        service,
        revision,
        task,
        must_not_generate,
        _contract(),
        canon,
    )
    assert resumed_diagnostics is None
    checkpoint_canon(service, revision, task, resumed, resumed_diagnostics)
    assert revision.generation_plan["canon_timeline_filter"] == {
        "dropped": diagnostics,
        "kept_count": 3,
    }
