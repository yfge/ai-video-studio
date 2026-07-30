from types import SimpleNamespace

from app.services.story import story_novel_prose_length_control as length_control


def test_v2_length_contract_rebuild_keeps_historical_calibration(monkeypatch):
    monkeypatch.setattr(
        length_control,
        "length_observations",
        lambda *_args: [
            {
                "position": position,
                "requested_chars": 2500,
                "actual_chars": 10000,
                "controlled": False,
            }
            for position in range(1, 4)
        ],
    )
    revision = SimpleNamespace(
        business_id="revision-v2",
        model="deepseek-v4-flash",
        continuity_ledger={"chapters": {}},
        generation_plan={},
    )
    prose_input = {
        "chapter_brief": {"beats": [{"beat_id": "B01", "target_chars": 2500}]},
        "chapter_length": {
            "min_chars": 2000,
            "target_chars": 2500,
            "max_chars": 3000,
        },
    }

    control = length_control.build_length_control(
        object(), revision, 4, prose_input, prompt_contract_version=2
    )

    assert control["requested_length"] == {
        "min_chars": 675,
        "target_chars": 750,
        "max_chars": 825,
    }
