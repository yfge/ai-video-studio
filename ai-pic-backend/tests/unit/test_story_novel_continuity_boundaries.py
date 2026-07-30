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
