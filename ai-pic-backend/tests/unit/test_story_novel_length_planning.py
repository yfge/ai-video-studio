import copy
import json
from types import SimpleNamespace

import pytest
from app.schemas.story_novel_export import (
    NovelLengthRange,
    StoryNovelCreateRevisionRequest,
    StoryNovelLengthSpecUpdateRequest,
)
from app.schemas.story_seed import StorySeedModel, StorySeedStructuredOutline
from app.services.story.story_novel_chapter_gate import chapter_output_tokens
from app.services.story.story_novel_length_service import (
    apply_length_spec,
    build_length_plan,
    generation_plan_hash,
)
from app.services.story.story_outline_positions import explicit_outline_positions
from app.services.story.story_seed_service import ensure_confirmable_seed
from app.services.story.story_seed_structure_service import _parse
from fastapi import HTTPException
from pydantic import ValidationError


def _seed(chapter_count=2):
    ending = "主角重写规则"
    return {
        "schema": "story_seed_v2",
        "title": "潮汐档案馆",
        "premise": "守门人发现真相",
        "outline_text": f"第1章至第{chapter_count}章",
        "structured_outline": {
            "status": "confirmed",
            "version": 3,
            "thread_schedule_version": 1,
            "thread_payoffs": [],
            "chapters": [
                {
                    "position": position,
                    "title": f"第{position}章",
                    "goal": ending if position == chapter_count else "推进冲突",
                    "key_events": [f"事件{position}"],
                    "character_focus": ["主角"],
                    "open_threads": [],
                    "end_state": ending if position == chapter_count else "继续追查",
                }
                for position in range(1, chapter_count + 1)
            ],
        },
        "protagonists": [
            {
                "virtual_ip_business_id": "vip-1",
                "initial_state": "只相信规则",
            }
        ],
        "world_constraints": [],
        "central_conflict": "真相与秩序冲突",
        "ending_direction": ending,
        "content_constraints": [],
    }


def _story(chapter_count=2):
    return SimpleNamespace(
        story_seed=_seed(chapter_count),
        story_seed_status="confirmed",
        story_seed_version=3,
    )


def test_explicit_chapter_range_requires_all_48_rows():
    snapshot = {
        "story_seed": {
            "schema": "story_seed_v1",
            "outline": "第1章至第48章",
        }
    }
    expected = explicit_outline_positions(snapshot)
    assert expected == list(range(1, 49))
    short = {
        "structured_outline": {
            "status": "draft",
            "version": 1,
            "chapters": _seed(8)["structured_outline"]["chapters"],
        }
    }
    parsed, error = _parse(json.dumps(short, ensure_ascii=False), expected)
    assert parsed is None
    assert "expected 1-48" in error


def test_structured_outline_rejects_non_contiguous_positions():
    rows = _seed()["structured_outline"]["chapters"]
    rows[1]["position"] = 3
    with pytest.raises(ValidationError):
        StorySeedStructuredOutline.model_validate(
            {"status": "confirmed", "version": 1, "chapters": rows}
        )


def test_profiles_and_overrides_create_independent_plans():
    short = build_length_plan(
        _story(),
        StoryNovelCreateRevisionRequest(length_profile_id="short_serial"),
    )
    standard = build_length_plan(
        _story(),
        StoryNovelCreateRevisionRequest(
            length_profile_id="standard_serial",
            chapter_length_overrides={
                "2": NovelLengthRange(min_chars=3800, target_chars=4600, max_chars=5200)
            },
        ),
    )
    assert short["version"] == standard["version"] == 4
    assert short["planned_target_chars"] == 4400
    assert standard["planned_target_chars"] == 8600
    assert standard["planned_min_chars"] == 6800
    assert standard["planned_max_chars"] == 10200
    assert standard["chapters"][1]["length_source"] == "chapter_override"
    assert short["outline_hash"] == standard["outline_hash"]


