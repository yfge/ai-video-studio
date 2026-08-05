from app.services.story.story_novel_incremental_plan import build_chapter_skeletons
from app.services.story.story_novel_v3_prompts import chapter_package_prompt


def _canon():
    return {
        "entities": [
            {
                "id": "obj-joint-ledger",
                "kind": "object",
                "name": "共同账本",
                "aliases": ["长期账册"],
                "attributes": {},
            },
            {
                "id": "loc-qinghe-market",
                "kind": "location",
                "name": "青禾县粮市",
                "aliases": [],
                "attributes": {},
            },
        ],
        "initial_state": {
            "obj-joint-ledger": {"status": "not_created", "owner_id": None},
            "loc-qinghe-market": {"status": "active"},
        },
        "milestones": [],
        "timeline": [],
    }


def _chapter(position: int, end_state: str):
    return {
        "position": position,
        "title": f"第{position}章",
        "goal": "推进当前事件",
        "key_events": ["两人处理眼前的经营选择。"],
        "character_focus": [],
        "open_threads": [],
        "end_state": end_state,
        "min_chars": 2000,
        "target_chars": 2500,
        "max_chars": 3000,
    }


def test_skeleton_binds_conservative_surface_variant_at_first_use():
    chapters = [_chapter(index, "暂未使用账目") for index in range(1, 5)]
    chapters.append(_chapter(5, "第一本共同账目开始使用。"))

    rows = build_chapter_skeletons(_canon(), {"chapters": chapters}, [])

    assert "obj-joint-ledger" in rows[4]["canon_refs"]
    assert "obj-joint-ledger" in rows[4]["future_guard_entity_ids"]


def test_skeleton_does_not_bind_entity_by_generic_suffix_only():
    rows = build_chapter_skeletons(
        _canon(), {"chapters": [_chapter(1, "双方抵达朔州粮市。")]}, []
    )

    assert "loc-qinghe-market" not in rows[0]["canon_refs"]


def test_chapter_package_requires_first_use_creation_transition():
    prompt = chapter_package_prompt({"current_chapter_skeleton": {}})

    assert "首次让它成为可持续使用" in prompt
    assert "不得延后到后续使用章" in prompt
    assert "不得提前复制未来里程碑终态" in prompt
