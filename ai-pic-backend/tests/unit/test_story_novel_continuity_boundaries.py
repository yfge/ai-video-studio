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


def test_reported_blocker_is_promoted_to_structured_issue():
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

    assert report["blocking_issues"] == ["时间线冲突"]
    assert report["issues"][0]["severity"] == "blocking"