def test_length_update_preserves_frozen_outline_and_extraction_facts():
    story = _story(1)
    plan = build_length_plan(
        story, StoryNovelCreateRevisionRequest(length_profile_id="standard_serial")
    )
    chapter = SimpleNamespace(
        position=1, content_text="字" * 2500, review_status="ready"
    )
    entry = {
        "extraction_status": "ready",
        "event_ids": ["event-1"],
        "memory_ids": ["memory-1"],
        "body_hash": "body",
        "source_hash": "source",
    }
    revision = SimpleNamespace(
        generation_plan=plan,
        story_snapshot={
            "story_seed": story.story_seed,
            "story_seed_version": story.story_seed_version,
        },
        model=None,
        temperature=0.7,
        chapters=[chapter],
        continuity_ledger={"chapters": {"1": entry}},
        continuity_status="passed",
        continuity_report={"plan_version": 4, "plan_hash": plan["plan_hash"]},
    )
    updated = apply_length_spec(
        revision,
        StoryNovelLengthSpecUpdateRequest(
            length_profile_id="short_serial",
            expected_plan_version=4,
        ),
    )
    assert updated["version"] == 5
    assert updated["chapters"][0]["goal"] == plan["chapters"][0]["goal"]
    assert chapter.review_status == "target_changed"
    after = revision.continuity_ledger["chapters"]["1"]
    assert after["event_ids"] == ["event-1"]
    assert after["extraction_status"] == "ready"
    assert updated["chapters"][0]["actual_chars"] == 2500
    assert updated["chapters"][0]["fact_ids"] == ["event-1"]
    assert updated["chapters"][0]["memory_ids"] == ["memory-1"]
    assert revision.continuity_status == "review_required"
    assert revision.continuity_report["status"] == "stale"


def test_prose_model_cannot_change_after_chapter_body_exists():
    story = _story(1)
    plan = build_length_plan(story, StoryNovelCreateRevisionRequest())
    revision = SimpleNamespace(
        generation_plan=plan,
        story_snapshot={
            "story_seed": story.story_seed,
            "story_seed_version": story.story_seed_version,
        },
        model="deepseek:deepseek-v4-flash",
        chapters=[SimpleNamespace(content_text="已有正文")],
    )

    with pytest.raises(HTTPException, match="不得修改正文模型"):
        apply_length_spec(
            revision,
            StoryNovelLengthSpecUpdateRequest(
                length_profile_id="standard_serial",
                expected_plan_version=4,
                model="deepseek:deepseek-v4-pro",
            ),
        )


def test_ranges_are_strict_and_model_budget_is_not_fixed_16k():
    with pytest.raises(ValidationError):
        NovelLengthRange(min_chars=1.5, target_chars=2, max_chars=3)
    assert (
        chapter_output_tokens(
            {"min_chars": 10000, "target_chars": 15000, "max_chars": 20000}
        )
        > 16000
    )
    with pytest.raises(HTTPException) as exc:
        build_length_plan(
            _story(),
            StoryNovelCreateRevisionRequest(
                length_profile_id="standard_serial", model="doubao-lite-4k"
            ),
        )
    assert exc.value.status_code == 422


def test_plan_hash_covers_canon_and_static_state_contracts():
    plan = build_length_plan(
        _story(),
        StoryNovelCreateRevisionRequest(length_profile_id="standard_serial"),
    )
    plan["canon_hash"] = "a" * 64
    plan["chapters"][0]["required_event_ids"] = ["event-1"]
    before = generation_plan_hash(plan)

    changed_event = copy.deepcopy(plan)
    changed_event["chapters"][0]["required_event_ids"] = ["event-changed"]
    changed_canon = copy.deepcopy(plan)
    changed_canon["canon_hash"] = "b" * 64

    assert generation_plan_hash(changed_event) != before
    assert generation_plan_hash(changed_canon) != before


def test_confirmed_seed_requires_final_chapter_to_cover_ending():
    seed = StorySeedModel.model_validate(_seed())
    ensure_confirmable_seed(seed)
    bad = _seed()
    bad["structured_outline"]["chapters"][-1]["goal"] = "另一个结局"
    bad["structured_outline"]["chapters"][-1]["end_state"] = "另一个结局"
    with pytest.raises(HTTPException) as exc:
        ensure_confirmable_seed(StorySeedModel.model_validate(bad))
    assert "ending_direction" in str(exc.value.detail)
