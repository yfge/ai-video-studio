import json

import pytest
from app.services.story.story_novel_arc_slot_contract import parse_arc_package
from tests.unit.test_story_novel_v4_arc_slots import _arc_payload, _target
from tests.unit.test_story_novel_v4_world_roadmap import _chapters


def test_arc_character_slot_must_preserve_required_capabilities():
    target = _target()
    target["character_slots"][0]["required_capabilities"] = ["识别契约"]
    payload = _arc_payload()

    with pytest.raises(ValueError, match="缺少预定能力"):
        parse_arc_package(json.dumps(payload, ensure_ascii=False), _chapters(2), target)

    payload["character_slots"][0]["capabilities"].append("识别契约")
    package = parse_arc_package(
        json.dumps(payload, ensure_ascii=False), _chapters(2), target
    )
    assert "识别契约" in package["instantiated_character_slots"][0]["capabilities"]
