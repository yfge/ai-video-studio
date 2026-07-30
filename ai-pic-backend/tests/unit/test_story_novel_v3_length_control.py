from types import SimpleNamespace

from app.services.story import story_novel_prose_length_control as length_control
from app.services.story.story_novel_prompt_renderer import prompt_template_evidence
from app.services.story.story_novel_prose_length_control import (
    POLICY_SCHEMA,
    build_length_control,
    controlled_prompt_input,
    record_length_observation,
    valid_length_control,
)
from app.services.story.story_novel_prose_length_history import metric_model, same_model
from app.services.story.story_novel_prose_length_policy import (
    activate_length_control,
    length_control_required,
)
from app.services.story.story_novel_v3_prompts import prose_blocks_prompt


def test_historical_overshoot_scales_only_the_model_facing_copy(monkeypatch):
    monkeypatch.setattr(
        length_control,
        "length_observations",
        lambda *_args: [_sample(position, 10000) for position in range(1, 4)],
    )
    revision = _revision({})
    source = _prose_input()

    control = build_length_control(object(), revision, 4, source)
    prompt_input = controlled_prompt_input(source, control)

    assert control["schema"] == POLICY_SCHEMA
    assert control["sample_source"] == "historical"
    assert control["sample_count"] == 3
    assert [item["position"] for item in control["sample_refs"]] == [1, 2, 3]
    assert control["sample_refs"][0] == {
        "position": 1,
        "body_hash": "body-10000",
        "source_hash": "source-10000",
        "invocation_ids": [10100],
        "requested_chars": 2500,
        "actual_chars": 10000,
        "controlled": False,
    }
    assert control["observed_response_ratio"] == 4.0
    assert control["requested_length"] == {
        "min_chars": 2000,
        "target_chars": 2223,
        "max_chars": 3000,
    }
    assert sum(item["target_chars"] for item in control["requested_blocks"]) == 2223
    assert prompt_input["chapter_length"]["target_chars"] == 2223
    assert (
        prompt_input["generation_length_hints"]["requested_length"]["target_chars"]
        == 2223
    )
    assert (
        sum(item["target_chars"] for item in prompt_input["chapter_brief"]["beats"])
        == 2223
    )
    assert source["chapter_length"]["target_chars"] == 2500
    assert (
        sum(item["target_chars"] for item in source["chapter_brief"]["beats"]) == 2500
    )


def test_fewer_than_three_historical_samples_leave_request_unchanged(monkeypatch):
    monkeypatch.setattr(
        length_control,
        "length_observations",
        lambda *_args: [_sample(1, 5000), _sample(2, 5000)],
    )
    revision = _revision({})

    control = build_length_control(object(), revision, 3, _prose_input())

    assert control["sample_count"] == 0
    assert control["request_scale"] == 1.0
    assert control["requested_length"]["target_chars"] == 2500


def test_controlled_sample_takes_priority_and_recovers_without_oscillation(
    monkeypatch,
):
    controlled = _sample(2, 1375, requested=1375, controlled=True)
    controlled["request_scale"] = 0.55
    monkeypatch.setattr(
        length_control,
        "length_observations",
        lambda *_args: [_sample(1, 5000), controlled],
    )
    revision = _revision({})

    control = build_length_control(object(), revision, 3, _prose_input())

    assert control["sample_source"] == "controlled"
    assert control["sample_count"] == 1
    assert control["request_scale"] == 0.825
    assert control["requested_length"]["target_chars"] == 2223


def test_observation_is_persistable_without_mutating_invocation_attempts(monkeypatch):
    monkeypatch.setattr(length_control, "length_observations", lambda *_args: [])
    control = build_length_control(object(), _revision({}), 1, _prose_input())
    prompt_input = controlled_prompt_input(_prose_input(), control)
    metrics = _metrics(prompt_input)
    result = record_length_observation(
        metrics,
        control,
        {"content_text": "田" * 2700, "char_count": 2700},
        prompt_input,
    )

    assert result["attempts"] == metrics["attempts"]
    assert result["length_control"]["observed_output_chars"] == 2700
    assert result["length_control"]["observed_output_ratio"] == 1.08
    assert len(result["length_control"]["prompt_input_hash"]) == 64
    assert "length_control" not in metrics
    revision = _revision({})
    activate_length_control(revision, 1)
    monkeypatch.setattr(
        length_control,
        "reconstruct_initial_prose",
        lambda *_args: _recorded_evidence(result),
    )
    assert valid_length_control(object(), revision, 1, _prose_input(), result)
    result["length_control"]["observed_output_chars"] = 2600
    assert not valid_length_control(object(), revision, 1, _prose_input(), result)


def test_prompt_template_hash_is_part_of_the_persisted_control_evidence(monkeypatch):
    monkeypatch.setattr(length_control, "length_observations", lambda *_args: [])
    prose_input = _prose_input()
    revision = _revision({})
    control = build_length_control(object(), revision, 1, prose_input)
    prompt_input = controlled_prompt_input(prose_input, control)
    metrics = _metrics(prompt_input)
    result = record_length_observation(
        metrics,
        control,
        {"content_text": "田" * 2500, "char_count": 2500},
        prompt_input,
    )
    activate_length_control(revision, 1)
    monkeypatch.setattr(
        length_control,
        "reconstruct_initial_prose",
        lambda *_args: _recorded_evidence(result),
    )
    result["attempts"][0]["prompt_template"]["rendered_hash"] = "tampered"

    assert not valid_length_control(object(), revision, 1, prose_input, result)


def test_same_model_name_from_another_provider_is_not_a_sample():
    assert not same_model("deepseek:shared-name", "openai:shared-name")


def test_history_without_an_explicit_provider_model_is_not_a_sample():
    assert metric_model({"attempts": []}) is None


def test_activation_requires_telemetry_without_breaking_legacy_entries():
    revision = _revision({})
    assert valid_length_control(object(), revision, 1, _prose_input(), {})

    activate_length_control(revision, 2)

    assert not length_control_required(revision, 1)
    assert length_control_required(revision, 2)
    assert not valid_length_control(object(), revision, 2, _prose_input(), {})
    revision.continuity_ledger["prose_length_control"] = {"schema": "tampered"}
    assert not valid_length_control(object(), revision, 1, _prose_input(), {})


def _sample(position, actual, *, requested=2500, controlled=False):
    return {
        "position": position,
        "body_hash": f"body-{actual}",
        "source_hash": f"source-{actual}",
        "invocation_ids": [100 + actual],
        "requested_chars": requested,
        "actual_chars": actual,
        "controlled": controlled,
    }


def _metrics(prompt_input):
    return {
        "calls": 1,
        "invocation_ids": [7],
        "attempts": [
            {
                "invocation_id": 7,
                "call_scene": "story_novel.revision-test.prose.1",
                "response_hash": "response-hash",
                "prompt_template": prompt_template_evidence(
                    prose_blocks_prompt(prompt_input)
                ),
            }
        ],
    }


def _recorded_evidence(metric):
    stored = metric["length_control"]
    return {
        key: stored[key]
        for key in (
            "initial_prose_body_hash",
            "observed_output_chars",
            "source_invocation_ids",
            "source_response_hashes",
        )
    }


def _revision(chapters):
    positions = [
        {"position": position, "target_chars": 2500}
        for position in range(1, max([int(key) for key in chapters] or [0]) + 2)
    ]
    return SimpleNamespace(
        business_id="revision-test",
        model="deepseek-v4-flash",
        continuity_ledger={"chapters": chapters},
        generation_plan={
            "model_policy": {"prose_model": "deepseek:deepseek-v4-flash"},
            "chapters": positions,
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
