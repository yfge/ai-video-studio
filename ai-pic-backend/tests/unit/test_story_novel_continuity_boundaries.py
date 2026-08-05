import json

from app.services.story.story_novel_continuity_contract import (
    normalize_continuity_report,
)
from app.services.story.story_novel_continuity_service import _windows


def test_continuity_windows_overlap_every_six_chapter_boundary():
    chapters = list(range(1, 14))

    assert _windows(chapters) == [
        [1, 2, 3, 4, 5, 6],
        [6, 7, 8, 9, 10, 11, 12],
        [12, 13],
    ]


def test_orphan_reported_blocker_is_not_promoted_without_source_evidence():
    report = normalize_continuity_report(
        json.dumps(
            {
                "summary": "有阻断",
                "issues": [],
                "blocking_issues": ["时间线冲突"],
            },
            ensure_ascii=False,
        ),
        "global",
        include_editorial=True,
    )

    assert report["blocking_issues"] == []
    assert report["issues"] == []


def test_blocking_issue_without_two_sided_evidence_is_downgraded():
    report = normalize_continuity_report(
        json.dumps(
            {
                "summary": "证据不足",
                "issues": [
                    {
                        "id": "travel",
                        "severity": "blocking",
                        "chapter_business_ids": ["chapter-1", "chapter-2"],
                        "evidence_refs": [
                            {
                                "chapter_business_id": "chapter-1",
                                "sentence_ids": ["S0001"],
                            }
                        ],
                        "message": "两章旅行时间冲突",
                    }
                ],
                "blocking_issues": ["两章旅行时间冲突"],
            },
            ensure_ascii=False,
        ),
        "global",
        include_editorial=True,
        evidence_catalog={
            "chapter-1": {"S0001"},
            "chapter-2": {"S0001"},
        },
    )

    assert report["issues"][0]["severity"] == "warning"
    assert report["issues"][0]["grounding_status"] == "unverified"
    assert report["blocking_issues"] == []


def test_canon_conflict_with_sentence_and_contract_ref_remains_blocking():
    report = normalize_continuity_report(
        json.dumps(
            {
                "summary": "身份冲突",
                "issues": [
                    {
                        "id": "identity",
                        "severity": "blocking",
                        "chapter_business_ids": ["chapter-1"],
                        "evidence_refs": [
                            {
                                "chapter_business_id": "chapter-1",
                                "sentence_ids": ["S0002"],
                            }
                        ],
                        "contract_refs": ["canon:entity:char-a:attributes.gender"],
                        "message": "人物性别与 Canon 冲突",
                    }
                ],
                "blocking_issues": ["人物性别与 Canon 冲突"],
            },
            ensure_ascii=False,
        ),
        "global",
        include_editorial=True,
        evidence_catalog={"chapter-1": {"S0001", "S0002"}},
        contract_catalog={"canon:entity:char-a:attributes.gender"},
    )

    assert report["issues"][0]["severity"] == "blocking"
    assert report["issues"][0]["grounding_status"] == "verified"
    assert report["blocking_issues"] == ["人物性别与 Canon 冲突"]


def test_sampled_global_issue_cannot_create_a_new_blocker():
    report = normalize_continuity_report(
        json.dumps(
            {
                "summary": "全局综合",
                "issues": [
                    {
                        "id": "identity",
                        "severity": "blocking",
                        "chapter_business_ids": ["chapter-1"],
                        "evidence_refs": [
                            {
                                "chapter_business_id": "chapter-1",
                                "sentence_ids": ["S0002"],
                            }
                        ],
                        "contract_refs": ["canon:entity:char-a:attributes.gender"],
                        "message": "抽样证据中的潜在冲突",
                    }
                ],
            },
            ensure_ascii=False,
        ),
        "global",
        evidence_catalog={"chapter-1": {"S0002"}},
        contract_catalog={"canon:entity:char-a:attributes.gender"},
        allow_blocking=False,
    )

    assert report["issues"][0]["severity"] == "warning"
    assert report["issues"][0]["grounding_status"] == "sampled_global"


def test_validated_state_chain_mismatch_is_editorial_not_blocking():
    report = normalize_continuity_report(
        json.dumps(
            {
                "summary": "状态链误判",
                "issues": [
                    {
                        "id": "state-before",
                        "severity": "blocking",
                        "chapter_business_ids": ["chapter-18"],
                        "evidence_refs": [
                            {
                                "chapter_business_id": "chapter-18",
                                "sentence_ids": ["S0001", "S0002"],
                            }
                        ],
                        "contract_refs": [
                            "canon:entity:obj-ledger",
                            "chapter:chapter-18:contract",
                            "chapter:chapter-18:state_before",
                        ],
                        "message": "本章发生的关系变化不同于章前状态",
                    }
                ],
            },
            ensure_ascii=False,
        ),
        "window-3",
        evidence_catalog={"chapter-18": {"S0001", "S0002"}},
        contract_catalog={
            "canon:entity:obj-ledger",
            "chapter:chapter-18:contract",
            "chapter:chapter-18:state_before",
        },
        state_chain_verified=True,
    )

    assert report["issues"][0]["severity"] == "warning"
    assert (
        report["issues"][0]["grounding_status"] == "deterministic_state_chain_verified"
    )


def test_specific_canon_state_conflict_remains_blocking_with_validated_chain():
    report = normalize_continuity_report(
        json.dumps(
            {
                "summary": "Canon 冲突",
                "issues": [
                    {
                        "id": "identity",
                        "severity": "blocking",
                        "chapter_business_ids": ["chapter-1"],
                        "evidence_refs": [
                            {
                                "chapter_business_id": "chapter-1",
                                "sentence_ids": ["S0001"],
                            }
                        ],
                        "contract_refs": ["canon:initial_state:char-a:identity"],
                        "message": "人物身份与 Canon 冲突",
                    }
                ],
            },
            ensure_ascii=False,
        ),
        "window-1",
        evidence_catalog={"chapter-1": {"S0001"}},
        contract_catalog={"canon:initial_state:char-a:identity"},
        state_chain_verified=True,
    )

    assert report["issues"][0]["severity"] == "blocking"
