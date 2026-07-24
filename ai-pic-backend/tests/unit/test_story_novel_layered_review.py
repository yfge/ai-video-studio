import json
from types import SimpleNamespace

import anyio
from app.services.story.story_novel_canon_service import content_hash
from app.services.story.story_novel_continuity_review import compile_report
from app.services.story.story_novel_continuity_service import (
    _review_windows,
    _windows,
    run_layered_continuity,
)
from tests.unit.test_story_novel_continuity_v3 import _ready_v2_revision


def test_layered_review_hard_metric_blocks_model_warning_only_report(
    db_session, monkeypatch
):
    _user, service, revision, _chapter, _canon_value = _ready_v2_revision(db_session)
    ledger = dict(revision.continuity_ledger)
    rows = dict(ledger["chapters"])
    first = dict(rows["1"])
    first["state_validation"] = {
        "status": "passed",
        "violations": [{"code": "duplicate_milestone"}],
    }
    rows["1"] = first
    ledger["chapters"] = rows
    revision.continuity_ledger = ledger
    db_session.commit()
    monkeypatch.setattr(
        "app.services.story.story_novel_continuity_service.revision_local_candidates",
        lambda *_args, **_kwargs: ([], []),
    )
    max_tokens = []

    async def generate(_revision, prompt, **kwargs):
        max_tokens.append(kwargs["max_tokens"])
        if "quality_scores" not in prompt:
            return json.dumps(
                {
                    "summary": "窗口只有提示",
                    "issues": [
                        {
                            "id": "warning-1",
                            "severity": "warning",
                            "chapter_business_ids": [],
                            "message": "轻微节奏问题",
                        }
                    ],
                },
                ensure_ascii=False,
            )
        return json.dumps(
            {
                "summary": "全局无模型阻断项",
                "issues": [],
                "overall_score": 82,
                "quality_scores": {"structure": {"score": 8, "rationale": "结构稳定"}},
                "major_strengths": ["结构稳定"],
                "blocking_issues": [],
                "revision_priorities": [{"priority": "P2", "items": ["压缩中段"]}],
                "repair_groups": [],
            },
            ensure_ascii=False,
        )

    report = anyio.run(
        run_layered_continuity,
        service,
        revision,
        type("Task", (), {"description": ""})(),
        generate,
    )
    assert max_tokens == [5000, 16_000]
    assert report["schema"] == "story_novel_continuity_review.v3"
    assert report["hard_metrics"]["duplicate_milestone_count"] == 1
    assert report["overall_score"] == 82.0
    assert report["quality_scores"]["structure"]["score"] == 8.0
    assert report["reviewer_model"] == revision.model
    assert report["review_batches"][0]["chapters"] == [
        {
            "business_id": _chapter.business_id,
            "content_hash": _chapter.content_hash,
            "position": 1,
        }
    ]
    assert revision.continuity_status == "failed"
    stored = dict(report)
    stored_hash = stored.pop("report_hash")
    assert stored_hash == content_hash(stored)


def test_review_batches_overlap_six_chapter_boundaries_with_hash_coverage():
    chapters = [
        SimpleNamespace(
            business_id=f"chapter-{position}",
            content_hash=f"hash-{position}",
            position=position,
            title=f"第{position}章",
            content_text=f"正文{position}",
        )
        for position in range(1, 49)
    ]
    batches = _windows(chapters)
    assert len(batches) == 8
    assert [row.position for row in batches[0]] == list(range(1, 7))
    assert [row.position for row in batches[1]] == list(range(6, 13))
    assert [row.position for row in batches[-1]] == list(range(42, 49))
    assert [len(batch) for batch in _windows(chapters[:8])] == [6, 3]

    class DB:
        def commit(self):
            pass

    calls = []

    async def generate(_revision, _prompt, **kwargs):
        calls.append(kwargs["max_tokens"])
        return '{"summary":"批次通过","issues":[]}'

    revision = SimpleNamespace(
        story_snapshot={},
        generation_plan={},
        model="openai:gpt-5.6",
    )
    reports = anyio.run(
        _review_windows,
        SimpleNamespace(db=DB()),
        revision,
        SimpleNamespace(description="", status=None),
        chapters,
        generate,
    )
    compiled = compile_report(
        revision,
        chapters,
        reports,
        {
            "summary": "全书通过",
            "issues": [],
            "overall_score": 80,
            "quality_scores": {},
        },
        {},
    )
    refs = [ref for batch in compiled["review_batches"] for ref in batch["chapters"]]
    assert calls == [5000] * 8
    assert {ref["business_id"] for ref in refs} == {row.business_id for row in chapters}
    assert [ref["position"] for ref in refs].count(6) == 2
