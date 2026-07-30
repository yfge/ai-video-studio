from types import SimpleNamespace

from app.services.story import story_novel_prose_length_control as length_control
from app.services.story.story_novel_prompt_renderer import prompt_template_evidence
from app.services.story.story_novel_prose_length_control import (
    build_length_control,
    controlled_prompt_input,
    record_length_observation,
    valid_length_control,
)
from app.services.story.story_novel_prose_length_policy import activate_length_control
from app.services.story.story_novel_v3_prompts import prose_blocks_prompt


def test_model_prompt_exposes_only_one_length_contract(monkeypatch):
    monkeypatch.setattr(
        length_control,
        "length_observations",
        lambda *_args: [_sample(1, 4000), _sample(2, 4000), _sample(3, 4000)],
    )
    source = _prose_input()
    control = build_length_control(object(), _revision(), 4, source)

    prompt_input = controlled_prompt_input(source, control)

    assert prompt_input["chapter_length"] == control["requested_length"]
    assert [
        item["target_chars"] for item in prompt_input["chapter_brief"]["beats"]
    ] == [item["target_chars"] for item in control["requested_blocks"]]
    assert control["acceptance_length"] == source["chapter_length"]
    assert source["chapter_length"]["target_chars"] == 2500


def test_v1_persisted_prompt_evidence_remains_replayable(monkeypatch):
    monkeypatch.setattr(length_control, "length_observations", lambda *_args: [])
    source = _prose_input()
    revision = _revision()
    legacy = build_length_control(
        object(), revision, 1, source, prompt_contract_version=1
    )
    prompt_input = controlled_prompt_input(source, legacy)
    metrics = {
        "calls": 1,
        "invocation_ids": [7],
        "attempts": [
            {
                "invocation_id": 7,
                "call_scene": "story_novel.revision-contract.prose.1",
                "response_hash": "response-v1",
                "prompt_template": prompt_template_evidence(
                    prose_blocks_prompt(prompt_input)
                ),
            }
        ],
    }
    stored = record_length_observation(
        metrics, legacy, {"content_text": "田" * 2500, "char_count": 2500}, prompt_input
    )
    activate_length_control(revision, 1)
    monkeypatch.setattr(
        length_control,
        "reconstruct_initial_prose",
        lambda *_args: {
            key: stored["length_control"][key]
            for key in (
                "initial_prose_body_hash",
                "observed_output_chars",
                "source_invocation_ids",
                "source_response_hashes",
            )
        },
    )

    assert "prompt_contract_version" not in legacy
    assert prompt_input["chapter_length"]["target_chars"] == 2500
    assert valid_length_control(object(), revision, 1, source, stored)


def _sample(position, actual):
    return {
        "position": position,
        "body_hash": f"body-{actual}",
        "source_hash": f"source-{actual}",
        "invocation_ids": [position],
        "requested_chars": 2500,
        "actual_chars": actual,
        "controlled": False,
    }


def _revision():
    return SimpleNamespace(
        business_id="revision-contract",
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
