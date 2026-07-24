from types import SimpleNamespace

from app.services.story.story_novel_gate_support import premature_plan_violations
from tests.unit.test_story_novel_longform import _canon, _plan_row


def test_deterministic_gate_catches_future_conclusion_without_future_action():
    current = {
        **_plan_row(2),
        "goal": "封存R-17样本并追查未知来源",
        "key_events": ["黎雁采集并封存R-17红尘样本，来源仍未知"],
    }
    future = {
        **_plan_row(19),
        "goal": "完成R-17来源化验",
        "key_events": ["银脊化验确认R-17来自人工增旱阀仓"],
        "required_event_ids": ["event-r17-confirmed"],
    }
    revision = SimpleNamespace(
        generation_plan={
            "schema": "story_novel_generation_plan.v2",
            "canon": _canon(),
            "chapters": [current, future],
        }
    )

    violations = premature_plan_violations(
        revision,
        2,
        "管壁附着增旱阀仓沉积物。黎雁断定R-17只可能来自人为投放。",
    )

    assert [item["message"] for item in violations] == [
        "正文提前完成未来事件: event-r17-confirmed"
    ]


def test_deterministic_gate_allows_uncertain_future_hint():
    current = {
        **_plan_row(2),
        "goal": "封存R-17样本并追查未知来源",
        "key_events": ["黎雁采集并封存R-17红尘样本，来源仍未知"],
    }
    future = {
        **_plan_row(19),
        "goal": "完成R-17来源化验",
        "key_events": ["银脊化验确认R-17来自人工增旱阀仓"],
        "required_event_ids": ["event-r17-confirmed"],
    }
    revision = SimpleNamespace(
        generation_plan={
            "schema": "story_novel_generation_plan.v2",
            "canon": _canon(),
            "chapters": [current, future],
        }
    )

    assert (
        premature_plan_violations(
            revision,
            2,
            "黎雁怀疑R-17可能与人工增旱阀仓有关，但仍待化验。",
        )
        == []
    )


def test_deterministic_gate_allows_explicitly_unconfirmed_future_claim():
    current = {
        **_plan_row(2),
        "goal": "封存R-17样本并追查未知来源",
        "key_events": ["黎雁采集并封存R-17红尘样本，来源仍未知"],
    }
    future = {
        **_plan_row(19),
        "goal": "完成R-17来源化验",
        "key_events": ["银脊化验确认R-17来自人工增旱阀仓"],
        "required_event_ids": ["event-r17-confirmed"],
    }
    revision = SimpleNamespace(
        generation_plan={
            "schema": "story_novel_generation_plan.v2",
            "canon": _canon(),
            "chapters": [current, future],
        }
    )

    assert (
        premature_plan_violations(
            revision,
            2,
            "目前无法确认R-17来自人工增旱阀仓，仍须等待化验。",
        )
        == []
    )


def test_deterministic_gate_ignores_shared_actor_and_verification_verb():
    current = {
        **_plan_row(2),
        "goal": "核对当前路线",
        "key_events": ["岑野确认当前路线安全，但身份仍未知"],
    }
    future = {
        **_plan_row(19),
        "goal": "揭露岑野身份",
        "key_events": ["岑野确认向导身份"],
        "required_event_ids": ["event-guide-revealed"],
    }
    revision = SimpleNamespace(
        generation_plan={
            "schema": "story_novel_generation_plan.v2",
            "canon": _canon(),
            "chapters": [current, future],
        }
    )

    assert (
        premature_plan_violations(
            revision,
            2,
            "岑野确认路线安全，身份仍未知。",
        )
        == []
    )


def test_deterministic_gate_allows_conclusion_in_current_contract():
    current = {
        **_plan_row(2),
        "goal": "完成R-17来源化验",
        "key_events": ["银脊化验确认R-17来自人工增旱阀仓"],
    }
    future = {
        **_plan_row(19),
        "goal": "公开R-17来源",
        "key_events": ["黎雁向议会公开R-17来自人工增旱阀仓"],
        "required_event_ids": ["event-r17-disclosed"],
    }
    revision = SimpleNamespace(
        generation_plan={
            "schema": "story_novel_generation_plan.v2",
            "canon": _canon(),
            "chapters": [current, future],
        }
    )

    assert (
        premature_plan_violations(
            revision,
            2,
            "银脊化验确认R-17来自人工增旱阀仓。",
        )
        == []
    )


def test_deterministic_gate_catches_exact_irreversible_future_event():
    current = {
        **_plan_row(1),
        "key_events": ["苏砚查看门锁"],
    }
    future = {
        **_plan_row(2),
        "key_events": ["苏砚杀死闻鹿"],
        "required_event_ids": ["event-wen-lu-killed"],
    }
    revision = SimpleNamespace(
        generation_plan={
            "schema": "story_novel_generation_plan.v2",
            "canon": _canon(),
            "chapters": [current, future],
        }
    )

    violations = premature_plan_violations(
        revision,
        1,
        "苏砚杀死闻鹿。门外的人群随即散去。",
    )

    assert [item["message"] for item in violations] == [
        "正文提前完成未来事件: event-wen-lu-killed"
    ]


def test_deterministic_gate_allows_hypothetical_future_event_quote():
    current = {
        **_plan_row(1),
        "key_events": ["苏砚查看门锁"],
    }
    future = {
        **_plan_row(2),
        "key_events": ["苏砚杀死闻鹿"],
        "required_event_ids": ["event-wen-lu-killed"],
    }
    revision = SimpleNamespace(
        generation_plan={
            "schema": "story_novel_generation_plan.v2",
            "canon": _canon(),
            "chapters": [current, future],
        }
    )

    assert (
        premature_plan_violations(
            revision,
            1,
            "守卫否认“苏砚杀死闻鹿”的传言，双方此刻仍在交谈。",
        )
        == []
    )
