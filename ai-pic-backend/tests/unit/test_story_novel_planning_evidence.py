from app.services.story.story_novel_planning_evidence import rank_planning_evidence


def _chapter(business_id, position):
    return type("Chapter", (), {"business_id": business_id, "position": position})()


def test_character_and_thread_relevance_outrank_unrelated_recent_evidence():
    contract = {
        "goal": "追查盐镜裂缝",
        "key_events": ["苏砚比对裂缝样本"],
        "character_focus": ["苏砚"],
        "open_threads": ["裂缝来源"],
        "payoffs_due": [],
        "knowledge_grants": [],
        "state_transitions": [],
        "location_transitions": [],
        "preconditions": [],
    }
    canon = {
        "entities": [
            {"id": "char-su", "kind": "character", "name": "苏砚"},
            {"id": "char-other", "kind": "character", "name": "闻鹿"},
        ]
    }
    rows = [
        {
            "business_id": "recent-unrelated",
            "source_chapter_business_id": "chapter-9",
            "source_hash": "hash-9",
            "participant_character_ids": ["char-other"],
            "summary": "闻鹿检查天气",
        },
        {
            "business_id": "older-relevant",
            "source_chapter_business_id": "chapter-4",
            "source_hash": "hash-4",
            "participant_character_ids": ["char-su"],
            "summary": "苏砚保留裂缝来源样本",
        },
    ]

    ranked = rank_planning_evidence(
        rows,
        kind="world_event",
        chapter_contract=contract,
        canon=canon,
        prior_chapters=[_chapter("chapter-4", 4), _chapter("chapter-9", 9)],
    )

    assert [item["business_id"] for item in ranked] == [
        "older-relevant",
        "recent-unrelated",
    ]
    assert ranked[0]["planning_rank"]["reasons"] == [
        "recent_prior_chapter",
        "chapter_character",
        "chapter_term",
    ]


def test_memory_is_ranked_for_its_owner_without_leaking_to_prose_contract():
    ranked = rank_planning_evidence(
        [
            {
                "business_id": "memory-a",
                "source_chapter_business_id": "chapter-1",
                "source_hash": "hash-1",
                "character_business_id": "char-a",
                "content": "记住门锁",
            }
        ],
        kind="character_memory",
        chapter_contract={
            "goal": "开门",
            "key_events": [],
            "character_focus": [],
            "open_threads": [],
            "payoffs_due": [],
            "knowledge_grants": [{"character_id": "char-a"}],
            "state_transitions": [],
            "location_transitions": [],
            "preconditions": [],
        },
        canon={"entities": []},
        prior_chapters=[_chapter("chapter-1", 1)],
    )

    assert ranked[0]["planning_rank"]["score"] >= 24
    assert "chapter_character" in ranked[0]["planning_rank"]["reasons"]
