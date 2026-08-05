from types import SimpleNamespace

from app.services.story import story_novel_chapter_package_context as package_context


def test_package_input_uses_projected_state_without_raw_ledger_duplication(
    monkeypatch,
):
    projected = {
        "subjects": {
            "char-shen": {
                "location": "loc-north-bay",
                "knowledge": ["fact-current"],
            }
        }
    }
    context = {
        "brief_input": {
            "state_before": {
                **projected,
                "subjects": {
                    **projected["subjects"],
                    "future-unrelated": {"knowledge": ["future-secret"]},
                },
            },
            "state_before_hash": "full-state-hash",
            "planning_evidence": {
                "world_events": [{"evidence_id": "event-19"}],
                "character_memories": [{"evidence_id": "memory-19"}],
            },
            "recent_chapters": [{"position": 19, "summary": "抵达北湾"}],
            "previous_chapter_tail": "只记录水车结构。",
            "prior_ledger": {"19": {"large": "must-not-be-duplicated"}},
            "allowed_entity_ids": ["char-shen", "loc-north-bay"],
            "expected_beat_count": 6,
        },
        "hard_constraints": {
            "current_state": projected,
            "compiled_canon": {"entities": []},
            "approved_story_canon": {},
            "must_not_repeat": {"event_ids": ["event-19-1"]},
        },
        "evidence": {"future_chapter_count_excluded": 28},
    }
    monkeypatch.setattr(
        package_context,
        "build_v3_planning_context",
        lambda *_args: context,
    )
    skeleton = {
        "position": 20,
        "title": "木轮第一次散架",
        "goal": "检验建造能力",
        "key_events": ["水轮散架"],
        "character_focus": ["沈禾"],
        "open_threads": [],
        "end_state": "必须返工",
        "min_chars": 2000,
        "target_chars": 2500,
        "max_chars": 3000,
        "length_source": "profile_default",
        "length": {
            "source": "profile_default",
            "min_chars": 2000,
            "target_chars": 2500,
            "max_chars": 3000,
        },
        "required_event_ids": ["event-20-1"],
        "timeline_event_bindings": {},
    }

    result = package_context.build_package_input(None, None, 20, skeleton)

    assert result["schema"] == "story_novel_chapter_package_input.v3"
    assert result["state_before"] == projected
    assert result["state_before_hash"] == "full-state-hash"
    assert "future-unrelated" not in str(result)
    assert "prior_ledger" not in result
    assert result["prior_world_events"] == [{"evidence_id": "event-19"}]
    assert result["prior_character_memories"] == [{"evidence_id": "memory-19"}]
    assert "effect_review_contracts" not in result


def test_package_input_includes_only_current_soft_progression_arc(monkeypatch):
    context = {
        "brief_input": {
            "state_before": {"subjects": {}},
            "state_before_hash": "state",
            "planning_evidence": {"world_events": [], "character_memories": []},
            "recent_chapters": [],
            "previous_chapter_tail": "",
            "allowed_entity_ids": [],
            "expected_beat_count": 4,
        },
        "hard_constraints": {
            "compiled_canon": {"entities": []},
            "approved_story_canon": {},
            "must_not_repeat": {},
        },
        "evidence": {"future_chapter_count_excluded": 780},
    }
    monkeypatch.setattr(
        package_context, "build_v3_planning_context", lambda *_: context
    )
    revision = SimpleNamespace(
        generation_plan={},
        story_snapshot={
            "story_seed": {
                "structured_outline": {
                    "planning_structure_version": 1,
                    "progression_arcs": [
                        {
                            "arc_id": "arc-001",
                            "title": "当前阶段",
                            "start_position": 1,
                            "end_position": 32,
                            "narrative_goal": "解决当前范围的矛盾",
                            "growth": {
                                "cognition": "认识更大的协作网络",
                                "capability": None,
                                "resources": None,
                                "activity_and_time_scale": None,
                            },
                            "major_entries": ["当前章以后才出现的人物"],
                            "threads": [{"payoff_intent": "未来答案"}],
                        },
                        {
                            "arc_id": "arc-002",
                            "title": "未来秘密阶段",
                            "start_position": 33,
                            "end_position": 64,
                            "narrative_goal": "未来秘密",
                            "growth": {},
                        },
                    ],
                }
            }
        },
    )
    skeleton = {"position": 20, "canon_refs": []}

    result = package_context.build_package_input(None, revision, 20, skeleton)

    assert result["current_progression_arc"]["arc_id"] == "arc-001"
    assert "未来秘密" not in str(result)
    assert "未来答案" not in str(result)
    assert "major_entries" not in result["current_progression_arc"]
