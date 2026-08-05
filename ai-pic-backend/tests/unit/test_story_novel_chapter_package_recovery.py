import json

from app.services.story.story_novel_chapter_package_contract import (
    extract_chapter_package_payload,
)


def test_package_recovers_one_missing_outer_closing_brace():
    payload = {
        "chapter_contract": {"position": 6},
        "chapter_brief": {"beats": [{"beat_id": "B01"}]},
    }
    response = json.dumps(payload, ensure_ascii=False)[:-1]

    assert extract_chapter_package_payload(response) == payload


def test_package_does_not_repair_non_eof_json_damage():
    response = '{"chapter_contract":{} "chapter_brief":{}}'

    assert extract_chapter_package_payload(response) is None


def test_package_does_not_repair_an_incomplete_inner_value():
    response = '{"chapter_contract":{},"chapter_brief":{"beats":['

    assert extract_chapter_package_payload(response) is None


def test_package_recovers_unwrapped_beat_objects_from_real_failure_shape():
    response = """{
      "chapter_contract": {"position": 6},
      "chapter_brief": {
        "beats": [
          "beat_id": "B01",
          "purpose": "发现渠标",
          "target_chars": 1200,
          "bound_event_ids": ["event-6-1"]
          "beat_id": "B02",
          "purpose": "确认人为移动",
          "target_chars": 1300,
          "bound_event_ids": ["event-6-2"]
        ],
        "character_motivations": [
          "character_id": "char-shenhe",
          "motivation": "查清渠标"
          "character_id": "char-guyan",
          "motivation": "核实旧界"
        ],
        "emotional_continuity": "互相试探"
      }"""

    payload = extract_chapter_package_payload(response)

    assert payload["chapter_brief"]["beats"] == [
        {
            "beat_id": "B01",
            "purpose": "发现渠标",
            "target_chars": 1200,
            "bound_event_ids": ["event-6-1"],
        },
        {
            "beat_id": "B02",
            "purpose": "确认人为移动",
            "target_chars": 1300,
            "bound_event_ids": ["event-6-2"],
        },
    ]
    assert payload["chapter_brief"]["character_motivations"] == [
        {"character_id": "char-shenhe", "motivation": "查清渠标"},
        {"character_id": "char-guyan", "motivation": "核实旧界"},
    ]
