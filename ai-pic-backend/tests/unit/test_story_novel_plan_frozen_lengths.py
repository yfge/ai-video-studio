import json

import pytest
from app.services.story.story_novel_plan_parser import parse_plan
from tests.unit.test_story_novel_longform import _canon, _plan_row


@pytest.mark.parametrize("provider_target", [None, 9999])
def test_parse_plan_injects_frozen_length_before_strict_schema(provider_target):
    provider_row = _plan_row(1)
    frozen_row = _plan_row(1)
    frozen_row.update(
        {
            "min_chars": 2000,
            "target_chars": 2500,
            "max_chars": 3000,
            "length_source": "chapter_override",
        }
    )
    if provider_target is None:
        provider_row.pop("target_chars")
    else:
        provider_row["target_chars"] = provider_target

    parsed, error = parse_plan(
        json.dumps({"chapters": [provider_row]}, ensure_ascii=False),
        [1],
        _canon(),
        {"chapters": [frozen_row]},
    )

    assert error is None
    assert parsed["chapters"][0]["min_chars"] == 2000
    assert parsed["chapters"][0]["target_chars"] == 2500
    assert parsed["chapters"][0]["max_chars"] == 3000
    assert parsed["chapters"][0]["length_source"] == "chapter_override"
