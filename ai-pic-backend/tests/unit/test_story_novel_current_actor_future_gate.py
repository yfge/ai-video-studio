from types import SimpleNamespace

from app.services.story.story_novel_gate_support import premature_plan_violations


def _revision(*, current_actor: bool):
    current = {
        "position": 11,
        "required_event_ids": ["event-11-1"],
        "key_events": ["沈禾在白石集购得两袋谷种"],
        "execution_contracts": (
            [
                {
                    "event_id": "event-11-1",
                    "actor_ids": ["char-shen", "char-seed-vendor"],
                }
            ]
            if current_actor
            else []
        ),
    }
    future = {
        "position": 12,
        "required_event_ids": ["event-12-1"],
        "key_events": ["种贩说明两袋谷种来自不同货路"],
    }
    return SimpleNamespace(
        generation_plan={
            "canon": {
                "entities": [
                    {
                        "id": "char-seed-vendor",
                        "kind": "character",
                        "name": "种贩",
                        "aliases": [],
                    }
                ]
            },
            "chapters": [current, future],
        }
    )


def test_current_execution_actor_is_not_misclassified_as_future_character():
    revision = _revision(current_actor=True)

    assert premature_plan_violations(revision, 11, "种贩递来两袋谷种。") == []


def test_future_character_remains_blocked_without_current_structured_reference():
    revision = _revision(current_actor=False)

    assert premature_plan_violations(revision, 11, "种贩提前登门。") == [
        {
            "code": "canon_violation",
            "message": "正文提前出现计划第 12 章角色: 种贩",
        }
    ]
