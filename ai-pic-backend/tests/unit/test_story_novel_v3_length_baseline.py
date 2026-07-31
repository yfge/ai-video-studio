from types import SimpleNamespace

from app.services.story import story_novel_prose_length_control as length_control
from app.services.story import story_novel_prose_length_history as length_history
from app.services.story.story_novel_prose_length_history import (
    prior_revision_length_samples,
)
from app.services.story.story_novel_prose_length_policy import (
    activate_length_control,
    valid_length_control_marker,
)


def test_frozen_prior_revision_samples_avoid_new_revision_cold_start():
    revision = _revision()
    samples = [
        _sample("revision-old", 1, 2500, 4900, 1.0),
        _sample("revision-old", 2, 1675, 3300, 0.67),
        _sample("revision-old", 3, 1375, 2800, 0.55),
    ]

    activate_length_control(revision, 1, baseline_samples=samples)
    control = length_control.build_length_control(object(), revision, 1, _prose_input())

    assert control["sample_source"] == "controlled"
    assert control["sample_count"] == 3
    assert control["request_scale"] == 0.507576
    assert control["requested_length"] == {
        "min_chars": 1142,
        "target_chars": 1269,
        "max_chars": 1395,
    }
    assert valid_length_control_marker(revision)


def test_frozen_baseline_is_copied_and_rejects_unproven_rows():
    revision = _revision()
    samples = [_sample("revision-old", 1, 2500, 5000, 1.0)]
    activate_length_control(revision, 1, baseline_samples=samples)
    samples[0]["actual_chars"] = 1

    stored = revision.continuity_ledger["prose_length_control"]["baseline_samples"]
    assert stored[0]["actual_chars"] == 5000
    stored[0].pop("source_revision_business_id")
    assert not valid_length_control_marker(revision)


def test_prior_revision_samples_are_same_story_older_revisions_only(monkeypatch):
    current = _revision()
    older = SimpleNamespace(id=19, revision_number=4, business_id="older")
    newer = SimpleNamespace(id=21, revision_number=6, business_id="newer")
    monkeypatch.setattr(
        length_history,
        "StoryNovelRepository",
        lambda _db: SimpleNamespace(
            story_revisions=lambda story_id: [newer, current, older]
        ),
    )
    monkeypatch.setattr(
        length_history,
        "_revision_observations",
        lambda _db, source, *_args: [
            {
                **_sample(source.business_id, 1, 1400, 2800, 0.56),
                "source_revision_business_id": None,
            }
        ],
    )

    samples = prior_revision_length_samples(
        object(), current, "story_novel_prose_length_control.v1", 2
    )

    assert [item["source_revision_business_id"] for item in samples] == ["older"]


def _sample(revision_id, position, requested, actual, scale):
    return {
        "source_revision_business_id": revision_id,
        "position": position,
        "requested_chars": requested,
        "actual_chars": actual,
        "request_scale": scale,
        "controlled": True,
        "body_hash": f"body-{position}",
        "source_hash": f"source-{position}",
        "invocation_ids": [100 + position],
    }


def _revision():
    return SimpleNamespace(
        business_id="revision-new",
        story_id=9,
        id=20,
        chapter_count=48,
        model="deepseek-v4-flash",
        continuity_ledger={"chapters": {}},
        generation_plan={
            "model_policy": {"prose_model": "deepseek:deepseek-v4-flash"},
            "chapters": [{"position": 1, "target_chars": 2500}],
        },
    )


def _prose_input():
    return {
        "chapter_brief": {
            "beats": [
                {"beat_id": f"B{index:02d}", "target_chars": target}
                for index, target in enumerate((420, 420, 420, 420, 410, 410), 1)
            ]
        },
        "chapter_length": {
            "min_chars": 2000,
            "target_chars": 2500,
            "max_chars": 3000,
        },
    }
